"""
sistema_coordenadas.py - Sistema de coordenadas en pantalla para ubicar castillos
Game of Thrones: Simulador Político

Muestra coordenadas en los bordes del mapa para facilitar la colocación manual de castillos.
"""
import pygame
from config_got import ANCHO, ALTO


class SistemaCoordenadas:
    """Sistema para mostrar coordenadas del mundo en los bordes de la pantalla"""
    
    def __init__(self):
        self.mostrar = False  # Toggle con tecla
        # Asegurar que pygame y el subsistema de fuentes estén inicializados
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        try:
            self.fuente = pygame.font.Font(None, 16)
        except Exception:
            # En entornos extraños, usar SysFont como fallback
            self.fuente = pygame.font.SysFont(None, 16)
        self.color_texto = (255, 255, 100)  # Amarillo
        self.color_linea = (255, 255, 100, 128)  # Amarillo semi-transparente
        self.espaciado_coords = 200  # Cada 200 unidades del mundo
        
    def toggle(self):
        """Alternar visibilidad de coordenadas"""
        self.mostrar = not self.mostrar
        
    def renderizar(self, pantalla, camara, mundo_ancho, mundo_alto):
        """
        Renderiza las coordenadas en los bordes del mapa
        
        Args:
            pantalla: Surface de pygame
            camara: Instancia de Camara
            mundo_ancho: Ancho del mundo en unidades
            mundo_alto: Alto del mundo en unidades
        """
        if not self.mostrar:
            return
        
        # Crear superficie semi-transparente para líneas
        surf_temp = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        
        # Obtener viewport bounds
        x_min, y_min, x_max, y_max = camara.obtener_viewport_bounds(ANCHO, ALTO, margen=0)
        
        # ===== COORDENADAS HORIZONTALES (parte superior e inferior) =====
        # Encontrar primera coordenada X visible (múltiplo de espaciado_coords)
        x_inicio = int(x_min // self.espaciado_coords) * self.espaciado_coords
        
        x = x_inicio
        while x <= x_max:
            if 0 <= x <= mundo_ancho:
                px, _ = camara.mundo_a_pantalla(x, 0)
                
                # Solo mostrar si está dentro de la pantalla
                if 0 <= px <= ANCHO:
                    # Línea vertical guía (semi-transparente)
                    pygame.draw.line(surf_temp, self.color_linea, (px, 0), (px, ALTO), 1)
                    
                    # Texto arriba
                    texto_sup = self.fuente.render(f"X:{int(x)}", True, self.color_texto)
                    pantalla.blit(texto_sup, (px - texto_sup.get_width()//2, 5))
                    
                    # Texto abajo
                    texto_inf = self.fuente.render(f"X:{int(x)}", True, self.color_texto)
                    pantalla.blit(texto_inf, (px - texto_inf.get_width()//2, ALTO - 20))
            
            x += self.espaciado_coords
        
        # ===== COORDENADAS VERTICALES (lados izquierdo y derecho) =====
        # Encontrar primera coordenada Y visible
        y_inicio = int(y_min // self.espaciado_coords) * self.espaciado_coords
        
        y = y_inicio
        while y <= y_max:
            if 0 <= y <= mundo_alto:
                _, py = camara.mundo_a_pantalla(0, y)
                
                # Solo mostrar si está dentro de la pantalla
                if 0 <= py <= ALTO:
                    # Línea horizontal guía (semi-transparente)
                    pygame.draw.line(surf_temp, self.color_linea, (0, py), (ANCHO, py), 1)
                    
                    # Texto izquierda
                    texto_izq = self.fuente.render(f"Y:{int(y)}", True, self.color_texto)
                    pantalla.blit(texto_izq, (5, py - texto_izq.get_height()//2))
                    
                    # Texto derecha
                    texto_der = self.fuente.render(f"Y:{int(y)}", True, self.color_texto)
                    pantalla.blit(texto_der, (ANCHO - texto_der.get_width() - 5, py - texto_der.get_height()//2))
            
            y += self.espaciado_coords
        
        # Blit superficie con líneas semi-transparentes
        pantalla.blit(surf_temp, (0, 0))
        
        # ===== COORDENADAS DEL CURSOR (esquina superior izquierda) =====
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mundo_x, mundo_y = camara.pantalla_a_mundo(mouse_x, mouse_y)
        
        # Fondo semi-transparente para el texto
        texto_cursor = f"Cursor: ({int(mundo_x)}, {int(mundo_y)})"
        surf_texto = self.fuente.render(texto_cursor, True, (255, 255, 255))
        
        # Fondo negro semi-transparente
        fondo_rect = pygame.Rect(ANCHO - surf_texto.get_width() - 20, 5, 
                                  surf_texto.get_width() + 10, surf_texto.get_height() + 5)
        s_fondo = pygame.Surface((fondo_rect.width, fondo_rect.height), pygame.SRCALPHA)
        s_fondo.fill((0, 0, 0, 180))
        pantalla.blit(s_fondo, fondo_rect.topleft)
        
        # Texto encima
        pantalla.blit(surf_texto, (ANCHO - surf_texto.get_width() - 15, 8))
        
        # ===== INSTRUCCIONES (esquina inferior izquierda) =====
        instrucciones = [
            "Sistema de Coordenadas: ON",
            "Presiona C para ocultar",
            "Haz clic en el mapa para ver coordenadas exactas"
        ]
        
        y_offset = ALTO - 80
        for instruccion in instrucciones:
            surf_instr = self.fuente.render(instruccion, True, self.color_texto)
            
            # Fondo semi-transparente
            fondo_rect = pygame.Rect(5, y_offset, surf_instr.get_width() + 10, surf_instr.get_height() + 2)
            s_fondo = pygame.Surface((fondo_rect.width, fondo_rect.height), pygame.SRCALPHA)
            s_fondo.fill((0, 0, 0, 160))
            pantalla.blit(s_fondo, fondo_rect.topleft)
            
            pantalla.blit(surf_instr, (10, y_offset))
            y_offset += 20
    
    def mostrar_click_coords(self, pantalla, camara, click_x, click_y):
        """
        Muestra coordenadas al hacer clic en el mapa
        
        Args:
            pantalla: Surface de pygame
            camara: Instancia de Camara
            click_x, click_y: Posición del clic en pantalla
        """
        if not self.mostrar:
            return
        
        # Convertir a coordenadas del mundo
        mundo_x, mundo_y = camara.pantalla_a_mundo(click_x, click_y)
        
        # Crear tooltip con coordenadas
        texto = f"Castillo aquí: ({int(mundo_x)}, {int(mundo_y)})"
        fuente_grande = pygame.font.Font(None, 24)
        surf_texto = fuente_grande.render(texto, True, (255, 255, 0))
        
        # Fondo semi-transparente
        padding = 10
        fondo_rect = pygame.Rect(
            click_x - surf_texto.get_width()//2 - padding, 
            click_y - 40,
            surf_texto.get_width() + padding*2, 
            surf_texto.get_height() + padding
        )
        
        # Asegurar que no salga de la pantalla
        if fondo_rect.left < 0:
            fondo_rect.left = 10
        if fondo_rect.right > ANCHO:
            fondo_rect.right = ANCHO - 10
        if fondo_rect.top < 0:
            fondo_rect.top = 50
        
        s_fondo = pygame.Surface((fondo_rect.width, fondo_rect.height), pygame.SRCALPHA)
        s_fondo.fill((0, 0, 0, 200))
        pantalla.blit(s_fondo, fondo_rect.topleft)
        
        # Texto encima
        pantalla.blit(surf_texto, (fondo_rect.centerx - surf_texto.get_width()//2, 
                                   fondo_rect.centery - surf_texto.get_height()//2))
        
        # Cruz pequeña en el punto exacto
        pygame.draw.line(pantalla, (255, 255, 0), (click_x - 10, click_y), (click_x + 10, click_y), 2)
        pygame.draw.line(pantalla, (255, 255, 0), (click_x, click_y - 10), (click_x, click_y + 10), 2)
        pygame.draw.circle(pantalla, (255, 255, 0), (click_x, click_y), 15, 2)


# Instancia global para facilitar uso
sistema_coordenadas = SistemaCoordenadas()
