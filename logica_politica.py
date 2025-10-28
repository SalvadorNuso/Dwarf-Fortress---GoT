"""
logica_politica.py - Sistema de política y sucesiones
Contiene toda la lógica relacionada con:
- Sucesiones y herencias
- Eventos políticos de casas
- Jerarquías de reinos
- Promociones de casas menores
"""
import random
from typing import TYPE_CHECKING

from npc_got import NPCGoT
from enums_got import *
from config_got import *

if TYPE_CHECKING:
    from juego_got import JuegoGoT


def procesar_eventos_casas(juego: 'JuegoGoT'):
    """Procesa eventos a nivel de casas"""
    from logica_combate import actualizar_guerras, declarar_guerra
    
    # PRIMERO: Procesar guerras activas y verificar si terminan
    actualizar_guerras(juego)
    
    for casa in juego.casas.values():
        # Eventos de guerra (reducir probabilidad)
        if not casa.en_guerra and random.random() < (PROB_GUERRA * 0.3):  # 30% de la prob original
            enemigos_posibles = list(casa.enemigos)
            if enemigos_posibles:
                enemigo = random.choice(enemigos_posibles)
                declarar_guerra(juego, casa.nombre, enemigo)
        
        # Alianzas aleatorias
        if random.random() < 0.05:
            otras_casas = [c for c in juego.casas.keys() if c != casa.nombre and c not in casa.enemigos]
            if otras_casas:
                aliado = random.choice(otras_casas)
                casa.aliados.add(aliado)
                juego.casas[aliado].aliados.add(casa.nombre)
                from juego_got import agregar_mensaje
                agregar_mensaje(juego, f"🤝 ¡Alianza! Casa {casa.nombre} y Casa {aliado} forman alianza")
        
        # Eventos de recursos
        if random.random() < 0.10:
            ganancia = random.randint(500, 2000)
            casa.oro += ganancia
            from juego_got import agregar_mensaje
            agregar_mensaje(juego, f"💰 Casa {casa.nombre} ganó {ganancia} de oro")
        
        # Eventos de pérdida
        if casa.en_guerra and random.random() < 0.15:
            perdida = random.randint(1000, 5000)
            casa.ejercito = max(1000, casa.ejercito - perdida)
            from juego_got import agregar_mensaje
            agregar_mensaje(juego, f"⚔️ Casa {casa.nombre} perdió {perdida} soldados en batalla")


def actualizar_jerarquias_reinos(juego: 'JuegoGoT'):
    """Actualiza las jerarquías de todos los reinos con los NPCs actuales."""
    for nombre_reino, reino in juego.reinos.items():
        # Obtener la casa gobernante
        casa_gobernante = juego.casas.get(reino.casa_gobernante)
        if not casa_gobernante:
            continue
        
        # Obtener NPCs del reino (NPCs de la casa gobernante principalmente)
        npcs_reino = [npc for npc in juego.npcs if npc.vivo and npc.casa == reino.casa_gobernante]
        
        # Obtener el gobernante (lord de la casa)
        gobernante_npc = next((npc for npc in npcs_reino if npc.id == casa_gobernante.lord), None)
        
        # Actualizar jerarquía
        if gobernante_npc:
            juego.gestor_jerarquia.actualizar_reino(nombre_reino, npcs_reino, gobernante_npc)


# ============================================================================
# SISTEMA DE SUCESIÓN Y HERENCIA
# ============================================================================

def encontrar_heredero(juego: 'JuegoGoT', lord_fallecido: NPCGoT, casa_nombre: str):
    """Encuentra el heredero legítimo de un lord fallecido"""
    from juego_got import agregar_mensaje
    
    # 1. PRIORIDAD: Hijos varones del lord
    hijos_varones = [
        npc for npc in juego.npcs 
        if npc.vivo and npc.padre_id == lord_fallecido.id and npc.sexo == Genero.MASCULINO
    ]
    
    if hijos_varones:
        # El hijo mayor hereda
        hijo_mayor = max(hijos_varones, key=lambda npc: npc.calcular_edad(juego.semana_actual))
        return hijo_mayor, "hijo_legitimo"
    
    # 2. Hijas mujeres (si no hay varones)
    hijas = [
        npc for npc in juego.npcs
        if npc.vivo and npc.padre_id == lord_fallecido.id and npc.sexo == Genero.FEMENINO
    ]
    
    if hijas:
        hija_mayor = max(hijas, key=lambda npc: npc.calcular_edad(juego.semana_actual))
        return hija_mayor, "hija_legitima"
    
    # 3. Hermanos del lord fallecido
    hermanos = [
        npc for npc in juego.npcs
        if npc.vivo and npc.casa == casa_nombre and 
        npc.padre_id == lord_fallecido.padre_id and
        npc.id != lord_fallecido.id and
        npc.sexo == Genero.MASCULINO
    ]
    
    if hermanos:
        hermano_mayor = max(hermanos, key=lambda npc: npc.calcular_edad(juego.semana_actual))
        return hermano_mayor, "hermano"
    
    # 4. Cualquier familiar varón de la casa
    varones_casa = [
        npc for npc in juego.npcs
        if npc.vivo and npc.casa == casa_nombre and npc.sexo == Genero.MASCULINO
        and npc.titulo in [TituloNoble.CABALLERO, TituloNoble.LORD, TituloNoble.PRINCIPE]
    ]
    
    if varones_casa:
        # El de mayor título nobiliario y edad (usar orden de títulos como prestigio)
        orden_titulos = {
            TituloNoble.PRINCIPE: 1,
            TituloNoble.LORD: 2,
            TituloNoble.CABALLERO: 3,
        }
        candidato = max(varones_casa, key=lambda npc: (
            -orden_titulos.get(npc.titulo, 100),  # Negativo para orden descendente
            npc.calcular_edad(juego.semana_actual)
        ))
        return candidato, "pariente"
    
    # 5. Si no hay nadie, una casa menor puede reclamar (DISPUTA)
    return None, "disputa"


def procesar_sucesion(juego: 'JuegoGoT', lord_fallecido: NPCGoT, casa_nombre: str):
    """Procesa la sucesión cuando un lord muere (casas principales Y menores)"""
    from juego_got import agregar_mensaje
    
    # Verificar si es casa principal o menor
    es_casa_principal = casa_nombre in juego.casas
    es_casa_menor = not es_casa_principal
    
    if es_casa_principal:
        casa = juego.casas[casa_nombre]
    elif es_casa_menor:
        # Buscar casa menor
        casa_menor = juego.gestor_rebeliones.casas_menores.get(casa_nombre)
        if not casa_menor:
            return  # Casa no encontrada
    else:
        return  # No es ni principal ni menor
    
    heredero, tipo_sucesion = encontrar_heredero(juego, lord_fallecido, casa_nombre)
    
    if heredero:
        # Heredero legítimo encontrado
        if tipo_sucesion == "hijo_legitimo":
            heredero.titulo = TituloNoble.LORD if heredero.sexo == Genero.MASCULINO else TituloNoble.LADY
            if es_casa_principal:
                casa.lord = heredero
            else:
                casa_menor.lord = heredero  # Actualizar casa menor
            agregar_mensaje(juego, f"👑 {heredero.nombre} hereda {casa_nombre} de su padre {lord_fallecido.nombre}")
            
        elif tipo_sucesion == "hija_legitima":
            heredero.titulo = TituloNoble.LADY
            if es_casa_principal:
                casa.lord = heredero
            else:
                casa_menor.lord = heredero
            agregar_mensaje(juego, f"👑 {heredero.nombre} hereda {casa_nombre} (sucesión femenina)")
            
        elif tipo_sucesion == "hermano":
            heredero.titulo = TituloNoble.LORD
            if es_casa_principal:
                casa.lord = heredero
            else:
                casa_menor.lord = heredero
            agregar_mensaje(juego, f"👑 {heredero.nombre} (hermano) hereda {casa_nombre}")
            
        elif tipo_sucesion == "pariente":
            heredero.titulo = TituloNoble.LORD
            if es_casa_principal:
                casa.lord = heredero
            else:
                casa_menor.lord = heredero
            agregar_mensaje(juego, f"👑 {heredero.nombre} (pariente) reclama {casa_nombre}")
        
        # Registrar en historia
        juego.gestor_continuidad.registrar_evento(
            juego.semana_actual, juego.año_actual,
            "sucesion",
            f"{heredero.nombre} hereda {casa_nombre} tras la muerte de {lord_fallecido.nombre}",
            casas=[casa_nombre],
            npcs=[heredero.nombre, lord_fallecido.nombre],
            importancia=9 if es_casa_principal else 7  # Menos importancia para casas menores
        )
    
    else:
        # DISPUTA - Solo aplica para casas principales
        if es_casa_principal:
            agregar_mensaje(juego, f"⚠️ CRISIS: Casa {casa_nombre} sin heredero legítimo!")
            
            # Buscar casas menores que puedan reclamar
            casas_menores_reino = []
            for nombre_reino, reino in juego.reinos.items():
                if reino.casa_gobernante == casa_nombre:
                    casas_menores_reino = [
                        cm for cm in juego.gestor_rebeliones.obtener_todas_casas_menores()
                        if cm.reino == nombre_reino and cm.lealtad > 60
                    ]
                    break
            
            if casas_menores_reino:
                # La casa menor más leal puede reclamar
                casa_reclamante = max(casas_menores_reino, key=lambda cm: cm.lealtad)
                
                # Promover casa menor a casa principal
                promover_casa_menor_a_principal(juego, casa_reclamante, casa_nombre)
            else:
                # Crear un lord de emergencia
                agregar_mensaje(juego, f"🆘 Se designa un nuevo lord para Casa {casa_nombre} de emergencia")
                crear_lord_emergencia(juego, casa_nombre)
        else:
            # Casa menor sin heredero - crear lord de emergencia
            agregar_mensaje(juego, f"🆘 {casa_nombre} (casa menor) sin heredero - designando nuevo lord")
            # Para casas menores, simplemente crear un nuevo NPC como lord
            # (implementación simplificada - en el futuro podría absorberse por otra casa)


def promover_casa_menor_a_principal(juego: 'JuegoGoT', casa_menor, casa_nombre_principal: str):
    """Promociona una casa menor a casa principal cuando esta pierde su línea sucesoria"""
    from juego_got import agregar_mensaje
    
    # Encontrar el líder de la casa menor
    npcs_casa_menor = [npc for npc in juego.npcs if npc.vivo and npc.casa == casa_menor.nombre]
    
    if npcs_casa_menor:
        # El NPC con mayor título nobiliario y edad se convierte en el nuevo lord
        orden_titulos = {
            TituloNoble.LORD: 1,
            TituloNoble.LADY: 1,
            TituloNoble.CABALLERO: 2,
            TituloNoble.MAESTER: 3,
            TituloNoble.PLEBEYO: 4,
        }
        nuevo_lord = max(npcs_casa_menor, key=lambda npc: (
            -orden_titulos.get(npc.titulo, 100),  # Negativo para orden descendente
            npc.calcular_edad(juego.semana_actual)
        ))
        
        # Cambiar su casa a la principal
        for npc in npcs_casa_menor:
            npc.casa = casa_nombre_principal
            if npc.casa in juego.casas:
                juego.casas[casa_nombre_principal].miembros.append(npc)
        
        # Establecer como lord
        nuevo_lord.titulo = TituloNoble.LORD if nuevo_lord.sexo == Genero.MASCULINO else TituloNoble.LADY
        juego.casas[casa_nombre_principal].lord = nuevo_lord
        
        agregar_mensaje(juego, f"🔥⚔️ Casa {casa_menor.nombre} reclama Casa {casa_nombre_principal}!")
        agregar_mensaje(juego, f"👑 {nuevo_lord.nombre} es el nuevo Lord de Casa {casa_nombre_principal}")
        
        # Registrar evento épico
        juego.gestor_continuidad.registrar_evento(
            juego.semana_actual, juego.año_actual,
            "ascenso_casa_menor",
            f"Casa {casa_menor.nombre} asciende a Casa Principal tras reclamar {casa_nombre_principal}",
            casas=[casa_nombre_principal],
            npcs=[nuevo_lord.nombre],
            importancia=10
        )


def crear_lord_emergencia(juego: 'JuegoGoT', casa_nombre: str):
    """Crea un lord de emergencia cuando no hay herederos ni casas menores"""
    from inicializacion_got import crear_npcs_para_casa
    
    # Crear algunos NPCs nuevos para la casa
    crear_npcs_para_casa(juego, casa_nombre, es_casa_principal=True)
    
    # El primero creado será el lord (ya lo hace crear_npcs_para_casa)
    casa = juego.casas[casa_nombre]
    if casa.lord:
        from juego_got import agregar_mensaje
        agregar_mensaje(juego, f"👤 {casa.lord.nombre} emerge como nuevo Lord de Casa {casa_nombre}")
