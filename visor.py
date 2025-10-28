# visor_clash_style.py
# Zoom real sin distorsión, océano de fondo, flechas para mover,
# y limpieza automática del "marco blanco" (parchment) en los bordes.

import pygame, json, math

# ---------- CONFIG ----------
MAP_JSON = "exports/got_tiles.json"  # JSON de tiles
SCREEN_W, SCREEN_H = 1200, 800

ZOOM_MIN, ZOOM_MAX = 0.08, 6.0
ARROW_BASE_SPEED = 600   # tiles/seg a zoom=1.0 (se escala por 1/zoom)

COLORS = {
    "water":    (38, 76, 115),
    "sand":     (220, 200, 140),
    "grass":    (124, 153, 93),
    "forest":   (60, 100, 70),
    "mountain": (125, 120, 115),
    "snow":     (245, 245, 245),
}

# océano alrededor para poder alejarte y ver mar
OCEAN_COLOR = (24, 60, 100)
OCEAN_PADDING_RATIO = 0.08  # 8 % del lado mayor del mapa como borde

# Borde "marco blanco" a limpiar:
FRAME_CLASSES = {"snow", "sand"}   # qué clases consideramos "marco"
FRAME_TOLERANCE = 0.95             # si el 95% de una fila/col es marco -> conviértelo a "water"
FRAME_MAX_STRIP = 200              # máxima cantidad de filas/columnas que limpiamos por cada lado


# ---------- UTILIDADES ----------
def load_tiles():
    with open(MAP_JSON) as f:
        tiles = json.load(f)
    H, W = len(tiles), len(tiles[0])
    return tiles, W, H

def wipe_frame_to_water(tiles, frame_classes=FRAME_CLASSES, tol=FRAME_TOLERANCE, max_strip=FRAME_MAX_STRIP):
    """
    Convierte a 'water' las filas/columnas del borde que sean casi todo 'marco' (snow/sand).
    No toca la nieve del norte porque sólo limpia mientras la franja completa cumple el porcentaje.
    """
    h, w = len(tiles), len(tiles[0])

    # Top
    stripped = 0
    y = 0
    while y < h and stripped < max_strip:
        row = tiles[y]
        frac = sum(1 for v in row if v in frame_classes) / w
        if frac >= tol:
            for x in range(w):
                tiles[y][x] = "water"
            y += 1
            stripped += 1
        else:
            break

    # Bottom
    stripped = 0
    y = h - 1
    while y >= 0 and stripped < max_strip:
        row = tiles[y]
        frac = sum(1 for v in row if v in frame_classes) / w
        if frac >= tol:
            for x in range(w):
                tiles[y][x] = "water"
            y -= 1
            stripped += 1
        else:
            break

    # Left
    stripped = 0
    x = 0
    while x < w and stripped < max_strip:
        col_vals = [tiles[y][x] for y in range(h)]
        frac = sum(1 for v in col_vals if v in frame_classes) / h
        if frac >= tol:
            for y in range(h):
                tiles[y][x] = "water"
            x += 1
            stripped += 1
        else:
            break

    # Right
    stripped = 0
    x = w - 1
    while x >= 0 and stripped < max_strip:
        col_vals = [tiles[y][x] for y in range(h)]
        frac = sum(1 for v in col_vals if v in frame_classes) / h
        if frac >= tol:
            for y in range(h):
                tiles[y][x] = "water"
            x -= 1
            stripped += 1
        else:
            break

def make_world_surface(tiles, W, H):
    """Superficie donde cada tile = 1 píxel."""
    surf = pygame.Surface((W, H))
    lock = pygame.PixelArray(surf)
    for y in range(H):
        row = tiles[y]
        for x in range(W):
            lock[x, y] = surf.map_rgb(COLORS[row[x]])
    del lock
    return surf.convert()

def add_ocean_padding(world, ratio, ocean_color):
    """Rodea el mapa con océano (padding)."""
    w, h = world.get_size()
    pad = int(max(w, h) * ratio)
    canvas = pygame.Surface((w + 2*pad, h + 2*pad)).convert()
    canvas.fill(ocean_color)
    canvas.blit(world, (pad, pad))
    return canvas

def clamp_camera(cam_x, cam_y, zoom, world_w, world_h, screen_w, screen_h):
    """Viewport seguro y cámara dentro del mundo."""
    vw = max(1, min(world_w, int(math.ceil(screen_w / zoom))))
    vh = max(1, min(world_h, int(math.ceil(screen_h / zoom))))
    cam_x = max(0, min(world_w - vw, cam_x))
    cam_y = max(0, min(world_h - vh, cam_y))
    return cam_x, cam_y, vw, vh


# ---------- PRINCIPAL ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Mapa con zoom real (sin distorsión) + flechas + limpieza de marco")

    tiles, W, H = load_tiles()

    # 1) Limpia el marco blanco si existe
    wipe_frame_to_water(tiles)

    # 2) Render base + océano alrededor
    world = make_world_surface(tiles, W, H)
    world = add_ocean_padding(world, OCEAN_PADDING_RATIO, OCEAN_COLOR)
    world_w, world_h = world.get_width(), world.get_height()

    # cámara
    cam_x = (world_w - SCREEN_W) // 2
    cam_y = (world_h - SCREEN_H) // 2
    zoom = 0.5

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0  # segundos por frame
        mx, my = pygame.mouse.get_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEWHEEL:
                # zoom anclado al cursor
                cam_x, cam_y, vw_old, vh_old = clamp_camera(cam_x, cam_y, zoom, world_w, world_h, SCREEN_W, SCREEN_H)
                world_px = cam_x + int(mx / SCREEN_W * vw_old)
                world_py = cam_y + int(my / SCREEN_H * vh_old)
                zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom + e.y * 0.1))
                _, _, vw, vh = clamp_camera(cam_x, cam_y, zoom, world_w, world_h, SCREEN_W, SCREEN_H)
                cam_x = world_px - int(mx / SCREEN_W * vw)
                cam_y = world_py - int(my / SCREEN_H * vh)

        # Arrastre con botón derecho
        if pygame.mouse.get_pressed()[2]:
            rx, ry = pygame.mouse.get_rel()
            cam_x -= int(rx / max(zoom, 1e-6))
            cam_y -= int(ry / max(zoom, 1e-6))
        else:
            pygame.mouse.get_rel()

        # --- Movimiento con flechas (velocidad proporcional al 1/zoom) ---
        keys = pygame.key.get_pressed()
        speed = int(ARROW_BASE_SPEED * dt / max(zoom, 1e-6))  # tiles por frame
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            cam_x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            cam_x += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            cam_y -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            cam_y += speed

        # clamp final
        cam_x, cam_y, vw, vh = clamp_camera(cam_x, cam_y, zoom, world_w, world_h, SCREEN_W, SCREEN_H)

        # Recorte del mundo
        view = world.subsurface((cam_x, cam_y, vw, vh))

        # Escala sin distorsión (letterbox/pillarbox AZUL)
        scale = min(SCREEN_W / vw, SCREEN_H / vh)
        dst_w = max(1, int(vw * scale))
        dst_h = max(1, int(vh * scale))
        frame = pygame.transform.smoothscale(view, (dst_w, dst_h))

        # Fondo azul (no negro) para las bandas
        screen.fill(OCEAN_COLOR)
        off_x = (SCREEN_W - dst_w) // 2
        off_y = (SCREEN_H - dst_h) // 2
        screen.blit(frame, (off_x, off_y))

        # HUD
        font = pygame.font.SysFont(None, 20)
        info = font.render(f"zoom {zoom:.2f}x  |  world {world_w}x{world_h}  |  view {vw}x{vh}", True, (230, 230, 230))
        screen.blit(info, (10, 10))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
