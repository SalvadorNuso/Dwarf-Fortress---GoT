"""
Sistema de Gestión de Tareas Optimizado para Game of Thrones
Usa Priority Heap + Deque para asignación inteligente y balanceada
"""

from collections import deque
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from priority_heap import PriorityHeap
from enum import Enum
import random


class NecesidadCasa(Enum):
    """Necesidades críticas de una casa"""
    CRITICA_ORO = "critica_oro"  # < 1000 oro
    CRITICA_COMIDA = "critica_comida"  # < 500 comida
    CRITICA_SOLDADOS = "critica_soldados"  # < 5000 soldados
    CRITICA_CONSTRUCCION = "critica_construccion"  # Edificios dañados
    NORMAL = "normal"


class TipoTarea(Enum):
    """Tipos de tareas disponibles"""
    MINERIA = "mineria"
    AGRICULTURA = "agricultura"
    COMERCIO = "comercio"
    ENTRENAMIENTO = "entrenamiento"
    CONSTRUCCION = "construccion"
    HERRERIA = "herreria"
    CARPINTERIA = "carpinteria"
    GUARDIA = "guardia"
    CAZA = "caza"
    PESCA = "pesca"
    ALQUIMIA = "alquimia"
    ESTUDIO = "estudio"
    ARTESANIA = "artesania"
    ADMINISTRACION = "administracion"


@dataclass
class Tarea:
    """Representa una tarea específica"""
    tipo: TipoTarea
    prioridad: int  # 1-10, donde 10 es más urgente
    duracion_semanas: int
    asignado_a: Optional[int] = None  # ID del NPC
    progreso: float = 0.0  # 0.0 - 1.0
    completada: bool = False
    
    # Recompensas al completar
    oro_ganado: int = 0
    comida_ganada: int = 0
    madera_ganada: int = 0  # 🆕 Madera obtenida al completar
    experiencia: int = 0
    
    # 🆕 Costos de recursos para iniciar
    costo_madera: int = 0  # Madera requerida para iniciar
    costo_comida: int = 0  # Comida requerida para iniciar
    recursos_consumidos: bool = False  # Si ya se consumieron los recursos
    
    # Metadata
    casa: str = ""
    ubicacion: Tuple[int, int] = (0, 0)
    id_tarea: int = field(default_factory=lambda: id(object()))  # ID único
    
    def __hash__(self):
        """Hacer hashable para uso en sets/dicts"""
        return self.id_tarea
    
    def __eq__(self, other):
        """Igualdad basada en ID"""
        if not isinstance(other, Tarea):
            return NotImplemented
        return self.id_tarea == other.id_tarea


@dataclass
class EstadoCasa:
    """Estado actual de recursos de una casa"""
    nombre: str
    oro: int
    comida: int
    soldados: int
    edificios_danados: int = 0
    npcs_activos: int = 0
    npcs_ociosos: int = 0
    
    def obtener_necesidad_critica(self) -> NecesidadCasa:
        """Determina la necesidad más crítica"""
        if self.oro < 1000:
            return NecesidadCasa.CRITICA_ORO
        elif self.comida < 500:
            return NecesidadCasa.CRITICA_COMIDA
        elif self.soldados < 5000:
            return NecesidadCasa.CRITICA_SOLDADOS
        elif self.edificios_danados > 0:
            return NecesidadCasa.CRITICA_CONSTRUCCION
        return NecesidadCasa.NORMAL


class GestorTareas:
    """
    Gestor inteligente de tareas usando:
    - Priority Heap: Para priorización dinámica
    - Deque: Para balanceo de carga entre NPCs
    """
    
    def __init__(self):
        self.heap_tareas = PriorityHeap()  # Tareas pendientes priorizadas
        self.cola_npcs_ociosos = deque()  # NPCs sin tarea
        self.tareas_activas: Dict[int, Tarea] = {}  # npc_id -> Tarea
        self.estados_casas: Dict[str, EstadoCasa] = {}
        
        # 🚀 OPTIMIZACIÓN: Índice de NPCs por oficio para acceso O(1)
        self.npcs_por_oficio: Dict[str, List[int]] = {}  # oficio_nombre -> [npc_ids]
        self.oficio_por_npc: Dict[int, str] = {}  # npc_id -> oficio_nombre
        
        # Configuración de prioridades dinámicas
        self.prioridades_base = {
            TipoTarea.MINERIA: 7,
            TipoTarea.AGRICULTURA: 8,
            TipoTarea.COMERCIO: 7,
            TipoTarea.ENTRENAMIENTO: 6,
            TipoTarea.CONSTRUCCION: 9,
            TipoTarea.HERRERIA: 7,
            TipoTarea.CARPINTERIA: 6,
            TipoTarea.GUARDIA: 5,
            TipoTarea.CAZA: 6,
            TipoTarea.PESCA: 5,
            TipoTarea.ALQUIMIA: 4,
            TipoTarea.ESTUDIO: 3,
            TipoTarea.ARTESANIA: 4,
            TipoTarea.ADMINISTRACION: 8,
        }
        
        # Relación necesidad -> tipo de tarea prioritaria
        self.tareas_para_necesidad = {
            NecesidadCasa.CRITICA_ORO: [TipoTarea.MINERIA, TipoTarea.COMERCIO],
            NecesidadCasa.CRITICA_COMIDA: [TipoTarea.AGRICULTURA, TipoTarea.CAZA, TipoTarea.PESCA],
            NecesidadCasa.CRITICA_SOLDADOS: [TipoTarea.ENTRENAMIENTO, TipoTarea.HERRERIA],
            NecesidadCasa.CRITICA_CONSTRUCCION: [TipoTarea.CONSTRUCCION, TipoTarea.CARPINTERIA],
            NecesidadCasa.NORMAL: []  # Tareas generales
        }
    
    def actualizar_estado_casa(self, casa: str, oro: int, comida: int, 
                               soldados: int, npcs_activos: int, npcs_ociosos: int,
                               edificios_danados: int = 0):
        """Actualiza el estado de recursos de una casa"""
        self.estados_casas[casa] = EstadoCasa(
            nombre=casa,
            oro=oro,
            comida=comida,
            soldados=soldados,
            edificios_danados=edificios_danados,
            npcs_activos=npcs_activos,
            npcs_ociosos=npcs_ociosos
        )
        
        # Si hay NPCs ociosos, generar tareas urgentes
        if npcs_ociosos > 0:
            self._generar_tareas_para_casa(casa)
    
    def _generar_tareas_para_casa(self, casa: str):
        """Genera tareas basadas en las necesidades de la casa"""
        if casa not in self.estados_casas:
            return
        
        estado = self.estados_casas[casa]
        necesidad = estado.obtener_necesidad_critica()
        
        # Generar 2-5 tareas según la necesidad
        num_tareas = min(estado.npcs_ociosos, random.randint(2, 5))
        
        for _ in range(num_tareas):
            tipo_tarea = self._seleccionar_tipo_tarea(necesidad)
            prioridad = self._calcular_prioridad_dinamica(tipo_tarea, necesidad)
            
            tarea = Tarea(
                tipo=tipo_tarea,
                prioridad=prioridad,
                duracion_semanas=self._duracion_por_tipo(tipo_tarea),
                casa=casa,
                oro_ganado=self._recompensa_oro(tipo_tarea),
                comida_ganada=self._recompensa_comida(tipo_tarea),
                madera_ganada=self._recompensa_madera(tipo_tarea),
                costo_madera=self._costo_madera(tipo_tarea),  # 🆕 Costo en madera
                costo_comida=self._costo_comida(tipo_tarea),  # 🆕 Costo en comida
                experiencia=10
            )
            
            self.agregar_tarea(tarea)
    
    def _seleccionar_tipo_tarea(self, necesidad: NecesidadCasa) -> TipoTarea:
        """Selecciona tipo de tarea según necesidad"""
        if necesidad != NecesidadCasa.NORMAL:
            tareas_criticas = self.tareas_para_necesidad[necesidad]
            if tareas_criticas:
                return random.choice(tareas_criticas)
        
        # Si no hay necesidad crítica, tarea aleatoria
        return random.choice(list(TipoTarea))
    
    def _calcular_prioridad_dinamica(self, tipo: TipoTarea, necesidad: NecesidadCasa) -> int:
        """Calcula prioridad dinámica según necesidad"""
        prioridad_base = self.prioridades_base[tipo]
        
        # Boost de +3 si la tarea satisface una necesidad crítica
        if necesidad != NecesidadCasa.NORMAL:
            tareas_criticas = self.tareas_para_necesidad[necesidad]
            if tipo in tareas_criticas:
                prioridad_base = min(10, prioridad_base + 3)
        
        return prioridad_base
    
    def _duracion_por_tipo(self, tipo: TipoTarea) -> int:
        """Duración en semanas por tipo de tarea"""
        duraciones = {
            TipoTarea.MINERIA: 3,
            TipoTarea.AGRICULTURA: 2,
            TipoTarea.COMERCIO: 2,
            TipoTarea.ENTRENAMIENTO: 2,
            TipoTarea.CONSTRUCCION: 4,
            TipoTarea.HERRERIA: 3,
            TipoTarea.CARPINTERIA: 2,
            TipoTarea.GUARDIA: 999,  # Continuo
            TipoTarea.CAZA: 1,
            TipoTarea.PESCA: 1,
            TipoTarea.ALQUIMIA: 5,
            TipoTarea.ESTUDIO: 4,
            TipoTarea.ARTESANIA: 3,
            TipoTarea.ADMINISTRACION: 999,  # Continuo
        }
        return duraciones.get(tipo, 2)
    
    def _recompensa_oro(self, tipo: TipoTarea) -> int:
        """Oro ganado al completar tarea"""
        recompensas = {
            TipoTarea.MINERIA: 50,
            TipoTarea.COMERCIO: 80,
            TipoTarea.HERRERIA: 50,
            TipoTarea.CARPINTERIA: 40,
            TipoTarea.ARTESANIA: 30,
            TipoTarea.CONSTRUCCION: 100,
        }
        return recompensas.get(tipo, 0)
    
    def _recompensa_comida(self, tipo: TipoTarea) -> int:
        """Comida ganada al completar tarea"""
        recompensas = {
            TipoTarea.AGRICULTURA: 30,
            TipoTarea.CAZA: 25,
            TipoTarea.PESCA: 20,
        }
        return recompensas.get(tipo, 0)
    
    def _recompensa_madera(self, tipo: TipoTarea) -> int:
        """Madera ganada al completar tarea"""
        recompensas = {
            TipoTarea.CARPINTERIA: 15,
            TipoTarea.CONSTRUCCION: 10,  # También genera algo de madera procesada
        }
        return recompensas.get(tipo, 0)
    
    def _costo_madera(self, tipo: TipoTarea) -> int:
        """Madera requerida para iniciar tarea"""
        costos = {
            TipoTarea.CONSTRUCCION: random.randint(150, 300),  # Construcción requiere mucha madera
            TipoTarea.CARPINTERIA: random.randint(50, 100),
            TipoTarea.HERRERIA: random.randint(20, 40),  # Carbón/leña
        }
        return costos.get(tipo, 0)
    
    def _costo_comida(self, tipo: TipoTarea) -> int:
        """Comida requerida para iniciar tarea (alimentar trabajadores)"""
        costos = {
            TipoTarea.CONSTRUCCION: random.randint(100, 200),
            TipoTarea.MINERIA: random.randint(50, 100),
            TipoTarea.CARPINTERIA: random.randint(30, 60),
            TipoTarea.ENTRENAMIENTO: random.randint(40, 80),
        }
        return costos.get(tipo, 0)
    
    def puede_iniciar_tarea(self, tarea: Tarea, casa) -> Tuple[bool, str]:
        """
        Verifica si una casa tiene recursos para iniciar una tarea
        Retorna: (puede_iniciar, mensaje_error)
        """
        if not hasattr(casa, 'madera'):
            return True, ""  # Casa antigua sin sistema de recursos
        
        if tarea.recursos_consumidos:
            return True, ""  # Ya se consumieron recursos
        
        # Verificar madera
        if tarea.costo_madera > 0:
            if casa.madera < tarea.costo_madera:
                return False, f"⚠️ Falta madera (necesitas {tarea.costo_madera}, tienes {casa.madera})"
        
        # Verificar comida
        if tarea.costo_comida > 0:
            if casa.comida < tarea.costo_comida:
                return False, f"⚠️ Falta comida (necesitas {tarea.costo_comida}, tienes {casa.comida})"
        
        return True, ""
    
    def consumir_recursos_tarea(self, tarea: Tarea, casa) -> bool:
        """
        Consume recursos de la casa al iniciar tarea
        Retorna: True si se consumieron recursos
        """
        if tarea.recursos_consumidos:
            return False
        
        if not hasattr(casa, 'madera'):
            return False
        
        # Consumir madera
        if tarea.costo_madera > 0:
            casa.madera -= tarea.costo_madera
        
        # Consumir comida
        if tarea.costo_comida > 0:
            casa.comida -= tarea.costo_comida
        
        tarea.recursos_consumidos = True
        return True
    
    def agregar_tarea(self, tarea: Tarea):
        """Agrega una tarea al heap CON su prioridad correcta"""
        # OPTIMIZACIÓN: Usar prioridad del heap en lugar de __lt__ de Tarea
        # Prioridad más BAJA = más urgente (se procesa primero)
        # Invertir prioridad: 10 (urgente) -> 0, 1 (baja) -> 9
        prioridad_heap = 10 - tarea.prioridad
        self.heap_tareas.push(tarea, priority=prioridad_heap)
    
    def registrar_npc_ocioso(self, npc_id: int):
        """Registra un NPC sin tarea en el deque"""
        if npc_id not in self.cola_npcs_ociosos:
            self.cola_npcs_ociosos.append(npc_id)
    
    def asignar_tareas_automaticamente(self, casas_dict=None) -> List[Tuple[int, Tarea, Optional[str]]]:
        """
        Asigna tareas a NPCs ociosos automáticamente
        Retorna: Lista de tuplas (npc_id, tarea, mensaje_error_opcional)
        """
        asignaciones = []
        tareas_rechazadas_consecutivas = 0
        max_rechazos = min(len(self.cola_npcs_ociosos), self.heap_tareas.size(), 100)
        
        while self.cola_npcs_ociosos and not self.heap_tareas.is_empty():
            # 🛡️ Protección contra bucle infinito
            if tareas_rechazadas_consecutivas >= max_rechazos:
                # Todas las tareas disponibles fueron rechazadas, salir del bucle
                break
            
            # Obtener NPC ocioso (FIFO con deque)
            npc_id = self.cola_npcs_ociosos.popleft()
            
            # Obtener tarea de mayor prioridad (heap)
            tarea = self.heap_tareas.pop()
            
            if tarea:
                # 🆕 Verificar recursos si se proporcionó diccionario de casas
                mensaje_error = None
                if casas_dict and tarea.casa in casas_dict:
                    casa = casas_dict[tarea.casa]
                    puede_iniciar, mensaje = self.puede_iniciar_tarea(tarea, casa)
                    
                    if not puede_iniciar:
                        # No se puede iniciar - devolver tarea al heap CON prioridad
                        prioridad_heap = 10 - tarea.prioridad
                        self.heap_tareas.push(tarea, priority=prioridad_heap)
                        mensaje_error = mensaje
                        asignaciones.append((npc_id, None, mensaje_error))
                        # NPC vuelve a estar ocioso
                        self.registrar_npc_ocioso(npc_id)
                        tareas_rechazadas_consecutivas += 1
                        continue
                
                # Asignar tarea exitosamente - resetear contador
                tarea.asignado_a = npc_id
                self.tareas_activas[npc_id] = tarea
                asignaciones.append((npc_id, tarea, None))
                tareas_rechazadas_consecutivas = 0
        
        return asignaciones
    
    def actualizar_progreso(self, npc_id: int, incremento: float = 0.1):
        """Actualiza el progreso de una tarea"""
        if npc_id in self.tareas_activas:
            tarea = self.tareas_activas[npc_id]
            tarea.progreso = min(1.0, tarea.progreso + incremento)
            
            # Si completada, marcar y liberar NPC
            if tarea.progreso >= 1.0:
                tarea.completada = True
                return self.completar_tarea(npc_id)
        
        return None
    
    def completar_tarea(self, npc_id: int) -> Optional[Tarea]:
        """Marca tarea como completada y libera NPC"""
        if npc_id in self.tareas_activas:
            tarea = self.tareas_activas[npc_id]
            del self.tareas_activas[npc_id]
            
            # NPC vuelve a estar ocioso
            self.registrar_npc_ocioso(npc_id)
            
            return tarea
        
        return None
    
    def reasignar_si_necesario(self, casa: str):
        """
        Reasigna tareas si cambian las necesidades críticas
        Cancela tareas de baja prioridad para hacer tareas urgentes
        """
        if casa not in self.estados_casas:
            return
        
        estado = self.estados_casas[casa]
        necesidad = estado.obtener_necesidad_critica()
        
        # Si hay necesidad crítica, buscar NPCs con tareas no críticas
        if necesidad != NecesidadCasa.NORMAL:
            tareas_criticas_tipos = self.tareas_para_necesidad[necesidad]
            
            # Buscar NPCs con tareas de baja prioridad
            npcs_para_reasignar = []
            for npc_id, tarea in list(self.tareas_activas.items()):
                if tarea.casa == casa and tarea.tipo not in tareas_criticas_tipos:
                    if tarea.prioridad < 7:  # Solo cancelar tareas de baja prioridad
                        npcs_para_reasignar.append(npc_id)
            
            # Cancelar hasta 2 tareas para reasignar
            for npc_id in npcs_para_reasignar[:2]:
                tarea_vieja = self.tareas_activas[npc_id]
                del self.tareas_activas[npc_id]
                
                # Crear nueva tarea crítica
                tipo_critico = random.choice(tareas_criticas_tipos)
                nueva_tarea = Tarea(
                    tipo=tipo_critico,
                    prioridad=10,  # Máxima prioridad
                    duracion_semanas=self._duracion_por_tipo(tipo_critico),
                    asignado_a=npc_id,
                    casa=casa,
                    oro_ganado=self._recompensa_oro(tipo_critico),
                    comida_ganada=self._recompensa_comida(tipo_critico),
                    madera_ganada=self._recompensa_madera(tipo_critico),
                    experiencia=15
                )
                
                self.tareas_activas[npc_id] = nueva_tarea
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas del gestor"""
        return {
            "tareas_pendientes": self.heap_tareas.size(),
            "tareas_activas": len(self.tareas_activas),
            "npcs_ociosos": len(self.cola_npcs_ociosos),
            "casas_monitoreadas": len(self.estados_casas)
        }
    
    def obtener_tarea_activa(self, npc_id: int) -> Optional[Tarea]:
        """Obtiene la tarea actual de un NPC"""
        return self.tareas_activas.get(npc_id)
    
    def hay_npcs_ociosos(self) -> bool:
        """Verifica si hay NPCs sin tarea"""
        return len(self.cola_npcs_ociosos) > 0
    
    def registrar_oficio_npc(self, npc_id: int, oficio_nombre: str):
        """
        🚀 OPTIMIZACIÓN: Registra el oficio de un NPC en el índice
        Permite acceso O(1) a NPCs por oficio
        """
        # Remover del oficio anterior si existía
        if npc_id in self.oficio_por_npc:
            oficio_anterior = self.oficio_por_npc[npc_id]
            if oficio_anterior in self.npcs_por_oficio:
                if npc_id in self.npcs_por_oficio[oficio_anterior]:
                    self.npcs_por_oficio[oficio_anterior].remove(npc_id)
        
        # Agregar al nuevo oficio
        if oficio_nombre not in self.npcs_por_oficio:
            self.npcs_por_oficio[oficio_nombre] = []
        
        if npc_id not in self.npcs_por_oficio[oficio_nombre]:
            self.npcs_por_oficio[oficio_nombre].append(npc_id)
        
        self.oficio_por_npc[npc_id] = oficio_nombre
    
    def obtener_npcs_por_oficio(self, oficio_nombre: str) -> List[int]:
        """
        🚀 OPTIMIZACIÓN: Obtiene NPCs con un oficio específico en O(1)
        En lugar de filtrar toda la lista de NPCs
        """
        return self.npcs_por_oficio.get(oficio_nombre, [])
    
    def remover_npc_del_indice(self, npc_id: int):
        """
        🚀 OPTIMIZACIÓN: Remueve NPC del índice (cuando muere o cambia de estado)
        """
        if npc_id in self.oficio_por_npc:
            oficio = self.oficio_por_npc[npc_id]
            if oficio in self.npcs_por_oficio:
                if npc_id in self.npcs_por_oficio[oficio]:
                    self.npcs_por_oficio[oficio].remove(npc_id)
            del self.oficio_por_npc[npc_id]
    
    def forzar_asignacion_completa(self, npcs_disponibles: List[int], casa: str, casas_dict=None):
        """
        Fuerza asignación de tareas a TODOS los NPCs disponibles
        Genera tareas si es necesario
        Retorna: Lista de tuplas (npc_id, tarea, mensaje_error_opcional)
        OPTIMIZADO: Limita generación de tareas y evita bucles infinitos
        """
        # Agregar todos los NPCs al deque si no están ya
        for npc_id in npcs_disponibles:
            if npc_id not in self.tareas_activas and npc_id not in self.cola_npcs_ociosos:
                self.registrar_npc_ocioso(npc_id)
        
        # Generar tareas suficientes (OPTIMIZADO: máximo 100 tareas pendientes)
        npcs_sin_tarea = len(self.cola_npcs_ociosos)
        tareas_pendientes = self.heap_tareas.size()
        
        if npcs_sin_tarea > 0 and tareas_pendientes < 100:
            # Generar solo las tareas necesarias, máximo 50 por vez
            tareas_a_generar = min(npcs_sin_tarea, 50, 100 - tareas_pendientes)
            
            # 🚀 OPTIMIZACIÓN: Priorizar tareas sin costo de recursos si la casa está baja
            estado_casa = self.estados_casas.get(casa)
            casa_obj = casas_dict.get(casa) if casas_dict else None
            tiene_pocos_recursos = False
            
            if casa_obj:
                madera_disponible = getattr(casa_obj, 'madera', 1000)
                comida_disponible = getattr(casa_obj, 'comida', 1000)
                tiene_pocos_recursos = madera_disponible < 100 or comida_disponible < 100
            
            for _ in range(tareas_a_generar):
                # Si tiene pocos recursos, priorizar tareas que no cuestan recursos
                if tiene_pocos_recursos and random.random() < 0.7:
                    # Tareas que generan recursos sin costo
                    tipos_gratis = [TipoTarea.MINERIA, TipoTarea.AGRICULTURA, TipoTarea.CAZA, 
                                   TipoTarea.PESCA, TipoTarea.COMERCIO, TipoTarea.GUARDIA]
                    tipo_tarea = random.choice(tipos_gratis)
                else:
                    tipo_tarea = random.choice(list(TipoTarea))
                
                necesidad = estado_casa.obtener_necesidad_critica() if estado_casa else NecesidadCasa.NORMAL
                prioridad = self._calcular_prioridad_dinamica(tipo_tarea, necesidad)
                
                tarea = Tarea(
                    tipo=tipo_tarea,
                    prioridad=prioridad,
                    duracion_semanas=self._duracion_por_tipo(tipo_tarea),
                    casa=casa,
                    oro_ganado=self._recompensa_oro(tipo_tarea),
                    comida_ganada=self._recompensa_comida(tipo_tarea),
                    madera_ganada=self._recompensa_madera(tipo_tarea),
                    costo_madera=self._costo_madera(tipo_tarea),  # 🆕
                    costo_comida=self._costo_comida(tipo_tarea),  # 🆕
                    experiencia=10
                )
                
                self.agregar_tarea(tarea)
        
        # Asignar tareas con validación de recursos
        return self.asignar_tareas_automaticamente(casas_dict)
