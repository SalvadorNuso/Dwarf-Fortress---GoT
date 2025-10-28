"""
rebeliones_got.py - Sistema de casas menores, vasallaje y rebeliones
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING
from enum import Enum
import random
from config_got import UBICACIONES_CASTILLOS

if TYPE_CHECKING:
    from npc_got import NPCGoT


class EstadoRebelion(Enum):
    """Estados de una rebelión"""
    LATENTE = "latente"              # Descontento creciente
    CONSPIRANDO = "conspirando"      # Planificación activa
    ACTIVA = "activa"                # Rebelión abierta
    SOFOCADA = "sofocada"            # Rebelión derrotada
    EXITOSA = "exitosa"              # Rebelión triunfante


class TipoCasaMenor(Enum):
    """Tipo de casa menor según su importancia"""
    LORD_MENOR = "Lord Menor"         # Pequeños señores
    CABALLERO_VASALLO = "Caballero"   # Caballeros con tierras
    BANNERMAN = "Bannerman"           # Vasallos importantes
    LORD_VASALLO = "Lord Vasallo"     # Señores vasallos de importancia


@dataclass
class CasaMenor:
    """Una casa menor/vasalla dentro de un reino"""
    nombre: str
    tipo: TipoCasaMenor
    reino: str  # Reino al que pertenece
    casa_señor: str  # Casa mayor a la que sirve
    
    # Recursos
    tropas: int = 500  # Menos tropas que casas mayores
    oro: int = 1000
    
    # Lealtad al señor (0-100)
    lealtad: int = 70
    
    # Ubicación aproximada
    posicion: tuple = (0, 0)
    
    # Lord de la casa menor
    lord_nombre: str = ""
    lord_id: Optional[str] = None
    lord: Optional['NPCGoT'] = None  # 🆕 Referencia al objeto NPC del lord
    
    # Estado
    en_rebelion: bool = False
    apoya_rebelion: bool = False
    
    def modificar_lealtad(self, cambio: int, razon: str = ""):
        """Modifica la lealtad de la casa menor"""
        self.lealtad = max(0, min(100, self.lealtad + cambio))
        return self.lealtad
    
    def evaluar_rebelion(self) -> bool:
        """Evalúa si la casa iniciará una rebelión"""
        if self.lealtad < 30:
            # Alta probabilidad de rebelión
            return random.random() < 0.4
        elif self.lealtad < 50:
            # Probabilidad media
            return random.random() < 0.1
        return False


@dataclass
class Rebelion:
    """Una rebelión dentro de un reino"""
    nombre: str
    reino: str
    fecha_inicio: int  # Semana
    
    # Casas involucradas
    casa_lider: str  # Casa menor que lidera
    casas_rebeldes: Set[str] = field(default_factory=set)  # Casas menores que se unen
    casa_objetivo: str = ""  # Casa mayor contra la que se rebelan
    
    # Fuerza militar
    tropas_rebeldes: int = 0
    tropas_leales: int = 0
    
    # Estado
    estado: EstadoRebelion = EstadoRebelion.LATENTE
    semanas_activa: int = 0
    
    # Demandas
    demandas: List[str] = field(default_factory=list)
    
    # Resultado
    exito: bool = False
    sofocada: bool = False
    nuevo_gobernante: Optional[str] = None
    
    def avanzar_semana(self):
        """Avanza la rebelión una semana"""
        self.semanas_activa += 1
        
        # Después de 10 semanas, evaluar resultado
        if self.semanas_activa >= 10:
            return self._evaluar_resultado()
        
        return None
    
    def _evaluar_resultado(self) -> str:
        """Evalúa el resultado de la rebelión"""
        # Comparar fuerzas
        ratio = self.tropas_rebeldes / max(1, self.tropas_leales)
        
        if ratio > 1.5:
            # Victoria rebelde clara
            self.estado = EstadoRebelion.EXITOSA
            self.exito = True
            return "victoria_rebelde"
        elif ratio < 0.6:
            # Victoria leal clara
            self.estado = EstadoRebelion.SOFOCADA
            self.sofocada = True
            return "rebelion_sofocada"
        else:
            # Continúa el conflicto
            return "continua"


class GestorRebeliones:
    """Gestiona casas menores y rebeliones dentro de los reinos"""
    
    def __init__(self):
        self.casas_menores: Dict[str, CasaMenor] = {}  # nombre_casa -> CasaMenor
        self.casas_por_reino: Dict[str, List[str]] = {}  # reino -> [nombres_casas_menores]
        self.rebeliones_activas: Dict[str, Rebelion] = {}  # nombre_rebelion -> Rebelion
        
        # Nombres de casas menores ficticias por región
        self.nombres_casas_norte = [
            "Karstark", "Umber", "Mormont", "Bolton", "Dustin", "Ryswell", 
            "Reed", "Manderly", "Cerwyn", "Tallhart", "Glover"
        ]
        self.nombres_casas_oeste = [
            "Clegane", "Payne", "Swyft", "Lefford", "Marbrand", "Brax",
            "Westerling", "Farman", "Banefort", "Lydden"
        ]
        self.nombres_casas_rios = [
            "Frey", "Blackwood", "Bracken", "Mallister", "Vance", "Piper",
            "Darry", "Mooton", "Ryger"
        ]
        self.nombres_casas_valle = [
            "Royce", "Corbray", "Waynwood", "Hunter", "Redfort", "Belmore",
            "Grafton", "Templeton"
        ]
        self.nombres_casas_islas = [
            "Harlaw", "Goodbrother", "Drumm", "Blacktyde", "Volmark",
            "Stonehouse", "Merlyn"
        ]
        self.nombres_casas_dominio = [
            "Tarly", "Hightower", "Redwyne", "Florent", "Fossoway", "Oakheart",
            "Crane", "Rowan", "Ashford"
        ]
        self.nombres_casas_tormenta = [
            "Connington", "Penrose", "Caron", "Swann", "Dondarrion", "Selmy",
            "Tarth", "Estermont"
        ]
        self.nombres_casas_dorne = [
            "Yronwood", "Dayne", "Fowler", "Uller", "Qorgyle", "Allyrion",
            "Blackmont", "Vaith", "Santagar"
        ]
    
    def crear_casas_menores_para_reino(self, reino: str, casa_mayor: str, 
                                       cantidad: int = 3) -> List[CasaMenor]:
        """Crea casas menores vasallas para un reino"""
        # Seleccionar nombres según la región
        nombres_disponibles = self._obtener_nombres_para_reino(reino)
        
        # Obtener posición del castillo de la casa mayor
        if casa_mayor in UBICACIONES_CASTILLOS:
            pos_castillo = UBICACIONES_CASTILLOS[casa_mayor]
        else:
            pos_castillo = (400, 400)  # Fallback
        
        casas_creadas = []
        for i in range(min(cantidad, len(nombres_disponibles))):
            nombre = nombres_disponibles[i]
            
            # Determinar tipo de casa menor
            if i == 0:
                tipo = TipoCasaMenor.BANNERMAN
                tropas = 800
                oro = 2000
            elif i < 2:
                tipo = TipoCasaMenor.LORD_VASALLO
                tropas = 600
                oro = 1500
            else:
                tipo = TipoCasaMenor.LORD_MENOR
                tropas = 400
                oro = 1000
            
            # Calcular posición cerca del castillo (distribuidas en círculo)
            angulo = (i / max(cantidad, 1)) * 360  # Distribuir en círculo
            radio = random.randint(80, 150)  # Distancia del castillo
            
            import math
            offset_x = int(radio * math.cos(math.radians(angulo)))
            offset_y = int(radio * math.sin(math.radians(angulo)))
            
            posicion = (
                pos_castillo[0] + offset_x,
                pos_castillo[1] + offset_y
            )
            
            # Crear casa menor
            casa_menor = CasaMenor(
                nombre=f"Casa {nombre}",
                tipo=tipo,
                reino=reino,
                casa_señor=casa_mayor,
                tropas=tropas,
                oro=oro,
                lealtad=random.randint(60, 90),
                posicion=posicion,  # 🆕 ASIGNAR POSICIÓN
                lord_nombre=f"Lord {nombre}"
            )
            
            self.casas_menores[casa_menor.nombre] = casa_menor
            casas_creadas.append(casa_menor)
            
            # Agregar al registro por reino
            if reino not in self.casas_por_reino:
                self.casas_por_reino[reino] = []
            self.casas_por_reino[reino].append(casa_menor.nombre)
        
        return casas_creadas
    
    def _obtener_nombres_para_reino(self, reino: str) -> List[str]:
        """Obtiene nombres de casas menores según el reino"""
        mapeo = {
            "El Norte": self.nombres_casas_norte,
            "Las Tierras del Oeste": self.nombres_casas_oeste,
            "Las Tierras de los Ríos": self.nombres_casas_rios,
            "El Valle": self.nombres_casas_valle,  # CORREGIDO: era "El Valle de Arryn"
            "Islas del Hierro": self.nombres_casas_islas,  # CORREGIDO: era "Las Islas del Hierro"
            "El Dominio": self.nombres_casas_dominio,
            "Las Tierras de la Tormenta": self.nombres_casas_tormenta,
            "Dorne": self.nombres_casas_dorne,
            "Rocadragón": [],  # No tiene casas menores (solo Targaryen)
        }
        return mapeo.get(reino, self.nombres_casas_norte[:])
    
    def actualizar_lealtades(self, reino: str, eventos: Dict[str, int]):
        """Actualiza las lealtades de las casas menores basado en eventos"""
        if reino not in self.casas_por_reino:
            return
        
        for nombre_casa in self.casas_por_reino[reino]:
            if nombre_casa in self.casas_menores:
                casa = self.casas_menores[nombre_casa]
                
                # Factores que afectan lealtad
                cambio = 0
                
                # Guerra larga reduce lealtad
                if eventos.get("en_guerra", 0) > 20:
                    cambio -= random.randint(1, 3)
                
                # Baja lealtad del reino reduce lealtad de vasallos
                if eventos.get("lealtad_reino", 70) < 40:
                    cambio -= random.randint(1, 2)
                
                # Alto oro aumenta lealtad
                if eventos.get("oro_reino", 0) > 50000:
                    cambio += 1
                
                # Aplicar cambio aleatorio natural
                cambio += random.randint(-1, 1)
                
                if cambio != 0:
                    casa.modificar_lealtad(cambio)
    
    def evaluar_posibles_rebeliones(self, semana_actual: int) -> List[str]:
        """Evalúa si alguna casa menor iniciará una rebelión"""
        nuevas_rebeliones = []
        
        for nombre_casa, casa in self.casas_menores.items():
            if casa.en_rebelion or casa.apoya_rebelion:
                continue
            
            if casa.evaluar_rebelion():
                # Iniciar rebelión
                nombre_rebelion = f"Rebelión de {nombre_casa}"
                
                rebelion = Rebelion(
                    nombre=nombre_rebelion,
                    reino=casa.reino,
                    fecha_inicio=semana_actual,
                    casa_lider=nombre_casa,
                    casa_objetivo=casa.casa_señor,
                    tropas_rebeldes=casa.tropas,
                    demandas=self._generar_demandas(casa)
                )
                
                rebelion.casas_rebeldes.add(nombre_casa)
                rebelion.estado = EstadoRebelion.CONSPIRANDO
                
                casa.en_rebelion = True
                
                # Buscar aliados entre otras casas descontentas
                for otra_casa_nombre in self.casas_por_reino.get(casa.reino, []):
                    if otra_casa_nombre != nombre_casa:
                        otra_casa = self.casas_menores.get(otra_casa_nombre)
                        if otra_casa and otra_casa.lealtad < 40 and random.random() < 0.5:
                            rebelion.casas_rebeldes.add(otra_casa_nombre)
                            rebelion.tropas_rebeldes += otra_casa.tropas
                            otra_casa.apoya_rebelion = True
                
                self.rebeliones_activas[nombre_rebelion] = rebelion
                nuevas_rebeliones.append(nombre_rebelion)
        
        return nuevas_rebeliones
    
    def _generar_demandas(self, casa: CasaMenor) -> List[str]:
        """Genera demandas para una rebelión"""
        demandas = []
        
        if casa.lealtad < 20:
            demandas.append("Independencia total del reino")
            demandas.append("Coronación de nuevo gobernante")
        elif casa.lealtad < 40:
            demandas.append("Mayor autonomía")
            demandas.append("Reducción de impuestos")
        else:
            demandas.append("Cambio de políticas")
            demandas.append("Compensación económica")
        
        return demandas
    
    def actualizar_rebeliones(self, tropas_leales_disponibles: int) -> Dict[str, str]:
        """Actualiza todas las rebeliones activas"""
        resultados = {}
        rebeliones_a_eliminar = []
        
        for nombre, rebelion in self.rebeliones_activas.items():
            # Asignar tropas leales si no están asignadas
            if rebelion.tropas_leales == 0:
                rebelion.tropas_leales = tropas_leales_disponibles
            
            # Avanzar la rebelión
            if rebelion.estado == EstadoRebelion.CONSPIRANDO:
                # Después de 2 semanas, se vuelve activa
                if rebelion.semanas_activa >= 2:
                    rebelion.estado = EstadoRebelion.ACTIVA
            
            resultado = rebelion.avanzar_semana()
            
            if resultado == "victoria_rebelde":
                resultados[nombre] = "victoria_rebelde"
                rebeliones_a_eliminar.append(nombre)
            elif resultado == "rebelion_sofocada":
                resultados[nombre] = "sofocada"
                # Penalizar casas rebeldes
                for casa_nombre in rebelion.casas_rebeldes:
                    if casa_nombre in self.casas_menores:
                        casa = self.casas_menores[casa_nombre]
                        casa.tropas = int(casa.tropas * 0.5)  # Pierden 50% tropas
                        casa.oro = int(casa.oro * 0.6)  # Pierden 40% oro
                        casa.lealtad = min(100, casa.lealtad + 30)  # Aumenta lealtad (sometidas)
                        casa.en_rebelion = False
                        casa.apoya_rebelion = False
                
                rebeliones_a_eliminar.append(nombre)
        
        # Eliminar rebeliones finalizadas
        for nombre in rebeliones_a_eliminar:
            del self.rebeliones_activas[nombre]
        
        return resultados
    
    def obtener_casas_de_reino(self, reino: str) -> List[CasaMenor]:
        """Obtiene todas las casas menores de un reino"""
        casas = []
        for nombre_casa in self.casas_por_reino.get(reino, []):
            if nombre_casa in self.casas_menores:
                casas.append(self.casas_menores[nombre_casa])
        return casas
    
    def obtener_todas_casas_menores(self) -> List[CasaMenor]:
        """Obtiene TODAS las casas menores de todos los reinos"""
        return list(self.casas_menores.values())
    
    def obtener_info_rebeliones(self) -> List[Dict]:
        """Obtiene información de todas las rebeliones activas"""
        info = []
        for nombre, rebelion in self.rebeliones_activas.items():
            info.append({
                "nombre": nombre,
                "reino": rebelion.reino,
                "estado": rebelion.estado.value,
                "casas_rebeldes": len(rebelion.casas_rebeldes),
                "tropas_rebeldes": rebelion.tropas_rebeldes,
                "tropas_leales": rebelion.tropas_leales,
                "semanas_activa": rebelion.semanas_activa
            })
        return info
