import math
import random
import sys
import os
import json
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import pygame
import time

# ========== IMPORTACIONES DE SISTEMAS EXTERNOS ==========
from priority_heap import PriorityHeap as ExternalPriorityHeap
from sistemas_tareas import GestorTareas, TipoTarea, Tarea, EstadoCasa
from sistema_coordenadas import SistemaCoordenadas

pygame.init()

ANCHO = 1280
ALTO = 720
FPS = 60
SPRITE_SIZE= 50
numero_npc = 10
CASTILLO = 100
CASAS = 40

# ============= CONFIGURACIÓN =============
MAP_JSON = "exports/got_tiles.json"
ASSETS_DIR = "assets"
MINER_FILE_PREFIX = "sprite_"

# ============= COLORES =============
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS = (128, 128, 128)
GRIS_OSCURO = (50, 50, 50)
DORADO = (255, 215, 0)
ROJO = (220, 20, 60)
CYAN = (0, 255, 255)
VERDE = (0, 255, 0)
NARANJA = (255, 140, 0)
ROSA = (255, 192, 203)
MORADO = (138, 43, 226)
OCEAN_COLOR = (24, 60, 100)
OCEAN_PADDING_RATIO = 0.08

COLORS_TERRAIN = {
    "water": (38, 76, 115),
    "sand": (220, 200, 140),
    "grass": (124, 153, 93),
    "forest": (60, 100, 70),
    "mountain": (125, 120, 115),
    "snow": (245, 245, 245),
}

COLORES_REINOS = [
    (220, 20, 60), (255, 215, 0), (34, 139, 34), (138, 43, 226),
    (255, 140, 0), (64, 224, 208), (70, 130, 180)
]

NOMBRES_REINOS_GOT = ["Norte", "Islas y Ríos", "Valle", "Tierras de la Roca", 
                      "Dominio", "Tierras de la Tormenta", "Dorne"]

# ============= UTILIDADES =============

def point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
    x, y = point
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def get_bounding_rect(polygon: List[List[float]]) -> pygame.Rect:
    if not polygon:
        return pygame.Rect(0, 0, 0, 0)
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)

def find_random_point_in_polygon(bbox: pygame.Rect, poly: List[List[float]], tiles_map=None, pad=0, map_w=0, map_h=0) -> Tuple[int, int]:
    if len(poly) < 3 or bbox.width <= 0 or bbox.height <= 0:
        if len(poly) == 0:
            return 0, 0
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        return int(cx), int(cy)
    tries = 0
    while tries < 200:
        rx = bbox.x + random.randint(0, bbox.width - 1)
        ry = bbox.y + random.randint(0, bbox.height - 1)
        if point_in_polygon((rx, ry), poly):
            if tiles_map is None or not is_water_tile(tiles_map, rx, ry, pad, map_w, map_h):
                return rx, ry
        tries += 1
    cx = sum(p[0] for p in poly) // len(poly)
    cy = sum(p[1] for p in poly) // len(poly)
    return int(cx), int(cy)

def get_random_world_point(world_w: int, world_h: int) -> Tuple[int, int]:
    return random.randint(0, world_w - 1), random.randint(0, world_h - 1)

def paint_destruction(surface: pygame.Surface, center_x: int, center_y: int, radius: int, is_water: bool):
    if radius <= 0:
        return
    lock = pygame.PixelArray(surface)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx*dx + dy*dy <= radius*radius:
                px = center_x + dx
                py = center_y + dy
                if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                    if is_water:
                        lock[px, py] = surface.map_rgb((10, 30, 50))
                    else:
                        lock[px, py] = surface.map_rgb((30, 20, 10))
    del lock

def paint_fire(surface: pygame.Surface, center_x: int, center_y: int, radius: int):
    if radius <= 0:
        return
    lock = pygame.PixelArray(surface)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx*dx + dy*dy <= radius*radius:
                px = center_x + dx
                py = center_y + dy
                if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                    intensity = 255 - (dx*dx + dy*dy) * 255 // (radius*radius)
                    color = (intensity // 2, intensity // 4, 0)
                    lock[px, py] = surface.map_rgb(color)
    del lock

def paint_burned(surface: pygame.Surface, center_x: int, center_y: int, radius: int):
    if radius <= 0:
        return
    lock = pygame.PixelArray(surface)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx*dx + dy*dy <= radius*radius:
                px = center_x + dx
                py = center_y + dy
                if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                    lock[px, py] = surface.map_rgb(NEGRO)
    del lock

def is_water_tile(tiles_map, x: int, y: int, pad: int, map_w: int, map_h: int) -> bool:
    adj_x = x - pad
    adj_y = y - pad
    if adj_x < 0 or adj_y < 0 or adj_x >= map_w or adj_y >= map_h:
        return True
    try:
        return tiles_map[adj_y][adj_x] == "water"
    except:
        return True

# ============= SISTEMA DE SPRITES =============

class SpriteBank:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self._raw: Dict[str, pygame.Surface] = {}
        self._cache_scaled: Dict[Tuple[str, int, int], pygame.Surface] = {}
        self._raw_sequences: Dict[Tuple[str, str], List[pygame.Surface]] = {}
        self._cache_seq_scaled: Dict[Tuple[str, str, int, int, int], pygame.Surface] = {}
        
        self.registry: Dict[str, str] = {
            "npc.minero": "images/miner/sprite_00.png",
            "estr.castillo": "images/castle.png",
            "estr.casa": "images/casa.png",
        }
    
    def has(self, key: str) -> bool:
        fn = self.registry.get(key)
        if not fn:
            return False
        return os.path.exists(os.path.join(self.assets_dir, fn))
    
    def _load_raw(self, key: str) -> Optional[pygame.Surface]:
        if key in self._raw:
            return self._raw[key]
        fn = self.registry.get(key)
        if not fn:
            return None
        path = os.path.join(self.assets_dir, fn)
        if not os.path.exists(path):
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            self._raw[key] = img
            return img
        except:
            return None
    
    def get(self, key: str, target_w: int, target_h: int) -> Optional[pygame.Surface]:
        raw = self._load_raw(key)
        if raw is None:
            return None
        
        ckey = (key, target_w, target_h)
        if ckey in self._cache_scaled:
            return self._cache_scaled[ckey]
        
        surf = pygame.transform.smoothscale(raw, (target_w, target_h))
        self._cache_scaled[ckey] = surf
        return surf
    
    @staticmethod
    def _sorted_sprite_list(folder: str, prefix: str) -> List[str]:
        if not os.path.isdir(folder):
            return []
        rex = re.compile(rf"^{re.escape(prefix)}(\d+)\.png$", re.IGNORECASE)
        items = []
        for fn in os.listdir(folder):
            m = rex.match(fn)
            if m:
                items.append((int(m.group(1)), fn))
        items.sort(key=lambda t: t[0])
        return [os.path.join(folder, fn) for _, fn in items]
    
    def has_sequence(self, folder: str, prefix: str) -> bool:
        files = self._sorted_sprite_list(folder, prefix)
        return len(files) > 0
    
    def _load_sequence_raw(self, folder: str, prefix: str) -> List[pygame.Surface]:
        key = (folder, prefix)
        if key in self._raw_sequences:
            return self._raw_sequences[key]
        frames: List[pygame.Surface] = []
        for path in self._sorted_sprite_list(folder, prefix):
            try:
                frames.append(pygame.image.load(path).convert_alpha())
            except:
                pass
        self._raw_sequences[key] = frames
        return frames
    
    def get_seq_frame(self, folder: str, prefix: str, index: int, target_w: int, target_h: int) -> Optional[pygame.Surface]:
        frames = self._load_sequence_raw(folder, prefix)
        if not frames:
            return None
        idx = index % len(frames)
        
        ckey = (folder, prefix, idx, target_w, target_h)
        if ckey in self._cache_seq_scaled:
            return self._cache_seq_scaled[ckey]
        
        raw = frames[idx]
        surf = pygame.transform.smoothscale(raw, (target_w, target_h))
        self._cache_seq_scaled[ckey] = surf
        return surf

# ============= ENUMS =============

class Profesion(Enum):
    LENADOR = "leñador"
    CONSTRUCTOR = "constructor"
    HERRERO = "herrero"
    MILITAR = "militar"
    MINERO = "minero"
    AGRICULTOR = "agricultor"
    GANADERO = "ganadero"
    COMERCIANTE = "comerciante"
    PESCADOR = "pescador"
    DIPLOMATA = "diplomata"

PROFESSION_TO_FOLDER = {
    Profesion.LENADOR: "lenador",
    Profesion.CONSTRUCTOR: "constructor",
    Profesion.HERRERO: "herrero",
    Profesion.MILITAR: "militar",
    Profesion.MINERO: "miner",
    Profesion.AGRICULTOR: "medieval_farmer_frames",
    Profesion.GANADERO: "medieval_farmer_frames",
    Profesion.COMERCIANTE: "comerciante",
    Profesion.PESCADOR: "pescador",
    Profesion.DIPLOMATA: "king",
}

# ============= MAPEO PROFESIÓN -> TIPOTAREA =============
PROFESION_A_TIPOTAREA = {
    Profesion.LENADOR: TipoTarea.CARPINTERIA,
    Profesion.CONSTRUCTOR: TipoTarea.CONSTRUCCION,
    Profesion.HERRERO: TipoTarea.HERRERIA,
    Profesion.MILITAR: TipoTarea.ENTRENAMIENTO,
    Profesion.MINERO: TipoTarea.MINERIA,
    Profesion.AGRICULTOR: TipoTarea.AGRICULTURA,
    Profesion.GANADERO: TipoTarea.CAZA,
    Profesion.COMERCIANTE: TipoTarea.COMERCIO,
    Profesion.PESCADOR: TipoTarea.PESCA,
    Profesion.DIPLOMATA: TipoTarea.ADMINISTRACION,
}

class EventoGlobal(Enum):
    NORMAL = "Normal"
    LLUVIA = "Lluvia"
    SOL_INTENSO = "Sol Intenso"
    NIEVE = "Nevada"
    FESTIVAL = "Festival"
    TORMENTA = "Tormenta"
    RAYO = "Rayo"
    DRAGON = "DRAGON"
    HAMBRUNA = "Hambruna"
    EPIDEMIA = "Epidemia"

class TipoRecurso(Enum):
    MADERA = "madera"
    PIEDRA = "piedra"
    ALIMENTO = "alimento"
    HIERRO = "hierro"
    ARMAS = "armas"

class EstadoCivil(Enum):
    SOLTERO = "Soltero/a"
    CASADO = "Casado/a"
    VIUDO = "Viudo/a"

class RelacionDiplomatica(Enum):
    ALIANZA = "Alianza"
    NEUTRAL = "Neutral"
    TENSION = "Tensión"
    GUERRA = "Guerra"

class Genero(Enum):
    MASCULINO = "Masculino"
    FEMENINO = "Femenino"

class TipoEvento(Enum):
    NACIMIENTO = "nacimiento"
    MUERTE = "muerte"
    BODA = "boda"
    TRABAJO = "trabajo"
    BATALLA = "batalla"
    CONQUISTA = "conquista"
    DIPLOMACIA = "diplomacia"
    EMBARAZO = "embarazo"
    RECUPERACION = "recuperación"
    CLIMA = "clima"
    PRODUCCION = "produccion"
    DESASTRE = "desastre"
    ENFERMEDAD = "enfermedad"

# ============= DATACLASSES =============

@dataclass
class EventoHistorico:
    semana: int
    dia: int
    descripcion: str
    tipo: TipoEvento
    importancia: int = 1
    npcs_involucrados: List[str] = field(default_factory=list)
    reinos_involucrados: List[int] = field(default_factory=list)

@dataclass
class Lesion:
    pie_roto: bool = False
    brazo_roto: bool = False
    enfermedad: bool = False
    herida_grave: bool = False
    embarazada: bool = False
    meses_embarazo: int = 0
    
    def puede_caminar(self) -> bool:
        return not self.pie_roto
    
    def puede_trabajar(self) -> bool:
        if self.brazo_roto or self.herida_grave:
            return False
        if self.embarazada and self.meses_embarazo > 6:
            return False
        return True
    
    def factor_eficiencia(self) -> float:
        factor = 1.0
        if self.pie_roto: factor *= 0.3
        if self.brazo_roto: factor *= 0.4
        if self.enfermedad: factor *= 0.5
        if self.herida_grave: factor *= 0.2
        if self.embarazada: factor *= max(0.6, 1.0 - self.meses_embarazo * 0.05)
        return factor
    
    def descripcion(self) -> str:
        problemas = []
        if self.pie_roto: problemas.append("Pie roto")
        if self.brazo_roto: problemas.append("Brazo roto")
        if self.enfermedad: problemas.append("Enfermo")
        if self.herida_grave: problemas.append("Herida grave")
        if self.embarazada: problemas.append(f"Embarazada {self.meses_embarazo}m")
        return ", ".join(problemas) if problemas else "Saludable"

# ============= RELACIONES =============

class RelacionPersonal:
    def __init__(self, npc1_id: str, npc2_id: str):
        self.npc1_id = npc1_id
        self.npc2_id = npc2_id
        self.amistad = random.uniform(0.3, 0.7)
        self.romance = random.uniform(0.0, 0.3) if random.random() < 0.3 else 0.0
        self.enemistad = 0.0
    
    def mejorar_relacion(self, cantidad: float = 0.1):
        self.amistad = min(1.0, self.amistad + cantidad)
        self.enemistad = max(0.0, self.enemistad - cantidad * 0.5)
        if self.amistad > 0.7:
            self.romance = min(1.0, self.romance + cantidad * 0.5)
    
    def puede_reproducirse(self) -> bool:
        return self.romance > 0.8 and self.amistad > 0.7

class ArbolRelaciones:
    def __init__(self):
        self.relaciones: Dict[str, RelacionPersonal] = {}
    
    def get_key(self, id1: str, id2: str) -> str:
        return f"{min(id1, id2)}_{max(id1, id2)}"
    
    def agregar_relacion(self, id1: str, id2: str):
        key = self.get_key(id1, id2)
        if key not in self.relaciones:
            self.relaciones[key] = RelacionPersonal(id1, id2)
    
    def get_relacion(self, id1: str, id2: str) -> Optional[RelacionPersonal]:
        return self.relaciones.get(self.get_key(id1, id2))
    
    def mejorar_relacion(self, id1: str, id2: str):
        key = self.get_key(id1, id2)
        if key in self.relaciones:
            self.relaciones[key].mejorar_relacion()
    
    def get_parejas_potenciales(self, npc_id: str) -> List[str]:
        parejas = []
        for rel in self.relaciones.values():
            if rel.puede_reproducirse():
                if rel.npc1_id == npc_id:
                    parejas.append(rel.npc2_id)
                elif rel.npc2_id == npc_id:
                    parejas.append(rel.npc1_id)
        return parejas

class DiplomaciaReino:
    def __init__(self, reino1: int, reino2: int):
        self.reino1 = reino1
        self.reino2 = reino2
        self.relacion = RelacionDiplomatica.NEUTRAL
        self.puntos_tension = random.uniform(0, 30)
    
    def mejorar_relacion(self):
        self.puntos_tension = max(0, self.puntos_tension - 20)
        if self.relacion == RelacionDiplomatica.GUERRA and self.puntos_tension < 60:
            self.relacion = RelacionDiplomatica.TENSION
        elif self.relacion == RelacionDiplomatica.TENSION and self.puntos_tension < 30:
            self.relacion = RelacionDiplomatica.NEUTRAL
        elif self.relacion == RelacionDiplomatica.NEUTRAL and self.puntos_tension < 10:
            self.relacion = RelacionDiplomatica.ALIANZA
    
    def empeorar_relacion(self):
        self.puntos_tension += random.uniform(15, 35)
        if self.puntos_tension > 100:
            self.relacion = RelacionDiplomatica.GUERRA
        elif self.puntos_tension > 60:
            self.relacion = RelacionDiplomatica.TENSION
        elif self.puntos_tension > 30:
            self.relacion = RelacionDiplomatica.NEUTRAL

class SistemaDiplomatico:
    def __init__(self, num_reinos: int):
        self.relaciones: Dict[str, DiplomaciaReino] = {}
        for i in range(num_reinos):
            for j in range(i + 1, num_reinos):
                self.relaciones[f"{i}_{j}"] = DiplomaciaReino(i, j)
    
    def get_relacion(self, r1: int, r2: int):#-> #[OptionalDiplomaciaReino]:
        key = f"{min(r1, r2)}_{max(r1, r2)}"
        return self.relaciones.get(key)
    
    def en_guerra(self, r1: int, r2: int) -> bool:
        rel = self.get_relacion(r1, r2)
        return rel.relacion == RelacionDiplomatica.GUERRA if rel else False

# ============= ANIMACIÓN =============

class AnimatedSpriteController:
    def __init__(self, folder: str, prefix: str, fps: float = 6.0):
        self.folder = folder
        self.prefix = prefix
        self.fps = fps
        self.time_acc = 0.0
        self.frame_idx = 0
        self.length = None
    
    def update(self, dt: float, bank: SpriteBank):
        if self.length is None:
            frames = bank._load_sequence_raw(self.folder, self.prefix)
            self.length = max(1, len(frames))
        if self.length <= 1:
            return
        self.time_acc += dt
        step = 1.0 / max(0.1, self.fps)
        while self.time_acc >= step:
            self.time_acc -= step
            self.frame_idx = (self.frame_idx + 1) % self.length
    
    def get_current_frame(self, bank: SpriteBank, w: int, h: int) -> Optional[pygame.Surface]:
        return bank.get_seq_frame(self.folder, self.prefix, self.frame_idx, w, h)

# ============= EFECTOS GLOBALES =============

class GlobalEffect:
    def __init__(self, effect_type: str, x: int, y: int, bank: SpriteBank, world_w: int, world_h: int, pad: int, tiles_map, map_w: int, map_h: int):
        self.type = effect_type
        self.x = x
        self.y = y
        self.bank = bank
        self.world_w = world_w
        self.world_h = world_h
        self.pad = pad
        self.tiles_map = tiles_map
        self.map_w = map_w
        self.map_h = map_h
        self.anim_folder = os.path.join(ASSETS_DIR, "images", self.type)
        self.anim = AnimatedSpriteController(self.anim_folder, "sprite_", fps=12.0 if self.type == "rayo" else 8.0)
        self.time_active = 0.0
        self.duration = 1.0 if self.type == "rayo" else 5.0
        self.radius = 15 if self.type == "rayo" else 25
        self.impact_applied = False
        self.is_water = is_water_tile(tiles_map, x, y, pad, map_w, map_h)

    def update(self, dt: float):
        self.time_active += dt
        self.anim.update(dt, self.bank)
        if self.time_active >= self.duration and not self.impact_applied:
            self.apply_impact()
            self.impact_applied = True
        if self.type == "dragon" and self.time_active < self.duration and hasattr(self, 'world'):
            paint_fire(self.world, self.x, self.y, self.radius)

    def apply_impact(self):
        if not hasattr(self, 'world') or self.world is None:
            return
        if self.type == "rayo":
            paint_destruction(self.world, self.x, self.y, self.radius, self.is_water)
        elif self.type == "dragon":
            paint_burned(self.world, self.x, self.y, self.radius)

    def draw(self, screen: pygame.Surface, cam_x: int, cam_y: int, zoom: float, off_x: int, off_y: int):
        if self.time_active > self.duration:
            return False
        wx = int((self.x - cam_x) * zoom) + off_x
        wy = int((self.y - cam_y) * zoom) + off_y
        target_w = int(SPRITE_SIZE * 2 * zoom)
        target_h = int(SPRITE_SIZE * 2 * zoom)
        img = self.anim.get_current_frame(self.bank, target_w, target_h)
        if img:
            screen.blit(img, (wx - target_w//2, wy - target_h))
        else:
            pygame.draw.circle(screen, ROJO if self.type == "dragon" else CYAN, (wx, wy), int(10 * zoom))

    def check_npc_impact(self, all_npcs: List['NPC'], reino_map: Dict[int, 'Reino']):
        for reino in reino_map.values():
            to_remove = []
            for npc in reino.todos_npcs:
                dist = math.sqrt((npc.x - self.x)**2 + (npc.y - self.y)**2)
                if dist <= self.radius:
                    to_remove.append(npc)
            for npc in to_remove:
                reino.todos_npcs.remove(npc)

# ============= NPC =============

class NPC:
    contador_id = 0
    
    def __init__(self, nombre: str, profesiones: List[Profesion], x: int, y: int, reino: int, 
                 polygon: List[List[float]], tiles_map, genero: Genero = None, 
                 padre_id: str = None, madre_id: str = None, es_rey: bool = False,
                 map_w: int = 1920, map_h: int = 1080, pad: int = 0):
        self.id = f"npc_{NPC.contador_id}"
        NPC.contador_id += 1
        
        self.nombre = nombre
        self.profesiones = profesiones
        self.x = float(x)
        self.y = float(y)
        self.reino = reino
        self.reino_nacimiento = reino
        self.polygon = [[float(px), float(py)] for px, py in polygon]
        self.bounding_rect = get_bounding_rect(self.polygon)
        self.tiles_map = tiles_map
        self.map_w = map_w
        self.map_h = map_h
        self.pad = pad
        self.genero = genero if genero else random.choice(list(Genero))
        self.edad = 0 if padre_id else (random.randint(18, 60) if not es_rey else random.randint(30, 70))
        self.es_rey = es_rey
        
        self.padre_id = padre_id
        self.madre_id = madre_id
        self.es_mestizo = False
        
        self.stamina = 100.0
        self.moral = random.uniform(0.5, 0.9)
        self.estado_animo = random.uniform(0.4, 0.8)
        self.lesiones = Lesion()
        self.estado_civil = EstadoCivil.SOLTERO
        self.pareja_id: Optional[str] = None
        self.hijos_ids: List[str] = []
        
        self.dinero = random.randint(5, 50)
        self.hambre = random.uniform(0.3, 0.8)
        
        
        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
        self.tarea_actual: Optional[Tarea] = None  # Cambiado de accion_actual
        self.progreso_tarea = 0.0  # Ahora float 0.0-1.0
        # ===================================================
        
        self.target_x = x
        self.target_y = y
        self.velocidad = 0.8
        self.estado = "idle"
        self.trabajos_completados = 0
        self.semanas_trabajadas = 0
        self.experiencia_guerra = 0
        self.ultimo_evento: Optional[EventoHistorico] = None
        
        self.is_task_path = False
        self.fallos_movimiento = 0

        self.color_base = self.get_color_profesion()
        
        self.anim: Optional[AnimatedSpriteController] = None
        prof_folder = "king" if self.es_rey else PROFESSION_TO_FOLDER.get(self.profesiones[0], "miner")
        self.anim_folder = os.path.join(ASSETS_DIR, "images", prof_folder)
        if os.path.isdir(self.anim_folder):
            self.anim = AnimatedSpriteController(self.anim_folder, "sprite_", fps=6.0)

        # Asegurar posición inicial en tierra
        if not self._is_land(self.x, self.y):
            self.x, self.y = self._get_random_valid_target()
            self.target_x = self.x
            self.target_y = self.y
    
    def get_color_profesion(self) -> Tuple[int, int, int]:
        if not self.profesiones:
            return (200, 200, 200)
        colores = {
            Profesion.LENADOR: (139, 69, 19),
            Profesion.CONSTRUCTOR: (255, 215, 0),
            Profesion.HERRERO: (192, 192, 192),
            Profesion.MILITAR: (220, 20, 60),
            Profesion.MINERO: (105, 105, 105),
            Profesion.AGRICULTOR: (34, 139, 34),
            Profesion.GANADERO: (160, 82, 45),
            Profesion.COMERCIANTE: (255, 215, 0),
            Profesion.PESCADOR: (70, 130, 180),
            Profesion.DIPLOMATA: (138, 43, 226)
        }
        return colores.get(self.profesiones[0], (200, 200, 200))
    
    def puede_reproducirse(self) -> bool:
        if self.genero == Genero.MASCULINO:
            return self.edad >= 18 and self.edad < 70 and self.estado_civil == EstadoCivil.CASADO
        else:
            return (self.edad >= 18 and self.edad < 45 and 
                   self.estado_civil == EstadoCivil.CASADO and 
                   not self.lesiones.embarazada)
    
    def avanzar_semana(self, todos_npcs: List['NPC'], arbol: ArbolRelaciones):
        self.semanas_trabajadas += 1
        eventos = []
        
        if self.lesiones.embarazada:
            self.lesiones.meses_embarazo += 0.25
            if self.lesiones.meses_embarazo >= 9:
                return self._dar_a_luz(todos_npcs, arbol)
        
        if random.random() < 0.05:
            self.edad += 1
        
        if self.edad > 70 and random.random() < 0.02:
            evento = EventoHistorico(0, 0, f"{self.nombre} falleció a los {self.edad} años", 
                                          TipoEvento.MUERTE, 3, [self.id], [self.reino])
            eventos.append(evento)
            return eventos
        
        self.hambre = max(0.0, self.hambre - random.uniform(0.05, 0.15))
        self.stamina = min(100, self.stamina + 2)
        
        if self.lesiones.pie_roto and random.random() < 0.3:
            self.lesiones.pie_roto = False
        if self.lesiones.enfermedad and random.random() < 0.4:
            self.lesiones.enfermedad = False
        if random.random() < 0.05:
            self.lesiones.enfermedad = True
            self.estado_animo -= 0.2
        
        if self.estado_civil == EstadoCivil.SOLTERO and self.edad >= 18 and random.random() < 0.04:
            parejas_pot = arbol.get_parejas_potenciales(self.id)
            disponibles = [p for p in parejas_pot if any(n.id == p and n.estado_civil == EstadoCivil.SOLTERO and 
                          n.genero != self.genero and n.edad >= 18 for n in todos_npcs)]
            if disponibles:
                pareja_id = random.choice(disponibles)
                pareja = next((n for n in todos_npcs if n.id == pareja_id), None)
                if pareja:
                    self.estado_civil = EstadoCivil.CASADO
                    self.pareja_id = pareja_id
                    pareja.estado_civil = EstadoCivil.CASADO
                    pareja.pareja_id = self.id
                    evento = EventoHistorico(0, 0, f"{self.nombre} y {pareja.nombre} se casaron", 
                                                  TipoEvento.BODA, 2, [self.id, pareja_id], [self.reino, pareja.reino])
                    eventos.append(evento)
        
        if self.puede_reproducirse() and self.pareja_id and random.random() < 0.20:
            pareja = next((n for n in todos_npcs if n.id == self.pareja_id), None)
            if pareja and pareja.puede_reproducirse() and self.genero == Genero.FEMENINO:
                self.lesiones.embarazada = True
                self.lesiones.meses_embarazo = 0
        
        if self.trabajos_completados > 0:
            ganancia = self.trabajos_completados * random.randint(5, 15)
            self.dinero += ganancia
        
        self.trabajos_completados = 0
        return eventos
    
    def _dar_a_luz(self, todos_npcs: List['NPC'], arbol: ArbolRelaciones):
        self.lesiones.embarazada = False
        self.lesiones.meses_embarazo = 0
        
        pareja = next((n for n in todos_npcs if n.id == self.pareja_id), None)
        if not pareja:
            return []
        
        es_mestizo = self.reino != pareja.reino
        
        genero_bebe = random.choice(list(Genero))
        nombres_m = ["Jon", "Robb", "Theon", "Jaime", "Tyrion"]
        nombres_f = ["Sansa", "Arya", "Cersei", "Daenerys", "Margaery"]
        nombre = random.choice(nombres_m if genero_bebe == Genero.MASCULINO else nombres_f) + str(random.randint(100, 999))
        
        profs = [random.choice(list(Profesion))]
        
        bebe = NPC(nombre, profs, int(self.x), int(self.y), self.reino, self.polygon, self.tiles_map,
                  genero=genero_bebe, padre_id=pareja.id if pareja.genero == Genero.MASCULINO else self.id,
                  madre_id=self.id if self.genero == Genero.FEMENINO else pareja.id,
                  map_w=self.map_w, map_h=self.map_h, pad=self.pad)
        bebe.es_mestizo = es_mestizo
        
        self.hijos_ids.append(bebe.id)
        pareja.hijos_ids.append(bebe.id)
        todos_npcs.append(bebe)
        
        evento = EventoHistorico(0, 0, f"Nació {nombre}", 
                               TipoEvento.NACIMIENTO, 3, [self.id, pareja.id, bebe.id], [self.reino])
        return [evento]
    
    # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
    def asignar_tarea(self, tarea: Tarea):
        """Asigna una tarea del nuevo sistema"""
        self.tarea_actual = tarea
        self.progreso_tarea = 0.0
        # Ubicación de la tarea (si existe)
        if tarea.ubicacion and tarea.ubicacion != (0, 0):
            self.target_x, self.target_y = tarea.ubicacion
        else:
            # Punto aleatorio dentro del polígono
            if len(self.polygon) >= 3:
                tx, ty = find_random_point_in_polygon(self.bounding_rect, self.polygon, self.tiles_map, self.pad, self.map_w, self.map_h)
                self.target_x, self.target_y = tx, ty

                if not self._is_land(self.target_x, self.target_y) or not point_in_polygon((self.target_x, self.target_y), self.polygon):
                    self.target_x, self.target_y = self._get_random_valid_target()  # Fallback seguro
                self.fallos_movimiento = 0  # Reset fallos
        self.estado = "moving"
        self.is_task_path = True
    # ===================================================
    
    def _is_land(self, x: float, y: float) -> bool:
        if self.tiles_map is None:
            return True
        try:
            adj_x = int(x - self.pad)
            adj_y = int(y - self.pad)
            if adj_x < 0 or adj_y < 0 or adj_x >= self.map_w or adj_y >= self.map_h:
                return False
            return self.tiles_map[adj_y][adj_x] != "water"
        except (IndexError, KeyError):
            return False

    def _get_random_valid_target(self) -> Tuple[float, float]:
        tries = 0
        while tries < 100:
            cand_tx = self.bounding_rect.x + random.randint(0, self.bounding_rect.width - 1)
            cand_ty = self.bounding_rect.y + random.randint(0, self.bounding_rect.height - 1)
            if point_in_polygon((cand_tx, cand_ty), self.polygon) and self._is_land(cand_tx, cand_ty):
                return float(cand_tx), float(cand_ty)
            tries += 1
        return self.x, self.y
    
    def actualizar(self, dt: float, bank: SpriteBank):
        if self.anim:
            moving = self.estado == "moving"
            self.anim.fps = 6.0 if moving else 2.0
            self.anim.update(dt, bank)
        
        if self.estado == "idle":
            self.stamina = min(100, self.stamina + 0.1)
            if random.random() < 0.01 and len(self.polygon) >= 3:
                self.target_x, self.target_y = self._get_random_valid_target()
                self.estado = "moving"
                self.is_task_path = False
        
        elif self.estado == "moving":
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 5:
                self.estado = "working" if self.tarea_actual else "idle"
            else:
                new_x = self.x + (dx / dist) * self.velocidad
                new_y = self.y + (dy / dist) * self.velocidad
                if self._is_land(new_x, new_y) and (len(self.polygon) < 3 or point_in_polygon((new_x, new_y), self.polygon)):
                    self.x = new_x
                    self.y = new_y
                else:
                    self.fallos_movimiento += 1
                    if self.fallos_movimiento >= 5:  # Umbral para extremos
                        # Reespawn aleatorio en reino (tierra + poly)
                        self.x, self.y = find_random_point_in_polygon(self.bounding_rect, self.polygon, self.tiles_map, self.pad, self.map_w, self.map_h)
                        self.target_x, self.target_y = self.x, self.y
                        self.estado = "idle"
                        self.fallos_movimiento = 0
                        if self.tarea_actual:  # Si era task, falla y libera
                            self.tarea_actual = None
                            self.progreso_tarea = 0.0
                        return False  # No completa nada
                    else:
                        self.target_x, self.target_y = self._get_random_valid_target()
                        if math.hypot(self.target_x - self.x, self.target_y - self.y) < 5:
                            self.estado = "idle"
                            self.fallos_movimiento = 0

        
        elif self.estado == "working":
            # Agrega al inicio del bloque (antes de if self.tarea_actual:):
            if not self.tarea_actual:
                self.estado = "idle"
                return False
            if self.tarea_actual:
                # Incremento basado en duración de la tarea
                incremento = dt / (self.tarea_actual.duracion_semanas * 7 * 0.1)  # Escala temporal
                self.progreso_tarea += incremento
                self.stamina = max(0, self.stamina - 0.05)
                
                if self.progreso_tarea >= 1.0:
                    self.trabajos_completados += 1
                    return True
        return False
    
    def terminar_trabajo(self):
        self.tarea_actual = None
        self.progreso_tarea = 0.0
        self.estado = "idle"
        self.is_task_path = False
    
    def dibujar(self, screen: pygame.Surface, bank: SpriteBank, cam_x: int, cam_y: int, 
                zoom: float, off_x: int, off_y: int):
        wx = int((self.x - cam_x) * zoom) + off_x
        wy = int((self.y - cam_y) * zoom) + off_y
        # Agrega este chequeo antes de cualquier dibujo:
        dist_to_cam = math.hypot(self.x - cam_x, self.y - cam_y)
        if dist_to_cam > max(ANCHO, ALTO) * zoom * 1.5: 
            return  

        target_w = int(SPRITE_SIZE * zoom)
        target_h = int(SPRITE_SIZE * zoom)
        
        if self.anim:
            img = self.anim.get_current_frame(bank, target_w, target_h)
            if img:
                screen.blit(img, (wx - target_w//2, wy - target_h))
            else:
                radius = int(8 * zoom)
                pygame.draw.circle(screen, self.color_base, (wx, wy), radius)
        else:
            radius = int(8 * zoom)
            pygame.draw.circle(screen, self.color_base, (wx, wy), radius)
        
        if self.es_rey:
            rey_radius = int(12 * zoom)
            pygame.draw.circle(screen, DORADO, (wx, wy), rey_radius, int(2 * zoom))
        
        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
        if self.estado == "working" and self.tarea_actual:
            barra_ancho = int(20 * zoom)
            barra_y = wy - int(25 * zoom)
            pygame.draw.rect(screen, GRIS_OSCURO, (wx - barra_ancho//2, barra_y, barra_ancho, int(3 * zoom)))
            pygame.draw.rect(screen, VERDE, (wx - barra_ancho//2, barra_y, int(barra_ancho * self.progreso_tarea), int(3 * zoom)))
        # ===================================================
        npc_screen_x = int((self.x - cam_x) * zoom) + off_x
        npc_screen_y = int((self.y - cam_y) * zoom) + off_y
        target_screen_x = int((self.target_x - cam_x) * zoom) + off_x
        target_screen_y = int((self.target_y - cam_y) * zoom) + off_y
        if (0 <= npc_screen_x <= ANCHO and 0 <= npc_screen_y <= ALTO) or (0 <= target_screen_x <= ANCHO and 0 <= target_screen_y <= ALTO):
            # Dibuja línea y círculo solo si visible
            pygame.draw.line(screen, (255, 255, 0), (npc_screen_x, npc_screen_y), (target_screen_x, target_screen_y), int(1 * zoom))  # Grueso menor
            pygame.draw.circle(screen, (255, 255, 0), (target_screen_x, target_screen_y), int(5 * zoom))  # Círculo más pequeño
            
        if self.estado == "moving" and self.tarea_actual and self.is_task_path:
            tx = int((self.target_x - cam_x) * zoom) + off_x
            ty = int((self.target_y - cam_y) * zoom) + off_y
            pygame.draw.line(screen, (255, 255, 0), (wx, wy), (tx, ty), int(2 * zoom))
            pygame.draw.circle(screen, (255, 255, 0), (tx, ty), int(10 * zoom))

# ============= ESTRUCTURAS =============

class Estructura:
    def __init__(self, tipo: str, x: int, y: int, reino: int):
        self.tipo = tipo
        self.x = x
        self.y = y
        self.reino = reino
        self.reino_original = reino
        self.hp = 100
        self.hp_max = 100
        self.destruida = False
        self.nivel_produccion = 100 if tipo in ["sembradio", "ganaderia"] else 0
        self.animales = 10 if tipo == "ganaderia" else 0
    
    def recibir_dano(self, dano: int):
        self.hp -= dano
        if self.hp <= 0:
            self.hp = 0
            self.destruida = True
    
    def reconstruir(self, reparacion: int):
        self.hp += reparacion
        if self.hp > 0:
            self.destruida = False
            self.hp = min(self.hp_max, self.hp)
    
    def cambiar_propietario(self, nuevo_reino: int):
        self.reino = nuevo_reino
    
    def dibujar(self, screen: pygame.Surface, bank: SpriteBank, cam_x: int, cam_y: int, 
                zoom: float, off_x: int, off_y: int, color: Tuple[int, int, int]):
        wx = int((self.x - cam_x) * zoom) + off_x
        wy = int((self.y - cam_y) * zoom) + off_y
        
        if self.destruida:
            line_length = int(16 * zoom)
            pygame.draw.line(screen, GRIS_OSCURO, (wx - line_length//2, wy - int(4 * zoom)), (wx + line_length//2, wy + int(4 * zoom)), int(2 * zoom))
            pygame.draw.line(screen, GRIS_OSCURO, (wx - line_length//2, wy + int(4 * zoom)), (wx + line_length//2, wy - int(4 * zoom)), int(2 * zoom))
            return
        
        target_w = int(100 * zoom)
        target_h = int(100 * zoom)
        if self.tipo != "castillo":
            target_w = int((CASAS * 2) * zoom)
            target_h = int(CASAS * zoom)
        
        key_map = {"castillo": "estr.castillo", "casa": "estr.casa"}
        sprite_key = key_map.get(self.tipo)
        
        if sprite_key and bank.has(sprite_key):
            img = bank.get(sprite_key, target_w, target_h)
            if img:
                screen.blit(img, (wx - target_w//2, wy - target_h))
                if self.hp < self.hp_max:
                    self._dibujar_barra_hp(screen, wx, wy, zoom)
                return
        
        if self.tipo == "castillo":
            size = int(CASTILLO * zoom)
            half_size = size // 2
            pygame.draw.rect(screen, color, (wx - half_size, wy - size, size, size))
            pygame.draw.rect(screen, BLANCO, (wx - half_size, wy - size, size, size), int(2 * zoom))
        else:
            size_w = int(20 * zoom)
            size_h = int(15 * zoom)
            half_w = size_w // 2
            half_h = size_h // 2
            pygame.draw.rect(screen, color, (wx - half_w, wy - half_h, size_w, size_h))
            pygame.draw.rect(screen, BLANCO, (wx - half_w, wy - half_h, size_w, size_h), int(1 * zoom))
        
        if self.hp < self.hp_max:
            self._dibujar_barra_hp(screen, wx, wy, zoom)
    
    def _dibujar_barra_hp(self, screen: pygame.Surface, wx: int, wy: int, zoom: float):
        barra_ancho = int(30 * zoom)
        barra_y = wy - int(35 * zoom)
        pygame.draw.rect(screen, ROJO, (wx - barra_ancho//2, barra_y, barra_ancho, int(4 * zoom)))
        hp_ancho = int(barra_ancho * (self.hp / self.hp_max))
        pygame.draw.rect(screen, VERDE, (wx - barra_ancho//2, barra_y, hp_ancho, int(4 * zoom)))

# ============= ALMACEN (SIMPLIFICADO) =============

class AlmacenCastillo:
    def __init__(self):
        self.recursos: Dict[TipoRecurso, int] = {
            TipoRecurso.MADERA: 500,  # Aumentado para sistema de costos
            TipoRecurso.PIEDRA: 300,
            TipoRecurso.ALIMENTO: 1000,  # Aumentado para sistema de costos
            TipoRecurso.HIERRO: 200,
            TipoRecurso.ARMAS: 100
        }
    
    def agregar(self, recurso: TipoRecurso, cantidad: int):
        self.recursos[recurso] = self.recursos.get(recurso, 0) + cantidad

# ============= REINO =============

class Reino:
    def __init__(self, id: int, nombre: str, color: Tuple[int, int, int], 
                 polygon: List[List[float]], sistema: 'SistemaDiplomatico', tiles_map,
                 map_w: int, map_h: int, pad: int):
        self.id = id
        self.nombre = nombre
        self.color = color
        self.polygon = polygon
        self.bounding_rect = get_bounding_rect(polygon)
        self.tiles_map = tiles_map
        self.map_w = map_w
        self.map_h = map_h
        self.pad = pad
        
        self.casas: List[Estructura] = []
        self.sembradios: List[Estructura] = []
        self.ganaderias: List[Estructura] = []
        self.todos_npcs: List[NPC] = []
        self.almacen = AlmacenCastillo()
        
        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
        # Recursos adicionales para el nuevo sistema
        self.oro = 10000
        self.comida = 1000  # Alias para AlmacenCastillo.ALIMENTO
        self.madera = 500   # Alias para AlmacenCastillo.MADERA
        self.soldados = 5000
        # ===================================================
        
        self.poder_militar = 10
        self.derrotado = False
        self.conquistado_por: Optional[int] = None
        self.razones_guerra: Dict[int, str] = {}
        
        if len(polygon) > 0:
            self.centroid = (sum(p[0] for p in polygon) // len(polygon), sum(p[1] for p in polygon) // len(polygon))
            cx, cy = self.centroid
            
            self.capital = Estructura("castillo", int(cx), int(cy), id)
            
            for _ in range(4):
                rx, ry = find_random_point_in_polygon(self.bounding_rect, self.polygon, self.tiles_map, self.pad, self.map_w, self.map_h)
                self.casas.append(Estructura("casa", rx, ry, id))
            
            for _ in range(3):
                rx, ry = find_random_point_in_polygon(self.bounding_rect, self.polygon, self.tiles_map, self.pad, self.map_w, self.map_h)
                self.sembradios.append(Estructura("sembradio", rx, ry, id))
            
            for _ in range(2):
                rx, ry = find_random_point_in_polygon(self.bounding_rect, self.polygon, self.tiles_map, self.pad, self.map_w, self.map_h)
                self.ganaderias.append(Estructura("ganaderia", rx, ry, id))
            
            self._crear_npcs()
        else:
            self.centroid = (map_w // 2 + random.randint(-100, 100), map_h // 2 + random.randint(-100, 100))
            self.capital = None
            print(f"Warning: {nombre} has empty polygon, no structures or NPCs created.")
    
    def _crear_npcs(self):
        nombres_m = ["Jon", "Robb", "Theon", "Jaime", "Tyrion", "Stannis"]
        nombres_f = ["Sansa", "Arya", "Cersei", "Daenerys", "Margaery", "Brienne"]
        
        if self.capital is None:
            return
        
        genero_rey = random.choice(list(Genero))
        nombre = f"Rey {self.nombre[:6]}" if genero_rey == Genero.MASCULINO else f"Reina {self.nombre[:6]}"
        rey = NPC(nombre, [Profesion.MILITAR], self.capital.x, self.capital.y, self.id, 
                 self.polygon, self.tiles_map, genero=genero_rey, es_rey=True,
                 map_w=self.map_w, map_h=self.map_h, pad=self.pad)
        self.todos_npcs.append(rey)
        
        for i, casa in enumerate(self.casas):
            for j in range(numero_npc):
                genero = random.choice(list(Genero))
                nombre = random.choice(nombres_m if genero == Genero.MASCULINO else nombres_f) + f"{self.id}{i}{j}"
                prof = [random.choice(list(Profesion))]
                rx = casa.x + random.randint(-10, 10)
                ry = casa.y + random.randint(-10, 10)
                # Asegurar posición en tierra
                while is_water_tile(self.tiles_map, rx, ry, self.pad, self.map_w, self.map_h):
                    rx = casa.x + random.randint(-10, 10)
                    ry = casa.y + random.randint(-10, 10)
                npc = NPC(nombre, prof, rx, ry, 
                         self.id, self.polygon, self.tiles_map, genero=genero,
                         map_w=self.map_w, map_h=self.map_h, pad=self.pad)
                self.todos_npcs.append(npc)
    
    def calcular_poder_total(self) -> int:
        if self.derrotado or len(self.polygon) == 0:
            return 0
        poder = self.poder_militar
        poder += self.almacen.recursos.get(TipoRecurso.ARMAS, 0) * 2
        militares = sum(1 for npc in self.todos_npcs if Profesion.MILITAR in npc.profesiones and npc.edad >= 14)
        poder += militares * 5
        return poder
    
    # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
    def sincronizar_recursos(self):
        """Sincroniza recursos entre almacén antiguo y nuevo sistema"""
        self.comida = self.almacen.recursos.get(TipoRecurso.ALIMENTO, 0)
        self.madera = self.almacen.recursos.get(TipoRecurso.MADERA, 0)
        self.oro += self.almacen.recursos.get(TipoRecurso.PIEDRA, 0) * 2  # Conversión piedra->oro
    # ===================================================
    
    def recibir_ataque(self, fuerza: int, atacante: 'Reino') -> Dict:
        if len(self.polygon) == 0:
            self.derrotado = True
            self.conquistado_por = atacante.id
            return {"dano": 0, "estructuras_destruidas": 0, "conquistado": True}
        resultado = {"dano": 0, "estructuras_destruidas": 0, "conquistado": False}
        estructuras = [e for e in self.get_todas_estructuras() if not e.destruida]
        if estructuras:
            estructura = random.choice(estructuras)
            dano = max(5, fuerza + random.randint(-10, 10))
            estructura.recibir_dano(dano)
            resultado["dano"] = dano
            if estructura.destruida:
                resultado["estructuras_destruidas"] = 1
        
        if self.capital and self.capital.destruida:
            self.derrotado = True
            self.conquistado_por = atacante.id
            resultado["conquistado"] = True
        
        return resultado
    
    def get_todas_estructuras(self) -> List[Estructura]:
        if self.capital is None:
            return []
        return [self.capital] + self.casas + self.sembradios + self.ganaderias

# ============= UTILIDADES DE MAPA =============

def load_tiles():
    if not os.path.exists(MAP_JSON):
        H, W = 1080, 1920
        tiles = []
        for y in range(H):
            row = []
            for x in range(W):
                dx = (x - W//2) / (W//2)
                dy = (y - H//2) / (H//2)
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist > 0.8:
                    row.append("water")
                elif dist > 0.7:
                    row.append("sand")
                elif dist > 0.5:
                    row.append("grass")
                elif dist > 0.3:
                    row.append("forest")
                else:
                    row.append("mountain")
            tiles.append(row)
        return tiles, W, H
    
    with open(MAP_JSON, "r", encoding="utf-8") as f:
        tiles = json.load(f)
    H, W = len(tiles), len(tiles[0])
    return tiles, W, H

def make_world_surface(tiles, W, H):
    surf = pygame.Surface((W, H))
    lock = pygame.PixelArray(surf)
    for y in range(H):
        row = tiles[y]
        for x in range(W):
            lock[x, y] = surf.map_rgb(COLORS_TERRAIN.get(row[x], (100, 100, 100)))
    del lock
    return surf.convert()

def add_ocean_padding(world, ratio, ocean_color):
    w, h = world.get_size()
    pad = int(max(w, h) * ratio)
    canvas = pygame.Surface((w + 2*pad, h + 2*pad)).convert()
    canvas.fill(ocean_color)
    canvas.blit(world, (pad, pad))
    return canvas, pad

def clamp_camera(cam_x, cam_y, zoom, world_w, world_h, screen_w, screen_h):
    vw = max(1, min(world_w, int(math.ceil(screen_w / zoom))))
    vh = max(1, min(world_h, int(math.ceil(screen_h / zoom))))
    cam_x = max(0, min(world_w - vw, cam_x))
    cam_y = max(0, min(world_h - vh, cam_y))
    return cam_x, cam_y, vw, vh

# ============= PANTALLA EVENTOS =============

class PantallaEventos:
    def __init__(self, ancho: int, alto: int):
        self.ancho = ancho
        self.alto = alto
        self.activa = False
        self.eventos: List[EventoHistorico] = []
        self.tiempo = 0
        self.duracion = 240
    
    def activar(self, eventos: List[EventoHistorico]):
        self.activa = True
        self.eventos = sorted(eventos, key=lambda x: x.importancia, reverse=True)[:15]
        self.tiempo = 0
    
    def actualizar(self):
        if self.activa:
            self.tiempo += 1
            if self.tiempo >= self.duracion:
                self.activa = False
    
    def dibujar(self, screen: pygame.Surface):
        if not self.activa:
            return
        
        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        panel_w = min(800, self.ancho - 100)
        panel_h = min(500, self.alto - 100)
        panel_x = (self.ancho - panel_w) // 2
        panel_y = (self.alto - panel_h) // 2
        
        pygame.draw.rect(screen, (20, 20, 40), (panel_x, panel_y, panel_w, panel_h), border_radius=15)
        pygame.draw.rect(screen, DORADO, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=15)
        
        fuente_titulo = pygame.font.Font(None, 36)
        fuente_evento = pygame.font.Font(None, 20)
        
        titulo = fuente_titulo.render("📜 EVENTOS DE LA SEMANA 📜", True, DORADO)
        screen.blit(titulo, titulo.get_rect(center=(self.ancho // 2, panel_y + 25)))
        
        y = panel_y + 70
        iconos = {
            TipoEvento.NACIMIENTO: "👶", TipoEvento.MUERTE: "💀", TipoEvento.BODA: "💑",
            TipoEvento.TRABAJO: "🛠️", TipoEvento.BATALLA: "⚔️", TipoEvento.CONQUISTA: "🏰",
            TipoEvento.DIPLOMACIA: "🤝", TipoEvento.EMBARAZO: "🤰", TipoEvento.RECUPERACION: "💚",
            TipoEvento.CLIMA: "🌤️", TipoEvento.PRODUCCION: "🌾", TipoEvento.DESASTRE: "⚠️",
            TipoEvento.ENFERMEDAD: "🦠"
        }
        colores = {1: BLANCO, 2: NARANJA, 3: ROJO}
        
        for evento in self.eventos[:12]:
            if y > panel_y + panel_h - 70:
                break
            color = colores.get(evento.importancia, BLANCO)
            icono = iconos.get(evento.tipo, "•")
            texto = fuente_evento.render(f"{icono} {evento.descripcion}", True, color)
            screen.blit(texto, (panel_x + 20, y))
            y += 30
        
        progreso = self.tiempo / self.duracion
        barra_w = 300
        barra_x = (self.ancho - barra_w) // 2
        barra_y = panel_y + panel_h - 30
        pygame.draw.rect(screen, GRIS_OSCURO, (barra_x, barra_y, barra_w, 12), border_radius=6)
        pygame.draw.rect(screen, VERDE, (barra_x, barra_y, int(barra_w * progreso), 12), border_radius=6)

# ============= PANEL DE ACTIVIDADES =============

class PanelActividades:
    def __init__(self, ancho: int, alto: int):
        self.ancho = ancho
        self.alto = alto
        self.logs: List[str] = []
        self.max_logs = 15
        self.update_cooldown = 300
        self.cooldown_timer = 0
    
    def agregar_log(self, log: str):
        self.logs.insert(0, log)
        if len(self.logs) > self.max_logs:
            self.logs.pop()
    
    def actualizar(self, dt: float, juego: 'Juego'):
        self.cooldown_timer += 1
        if self.cooldown_timer >= self.update_cooldown:
            for reino in juego.reinos:
                for npc in reino.todos_npcs:
                    if npc.estado == "working" and random.random() < 0.1:
                        tarea_desc = npc.tarea_actual.tipo.value if npc.tarea_actual else "idle"
                        log = f"{npc.nombre} {tarea_desc} en {reino.nombre}"
                        self.agregar_log(log)
            self.cooldown_timer = 0
    
    def dibujar(self, screen: pygame.Surface):
        panel_x = 10
        panel_y = 220
        panel_w = 200
        panel_h = min(500, self.alto - 100)
        
        pygame.draw.rect(screen, (20, 20, 40), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(screen, DORADO, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)
        
        fuente_titulo = pygame.font.Font(None, 24)
        titulo = fuente_titulo.render("📋 ACTIVIDADES", True, DORADO)
        screen.blit(titulo, (panel_x + 10, panel_y + 10))
        
        fuente_peq = pygame.font.Font(None, 16)
        y_off = 50
        for log in self.logs:
            if y_off > panel_h - 30:
                break
            wrapped = [log[i:i+20] for i in range(0, len(log), 20)]
            for line in wrapped[:2]:
                texto = fuente_peq.render(line, True, BLANCO)
                screen.blit(texto, (panel_x + 10, panel_y + y_off))
                y_off += 16
            y_off += 5

# ============= JUEGO PRINCIPAL =============

class Juego:
    def __init__(self):
        self.screen = pygame.display.set_mode((ANCHO, ALTO), pygame.RESIZABLE)
        pygame.display.set_caption("BLODD THRONE - Simulador de Reinos")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 18)
        
        self.sprite_bank = SpriteBank(ASSETS_DIR)
        
        self.tiles_map, self.map_w, self.map_h = load_tiles()
        world = make_world_surface(self.tiles_map, self.map_w, self.map_h)
        self.world, self.pad = add_ocean_padding(world, OCEAN_PADDING_RATIO, OCEAN_COLOR)
        self.world_w, self.world_h = self.world.get_size()
        
        # Load polygons from JSON
        with open("reinos_poligonos.json", "r") as f:
            data = json.load(f)
        scale_x = self.map_w / data["mapa_w"]
        scale_y = self.map_h / data["mapa_h"]
        
        self.sistema_diplomatico = SistemaDiplomatico(7)
        self.arbol_relaciones = ArbolRelaciones()
        
        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
        self.gestor_tareas = GestorTareas()
        # ===================================================
        
        self.reinos: List[Reino] = []
        self.reino_map: Dict[int, Reino] = {}
        for i, reino_data in enumerate(data["reinos"]):
            nombre = NOMBRES_REINOS_GOT[i] if i < len(NOMBRES_REINOS_GOT) else f"Reino {i}"
            raw_poly = reino_data["polygon"]
            poly = [[int(p[0] * scale_x), int(p[1] * scale_y)] for p in raw_poly]
            color = COLORES_REINOS[i % len(COLORES_REINOS)]
            reino = Reino(i, nombre, color, poly, self.sistema_diplomatico, self.tiles_map,
                          self.map_w, self.map_h, self.pad)
            self.reinos.append(reino)
            self.reino_map[i] = reino
        
        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
        # Registrar oficios de todos los NPCs en el índice
        for reino in self.reinos:
            for npc in reino.todos_npcs:
                if npc.profesiones:
                    self.gestor_tareas.registrar_oficio_npc(int(npc.id.split('_')[1]), npc.profesiones[0].value)
        # ===================================================
        
        todos = [npc for r in self.reinos for npc in r.todos_npcs]
        for i, npc1 in enumerate(todos):
            for npc2 in todos[i+1:i+20]:
                self.arbol_relaciones.agregar_relacion(npc1.id, npc2.id)
        
        self.evento_global = EventoGlobal.NORMAL
        self.probabilidades = {
            EventoGlobal.NORMAL: 0.40, EventoGlobal.LLUVIA: 0.15, EventoGlobal.SOL_INTENSO: 0.10,
            EventoGlobal.FESTIVAL: 0.08, EventoGlobal.TORMENTA: 0.04, EventoGlobal.NIEVE: 0.03,
            EventoGlobal.RAYO: 0.05, EventoGlobal.HAMBRUNA: 0.015, EventoGlobal.EPIDEMIA: 0.015, 
            EventoGlobal.DRAGON: 0.01
        }
        
        self.active_effects: List[GlobalEffect] = []
        
        self.cam_x = (self.world_w - ANCHO) // 2
        self.cam_y = (self.world_h - ALTO) // 2
        self.zoom = 0.5
        self.dragging = False
        
        self.semana_actual, self.dia_actual = 1, 1
        self.historial: List[EventoHistorico] = []
        
        self.npc_seleccionado: Optional[NPC] = None
        self.mostrar_panel_npc = False
        self.mostrar_panel_dip = False
        self.mostrar_panel_castillo = False
        self.castillo_seleccionado: Optional[Estructura] = None
        self.pantalla_eventos = PantallaEventos(ANCHO, ALTO)
        
        self.panel_actividades = PanelActividades(ANCHO, ALTO)
        
        # ========== INTEGRACIÓN SISTEMA DE COORDENADAS ==========
        self.sistema_coordenadas = SistemaCoordenadas()
        self.mostrar_click_coords = False
        self.click_coords_pos = (0, 0)
        self.click_coords_timer = 0
        # ========================================================
        
        self.boton_rayo = pygame.Rect(10, 90, 120, 35)
        self.boton_dragon = pygame.Rect(10, 130, 120, 35)
        self.boton_estres = pygame.Rect(10, 170, 120, 35)
        
        self.actualizar_botones()
        self.ejecutando = True
        self.pausado = False
        self.tareas_asignadas_tiempo = 0
        
        self.moving_speed = 300.0
    
    def actualizar_botones(self):
        self.boton_continuar = pygame.Rect(ANCHO - 180, ALTO - 60, 160, 45)
        self.boton_diplomacia = pygame.Rect(ANCHO - 180, 90, 160, 35)
    
    def clamp_cam(self):
        self.cam_x, self.cam_y, _, _ = clamp_camera(self.cam_x, self.cam_y, self.zoom, 
                                                    self.world_w, self.world_h, ANCHO, ALTO)
    
    def spawn_effect(self, event_type: EventoGlobal):
        if event_type == EventoGlobal.RAYO:
            effect_type = "rayo"
        elif event_type == EventoGlobal.DRAGON:
            effect_type = "dragon"
        else:
            return
        x, y = get_random_world_point(self.world_w, self.world_h)
        effect = GlobalEffect(effect_type, x, y, self.sprite_bank, self.world_w, self.world_h, 
                              self.pad, self.tiles_map, self.map_w, self.map_h)
        effect.world = self.world
        self.active_effects.append(effect)
        log = f"{event_type.value} en [{x}, {y}]"
        self.panel_actividades.agregar_log(log)
    
    def update_effects(self, dt: float):
        to_remove = []
        for effect in self.active_effects:
            effect.update(dt)
            if effect.time_active > effect.duration:
                to_remove.append(effect)
            effect.check_npc_impact([n for r in self.reinos for n in r.todos_npcs], self.reino_map)
        for eff in to_remove:
            self.active_effects.remove(eff)
    
    def probar_estres(self):
        ociosos = [npc for r in self.reinos for npc in r.todos_npcs if not npc.tarea_actual and npc.stamina > 40]
        for npc in ociosos[:100]:  # Asigna a max 100 ociosos
            # Genera tarea manual/simple (e.g., TipoTarea.MINERIA con random pos)
            tarea = Tarea(TipoTarea.MINERIA, prioridad=1, duracion_semanas=1, ubicacion=(random.randint(0, self.map_w), random.randint(0, self.map_h)))
            npc.asignar_tarea(tarea)
        self.panel_actividades.agregar_log(f"Prueba de estrés: {min(100, len(ociosos))} tareas forzadas")
    
    def avanzar_semana(self):
        self.semana_actual += 1
        self.dia_actual += 7
        
        eventos_semana: List[EventoHistorico] = []
        todos_npcs = [npc for r in self.reinos for npc in r.todos_npcs]
        
        for reino in self.reinos:
            npcs_vivos = []
            for npc in list(reino.todos_npcs):
                resultados = npc.avanzar_semana(todos_npcs, self.arbol_relaciones)
                if resultados:
                    for evento in resultados:
                        if isinstance(evento, EventoHistorico):
                            evento.semana = self.semana_actual
                            evento.dia = self.dia_actual
                            eventos_semana.append(evento)
                
                if npc.edad < 100:
                    npcs_vivos.append(npc)
            reino.todos_npcs = npcs_vivos
        
        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
        # Actualizar progreso de tareas y procesar completadas
        for reino in self.reinos:
            reino.sincronizar_recursos()
            
            # Actualizar estado de la casa en el gestor
            npcs_activos = sum(1 for npc in reino.todos_npcs if npc.tarea_actual)
            npcs_ociosos = sum(1 for npc in reino.todos_npcs if not npc.tarea_actual and npc.edad >= 14)
            edificios_danados = sum(1 for e in reino.get_todas_estructuras() if e.destruida)
            
            self.gestor_tareas.actualizar_estado_casa(
                casa=reino.nombre,
                oro=reino.oro,
                comida=reino.comida,
                soldados=reino.soldados,
                npcs_activos=npcs_activos,
                npcs_ociosos=npcs_ociosos,
                edificios_danados=edificios_danados
            )
            
            # Procesar tareas completadas
            for npc in reino.todos_npcs:
                if npc.tarea_actual and npc.tarea_actual.completada:
                    tarea = npc.tarea_actual
                    
                    # Aplicar recompensas
                    reino.oro += tarea.oro_ganado
                    reino.almacen.agregar(TipoRecurso.ALIMENTO, tarea.comida_ganada)
                    reino.almacen.agregar(TipoRecurso.MADERA, tarea.madera_ganada)
                    
                    # Log de producción
                    if tarea.oro_ganado > 0 or tarea.comida_ganada > 0 or tarea.madera_ganada > 0:
                        eventos_semana.append(EventoHistorico(
                            self.semana_actual, self.dia_actual,
                            f"{reino.nombre}: +{tarea.oro_ganado} oro +{tarea.comida_ganada} comida +{tarea.madera_ganada} madera",
                            TipoEvento.PRODUCCION, 1, [], [reino.id]
                        ))
                    
                    # Liberar NPC
                    npc.terminar_trabajo()
                    npc_id_int = int(npc.id.split('_')[1])
                    self.gestor_tareas.registrar_npc_ocioso(npc_id_int)
        
        # Generar recursos pasivos
        for reino in self.reinos:
            if reino.derrotado or len(reino.polygon) == 0:
                continue
            for rec in [TipoRecurso.MADERA, TipoRecurso.PIEDRA, TipoRecurso.HIERRO]:
                cantidad = random.randint(10, 20)
                reino.almacen.agregar(rec, cantidad)
            reino.almacen.agregar(TipoRecurso.ALIMENTO, random.randint(15, 30))
        # ===================================================
        
        self.actualizar_diplomacia(eventos_semana)
        
        nuevo_evento = random.choices(list(EventoGlobal), weights=list(self.probabilidades.values()))[0]
        if nuevo_evento != self.evento_global:
            self.evento_global = nuevo_evento
            desc = self.get_descripcion_evento_global(nuevo_evento)
            eventos_semana.append(EventoHistorico(
                self.semana_actual, self.dia_actual, desc, TipoEvento.CLIMA, 2, [], list(range(7))
            ))
        
        self.pantalla_eventos.activar(eventos_semana)
    
    def get_descripcion_evento_global(self, evento: EventoGlobal) -> str:
        descripciones = {
            EventoGlobal.LLUVIA: "Lluvias benefician cultivos",
            EventoGlobal.SOL_INTENSO: "Sol intenso",
            EventoGlobal.TORMENTA: "Tormenta devastadora",
            EventoGlobal.NIEVE: "Nevada cubre la isla",
            EventoGlobal.FESTIVAL: "Gran festival",
            EventoGlobal.DRAGON: "¡DRAGÓN APARECE!",
            EventoGlobal.HAMBRUNA: "Hambruna generalizada",
            EventoGlobal.EPIDEMIA: "Epidemia se propaga",
            EventoGlobal.NORMAL: "Clima normal"
        }
        return descripciones.get(evento, f"{evento.value}")
    
    def actualizar_diplomacia(self, eventos: List[EventoHistorico]):
        for i in range(len(self.reinos)):
            for j in range(i + 1, len(self.reinos)):
                rel = self.sistema_diplomatico.get_relacion(i, j)
                if not rel:
                    continue
                
                r1, r2 = self.reinos[i], self.reinos[j]
                if r1.derrotado or r2.derrotado or len(r1.polygon) == 0 or len(r2.polygon) == 0:
                    continue
                
                if random.random() < 0.15:
                    estado_anterior = rel.relacion
                    if random.random() < 0.6:
                        rel.mejorar_relacion()
                    else:
                        rel.empeorar_relacion()
                        if rel.relacion == RelacionDiplomatica.GUERRA and rel.relacion != estado_anterior:
                            razon = random.choice(["disputa territorial", "robo de recursos", "traición"])
                            r1.razones_guerra[j] = razon
                            eventos.append(EventoHistorico(
                                self.semana_actual, self.dia_actual,
                                f"¡{r1.nombre} declaró guerra a {r2.nombre}!",
                                TipoEvento.DIPLOMACIA, 3, [], [i, j]
                            ))
                        if rel.relacion == RelacionDiplomatica.GUERRA and random.random() < 0.5:
                            self.ejecutar_batalla(r1, r2, eventos)
    
    def ejecutar_batalla(self, r1: Reino, r2: Reino, eventos: List[EventoHistorico]):
        if len(r1.polygon) == 0 or len(r2.polygon) == 0:
            return
        atacante = r1 if r1.calcular_poder_total() > r2.calcular_poder_total() else r2
        defensor = r2 if atacante == r1 else r1
        
        fuerza = max(10, (atacante.calcular_poder_total() - defensor.calcular_poder_total()) // 2)
        resultado = defensor.recibir_ataque(fuerza, atacante)
        
        if resultado["conquistado"]:
            eventos.append(EventoHistorico(
                self.semana_actual, self.dia_actual,
                f"¡{atacante.nombre} conquistó {defensor.nombre}!",
                TipoEvento.CONQUISTA, 3, [], [atacante.id, defensor.id]
            ))
    
    # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
    def asignar_tareas_inteligentes(self):
        """Sistema inteligente de asignación de tareas usando el gestor"""
        if self.pausado:
            return
        
        # Crear diccionario de casas para validación de recursos
        casas_dict = {reino.nombre: reino for reino in self.reinos}
        
        for reino in self.reinos:
            if reino.derrotado or len(reino.polygon) == 0:
                continue
            
            # Identificar NPCs ociosos
            npcs_ociosos_ids = []
            for npc in reino.todos_npcs:
                if npc.edad >= 14 and not npc.tarea_actual and npc.estado == "idle" and npc.stamina > 40:
                    npc_id_int = int(npc.id.split('_')[1])
                    npcs_ociosos_ids.append(npc_id_int)
            
            if not npcs_ociosos_ids:
                continue
            
            # Forzar asignación completa
            asignaciones = self.gestor_tareas.forzar_asignacion_completa(
                npcs_ociosos_ids, 
                reino.nombre,
                casas_dict
            )
            
            # Aplicar asignaciones
            for npc_id_int, tarea, mensaje_error in asignaciones:
                if tarea is None:
                    # Tarea rechazada por falta de recursos
                    if mensaje_error:
                        self.panel_actividades.agregar_log(mensaje_error)
                    continue
                
                # Encontrar NPC correspondiente
                npc_id_str = f"npc_{npc_id_int}"
                npc = next((n for n in reino.todos_npcs if n.id == npc_id_str), None)
                
                if npc:
                    # Consumir recursos de la tarea
                    self.gestor_tareas.consumir_recursos_tarea(tarea, reino)
                    
                    # Asignar tarea al NPC
                    npc.asignar_tarea(tarea)
                    
                    # Log de asignación
                    self.panel_actividades.agregar_log(
                        f"{npc.nombre}: {tarea.tipo.value}"
                    )
                    self.tareas_asignadas_tiempo += 1
    # ===================================================
    
    def get_castillo_en_pos(self, x: int, y: int) -> Optional[Estructura]:
        self.cam_x, self.cam_y, vw, vh = clamp_camera(self.cam_x, self.cam_y, self.zoom, 
                                                       self.world_w, self.world_h, ANCHO, ALTO)
        scale = min(ANCHO / vw, ALTO / vh)
        off_x = (ANCHO - int(vw * scale)) // 2
        off_y = (ALTO - int(vh * scale)) // 2
        
        for reino in self.reinos:
            if reino.capital:
                est_x = int((reino.capital.x - self.cam_x) * self.zoom) + off_x
                est_y = int((reino.capital.y - self.cam_y) * self.zoom) + off_y
                dist = math.sqrt((est_x - x)**2 + (est_y - y)**2)
                if dist <= int(50 * self.zoom):
                    return reino.capital
        return None
    
    def manejar_eventos(self):
        mouse_pos = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False
            
            elif evento.type == pygame.VIDEORESIZE:
                global ANCHO, ALTO
                ANCHO, ALTO = evento.w, evento.h
                self.screen = pygame.display.set_mode((ANCHO, ALTO), pygame.RESIZABLE)
                self.pantalla_eventos = PantallaEventos(ANCHO, ALTO)
                self.panel_actividades = PanelActividades(ANCHO, ALTO)
                self.actualizar_botones()
            
            elif evento.type == pygame.MOUSEWHEEL:
                if not self.pantalla_eventos.activa:
                    self.zoom = max(0.08, min(6.0, self.zoom + evento.y * 0.1))
            
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    if self.boton_continuar.collidepoint(evento.pos):
                        self.avanzar_semana()
                        self.pausado = False
                    elif self.boton_diplomacia.collidepoint(evento.pos):
                        self.mostrar_panel_dip = not self.mostrar_panel_dip
                        self.mostrar_panel_npc = False
                        self.mostrar_panel_castillo = False
                    elif self.boton_rayo.collidepoint(evento.pos):
                        self.spawn_effect(EventoGlobal.RAYO)
                    elif self.boton_dragon.collidepoint(evento.pos):
                        self.spawn_effect(EventoGlobal.DRAGON)
                    elif self.boton_estres.collidepoint(evento.pos):
                        self.probar_estres()
                    else:
                        # ========== INTEGRACIÓN SISTEMA DE COORDENADAS ==========
                        if self.sistema_coordenadas.mostrar:
                            self.mostrar_click_coords = True
                            self.click_coords_pos = evento.pos
                            self.click_coords_timer = 180  # 3 segundos
                        # ========================================================
                        
                        npc = self.get_npc_en_pos(evento.pos[0], evento.pos[1])
                        if npc:
                            self.npc_seleccionado = npc
                            self.mostrar_panel_npc = True
                            self.mostrar_panel_dip = False
                            self.mostrar_panel_castillo = False
                        else:
                            castillo = self.get_castillo_en_pos(evento.pos[0], evento.pos[1])
                            if castillo:
                                self.castillo_seleccionado = castillo
                                self.mostrar_panel_castillo = True
                                self.mostrar_panel_npc = False
                                self.mostrar_panel_dip = False
                            else:
                                self.mostrar_panel_npc = False
                                self.mostrar_panel_castillo = False
                elif evento.button == 3:
                    self.dragging = True
                    pygame.mouse.get_rel()
            
            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 3:
                    self.dragging = False
            
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    self.avanzar_semana()
                elif evento.key == pygame.K_p:
                    self.pausado = not self.pausado
                elif evento.key == pygame.K_ESCAPE:
                    self.mostrar_panel_npc = False
                    self.mostrar_panel_dip = False
                    self.mostrar_panel_castillo = False
                # ========== INTEGRACIÓN SISTEMA DE COORDENADAS ==========
                elif evento.key == pygame.K_c:
                    self.sistema_coordenadas.toggle()
                # ========================================================
        
        if self.dragging:
            rx, ry = pygame.mouse.get_rel()
            self.cam_x -= int(rx / max(self.zoom, 1e-6))
            self.cam_y -= int(ry / max(self.zoom, 1e-6))
            self.clamp_cam()
        else:
            pygame.mouse.get_rel()
    
    def get_npc_en_pos(self, x: int, y: int) -> Optional[NPC]:
        self.cam_x, self.cam_y, vw, vh = clamp_camera(self.cam_x, self.cam_y, self.zoom, 
                                                       self.world_w, self.world_h, ANCHO, ALTO)
        scale = min(ANCHO / vw, ALTO / vh)
        off_x = (ANCHO - int(vw * scale)) // 2
        off_y = (ALTO - int(vh * scale)) // 2
        
        for reino in self.reinos:
            for npc in reino.todos_npcs:
                npc_x = int((npc.x - self.cam_x) * self.zoom) + off_x
                npc_y = int((npc.y - self.cam_y) * self.zoom) + off_y
                dist = math.sqrt((npc_x - x)**2 + (npc_y - y)**2)
                if dist <= int(15 * self.zoom):
                    return npc
        return None
    
    def actualizar(self):
        dt = self.clock.tick(FPS) / 1000.0
        
        keys = pygame.key.get_pressed()
        delta_screen = self.moving_speed * dt
        delta_world = delta_screen / max(self.zoom, 1e-6)
        if keys[pygame.K_LEFT]:
            self.cam_x -= delta_world
        if keys[pygame.K_RIGHT]:
            self.cam_x += delta_world
        if keys[pygame.K_UP]:
            self.cam_y -= delta_world
        if keys[pygame.K_DOWN]:
            self.cam_y += delta_world
        self.clamp_cam()
        
        self.pantalla_eventos.actualizar()
        
        self.update_effects(dt)
        
        self.panel_actividades.actualizar(dt, self)
        
        # ========== INTEGRACIÓN SISTEMA DE COORDENADAS ==========
        if self.mostrar_click_coords:
            self.click_coords_timer -= 1
            if self.click_coords_timer <= 0:
                self.mostrar_click_coords = False
        # ========================================================
        
        if not self.pausado and not self.pantalla_eventos.activa:
            # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
            # Asignar tareas inteligentemente cada 10 segundos
            if int(pygame.time.get_ticks() / 10000) % 1 == 0:
                self.asignar_tareas_inteligentes()
            # ===================================================
            
            for reino in self.reinos:
                if reino.derrotado or len(reino.polygon) == 0:
                    continue
                for npc in reino.todos_npcs:
                    if npc.actualizar(dt, self.sprite_bank):
                        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
                        if npc.tarea_actual:
                            tarea = npc.tarea_actual
                            
                            # Marcar como completada
                            tarea.completada = True
                            tarea.progreso = 1.0
                            
                            # Aplicar recompensas inmediatamente
                            reino.oro += tarea.oro_ganado
                            reino.almacen.agregar(TipoRecurso.ALIMENTO, tarea.comida_ganada)
                            reino.almacen.agregar(TipoRecurso.MADERA, tarea.madera_ganada)
                            
                            # Completar en el gestor
                            npc_id_int = int(npc.id.split('_')[1])
                            self.gestor_tareas.completar_tarea(npc_id_int)
                            
                            # Log de producción
                            if tarea.oro_ganado > 0 or tarea.comida_ganada > 0 or tarea.madera_ganada > 0:
                                self.panel_actividades.agregar_log(
                                    f"{npc.nombre}: Recolectó +{tarea.oro_ganado} oro +{tarea.comida_ganada} comida +{tarea.madera_ganada} madera"
                                )
                        # ===================================================
                        
                        npc.terminar_trabajo()
    
    def dibujar(self):
        self.cam_x, self.cam_y, vw, vh = clamp_camera(self.cam_x, self.cam_y, self.zoom, 
                                                       self.world_w, self.world_h, ANCHO, ALTO)
        
        self.screen.fill(OCEAN_COLOR)
        view = self.world.subsurface((self.cam_x, self.cam_y, vw, vh))
        scale = min(ANCHO / vw, ALTO / vh)
        dst_w = max(1, int(vw * scale))
        dst_h = max(1, int(vh * scale))
        frame = pygame.transform.smoothscale(view, (dst_w, dst_h))
        off_x = (ANCHO - dst_w) // 2
        off_y = (ALTO - dst_h) // 2
        self.screen.blit(frame, (off_x, off_y))
        
        for effect in self.active_effects:
            effect.draw(self.screen, self.cam_x, self.cam_y, self.zoom, off_x, off_y)
        
        for reino in self.reinos:
            if len(reino.polygon) > 0:
                adjusted_points = [[int((p[0] - self.cam_x) * self.zoom + off_x), 
                                    int((p[1] - self.cam_y) * self.zoom + off_y)] for p in reino.polygon]
                pygame.draw.polygon(self.screen, reino.color, adjusted_points, int(2 * self.zoom))
            
            cx, cy = reino.centroid
            nx = int((cx - self.cam_x) * self.zoom) + off_x
            ny = int((cy - self.cam_y) * self.zoom) + off_y
            nombre_surf = self.font.render(reino.nombre, True, reino.color)
            self.screen.blit(nombre_surf, (nx, ny))
        
        for reino in self.reinos:
            for est in reino.get_todas_estructuras():
                est.dibujar(self.screen, self.sprite_bank, self.cam_x, self.cam_y, 
                           self.zoom, off_x, off_y, reino.color)
                # Contador de tareas en castillos
                if est.tipo == "castillo":
                    num_tareas = sum(1 for npc in reino.todos_npcs if npc.tarea_actual)
                    texto_tareas = self.font.render(str(num_tareas), True, BLANCO)
                    self.screen.blit(texto_tareas, (int((est.x - self.cam_x) * self.zoom) + off_x - 10, int((est.y - self.cam_y) * self.zoom) + off_y - 50))
        
        for reino in self.reinos:
            for npc in reino.todos_npcs:
                if npc.edad >= 14 or self.zoom > 1.5:
                    npc.dibujar(self.screen, self.sprite_bank, self.cam_x, self.cam_y, 
                               self.zoom, off_x, off_y)
        
        self.dibujar_ui()
        if self.mostrar_panel_npc:
            self.dibujar_panel_npc()
        if self.mostrar_panel_dip:
            self.dibujar_panel_dip()
        if self.mostrar_panel_castillo:
            self.dibujar_panel_castillo()
        
        self.panel_actividades.dibujar(self.screen)
        
        self.dibujar_botones_spawn()
        
        # ========== INTEGRACIÓN SISTEMA DE COORDENADAS ==========
        # Crear objeto cámara temporal para el sistema de coordenadas
        class CamaraTemp:
            def __init__(self, cam_x, cam_y, zoom):
                self.cam_x = cam_x
                self.cam_y = cam_y
                self.zoom = zoom
            
            def mundo_a_pantalla(self, x, y):
                return int((x - self.cam_x) * self.zoom) + off_x, int((y - self.cam_y) * self.zoom) + off_y
            
            def pantalla_a_mundo(self, px, py):
                return int((px - off_x) / self.zoom + self.cam_x), int((py - off_y) / self.zoom + self.cam_y)
            
            def obtener_viewport_bounds(self, ancho, alto, margen=0):
                x_min = self.cam_x
                y_min = self.cam_y
                x_max = self.cam_x + ancho / self.zoom
                y_max = self.cam_y + alto / self.zoom
                return x_min, y_min, x_max, y_max
        
        camara_temp = CamaraTemp(self.cam_x, self.cam_y, self.zoom)
        self.sistema_coordenadas.renderizar(self.screen, camara_temp, self.world_w, self.world_h)
        
        if self.mostrar_click_coords:
            self.sistema_coordenadas.mostrar_click_coords(self.screen, camara_temp, 
                                                          self.click_coords_pos[0], self.click_coords_pos[1])
        # ========================================================
        
        self.pantalla_eventos.dibujar(self.screen)
        pygame.display.flip()

    def dibujar_panel_castillo(self):
        if not self.castillo_seleccionado:
            return
        
        reino = self.reino_map[self.castillo_seleccionado.reino]
        
        panel_w, panel_h = 500, 400
        panel_x = (ANCHO - panel_w) // 2
        panel_y = (ALTO - panel_h) // 2
        
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 230))
        pygame.draw.rect(panel, reino.color, (0, 0, panel_w, panel_h), 3)
        
        fuente_titulo = pygame.font.Font(None, 28)
        fuente_normal = pygame.font.Font(None, 18)
        
        y = 15
        titulo = fuente_titulo.render(f"TAREAS EN {reino.nombre}", True, DORADO)
        panel.blit(titulo, (15, y))
        y += 35
        
        y += 8
        pygame.draw.line(panel, reino.color, (15, y), (panel_w - 15, y), 2)
        y += 12
        
        for npc in reino.todos_npcs:
            if npc.tarea_actual:
                estado_str = " (Moviendo)" if npc.estado == "moving" else f" (Progreso: {int(npc.progreso_tarea * 100)}%)"
                linea = f"{npc.nombre} - {npc.tarea_actual.tipo.value} en [{int(npc.target_x)}, {int(npc.target_y)}]{estado_str}"
                texto = fuente_normal.render(linea[:50], True, BLANCO)
                panel.blit(texto, (15, y))
                y += 25
                if y > panel_h - 50:
                    break
        
        self.screen.blit(panel, (panel_x, panel_y))
    
    def dibujar_botones_spawn(self):
        pygame.draw.rect(self.screen, ROJO, self.boton_rayo)
        pygame.draw.rect(self.screen, BLANCO, self.boton_rayo, 2)
        texto_rayo = self.font.render("Spawn Rayo", True, BLANCO)
        self.screen.blit(texto_rayo, texto_rayo.get_rect(center=self.boton_rayo.center))
        
        pygame.draw.rect(self.screen, NARANJA, self.boton_dragon)
        pygame.draw.rect(self.screen, BLANCO, self.boton_dragon, 2)
        texto_dragon = self.font.render("Spawn Dragon", True, BLANCO)
        self.screen.blit(texto_dragon, texto_dragon.get_rect(center=self.boton_dragon.center))
        
        pygame.draw.rect(self.screen, MORADO, self.boton_estres)
        pygame.draw.rect(self.screen, BLANCO, self.boton_estres, 2)
        texto_estres = self.font.render("Pruebas de Estrés", True, BLANCO)
        self.screen.blit(texto_estres, texto_estres.get_rect(center=self.boton_estres.center))
    
    def dibujar_ui(self):
        panel_sup = pygame.Surface((ANCHO, 70), pygame.SRCALPHA)
        panel_sup.fill((0, 0, 0, 200))
        self.screen.blit(panel_sup, (0, 0))
        
        fuente_titulo = pygame.font.Font(None, 32)
        fuente_info = pygame.font.Font(None, 20)
        
        titulo = fuente_titulo.render("BLODD THRONE - Simulador de Reinos", True, DORADO)
        self.screen.blit(titulo, (15, 8))
        
        info = fuente_info.render(f"Semana: {self.semana_actual} | Día: {self.dia_actual}", True, BLANCO)
        self.screen.blit(info, (15, 42))
        
        evento_color = ROJO if self.evento_global == EventoGlobal.DRAGON else CYAN
        info_evento = fuente_info.render(f"Evento: {self.evento_global.value}", True, evento_color)
        self.screen.blit(info_evento, (250, 42))
        
        total_npcs = sum(len(r.todos_npcs) for r in self.reinos)
        info_pob = fuente_info.render(f"Población: {total_npcs}", True, VERDE)
        self.screen.blit(info_pob, (500, 42))
        
        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
        stats = self.gestor_tareas.obtener_estadisticas()
        info_tareas = fuente_info.render(
            f"Tareas Global: {stats['tareas_activas']}/{stats['tareas_pendientes']+stats['tareas_activas']}", 
            True, NARANJA
        )
        self.screen.blit(info_tareas, (680, 42))
        # ===================================================
        
        pygame.draw.rect(self.screen, VERDE if not self.pausado else NARANJA, self.boton_continuar)
        pygame.draw.rect(self.screen, BLANCO, self.boton_continuar, 2)
        texto_boton = fuente_info.render("Avanzar Semana", True, BLANCO)
        self.screen.blit(texto_boton, texto_boton.get_rect(center=self.boton_continuar.center))
        
        pygame.draw.rect(self.screen, MORADO, self.boton_diplomacia)
        pygame.draw.rect(self.screen, BLANCO, self.boton_diplomacia, 2)
        texto_dip = fuente_info.render("Diplomacia", True, BLANCO)
        self.screen.blit(texto_dip, texto_dip.get_rect(center=self.boton_diplomacia.center))
        
        panel_x = ANCHO - 170
        panel_y = 140
        panel_h = min(350, ALTO - 200)
        panel = pygame.Surface((160, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        self.screen.blit(panel, (panel_x, panel_y))
        
        fuente_peq = pygame.font.Font(None, 16)
        y_off = 8
        
        for reino in self.reinos:
            if y_off > panel_h - 50:
                break
            
            texto_nombre = fuente_peq.render(reino.nombre[:10], True, reino.color)
            panel.blit(texto_nombre, (8, y_off))
            y_off += 18
            
            if len(reino.polygon) == 0:
                texto_estado = fuente_peq.render("VACÍO", True, ROJO)
                panel.blit(texto_estado, (8, y_off))
            elif reino.derrotado:
                texto_estado = fuente_peq.render("CONQUISTADO", True, ROJO)
                panel.blit(texto_estado, (8, y_off))
            else:
                poder = reino.calcular_poder_total()
                texto_poder = fuente_peq.render(f"Poder: {poder}", True, BLANCO)
                panel.blit(texto_poder, (8, y_off))
            y_off += 18
            
            # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
            npcs_count = len(reino.todos_npcs)
            texto_npcs = fuente_peq.render(f"NPCs: {npcs_count}", True, CYAN)
            panel.blit(texto_npcs, (8, y_off))
            y_off += 18
            
            texto_oro = fuente_peq.render(f"Oro: {reino.oro}", True, DORADO)
            panel.blit(texto_oro, (8, y_off))
            y_off += 18
            
            texto_comida = fuente_peq.render(f"Comida: {reino.comida}", True, DORADO)
            panel.blit(texto_comida, (8, y_off))
            y_off += 18
            
            texto_madera = fuente_peq.render(f"Madera: {reino.madera}", True, (139, 69, 19))
            panel.blit(texto_madera, (8, y_off))
            # ===================================================
            y_off += 22
        
        self.screen.blit(panel, (panel_x, panel_y))
    
    def dibujar_panel_npc(self):
        if not self.npc_seleccionado:
            return
        
        npc = self.npc_seleccionado
        reino = self.reinos[npc.reino]
        
        panel_w, panel_h = 400, 500
        panel_x = (ANCHO - panel_w) // 2
        panel_y = (ALTO - panel_h) // 2
        
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 230))
        pygame.draw.rect(panel, reino.color, (0, 0, panel_w, panel_h), 3)
        
        fuente_titulo = pygame.font.Font(None, 28)
        fuente_normal = pygame.font.Font(None, 19)
        
        y = 15
        titulo = fuente_titulo.render(npc.nombre, True, DORADO if npc.es_rey else BLANCO)
        panel.blit(titulo, (15, y))
        y += 35
        
        info = [
            f"Reino: {reino.nombre}",
            f"Género: {npc.genero.value}",
            f"Profesiones: {', '.join(p.value for p in npc.profesiones)}",
            f"Edad: {npc.edad} años",
            f"Estado civil: {npc.estado_civil.value}",
            f"Estado: {npc.estado}",
            f"Ánimo: {int(npc.estado_animo * 100)}%"
        ]
        
        if npc.es_mestizo:
            info.append("MESTIZO")
        if len(npc.hijos_ids) > 0:
            info.append(f"Hijos: {len(npc.hijos_ids)}")
        
        for linea in info:
            color = CYAN if "MESTIZO" in linea else BLANCO
            texto = fuente_normal.render(linea, True, color)
            panel.blit(texto, (15, y))
            y += 22
        
        # ========== INTEGRACIÓN SISTEMA DE TAREAS ==========
        y += 8
        pygame.draw.line(panel, reino.color, (15, y), (panel_w - 15, y), 2)
        y += 12
        
        titulo_tarea = fuente_normal.render("TAREA ACTUAL:", True, DORADO)
        panel.blit(titulo_tarea, (15, y))
        y += 25
        
        if npc.tarea_actual:
            tarea = npc.tarea_actual
            texto_tipo = fuente_normal.render(f"Tipo: {tarea.tipo.value}", True, VERDE)
            panel.blit(texto_tipo, (15, y))
            y += 22
            
            texto_progreso = fuente_normal.render(f"Progreso: {int(npc.progreso_tarea * 100)}%", True, CYAN)
            panel.blit(texto_progreso, (15, y))
            y += 22
            
            recompensas = []
            if tarea.oro_ganado > 0:
                recompensas.append(f"oro {tarea.oro_ganado}")
            if tarea.comida_ganada > 0:
                recompensas.append(f"comida {tarea.comida_ganada}")
            if tarea.madera_ganada > 0:
                recompensas.append(f"madera {tarea.madera_ganada}")
            
            if recompensas:
                texto_recomp = fuente_normal.render(f"Recompensa: {' '.join(recompensas)}", True, DORADO)
                panel.blit(texto_recomp, (15, y))
                y += 22
        else:
            texto_sin_tarea = fuente_normal.render("Sin tarea asignada", True, GRIS)
            panel.blit(texto_sin_tarea, (15, y))
            y += 22
        # ===================================================
        
        y += 8
        pygame.draw.line(panel, reino.color, (15, y), (panel_w - 15, y), 2)
        y += 12
        
        titulo_salud = fuente_normal.render("SALUD:", True, DORADO)
        panel.blit(titulo_salud, (15, y))
        y += 25
        
        lesiones = npc.lesiones.descripcion()
        color_salud = ROJO if lesiones != "Saludable" else VERDE
        texto_lesiones = fuente_normal.render(lesiones, True, color_salud)
        panel.blit(texto_lesiones, (15, y))
        y += 30
        
        titulo_stats = fuente_normal.render("ESTADÍSTICAS:", True, DORADO)
        panel.blit(titulo_stats, (15, y))
        y += 25
        
        stats = [
            f"Stamina: {int(npc.stamina)}/100",
            f"Dinero: {npc.dinero} monedas",
            f"Exp. guerra: {npc.experiencia_guerra}",
            f"Trabajos: {npc.trabajos_completados}",
        ]
        
        for stat in stats:
            texto = fuente_normal.render(stat, True, BLANCO)
            panel.blit(texto, (15, y))
            y += 22
        
        self.screen.blit(panel, (panel_x, panel_y))
        
        boton_cerrar = pygame.Rect(panel_x + panel_w - 40, panel_y + 8, 32, 32)
        pygame.draw.rect(self.screen, ROJO, boton_cerrar, border_radius=5)
        pygame.draw.rect(self.screen, BLANCO, boton_cerrar, 2, border_radius=5)
        cerrar_texto = fuente_titulo.render("X", True, BLANCO)
        self.screen.blit(cerrar_texto, (boton_cerrar.centerx - 8, boton_cerrar.centery - 12))
        
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and boton_cerrar.collidepoint(mouse_pos):
            self.mostrar_panel_npc = False
    
    def dibujar_panel_dip(self):
        panel_w, panel_h = 600, 500
        panel_x = (ANCHO - panel_w) // 2
        panel_y = (ALTO - panel_h) // 2
        
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 230))
        pygame.draw.rect(panel, DORADO, (0, 0, panel_w, panel_h), 3)
        
        fuente_titulo = pygame.font.Font(None, 32)
        fuente_normal = pygame.font.Font(None, 18)
        
        titulo = fuente_titulo.render("RELACIONES DIPLOMÁTICAS", True, DORADO)
        panel.blit(titulo, (15, 15))
        
        y = 60
        
        for i in range(len(self.reinos)):
            for j in range(i + 1, len(self.reinos)):
                if y > panel_h - 45:
                    break
                rel = self.sistema_diplomatico.get_relacion(i, j)
                if not rel:
                    continue
                
                r1, r2 = self.reinos[i], self.reinos[j]
                if len(r1.polygon) == 0 or len(r2.polygon) == 0:
                    continue
                texto_reinos = fuente_normal.render(f"{r1.nombre} <-> {r2.nombre}", True, BLANCO)
                panel.blit(texto_reinos, (15, y))
                y += 22
                
                colores = {
                    RelacionDiplomatica.ALIANZA: VERDE,
                    RelacionDiplomatica.NEUTRAL: CYAN,
                    RelacionDiplomatica.TENSION: NARANJA,
                    RelacionDiplomatica.GUERRA: ROJO
                }
                color = colores[rel.relacion]
                
                estado_texto = f"{rel.relacion.value} (Tensión: {int(rel.puntos_tension)})"
                texto_estado = fuente_normal.render(estado_texto, True, color)
                panel.blit(texto_estado, (25, y))
                y += 26
        
        self.screen.blit(panel, (panel_x, panel_y))
        
        boton_cerrar = pygame.Rect(panel_x + panel_w - 40, panel_y + 8, 32, 32)
        pygame.draw.rect(self.screen, ROJO, boton_cerrar, border_radius=5)
        pygame.draw.rect(self.screen, BLANCO, boton_cerrar, 2, border_radius=5)
        cerrar_texto = fuente_titulo.render("X", True, BLANCO)
        self.screen.blit(cerrar_texto, (boton_cerrar.centerx - 8, boton_cerrar.centery - 12))
        
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and boton_cerrar.collidepoint(mouse_pos):
            self.mostrar_panel_dip = False
    
    def ejecutar(self):
        print("=" * 80)
        print("7 REINOS - GAME OF THRONES EDITION")
        print("=" * 80)
        print("\n✨ CARACTERÍSTICAS:")
        print("  • 🗺️ MAPA DIVIDIDO EN 7 REINOS de Game of Thrones")
        print("  • 👥 NPCs con animaciones (sprites)")
        print("  • 🏰 Estructuras escaladas (castillos, casas)")
        print("  • 🚶 Movimiento limitado a territorio propio (no agua)")
        print("  • 🌳 Sistema completo: relaciones, reproducción, guerras")
        print("  • 📜 Eventos narrativos y clima dinámico")
        print("  • 🎯 SISTEMA DE TAREAS INTELIGENTE con prioridades")
        print("  • 💰 RECURSOS: Oro, Comida, Madera con costos")
        print("  • 📊 PANEL DE ACTIVIDADES en tiempo real")
        print("\n🎮 CONTROLES:")
        print("  • Click en NPC: Ver información")
        print("  • Click en Castillo: Ver tareas del territorio")
        print("  • ESPACIO/Botón: Avanzar semana")
        print("  • P: Pausar/Reanudar")
        print("  • C: Toggle sistema de coordenadas")
        print("  • ESC: Cerrar paneles")
        print("  • Rueda ratón: Zoom")
        print("  • Click derecho + arrastrar: Mover cámara")
        print("  • Flechas: Mover cámara")
        print("  • Botones izquierdo: Spawn Rayo/Dragon manual")
        print("  • Botón Pruebas de Estrés: Asignar 100 tareas")
        print("\n" + "=" * 80)
        
        while self.ejecutando:
            self.manejar_eventos()
            self.actualizar()
            self.dibujar()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()