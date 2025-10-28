"""
jerarquia_got.py - Sistema de Jerarquía Social y Árbol Genealógico
Maneja rangos sociales, organización por trabajo y familias nobles
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum


class RangoSocial(Enum):
    """Rangos sociales en orden descendente de jerarquía"""
    REY = "Rey/Reina"                      # 10 - Gobernante del reino
    PRINCIPE = "Príncipe/Princesa"         # 9 - Herederos
    LORD_SUPREMO = "Lord/Lady Supremo"     # 8 - Familia del gobernante
    LORD = "Lord/Lady"                     # 7 - Nobles menores
    CABALLERO = "Ser (Caballero)"          # 6 - Caballeros
    MAESTRE = "Maestre"                    # 5 - Eruditos
    COMANDANTE = "Comandante"              # 4 - Militares
    ARTESANO_MAESTRO = "Maestro Artesano"  # 3 - Artesanos expertos
    GUARDIA = "Guardia"                    # 2 - Soldados
    PLEBEYO = "Plebeyo"                    # 1 - Gente común
    SIERVO = "Siervo"                      # 0 - Trabajadores


@dataclass
class NodoFamiliar:
    """Nodo del árbol genealógico"""
    npc_id: str
    nombre: str
    es_gobernante: bool = False
    conyuge_id: Optional[str] = None
    padre_id: Optional[str] = None
    madre_id: Optional[str] = None
    hijos_ids: List[str] = field(default_factory=list)
    rango: RangoSocial = RangoSocial.PLEBEYO


@dataclass
class JerarquiaReino:
    """Jerarquía completa de un reino"""
    nombre_reino: str
    casa_gobernante: str
    gobernante_id: Optional[str] = None
    
    # Organización por rango
    por_rango: Dict[RangoSocial, List[str]] = field(default_factory=dict)
    
    # Árbol genealógico de la familia gobernante
    arbol_familiar: Dict[str, NodoFamiliar] = field(default_factory=dict)
    
    # Organización por trabajo/profesión
    mineros: List[str] = field(default_factory=list)
    agricultores: List[str] = field(default_factory=list)
    soldados: List[str] = field(default_factory=list)
    artesanos: List[str] = field(default_factory=list)
    comerciantes: List[str] = field(default_factory=list)
    guardias: List[str] = field(default_factory=list)
    maestres: List[str] = field(default_factory=list)
    
    def agregar_npc(self, npc_id: str, nombre: str, rango: RangoSocial):
        """Agrega un NPC a la jerarquía"""
        if rango not in self.por_rango:
            self.por_rango[rango] = []
        
        if npc_id not in self.por_rango[rango]:
            self.por_rango[rango].append(npc_id)
    
    def establecer_gobernante(self, npc_id: str, nombre: str):
        """Establece el gobernante del reino"""
        self.gobernante_id = npc_id
        self.agregar_npc(npc_id, nombre, RangoSocial.REY)
        
        # Crear nodo en árbol familiar
        if npc_id not in self.arbol_familiar:
            self.arbol_familiar[npc_id] = NodoFamiliar(
                npc_id=npc_id,
                nombre=nombre,
                es_gobernante=True,
                rango=RangoSocial.REY
            )
    
    def agregar_familiar(self, npc_id: str, nombre: str, rango: RangoSocial,
                        padre_id: Optional[str] = None,
                        madre_id: Optional[str] = None,
                        conyuge_id: Optional[str] = None):
        """Agrega un miembro de la familia gobernante al árbol"""
        nodo = NodoFamiliar(
            npc_id=npc_id,
            nombre=nombre,
            padre_id=padre_id,
            madre_id=madre_id,
            conyuge_id=conyuge_id,
            rango=rango
        )
        
        self.arbol_familiar[npc_id] = nodo
        self.agregar_npc(npc_id, nombre, rango)
        
        # Actualizar relaciones de padres
        if padre_id and padre_id in self.arbol_familiar:
            if npc_id not in self.arbol_familiar[padre_id].hijos_ids:
                self.arbol_familiar[padre_id].hijos_ids.append(npc_id)
        
        if madre_id and madre_id in self.arbol_familiar:
            if npc_id not in self.arbol_familiar[madre_id].hijos_ids:
                self.arbol_familiar[madre_id].hijos_ids.append(npc_id)
    
    def obtener_heredero(self) -> Optional[str]:
        """Obtiene el heredero del reino (primogénito del gobernante)"""
        if not self.gobernante_id or self.gobernante_id not in self.arbol_familiar:
            return None
        
        gobernante = self.arbol_familiar[self.gobernante_id]
        if gobernante.hijos_ids:
            # Retornar el primer hijo
            return gobernante.hijos_ids[0]
        
        return None
    
    def obtener_familia_cercana(self, npc_id: str) -> Dict[str, List[str]]:
        """Obtiene la familia cercana de un NPC"""
        if npc_id not in self.arbol_familiar:
            return {}
        
        nodo = self.arbol_familiar[npc_id]
        familia = {
            "conyuge": [nodo.conyuge_id] if nodo.conyuge_id else [],
            "padre": [nodo.padre_id] if nodo.padre_id else [],
            "madre": [nodo.madre_id] if nodo.madre_id else [],
            "hijos": nodo.hijos_ids.copy()
        }
        
        return familia


class GestorJerarquia:
    """Gestiona la jerarquía de todos los reinos"""
    
    def __init__(self):
        self.jerarquias: Dict[str, JerarquiaReino] = {}
    
    def crear_jerarquia_reino(self, nombre_reino: str, casa_gobernante: str):
        """Crea la jerarquía de un reino"""
        self.jerarquias[nombre_reino] = JerarquiaReino(
            nombre_reino=nombre_reino,
            casa_gobernante=casa_gobernante
        )
    
    def actualizar_reino(self, nombre_reino: str, npcs_reino: List, gobernante_npc=None):
        """Actualiza la jerarquía de un reino con los NPCs actuales"""
        if nombre_reino not in self.jerarquias:
            return
        
        jerarquia = self.jerarquias[nombre_reino]
        
        # Limpiar listas anteriores
        jerarquia.por_rango.clear()
        jerarquia.mineros.clear()
        jerarquia.agricultores.clear()
        jerarquia.soldados.clear()
        jerarquia.artesanos.clear()
        jerarquia.comerciantes.clear()
        jerarquia.guardias.clear()
        jerarquia.maestres.clear()
        
        # Establecer gobernante si existe
        if gobernante_npc:
            jerarquia.establecer_gobernante(gobernante_npc.id, gobernante_npc.nombre)
        
        # Clasificar NPCs
        for npc in npcs_reino:
            if not npc.vivo:
                continue
            
            # Determinar rango basado en título
            rango = self._determinar_rango(npc)
            jerarquia.agregar_npc(npc.id, npc.nombre, rango)
            
            # Agregar a árbol familiar si es familia del gobernante
            if gobernante_npc and self._es_familia_gobernante(npc, gobernante_npc):
                jerarquia.agregar_familiar(
                    npc.id,
                    npc.nombre,
                    rango,
                    padre_id=npc.padre_id if hasattr(npc, 'padre_id') else None,
                    madre_id=npc.madre_id if hasattr(npc, 'madre_id') else None,
                    conyuge_id=npc.conyuge_id if npc.casado else None
                )
    
    def _determinar_rango(self, npc) -> RangoSocial:
        """Determina el rango social de un NPC"""
        from enums_got import TituloNoble
        
        if not hasattr(npc, 'titulo'):
            return RangoSocial.PLEBEYO
        
        if npc.titulo == TituloNoble.LORD or npc.titulo == TituloNoble.LADY:
            return RangoSocial.REY  # El lord de la casa es el rey del reino
        elif npc.titulo == TituloNoble.CABALLERO:
            return RangoSocial.CABALLERO
        elif npc.titulo == TituloNoble.MAESTER:
            return RangoSocial.MAESTRE
        else:
            return RangoSocial.PLEBEYO
    
    def _es_familia_gobernante(self, npc, gobernante) -> bool:
        """Verifica si un NPC es familia del gobernante"""
        # Mismo apellido o cónyuge del gobernante
        if not hasattr(gobernante, 'nombre'):
            return False
        
        apellido_gobernante = gobernante.nombre.split()[-1] if ' ' in gobernante.nombre else gobernante.nombre
        apellido_npc = npc.nombre.split()[-1] if ' ' in npc.nombre else npc.nombre
        
        # Mismo apellido
        if apellido_gobernante == apellido_npc:
            return True
        
        # Es cónyuge del gobernante
        if hasattr(npc, 'conyuge_id') and npc.conyuge_id == gobernante.id:
            return True
        
        return False
    
    def obtener_jerarquia_reino(self, nombre_reino: str) -> Optional[JerarquiaReino]:
        """Obtiene la jerarquía de un reino"""
        return self.jerarquias.get(nombre_reino)
    
    def cambiar_gobernante(self, nombre_reino: str, nuevo_gobernante_npc):
        """Cambia el gobernante de un reino"""
        if nombre_reino not in self.jerarquias:
            return
        
        jerarquia = self.jerarquias[nombre_reino]
        
        # Remover rango de rey del gobernante anterior
        if jerarquia.gobernante_id:
            antiguo_id = jerarquia.gobernante_id
            if antiguo_id in jerarquia.arbol_familiar:
                jerarquia.arbol_familiar[antiguo_id].es_gobernante = False
                jerarquia.arbol_familiar[antiguo_id].rango = RangoSocial.LORD_SUPREMO
        
        # Establecer nuevo gobernante
        jerarquia.establecer_gobernante(nuevo_gobernante_npc.id, nuevo_gobernante_npc.nombre)
