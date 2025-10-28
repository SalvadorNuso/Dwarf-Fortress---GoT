"""
sistemas_animales.py - Sistema de animales visibles en el mapa
Game of Thrones: Simulador Político

Animales que se ven en el mapa:
- Vacas, caballos, cerdos, ovejas, cabras
- Animales salvajes: lobos, osos, jabalíes
- Aves: cuervos, águilas
"""
import random
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum


class TipoAnimal(Enum):
    """Tipos de animales"""
    # Domésticos
    VACA = "vaca"
    CABALLO = "caballo"
    CERDO = "cerdo"
    OVEJA = "oveja"
    CABRA = "cabra"
    GALLINA = "gallina"
    
    # Salvajes
    LOBO = "lobo"
    OSO = "oso"
    JABALI = "jabali"
    CIERVO = "ciervo"
    
    # Aves
    CUERVO = "cuervo"
    AGUILA = "aguila"


@dataclass
class Animal:
    """Un animal en el mapa"""
    tipo: TipoAnimal
    x: float
    y: float
    vivo: bool = True
    
    # ID único
    id: int = 0
    
    # Movimiento aleatorio
    velocidad: float = 0.5
    direccion_x: float = 0.0
    direccion_y: float = 0.0
    contador_cambio_direccion: int = 0
    
    # Stats adicionales
    edad: int = 1  # años
    salud: int = 100  # 0-100
    domestico: bool = True
    
    # Visual
    color: Tuple[int, int, int] = (255, 255, 255)
    radio: int = 8
    
    def __post_init__(self):
        """Inicializar características según tipo"""
        if self.tipo == TipoAnimal.VACA:
            self.color = (139, 69, 19)  # Marrón
            self.radio = 12
            self.velocidad = 0.3
            self.domestico = True
            self.edad = random.randint(1, 8)
        elif self.tipo == TipoAnimal.CABALLO:
            self.color = (101, 67, 33)  # Marrón oscuro
            self.radio = 14
            self.velocidad = 1.0
            self.domestico = True
            self.edad = random.randint(1, 12)
        elif self.tipo == TipoAnimal.CERDO:
            self.color = (255, 182, 193)  # Rosa
            self.radio = 10
            self.velocidad = 0.4
            self.domestico = True
            self.edad = random.randint(1, 5)
        elif self.tipo == TipoAnimal.OVEJA:
            self.color = (245, 245, 245)  # Blanco
            self.radio = 9
            self.velocidad = 0.4
            self.domestico = True
            self.edad = random.randint(1, 6)
        elif self.tipo == TipoAnimal.CABRA:
            self.color = (211, 211, 211)  # Gris claro
            self.radio = 8
            self.velocidad = 0.5
            self.domestico = True
            self.edad = random.randint(1, 7)
        elif self.tipo == TipoAnimal.GALLINA:
            self.color = (255, 255, 200)  # Amarillo claro
            self.radio = 5
            self.velocidad = 0.6
            self.domestico = True
            self.edad = random.randint(1, 3)
        elif self.tipo == TipoAnimal.LOBO:
            self.color = (80, 80, 80)  # Gris oscuro
            self.radio = 11
            self.velocidad = 1.5
            self.domestico = False
            self.edad = random.randint(2, 8)
        elif self.tipo == TipoAnimal.OSO:
            self.color = (60, 30, 15)  # Marrón muy oscuro
            self.radio = 18
            self.velocidad = 0.7
            self.domestico = False
            self.edad = random.randint(3, 15)
        elif self.tipo == TipoAnimal.JABALI:
            self.color = (50, 25, 25)  # Marrón oscuro
            self.radio = 13
            self.velocidad = 1.2
            self.domestico = False
            self.edad = random.randint(2, 10)
        elif self.tipo == TipoAnimal.CIERVO:
            self.color = (160, 100, 60)  # Marrón claro
            self.radio = 13
            self.velocidad = 1.3
            self.domestico = False
            self.edad = random.randint(1, 12)
        elif self.tipo == TipoAnimal.CUERVO:
            self.color = (20, 20, 20)  # Negro
            self.radio = 4
            self.velocidad = 2.0
            self.domestico = False
            self.edad = random.randint(1, 5)
        elif self.tipo == TipoAnimal.AGUILA:
            self.color = (80, 60, 40)  # Marrón
            self.radio = 6
            self.velocidad = 2.5
            self.domestico = False
            self.edad = random.randint(2, 15)
        
        # Dirección aleatoria inicial
        self.direccion_x = random.uniform(-1, 1)
        self.direccion_y = random.uniform(-1, 1)
    
    def actualizar(self, mundo_ancho: int, mundo_alto: int):
        """Actualiza posición del animal (movimiento aleatorio)"""
        if not self.vivo:
            return
        
        # Cambiar dirección cada 60-120 frames
        self.contador_cambio_direccion += 1
        if self.contador_cambio_direccion > random.randint(60, 120):
            self.direccion_x = random.uniform(-1, 1)
            self.direccion_y = random.uniform(-1, 1)
            self.contador_cambio_direccion = 0
        
        # Mover
        self.x += self.direccion_x * self.velocidad
        self.y += self.direccion_y * self.velocidad
        
        # Mantener dentro del mundo
        if self.x < 0:
            self.x = 0
            self.direccion_x *= -1
        elif self.x > mundo_ancho:
            self.x = mundo_ancho
            self.direccion_x *= -1
        
        if self.y < 0:
            self.y = 0
            self.direccion_y *= -1
        elif self.y > mundo_alto:
            self.y = mundo_alto
            self.direccion_y *= -1


class GestorAnimales:
    """Gestor de animales en el mapa"""
    
    def __init__(self):
        self.animales: List[Animal] = []
        self.siguiente_id = 1
        self.rebanos_por_casa: dict = {}  # {casa_nombre: [lista de IDs de animales]}
    
    def inicializar_animales(self, mundo_ancho: int, mundo_alto: int, casas_ubicaciones: dict = None, gestor_agricultura=None):
        """
        Crea animales iniciales en ubicaciones lógicas
        - Domésticos: cerca de castillos (praderas)
        - Salvajes: bosques y montañas
        """
        if casas_ubicaciones is None:
            casas_ubicaciones = {}
        
        # ANIMALES DOMÉSTICOS - cerca de asentamientos
        if casas_ubicaciones and gestor_agricultura:
            tipos_domesticos = [
                (TipoAnimal.VACA, 15),
                (TipoAnimal.CABALLO, 10),
                (TipoAnimal.CERDO, 12),
                (TipoAnimal.OVEJA, 20),
                (TipoAnimal.CABRA, 15),
                (TipoAnimal.GALLINA, 25),
            ]
            
            for casa_nombre, posicion_castillo in casas_ubicaciones.items():
                self.rebanos_por_casa[casa_nombre] = []
                
                for tipo_animal, cantidad in tipos_domesticos:
                    for _ in range(cantidad):
                        # Buscar posición cultivable cerca del castillo
                        intentos = 0
                        while intentos < 20:
                            # Radio de 150-400 unidades del castillo
                            angulo = random.uniform(0, 6.28)
                            distancia = random.uniform(150, 400)
                            x = posicion_castillo[0] + distancia * random.uniform(-1, 1)
                            y = posicion_castillo[1] + distancia * random.uniform(-1, 1)
                            
                            # Verificar que esté en pradera/llanura
                            if gestor_agricultura.es_terreno_cultivable(x, y, mundo_ancho, mundo_alto):
                                animal = Animal(tipo=tipo_animal, x=x, y=y, id=self.siguiente_id)
                                self.animales.append(animal)
                                self.rebanos_por_casa[casa_nombre].append(self.siguiente_id)
                                self.siguiente_id += 1
                                break
                            intentos += 1
        
        # ANIMALES SALVAJES - en zonas salvajes (bosques, montañas)
        tipos_salvajes_bosque = [
            (TipoAnimal.LOBO, 15),      # Bosques
            (TipoAnimal.JABALI, 20),    # Bosques
            (TipoAnimal.CIERVO, 25),    # Bosques y praderas
        ]
        
        tipos_salvajes_montana = [
            (TipoAnimal.OSO, 10),       # Montañas
        ]
        
        # Animales de bosque
        for tipo_animal, cantidad in tipos_salvajes_bosque:
            for _ in range(cantidad):
                intentos = 0
                while intentos < 50:
                    x = random.uniform(100, mundo_ancho - 100)
                    y = random.uniform(100, mundo_alto - 100)
                    
                    if gestor_agricultura:
                        terreno = gestor_agricultura.determinar_tipo_terreno(x, y, mundo_ancho, mundo_alto)
                        # Lobos y jabalíes en bosques, ciervos también en praderas
                        if tipo_animal == TipoAnimal.CIERVO:
                            if terreno.name in ['BOSQUE', 'PRADERA', 'COLINA']:
                                animal = Animal(tipo=tipo_animal, x=x, y=y, id=self.siguiente_id)
                                self.animales.append(animal)
                                self.siguiente_id += 1
                                break
                        else:
                            if terreno.name in ['BOSQUE', 'COLINA']:
                                animal = Animal(tipo=tipo_animal, x=x, y=y, id=self.siguiente_id)
                                self.animales.append(animal)
                                self.siguiente_id += 1
                                break
                    else:
                        # Sin gestor, colocar en zona media-exterior
                        centro_x, centro_y = mundo_ancho / 2, mundo_alto / 2
                        dist = ((x - centro_x)**2 + (y - centro_y)**2)**0.5
                        max_dist = ((centro_x**2 + centro_y**2)**0.5)
                        if dist > max_dist * 0.4:  # Fuera del centro
                            animal = Animal(tipo=tipo_animal, x=x, y=y, id=self.siguiente_id)
                            self.animales.append(animal)
                            self.siguiente_id += 1
                            break
                    intentos += 1
        
        # Animales de montaña
        for tipo_animal, cantidad in tipos_salvajes_montana:
            for _ in range(cantidad):
                intentos = 0
                while intentos < 50:
                    x = random.uniform(100, mundo_ancho - 100)
                    y = random.uniform(100, mundo_alto - 100)
                    
                    if gestor_agricultura:
                        terreno = gestor_agricultura.determinar_tipo_terreno(x, y, mundo_ancho, mundo_alto)
                        if terreno.name in ['MONTAÑA', 'COLINA']:
                            animal = Animal(tipo=tipo_animal, x=x, y=y, id=self.siguiente_id)
                            self.animales.append(animal)
                            self.siguiente_id += 1
                            break
                    else:
                        # Sin gestor, colocar en zona exterior
                        centro_x, centro_y = mundo_ancho / 2, mundo_alto / 2
                        dist = ((x - centro_x)**2 + (y - centro_y)**2)**0.5
                        max_dist = ((centro_x**2 + centro_y**2)**0.5)
                        if dist > max_dist * 0.6:  # Zona muy exterior
                            animal = Animal(tipo=tipo_animal, x=x, y=y, id=self.siguiente_id)
                            self.animales.append(animal)
                            self.siguiente_id += 1
                            break
                    intentos += 1
        
        # AVES - pueden estar en cualquier lugar
        for _ in range(30):  # Cuervos
            x = random.uniform(0, mundo_ancho)
            y = random.uniform(0, mundo_alto)
            animal = Animal(tipo=TipoAnimal.CUERVO, x=x, y=y, id=self.siguiente_id)
            self.animales.append(animal)
            self.siguiente_id += 1
        
        for _ in range(15):  # Águilas (menos comunes)
            x = random.uniform(0, mundo_ancho)
            y = random.uniform(0, mundo_alto)
            animal = Animal(tipo=TipoAnimal.AGUILA, x=x, y=y, id=self.siguiente_id)
            self.animales.append(animal)
            self.siguiente_id += 1
    
    def actualizar_animales(self, mundo_ancho: int, mundo_alto: int):
        """Actualiza todos los animales"""
        for animal in self.animales:
            animal.actualizar(mundo_ancho, mundo_alto)
    
    def obtener_animales_en_viewport(self, x_min: float, y_min: float, 
                                     x_max: float, y_max: float) -> List[Animal]:
        """Obtiene animales visibles en el viewport"""
        animales_visibles = []
        for animal in self.animales:
            if animal.vivo and x_min <= animal.x <= x_max and y_min <= animal.y <= y_max:
                animales_visibles.append(animal)
        return animales_visibles
    
    def matar_animales_en_radio(self, x: float, y: float, radio: float, probabilidad: float = 1.0):
        """Mata animales en un radio (para eventos)"""
        for animal in self.animales:
            if animal.vivo:
                distancia = ((animal.x - x)**2 + (animal.y - y)**2)**0.5
                if distancia < radio and random.random() < probabilidad:
                    animal.vivo = False
