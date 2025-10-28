"""
config_got.py - Configuración estilo Game of Thrones
Nombres, casas nobles, lugares y configuración del mundo de Poniente
"""

# Dimensiones
ANCHO = 1400
ALTO = 800
FPS = 60

# Colores base
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS = (128, 128, 128)
GRIS_OSCURO = (50, 50, 50)

# Colores de las Grandes Casas
COLOR_STARK = (150, 150, 150)      # Gris lobo
COLOR_LANNISTER = (220, 20, 60)    # Rojo y oro
COLOR_TARGARYEN = (220, 20, 60)    # Rojo y negro
COLOR_BARATHEON = (255, 215, 0)    # Oro y negro
COLOR_GREYJOY = (70, 130, 180)     # Acero y negro
COLOR_TYRELL = (34, 139, 34)       # Verde y dorado
COLOR_MARTELL = (255, 140, 0)      # Naranja y dorado
COLOR_ARRYN = (135, 206, 250)      # Azul cielo
COLOR_TULLY = (64, 224, 208)       # Azul y rojo

COLORES_CASAS = [
    COLOR_STARK,
    COLOR_LANNISTER, 
    COLOR_TARGARYEN,
    COLOR_BARATHEON,
    COLOR_GREYJOY,
    COLOR_TYRELL,
    COLOR_MARTELL,
    COLOR_ARRYN,
    COLOR_TULLY
]

# Nombres de las Grandes Casas
CASAS_NOMBRES = [
    "Stark",
    "Lannister",
    "Targaryen", 
    "Baratheon",
    "Greyjoy",
    "Tyrell",
    "Martell",
    "Arryn",
    "Tully"
]

# Diccionarios por casa
LEMAS_CASAS = {
    "Stark": "Winter is Coming",
    "Lannister": "Hear Me Roar",
    "Targaryen": "Fire and Blood",
    "Baratheon": "Ours is the Fury",
    "Greyjoy": "We Do Not Sow",
    "Tyrell": "Growing Strong",
    "Martell": "Unbowed, Unbent, Unbroken",
    "Arryn": "As High as Honor",
    "Tully": "Family, Duty, Honor"
}

CASTILLOS = {
    "Stark": "Winterfell",
    "Lannister": "Casterly Rock",
    "Targaryen": "Dragonstone",
    "Baratheon": "Storm's End",
    "Greyjoy": "Pyke",
    "Tyrell": "Highgarden",
    "Martell": "Sunspear",
    "Arryn": "The Eyrie",
    "Tully": "Riverrun"
}

# REINOS DE PONIENTE (Entidades políticas/geográficas permanentes)
REINOS_PONIENTE = {
    "El Norte": {
        "capital": "Winterfell",
        "casa_inicial": "Stark",
        "titulo": "Warden of the North",
        "fertilidad": 30,
        "riqueza_mineral": 40,
        "posicion_estrategica": 70,
        "centro": (500, 300),
        "color": (150, 150, 150)
    },
    "Las Tierras del Oeste": {
        "capital": "Casterly Rock",
        "casa_inicial": "Lannister",
        "titulo": "Warden of the West",
        "fertilidad": 50,
        "riqueza_mineral": 95,
        "posicion_estrategica": 60,
        "centro": (300, 800),
        "color": (220, 20, 60)
    },
    "El Dominio": {
        "capital": "Highgarden",
        "casa_inicial": "Tyrell",
        "titulo": "Warden of the South",
        "fertilidad": 95,
        "riqueza_mineral": 30,
        "posicion_estrategica": 50,
        "centro": (600, 1400),
        "color": (34, 139, 34)
    },
    "Dorne": {
        "capital": "Sunspear",
        "casa_inicial": "Martell",
        "titulo": "Prince/Princess of Dorne",
        "fertilidad": 20,
        "riqueza_mineral": 40,
        "posicion_estrategica": 60,
        "centro": (900, 1700),
        "color": (255, 140, 0)
    },
    "Las Tierras de la Tormenta": {
        "capital": "Storm's End",
        "casa_inicial": "Baratheon",
        "titulo": "Lord of Storm's End",
        "fertilidad": 60,
        "riqueza_mineral": 50,
        "posicion_estrategica": 75,
        "centro": (1100, 1300),
        "color": (255, 215, 0)
    },
    "Las Tierras de los Ríos": {
        "capital": "Riverrun",
        "casa_inicial": "Tully",
        "titulo": "Lord of the Riverlands",
        "fertilidad": 80,
        "riqueza_mineral": 40,
        "posicion_estrategica": 90,
        "centro": (800, 900),
        "color": (64, 224, 208)
    },
    "El Valle": {
        "capital": "The Eyrie",
        "casa_inicial": "Arryn",
        "titulo": "Warden of the East",
        "fertilidad": 50,
        "riqueza_mineral": 60,
        "posicion_estrategica": 80,
        "centro": (1300, 800),
        "color": (135, 206, 250)
    },
    "Islas del Hierro": {
        "capital": "Pyke",
        "casa_inicial": "Greyjoy",
        "titulo": "Lord Reaper of Pyke",
        "fertilidad": 10,
        "riqueza_mineral": 30,
        "posicion_estrategica": 85,
        "centro": (200, 600),
        "color": (70, 130, 180)
    },
    "Rocadragón": {
        "capital": "Dragonstone",
        "casa_inicial": "Targaryen",
        "titulo": "Lord of Dragonstone",
        "fertilidad": 30,
        "riqueza_mineral": 60,
        "posicion_estrategica": 70,
        "centro": (1400, 1100),
        "color": (139, 0, 0)
    }
}

# Mapeo de casas a reinos (inicial, puede cambiar durante el juego)
REGIONES_POR_CASA = {
    "Stark": "El Norte",
    "Lannister": "Las Tierras del Oeste",
    "Targaryen": "Rocadragón",
    "Baratheon": "Las Tierras de la Tormenta",
    "Greyjoy": "Islas del Hierro",
    "Tyrell": "El Dominio",
    "Martell": "Dorne",
    "Arryn": "El Valle",
    "Tully": "Las Tierras de los Ríos"
}

APELLIDOS_CASAS = {
    "Stark": "Stark",
    "Lannister": "Lannister",
    "Targaryen": "Targaryen",
    "Baratheon": "Baratheon",
    "Greyjoy": "Greyjoy",
    "Tyrell": "Tyrell",
    "Martell": "Martell",
    "Arryn": "Arryn",
    "Tully": "Tully"
}

# Lemas de las casas (legacy, mantenido por compatibilidad)
CASAS_LEMAS = {
    "Stark": "Winter is Coming",
    "Lannister": "Hear Me Roar",
    "Targaryen": "Fire and Blood",
    "Baratheon": "Ours is the Fury",
    "Greyjoy": "We Do Not Sow",
    "Tyrell": "Growing Strong",
    "Martell": "Unbowed, Unbent, Unbroken",
    "Arryn": "As High as Honor",
    "Tully": "Family, Duty, Honor"
}

# Nombres masculinos de Poniente
NOMBRES_MASCULINOS = [
    # Stark
    "Eddard", "Brandon", "Rickon", "Robb", "Bran", "Jon",
    # Lannister
    "Tywin", "Jaime", "Tyrion", "Kevan", "Lancel", "Tommen",
    # Targaryen
    "Aerys", "Rhaegar", "Viserys", "Aegon", "Daemon", "Aemon",
    # Baratheon
    "Robert", "Stannis", "Renly", "Joffrey", "Gendry",
    # Otros
    "Oberyn", "Doran", "Theon", "Balon", "Edmure", "Brynden",
    "Petyr", "Varys", "Jorah", "Davos", "Samwell", "Thoros",
    "Sandor", "Gregor", "Bronn", "Podrick", "Tormund", "Mance"
]

# Nombres femeninos de Poniente
NOMBRES_FEMENINOS = [
    # Stark
    "Catelyn", "Sansa", "Arya", "Lyanna", "Lysa",
    # Lannister
    "Cersei", "Myrcella",
    # Targaryen
    "Daenerys", "Rhaenys", "Visenya",
    # Otros
    "Margaery", "Olenna", "Elia", "Ellaria", "Ygritte",
    "Brienne", "Melisandre", "Talisa", "Roslin", "Shireen",
    "Gilly", "Meera", "Osha", "Shae", "Missandei"
]

# Apellidos nobles y comunes
APELLIDOS = [
    # Grandes casas
    "Stark", "Lannister", "Targaryen", "Baratheon", "Greyjoy",
    "Tyrell", "Martell", "Arryn", "Tully",
    # Casas menores
    "Bolton", "Frey", "Karstark", "Mormont", "Reed", "Umber",
    "Clegane", "Payne", "Dondarrion", "Selmy", "Tarly", "Hightower",
    "Redwyne", "Florent", "Yronwood", "Dayne", "Royce", "Corbray",
    # Bastardos por región
    "Snow", "Hill", "Sand", "Stone", "Waters", "Storm", "Rivers"
]

# Ciudades y lugares principales
CIUDADES = {
    0: "Winterfell",      # Stark - Norte
    1: "Casterly Rock",   # Lannister - Oeste
    2: "Dragonstone",     # Targaryen - Islas
    3: "Storm's End",     # Baratheon - Tierras de la Tormenta
    4: "Pyke",           # Greyjoy - Islas del Hierro
    5: "Highgarden",     # Tyrell - El Dominio
    6: "Sunspear",       # Martell - Dorne
    7: "The Eyrie",      # Arryn - Valle
    8: "Riverrun"        # Tully - Tierras de los Ríos
}

# Regiones de Poniente
REGIONES = {
    0: "The North",
    1: "The Westerlands",
    2: "Dragonstone",
    3: "The Stormlands",
    4: "The Iron Islands",
    5: "The Reach",
    6: "Dorne",
    7: "The Vale",
    8: "The Riverlands"
}

# Títulos nobles
TITULOS = [
    "Lord",
    "Lady", 
    "Ser",
    "King",
    "Queen",
    "Prince",
    "Princess",
    "Maester",
    "Hand of the King",
    "Master of Coin",
    "Master of Ships",
    "Master of Whispers"
]

# Mapa - Coordenadas realistas según Poniente (basado en los libros)
# El mapa va de Norte (arriba) a Sur (abajo), Oeste (izquierda) a Este (derecha)
# Dimensiones: 2000x2000 (más espacio para el continente completo)

MAPA_CASTILLOS = {
    # EL NORTE (arriba)
    "The Wall": (500, 50),           # Extremo Norte - La Guardia de la Noche
    "Winterfell": (500, 200),        # Capital del Norte - Casa Stark
    
    # OESTE - THE WESTERLANDS
    "Casterly Rock": (200, 550),     # Oeste - Casa Lannister
    
    # CENTRO - THE RIVERLANDS
    "Riverrun": (450, 450),          # Centro - Casa Tully
    "Harrenhal": (550, 500),         # Castillo maldito en Riverlands
    
    # ESTE - THE VALE
    "The Eyrie": (650, 400),         # Este montañoso - Casa Arryn
    
    # ISLAS DEL HIERRO - IRON ISLANDS
    "Pyke": (100, 450),              # Oeste en islas - Casa Greyjoy
    
    # CAPITAL DEL REINO
    "King's Landing": (600, 650),    # Costa Este-Centro - Trono de Hierro
    
    # DRAGONSTONE
    "Dragonstone": (750, 650),       # Isla Este - Casa Targaryen
    
    # SUR - THE STORMLANDS
    "Storm's End": (600, 800),       # Sur-Este - Casa Baratheon
    
    # SUR-OESTE - THE REACH
    "Highgarden": (350, 750),        # Sur-Oeste fértil - Casa Tyrell
    
    # EXTREMO SUR - DORNE
    "Sunspear": (550, 950),          # Extremo Sur desértico - Casa Martell
    
    # Otras ciudades importantes
    "Oldtown": (250, 850),           # Sur-Oeste - Ciudad más antigua
    "White Harbor": (600, 250),      # Norte-Este - Puerto del Norte
    "Lannisport": (180, 580),        # Oeste - Ciudad Lannister
    "Gulltown": (700, 450),          # Este - Puerto del Valle
}

# Configuración del mapa - Continente completo de Poniente
ANCHO_MAPA = 2000
ALTO_MAPA = 1200

# King's Landing - Capital del Reino
KINGS_LANDING_POS = (600, 650)
KINGS_LANDING_POBLACION_INICIAL = 500000  # Medio millón de habitantes

# Terrenos
COLOR_MAR = (20, 50, 100)
COLOR_TIERRA = (100, 80, 60)
COLOR_BOSQUE = (34, 100, 34)
COLOR_MONTAÑA = (80, 80, 80)
COLOR_NIEVE = (240, 240, 255)
COLOR_DESIERTO = (210, 180, 140)

# Recursos por región
RECURSOS_REGIONES = {
    0: {"madera": 1000, "piedra": 500, "alimento": 300},    # Norte
    1: {"oro": 2000, "hierro": 800, "alimento": 400},       # Oeste
    2: {"piedra": 600, "hierro": 400, "alimento": 200},     # Dragonstone
    3: {"alimento": 500, "madera": 600, "piedra": 400},     # Stormlands
    4: {"hierro": 800, "madera": 400, "alimento": 200},     # Iron Islands
    5: {"alimento": 1500, "oro": 600, "madera": 500},       # Reach
    6: {"oro": 800, "hierro": 400, "alimento": 300},        # Dorne
    7: {"piedra": 1000, "hierro": 500, "alimento": 300},    # Vale
    8: {"alimento": 700, "madera": 600, "piedra": 400}      # Riverlands
}

# Configuración de eventos especiales GoT
PROBABILIDAD_TRAICION = 0.02     # 2% por semana
PROBABILIDAD_COMPLOT = 0.03      # 3% por semana
PROBABILIDAD_ASESINATO = 0.01    # 1% por semana
PROBABILIDAD_GUERRA = 0.05       # 5% por semana
PROBABILIDAD_DRAGON = 0.001      # 0.1% por semana (muy raro)

# Tamaños de ejércitos iniciales
EJERCITO_BASE = {
    "Stark": 20000,
    "Lannister": 30000,
    "Targaryen": 5000,
    "Baratheon": 25000,
    "Greyjoy": 15000,
    "Tyrell": 35000,
    "Martell": 20000,
    "Arryn": 18000,
    "Tully": 22000
}

# Riqueza inicial por casa
RIQUEZA_BASE = {
    "Stark": 5000,
    "Lannister": 50000,     # Los más ricos
    "Targaryen": 10000,
    "Baratheon": 15000,
    "Greyjoy": 3000,
    "Tyrell": 30000,        # Segundo más rico
    "Martell": 12000,
    "Arryn": 10000,
    "Tully": 8000
}

# Zoom y cámara
ZOOM_MIN = 0.5
ZOOM_MAX = 3.0
ZOOM_DEFAULT = 1.0

# Probabilidades de eventos políticos GoT (AUMENTADAS PARA MÁS ACCIÓN)
PROB_TRAICION = 0.15       # 15% probabilidad semanal de traición
PROB_COMPLOT = 0.25        # 25% probabilidad semanal de iniciar complot
PROB_ASESINATO = 0.10      # 10% probabilidad semanal de asesinato
PROB_GUERRA = 0.20         # 20% probabilidad semanal de declarar guerra
PROB_DRAGON = 0.01         # 1% probabilidad de evento dragón
PROB_MATRIMONIO_POLITICO = 0.15  # 15% probabilidad de matrimonio por alianza
PROB_REBELION = 0.10       # 10% probabilidad de rebelión

# Alias para nombres GoT (usados en juego_got.py)
NOMBRES_MASCULINOS_GOT = NOMBRES_MASCULINOS
NOMBRES_FEMENINOS_GOT = NOMBRES_FEMENINOS

# Ubicaciones por casa (nombre de casa como clave) - POSICIONES REALISTAS
UBICACIONES_CASTILLOS = {
    "Stark": (500, 200),        # Winterfell - Norte
    "Lannister": (200, 550),    # Casterly Rock - Oeste
    "Targaryen": (750, 650),    # Dragonstone - Isla Este
    "Baratheon": (600, 800),    # Storm's End - Sur-Este
    "Greyjoy": (100, 450),      # Pyke - Islas del Hierro (Oeste)
    "Tyrell": (350, 750),       # Highgarden - Sur-Oeste
    "Martell": (550, 950),      # Sunspear - Extremo Sur
    "Arryn": (650, 400),        # The Eyrie - Este montañoso
    "Tully": (450, 450),        # Riverrun - Centro
}
# Recursos por región (nombre de región como clave)
RECURSOS_POR_REGION = {
    "The North": {"madera": 1000, "piedra": 500, "alimento": 300},
    "The Westerlands": {"oro": 2000, "hierro": 800, "alimento": 400},
    "Dragonstone": {"piedra": 600, "hierro": 400, "alimento": 200},
    "The Stormlands": {"alimento": 500, "madera": 600, "piedra": 400},
    "Iron Islands": {"hierro": 800, "madera": 400, "alimento": 200},
    "The Reach": {"alimento": 1500, "oro": 600, "madera": 500},
    "Dorne": {"oro": 800, "hierro": 400, "alimento": 300},
    "The Vale": {"piedra": 1000, "hierro": 500, "alimento": 300},
    "The Riverlands": {"alimento": 700, "madera": 600, "piedra": 400}
}
EJERCITOS_BASE = {
    "Stark": 25000,
    "Lannister": 35000,
    "Targaryen": 15000,
    "Baratheon": 30000,
    "Greyjoy": 18000,
    "Tyrell": 32000,
    "Martell": 20000,
    "Arryn": 22000,
    "Tully": 24000
}
