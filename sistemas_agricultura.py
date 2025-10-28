"""
sistemas_agricultura.py - Sistema de agricultura y ganadería
Game of Thrones: Simulador Político

Sistema realista de producción de alimentos:
- Campos de cultivo por tipo (trigo, maíz, cebada, etc.)
- Solo en terreno cultivable (praderas, llanuras)
- Animales domésticos con NPCs cuidadores
- Producción de comida por casa
"""
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class TipoCultivo(Enum):
    """Tipos de cultivos"""
    TRIGO = "trigo"
    MAIZ = "maíz"
    CEBADA = "cebada"
    CENTENO = "centeno"
    VERDURAS = "verduras"
    NABOS = "nabos"


class TipoTerreno(Enum):
    """Tipos de terreno del mapa"""
    PRADERA = "pradera"
    LLANURA = "llanura"
    BOSQUE = "bosque"
    MONTAÑA = "montaña"
    COLINA = "colina"
    AGUA = "agua"


@dataclass
class Campo:
    """Un campo de cultivo"""
    x: float
    y: float
    ancho: float = 60
    alto: float = 60
    tipo_cultivo: TipoCultivo = TipoCultivo.TRIGO
    casa: str = ""  # Casa propietaria
    
    # Estado del cultivo
    semanas_crecimiento: int = 0  # 0 = recién plantado, 8 = maduro
    semanas_para_cosecha: int = 8
    cosechado: bool = False
    
    # NPCs trabajando
    npc_id: Optional[int] = None  # ID del NPC que trabaja este campo
    
    def actualizar(self):
        """Actualiza el crecimiento del cultivo"""
        if not self.cosechado and self.semanas_crecimiento < self.semanas_para_cosecha:
            self.semanas_crecimiento += 1
    
    def esta_listo_para_cosechar(self) -> bool:
        """Verifica si el cultivo está maduro"""
        return self.semanas_crecimiento >= self.semanas_para_cosecha and not self.cosechado
    
    def cosechar(self) -> int:
        """Cosecha el campo y retorna cantidad de comida"""
        if self.esta_listo_para_cosechar():
            self.cosechado = True
            # Producción según tipo
            produccion = {
                TipoCultivo.TRIGO: 150,
                TipoCultivo.MAIZ: 120,
                TipoCultivo.CEBADA: 100,
                TipoCultivo.CENTENO: 110,
                TipoCultivo.VERDURAS: 80,
                TipoCultivo.NABOS: 90,
            }
            return produccion.get(self.tipo_cultivo, 100)
        return 0
    
    def resembrar(self):
        """Vuelve a plantar el campo"""
        self.semanas_crecimiento = 0
        self.cosechado = False


@dataclass
class Rebano:
    """Un rebaño de animales domésticos"""
    x: float
    y: float
    tipo_animal: str  # "vaca", "oveja", "cerdo", etc.
    cantidad: int = 10
    casa: str = ""
    
    # NPCs cuidadores
    npc_pastor_id: Optional[int] = None
    
    def producir_comida(self) -> int:
        """Produce comida del rebaño (leche, carne, huevos)"""
        produccion_por_animal = {
            "vaca": 5,      # Leche diaria
            "oveja": 3,     # Lana + carne
            "cerdo": 4,     # Carne
            "cabra": 3,     # Leche + carne
            "gallina": 2,   # Huevos
            "caballo": 0,   # No se come (transporte)
        }
        return produccion_por_animal.get(self.tipo_animal, 2) * self.cantidad


class GestorAgricultura:
    """Gestor del sistema de agricultura y ganadería"""
    
    def __init__(self):
        self.campos: List[Campo] = []
        self.rebanos: List[Rebano] = []
        self.mapa_terreno: dict = {}  # Cache de tipo de terreno por posición
    
    def determinar_tipo_terreno(self, x: float, y: float, mundo_ancho: int, mundo_alto: int) -> TipoTerreno:
        """Determina el tipo de terreno en una posición"""
        # Usar posición para determinar bioma de forma procedural
        
        # Bordes del mapa = agua (ríos/mar)
        margen = 50
        if x < margen or x > mundo_ancho - margen or y < margen or y > mundo_alto - margen:
            return TipoTerreno.AGUA
        
        # Usar coordenadas para determinar terreno
        # Centro del mapa = más praderas/llanuras (cultivable)
        centro_x = mundo_ancho / 2
        centro_y = mundo_alto / 2
        
        distancia_centro = ((x - centro_x)**2 + (y - centro_y)**2)**0.5
        max_distancia = ((centro_x**2 + centro_y**2)**0.5)
        
        # Ruido pseudo-aleatorio basado en posición
        seed_x = int(x / 100)
        seed_y = int(y / 100)
        ruido = ((seed_x * 12345 + seed_y * 67890) % 100) / 100.0
        
        # Cerca del centro = praderas y llanuras (cultivable)
        if distancia_centro < max_distancia * 0.4:
            if ruido < 0.6:
                return TipoTerreno.PRADERA
            elif ruido < 0.8:
                return TipoTerreno.LLANURA
            else:
                return TipoTerreno.BOSQUE
        
        # Zona media = bosques y colinas
        elif distancia_centro < max_distancia * 0.7:
            if ruido < 0.3:
                return TipoTerreno.PRADERA
            elif ruido < 0.5:
                return TipoTerreno.LLANURA
            elif ruido < 0.75:
                return TipoTerreno.BOSQUE
            else:
                return TipoTerreno.COLINA
        
        # Zona exterior = montañas y bosques
        else:
            if ruido < 0.2:
                return TipoTerreno.COLINA
            elif ruido < 0.4:
                return TipoTerreno.BOSQUE
            else:
                return TipoTerreno.MONTAÑA
    
    def es_terreno_cultivable(self, x: float, y: float, mundo_ancho: int, mundo_alto: int) -> bool:
        """Verifica si un terreno es cultivable"""
        terreno = self.determinar_tipo_terreno(x, y, mundo_ancho, mundo_alto)
        return terreno in [TipoTerreno.PRADERA, TipoTerreno.LLANURA]
    
    def inicializar_campos(self, casas: dict, ubicaciones_castillos: dict, mundo_ancho: int, mundo_alto: int):
        """Crea campos de cultivo alrededor de cada casa"""
        for casa_nombre, posicion_castillo in ubicaciones_castillos.items():
            if casa_nombre not in casas:
                continue
            
            casa = casas[casa_nombre]
            # Número de campos según población
            miembros_vivos = len([npc for npc in casa.miembros if npc.vivo])
            num_campos = max(3, miembros_vivos // 5)  # 1 campo por cada 5 personas
            
            campos_creados = 0
            intentos = 0
            max_intentos = 100
            
            while campos_creados < num_campos and intentos < max_intentos:
                # Buscar posición cercana al castillo
                angulo = random.uniform(0, 6.28)  # 2*pi
                distancia = random.uniform(100, 300)
                
                x = posicion_castillo[0] + distancia * random.uniform(-1, 1)
                y = posicion_castillo[1] + distancia * random.uniform(-1, 1)
                
                # Verificar si es cultivable
                if self.es_terreno_cultivable(x, y, mundo_ancho, mundo_alto):
                    # Tipo de cultivo aleatorio con pesos
                    tipo_cultivo = random.choices(
                        [TipoCultivo.TRIGO, TipoCultivo.MAIZ, TipoCultivo.CEBADA, 
                         TipoCultivo.CENTENO, TipoCultivo.VERDURAS, TipoCultivo.NABOS],
                        weights=[30, 20, 20, 10, 15, 5]
                    )[0]
                    
                    campo = Campo(
                        x=x, y=y,
                        ancho=random.uniform(50, 80),
                        alto=random.uniform(50, 80),
                        tipo_cultivo=tipo_cultivo,
                        casa=casa_nombre,
                        semanas_crecimiento=random.randint(0, 8)  # Estados variados
                    )
                    self.campos.append(campo)
                    campos_creados += 1
                
                intentos += 1
    
    def inicializar_rebanos(self, casas: dict, ubicaciones_castillos: dict):
        """Crea rebaños de animales domésticos para cada casa"""
        for casa_nombre, posicion_castillo in ubicaciones_castillos.items():
            if casa_nombre not in casas:
                continue
            
            # Tipos de ganado por casa
            tipos_ganado = ["vaca", "oveja", "cerdo", "cabra", "gallina"]
            
            for tipo in random.sample(tipos_ganado, k=random.randint(2, 4)):
                # Posición cerca del castillo
                x = posicion_castillo[0] + random.uniform(-200, 200)
                y = posicion_castillo[1] + random.uniform(-200, 200)
                
                rebano = Rebano(
                    x=x, y=y,
                    tipo_animal=tipo,
                    cantidad=random.randint(5, 20),
                    casa=casa_nombre
                )
                self.rebanos.append(rebano)
    
    def actualizar_agricultura(self):
        """Actualiza todos los campos (crecimiento)"""
        for campo in self.campos:
            campo.actualizar()
    
    def cosechar_campos_maduros(self, casas: dict) -> dict:
        """Cosecha campos maduros y retorna producción por casa"""
        produccion = {}
        
        for campo in self.campos:
            if campo.esta_listo_para_cosechar():
                comida = campo.cosechar()
                if campo.casa in produccion:
                    produccion[campo.casa] += comida
                else:
                    produccion[campo.casa] = comida
                
                # Resembrar automáticamente
                campo.resembrar()
        
        # Agregar comida a las casas
        for casa_nombre, cantidad in produccion.items():
            if casa_nombre in casas:
                if hasattr(casas[casa_nombre], 'comida'):
                    casas[casa_nombre].comida += cantidad
        
        return produccion
    
    def producir_de_rebanos(self, casas: dict) -> dict:
        """Produce comida de los rebaños cada semana"""
        produccion = {}
        
        for rebano in self.rebanos:
            comida = rebano.producir_comida()
            if rebano.casa in produccion:
                produccion[rebano.casa] += comida
            else:
                produccion[rebano.casa] = comida
        
        # Agregar comida a las casas
        for casa_nombre, cantidad in produccion.items():
            if casa_nombre in casas:
                if hasattr(casas[casa_nombre], 'comida'):
                    casas[casa_nombre].comida += cantidad
        
        return produccion
    
    def obtener_campos_en_viewport(self, camara, mundo_ancho: int, mundo_alto: int) -> List[Campo]:
        """Retorna solo los campos visibles en la cámara"""
        # Obtener bounds del viewport
        try:
            x_min, y_min, x_max, y_max = camara.obtener_viewport_bounds(1600, 900)
        except:
            # Fallback si hay error
            return self.campos[:50]  # Retornar primeros 50
        
        campos_visibles = []
        for campo in self.campos:
            # Verificar si el campo está en el viewport
            if (x_min - campo.ancho <= campo.x <= x_max + campo.ancho and
                y_min - campo.alto <= campo.y <= y_max + campo.alto):
                campos_visibles.append(campo)
        
        return campos_visibles
    
    def obtener_rebanos_en_viewport(self, camara) -> List[Rebano]:
        """Retorna solo los rebaños visibles en la cámara"""
        try:
            x_min, y_min, x_max, y_max = camara.obtener_viewport_bounds(1600, 900)
        except:
            return self.rebanos[:20]
        
        rebanos_visibles = []
        for rebano in self.rebanos:
            margen = 100
            if (x_min - margen <= rebano.x <= x_max + margen and
                y_min - margen <= rebano.y <= y_max + margen):
                rebanos_visibles.append(rebano)
        
        return rebanos_visibles
