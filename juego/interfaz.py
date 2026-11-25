"""Escape del laberinto: interfaz gráfica (PyGame).

Controles: flechas o WASD para moverse · 1-3 (o clic en cámaras) cambiar nivel ·
U deshacer · R reiniciar nivel · Enter continuar · F11 pantalla completa · Esc salir.
"""

import copy
import math
import random
import sys

import pygame

try:
    from juego.agentes import mover_agente
    from juego.niveles import MOVIMIENTOS, PATRULLA_NIVEL_3, TAM, Nivel
except ImportError:
    from agentes import mover_agente
    from niveles import MOVIMIENTOS, PATRULLA_NIVEL_3, TAM, Nivel

# ------------------------------------------------------------------ medidas
ANCHO, ALTO = 1000, 772
PANEL_W = 240
CELDA = 56
TABLERO_X, TABLERO_Y = 318, 118
TABLERO_LADO = CELDA * TAM
DUR_PASO = 0.16  # segundos por movimiento

# ------------------------------------------------------------------ paleta
FONDO = (30, 21, 15)
PIEDRA = (96, 76, 56)
PIEDRA_OSC = (64, 49, 36)
PIEDRA_CLARA = (128, 104, 78)
ARENA_A = (199, 168, 121)
ARENA_B = (188, 156, 110)
BLOQUE = (118, 90, 62)
BLOQUE_TOPE = (152, 121, 86)
CREMA = (243, 228, 196)
CREMA_TENUE = (206, 186, 150)
ORO = (226, 180, 74)
ORO_OSC = (150, 112, 40)
PELIGRO = (190, 64, 44)
TURQUESA = (52, 112, 128)

TECLAS = {
    pygame.K_UP: "arriba", pygame.K_w: "arriba",
    pygame.K_DOWN: "abajo", pygame.K_s: "abajo",
    pygame.K_LEFT: "izquierda", pygame.K_a: "izquierda",
    pygame.K_RIGHT: "derecha", pygame.K_d: "derecha",
}


def fuente(tam, negrita=False):
    for nombre in ("palatinolinotype", "bookantiqua", "georgia", "timesnewroman"):
        ruta = pygame.font.match_font(nombre, bold=negrita)
        if ruta:
            return pygame.font.Font(ruta, tam)
    return pygame.font.Font(None, tam + 6)


def ease_out(t):
    return 1 - (1 - t) ** 3


def celda_a_px(pos):
    """Centro en píxeles de la celda (x, y); acepta coordenadas fraccionarias."""
    x, y = pos
    return (TABLERO_X + (x - 0.5) * CELDA, TABLERO_Y + (TAM - y + 0.5) * CELDA)


def mezclar(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ------------------------------------------------------------------ texturas
def textura_piedra(w, h, base, semilla, grietas=3):
    rnd = random.Random(semilla)
    sup = pygame.Surface((w, h))
    sup.fill(base)
    for _ in range(w * h // 30):
        d = rnd.randint(-12, 12)
        c = tuple(max(0, min(255, v + d)) for v in base)
        sup.set_at((rnd.randrange(w), rnd.randrange(h)), c)
    oscuro = mezclar(base, (0, 0, 0), 0.25)
    for _ in range(grietas):
        x, y = rnd.randrange(w), rnd.randrange(h)
        for _ in range(rnd.randint(3, 6)):
            nx, ny = x + rnd.randint(-14, 14), y + rnd.randint(-14, 14)
            pygame.draw.line(sup, oscuro, (x, y), (nx, ny), 1)
            x, y = nx, ny
    return sup


def construir_tablero(nivel):
    sup = pygame.Surface((TABLERO_LADO, TABLERO_LADO))
    for y in range(1, TAM + 1):
        for x in range(1, TAM + 1):
            base = ARENA_A if (x + y) % 2 == 0 else ARENA_B
            tile = textura_piedra(CELDA, CELDA, base, x * 31 + y * 7 + nivel.numero, grietas=1)
            px, py = (x - 1) * CELDA, (TAM - y) * CELDA
            sup.blit(tile, (px, py))
            pygame.draw.line(sup, mezclar(base, (0, 0, 0), 0.12), (px, py), (px + CELDA, py))
            pygame.draw.line(sup, mezclar(base, (0, 0, 0), 0.12), (px, py), (px, py + CELDA))
    # Salida: losa dorada con escalones
    sx, sy = (nivel.salida[0] - 1) * CELDA, (TAM - nivel.salida[1]) * CELDA
    for i in range(4):
        inset = 6 + i * 6
        color = mezclar(ORO, (60, 40, 20), i * 0.22)
        pygame.draw.rect(sup, color, (sx + inset, sy + inset, CELDA - 2 * inset, CELDA - 2 * inset))
    # Bloques de piedra (obstáculos) con volumen
    for (x, y) in sorted(nivel.muros, key=lambda p: -p[1]):
        px, py = (x - 1) * CELDA, (TAM - y) * CELDA
        sombra = pygame.Surface((CELDA, CELDA), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 70))
        sup.blit(sombra, (px + 5, py + 6))
        cuerpo = textura_piedra(CELDA - 4, CELDA - 4, BLOQUE, x * 13 + y, grietas=2)
        sup.blit(cuerpo, (px + 2, py + 2))
        tope = textura_piedra(CELDA - 4, CELDA - 16, BLOQUE_TOPE, x * 17 + y * 3, grietas=1)
        sup.blit(tope, (px + 2, py + 2))
        pygame.draw.rect(sup, mezclar(BLOQUE, (0, 0, 0), 0.35), (px + 2, py + 2, CELDA - 4, CELDA - 4), 1)
    return sup


def construir_friso(ancho, semilla):
    """Banda superior con glifos inventados tallados en la piedra."""
    alto = 52
    sup = textura_piedra(ancho, alto, PIEDRA_CLARA, semilla, grietas=6)
    rnd = random.Random(semilla)
    tinta = mezclar(PIEDRA_CLARA, (0, 0, 0), 0.5)
    luz = mezclar(PIEDRA_CLARA, (255, 255, 255), 0.25)
    x = 18
    while x < ancho - 30:
        tipo = rnd.randrange(6)
        cy = alto // 2
        for color, d in ((luz, 1), (tinta, 0)):
            if tipo == 0:
                pygame.draw.circle(sup, color, (x + 9 + d, cy + d), 8, 2)
                pygame.draw.circle(sup, color, (x + 9 + d, cy + d), 2)
            elif tipo == 1:
                pygame.draw.polygon(sup, color, [(x + d, cy + 10 + d), (x + 9 + d, cy - 10 + d), (x + 18 + d, cy + 10 + d)], 2)
            elif tipo == 2:
                for k in range(3):
                    pygame.draw.line(sup, color, (x + d + k * 6, cy - 9 + d), (x + d + k * 6, cy + 9 + d), 2)
            elif tipo == 3:
                pygame.draw.arc(sup, color, (x + d, cy - 10 + d, 18, 20), 0, math.pi, 2)
                pygame.draw.line(sup, color, (x + 9 + d, cy + d), (x + 9 + d, cy + 10 + d), 2)
            elif tipo == 4:
                pygame.draw.lines(sup, color, False, [(x + d, cy + d), (x + 6 + d, cy - 8 + d), (x + 12 + d, cy + d), (x + 18 + d, cy - 8 + d)], 2)
            else:
                pygame.draw.ellipse(sup, color, (x + d, cy - 5 + d, 18, 10), 2)
                pygame.draw.circle(sup, color, (x + 9 + d, cy + d), 2)
        x += 34
    pygame.draw.line(sup, tinta, (0, alto - 1), (ancho, alto - 1), 2)
    return sup


# ------------------------------------------------------------------ personajes
def dibujar_sombra(sup, cx, cy, w=30):
    s = pygame.Surface((w, w // 3), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 80), s.get_rect())
    sup.blit(s, (cx - w // 2, cy + 14))


def dibujar_explorador(sup, cx, cy, t):
    dibujar_sombra(sup, cx, cy)
    cx, cy = int(cx), int(cy)
    pygame.draw.polygon(sup, TURQUESA, [(cx - 12, cy + 17), (cx + 12, cy + 17), (cx + 7, cy - 4), (cx - 7, cy - 4)])
    pygame.draw.polygon(sup, mezclar(TURQUESA, (0, 0, 0), 0.3), [(cx - 12, cy + 17), (cx + 12, cy + 17), (cx + 7, cy - 4), (cx - 7, cy - 4)], 2)
    pygame.draw.circle(sup, (214, 170, 128), (cx, cy - 10), 8)
    pygame.draw.arc(sup, mezclar(TURQUESA, (0, 0, 0), 0.2), (cx - 10, cy - 20, 20, 20), 0, math.pi, 4)
    # antorcha con llama viva
    pygame.draw.line(sup, (92, 60, 32), (cx + 12, cy + 8), (cx + 16, cy - 10), 3)
    f = math.sin(t * 14) * 1.5
    pygame.draw.circle(sup, (240, 120, 40), (cx + 16, int(cy - 14 + f / 2)), 5)
    pygame.draw.circle(sup, (255, 214, 110), (cx + 16, int(cy - 15 + f / 2)), 3)


def dibujar_escarabajo(sup, cx, cy, t):
    dibujar_sombra(sup, cx, cy, 34)
    cx, cy = int(cx), int(cy)
    pata = math.sin(t * 10) * 2
    for lado in (-1, 1):
        for k in (-6, 2, 10):
            pygame.draw.line(sup, (30, 34, 26), (cx, cy + k), (cx + lado * 17, int(cy + k + lado * pata)), 2)
    pygame.draw.ellipse(sup, (40, 70, 52), (cx - 12, cy - 8, 24, 26))
    pygame.draw.ellipse(sup, (70, 120, 86), (cx - 9, cy - 5, 8, 12))
    pygame.draw.line(sup, (20, 30, 22), (cx, cy - 7), (cx, cy + 17), 2)
    pygame.draw.circle(sup, (30, 44, 34), (cx, cy - 12), 6)
    pygame.draw.circle(sup, ORO, (cx - 2, cy - 13), 1)
    pygame.draw.circle(sup, ORO, (cx + 2, cy - 13), 1)


def dibujar_estatua(sup, cx, cy, t):
    dibujar_sombra(sup, cx, cy, 34)
    cx, cy = int(cx), int(cy)
    piedra = (112, 116, 124)
    pygame.draw.rect(sup, mezclar(piedra, (0, 0, 0), 0.3), (cx - 14, cy + 10, 28, 8))
    pygame.draw.polygon(sup, piedra, [(cx - 10, cy + 10), (cx + 10, cy + 10), (cx + 6, cy - 14), (cx - 6, cy - 14)])
    pygame.draw.polygon(sup, mezclar(piedra, (255, 255, 255), 0.2), [(cx - 6, cy - 14), (cx + 6, cy - 14), (cx, cy - 22)])
    brillo = int(160 + 90 * (0.5 + 0.5 * math.sin(t * 4)))
    for dx in (-3, 3):
        pygame.draw.circle(sup, (brillo, 40, 30), (cx + dx, cy - 6), 2)
    pygame.draw.line(sup, mezclar(piedra, (0, 0, 0), 0.4), (cx - 5, cy + 2), (cx + 5, cy + 2), 1)


def dibujar_centinela(sup, cx, cy, t):
    dibujar_sombra(sup, cx, cy)
    cx, cy = int(cx), int(cy)
    tunica = (58, 40, 66)
    pygame.draw.polygon(sup, tunica, [(cx - 13, cy + 17), (cx + 13, cy + 17), (cx + 6, cy - 8), (cx - 6, cy - 8)])
    pygame.draw.circle(sup, tunica, (cx, cy - 12), 8)
    pygame.draw.circle(sup, (20, 14, 22), (cx, cy - 11), 5)
    pygame.draw.circle(sup, ORO, (cx - 2, cy - 11), 1)
    pygame.draw.circle(sup, ORO, (cx + 2, cy - 11), 1)
    # farol
    oscila = math.sin(t * 3) * 2
    lx, ly = cx - 15, int(cy + 2 + oscila)
    halo = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(halo, (255, 200, 90, 60), (15, 15), 14)
    sup.blit(halo, (lx - 15, ly - 15))
    pygame.draw.rect(sup, ORO, (lx - 4, ly - 5, 8, 10), border_radius=2)
    pygame.draw.rect(sup, (255, 236, 160), (lx - 2, ly - 3, 4, 6))


GUARDIANES = {1: dibujar_escarabajo, 2: dibujar_estatua, 3: dibujar_centinela}
NOMBRE_GUARDIAN = {1: "El escarabajo rastreador", 2: "La estatua estratega", 3: "El centinela del farol"}


# ------------------------------------------------------------------ botones
class Boton:
    def __init__(self, texto, atajo, rect, accion):
        self.texto, self.atajo, self.rect, self.accion = texto, atajo, pygame.Rect(rect), accion
        self.hover = 0.0
        self.presionado = False
        self.cara = textura_piedra(self.rect.w, self.rect.h, PIEDRA, hash(texto) & 0xFFFF, grietas=2)

    def actualizar(self, dt, raton, activo):
        objetivo = 1.0 if activo and self.rect.collidepoint(raton) else 0.0
        self.hover += (objetivo - self.hover) * min(1, dt * 14)

    def dibujar(self, sup, f, fa, activo):
        r = self.rect.move(0, 2 if self.presionado else 0)
        sombra = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 90), sombra.get_rect(), border_radius=6)
        sup.blit(sombra, (r.x + 2, r.y + 4 - (2 if self.presionado else 0)))
        sup.blit(self.cara, r)
        if self.hover > 0.01:
            luz = pygame.Surface(r.size, pygame.SRCALPHA)
            luz.fill((255, 220, 150, int(28 * self.hover)))
            sup.blit(luz, r)
        borde = mezclar(PIEDRA_OSC, ORO, self.hover) if activo else PIEDRA_OSC
        pygame.draw.rect(sup, borde, r, 2, border_radius=6)
        pygame.draw.line(sup, PIEDRA_CLARA, (r.x + 4, r.y + 2), (r.right - 4, r.y + 2))
        color = mezclar(CREMA_TENUE, CREMA, self.hover) if activo else mezclar(PIEDRA_OSC, CREMA_TENUE, 0.4)
        # texto "tallado": luz debajo, tinta encima
        txt = f.render(self.texto, True, color)
        luzt = f.render(self.texto, True, mezclar(PIEDRA, (0, 0, 0), 0.5))
        x = r.x + 16
        y = r.centery - txt.get_height() // 2
        sup.blit(luzt, (x + 1, y + 1))
        sup.blit(txt, (x, y))
        a = fa.render(self.atajo, True, mezclar(color, PIEDRA, 0.35))
        sup.blit(a, (r.right - a.get_width() - 14, r.centery - a.get_height() // 2))


# ------------------------------------------------------------------ juego
class Juego:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Escape del laberinto")
        # Se dibuja en un lienzo fijo y se escala a la ventana real.
        self.pantalla = pygame.Surface((ANCHO, ALTO))
        escritorio = pygame.display.get_desktop_sizes()[0]
        escala = min(1.0, escritorio[0] * 0.9 / ANCHO, escritorio[1] * 0.82 / ALTO)
        self.tam_ventana = (int(ANCHO * escala), int(ALTO * escala))
        self.completa = False
        self.ventana = pygame.display.set_mode(self.tam_ventana, pygame.RESIZABLE)
        self.reloj = pygame.time.Clock()
        self.f_titulo = fuente(34, True)
        self.f_grande = fuente(46, True)
        self.f_media = fuente(22, True)
        self.f_texto = fuente(18)
        self.f_peque = fuente(14)
        self.t = 0.0
        self.fondo = textura_piedra(ANCHO, ALTO, FONDO, 1, grietas=40)
        self.panel = textura_piedra(PANEL_W, ALTO, PIEDRA_OSC, 2, grietas=14)
        self.friso = construir_friso(TABLERO_LADO + 24, 9)
        bx, bw = 24, PANEL_W - 48
        self.botones = [
            Boton("Deshacer", "U", (bx, 250, bw, 46), self.deshacer),
            Boton("Reiniciar nivel", "R", (bx, 306, bw, 46), self.reiniciar),
            Boton("Salir", "Esc", (bx, ALTO - 74, bw, 46), self.salir),
        ]
        self.rects_camaras = {
            n: pygame.Rect(24, 392 + 24 + i * 58, PANEL_W - 48, 48)
            for i, n in enumerate((1, 2, 3))
        }
        self.hover_camara = None
        self.completados = set()
        self.cargar_nivel(1)

    # ---------------------------------------------------------- estado
    def cargar_nivel(self, n):
        self.nivel = Nivel(n)
        self.superficie_tablero = construir_tablero(self.nivel)
        self.reiniciar()

    def reiniciar(self):
        self.jugador = self.nivel.inicio_jugador
        self.agente = self.nivel.inicio_agente
        self.memoria = {}
        self.turno = 0
        self.historial = []
        self.estado = "jugador"  # jugador | anim_jugador | anim_agente | victoria | derrota | final
        self.anim_j = None
        self.anim_a = None
        self.mensaje = "Tu turno. Llega a la salida dorada."
        self.fin_t = 0.0

    def deshacer(self):
        if self.estado in ("jugador", "derrota") and self.historial:
            self.jugador, self.agente, self.memoria, self.turno = self.historial.pop()
            self.estado = "jugador"
            self.mensaje = "Jugada deshecha."

    def salir(self):
        pygame.quit()
        sys.exit()

    def mover_jugador(self, direccion):
        if self.estado != "jugador":
            return
        dx, dy = MOVIMIENTOS[direccion]
        destino = (self.jugador[0] + dx, self.jugador[1] + dy)
        if not self.nivel.libre(destino):
            self.mensaje = "La piedra no cede por ahí."
            return
        self.historial.append((self.jugador, self.agente, copy.deepcopy(self.memoria), self.turno))
        self.anim_j = (self.jugador, destino, 0.0)
        self.jugador = destino
        self.estado = "anim_jugador"

    def turno_agente(self):
        nuevo = mover_agente(self.nivel, self.agente, self.jugador, self.memoria)
        if nuevo != self.agente and nuevo not in self.nivel.vecinos(self.agente):
            raise ValueError(f"Movimiento inválido del agente: {self.agente} -> {nuevo}")
        self.anim_a = (self.agente, nuevo, 0.0)
        self.agente = nuevo
        self.estado = "anim_agente"

    def resolver(self):
        if self.jugador == self.agente:
            self.estado, self.fin_t = "derrota", 0.0
            self.mensaje = "Te atraparon."
            return True
        if self.jugador == self.nivel.salida:
            self.completados.add(self.nivel.numero)
            self.estado = "final" if self.completados == {1, 2, 3} else "victoria"
            self.fin_t = 0.0
            self.mensaje = "¡Escapaste!"
            return True
        return False

    # ---------------------------------------------------------- bucle
    def actualizar(self, dt):
        self.t += dt
        self.fin_t += dt
        raton = self.a_lienzo(pygame.mouse.get_pos())
        for b in self.botones:
            b.actualizar(dt, raton, self.boton_activo(b))
        self.hover_camara = next(
            (n for n, r in self.rects_camaras.items() if r.collidepoint(raton)),
            None,
        )
        if self.estado == "anim_jugador":
            a, b, p = self.anim_j
            p += dt / DUR_PASO
            self.anim_j = (a, b, p)
            if p >= 1:
                self.anim_j = None
                if not self.resolver():
                    self.turno_agente()
        elif self.estado == "anim_agente":
            a, b, p = self.anim_a
            p += dt / DUR_PASO
            self.anim_a = (a, b, p)
            if p >= 1:
                self.anim_a = None
                self.turno += 1
                if not self.resolver():
                    self.estado = "jugador"
                    self.mensaje = "Tu turno."

    def boton_activo(self, b):
        if b.accion == self.deshacer:
            return bool(self.historial) and self.estado in ("jugador", "derrota")
        return True

    def eventos(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.salir()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F11 or (e.key == pygame.K_RETURN and e.mod & pygame.KMOD_ALT):
                    self.alternar_completa()
                elif e.key == pygame.K_ESCAPE:
                    if self.completa:
                        self.alternar_completa()
                    else:
                        self.salir()
                elif e.key == pygame.K_u:
                    self.deshacer()
                elif e.key == pygame.K_r:
                    self.reiniciar()
                elif e.key in (pygame.K_1, pygame.K_KP1):
                    self.cargar_nivel(1)
                elif e.key in (pygame.K_2, pygame.K_KP2):
                    self.cargar_nivel(2)
                elif e.key in (pygame.K_3, pygame.K_KP3):
                    self.cargar_nivel(3)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self.continuar()
                elif e.key in TECLAS:
                    self.mover_jugador(TECLAS[e.key])
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos_l = self.a_lienzo(e.pos)
                for b in self.botones:
                    if b.rect.collidepoint(pos_l) and self.boton_activo(b):
                        b.presionado = True
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                pos_l = self.a_lienzo(e.pos)
                clic_boton = False
                for b in self.botones:
                    if b.presionado and b.rect.collidepoint(pos_l):
                        b.accion()
                        clic_boton = True
                    b.presionado = False
                if not clic_boton:
                    for n, r in self.rects_camaras.items():
                        if r.collidepoint(pos_l) and n != self.nivel.numero:
                            self.cargar_nivel(n)
                            break

    def continuar(self):
        if self.estado == "victoria":
            if self.nivel.numero < 3 and (self.nivel.numero + 1) not in self.completados:
                siguiente = self.nivel.numero + 1
            else:
                siguiente = next((n for n in (1, 2, 3) if n not in self.completados), 1)
            self.cargar_nivel(siguiente)
        elif self.estado == "derrota":
            self.reiniciar()
        elif self.estado == "final":
            self.completados.clear()
            self.cargar_nivel(1)

    # ---------------------------------------------------------- dibujo
    def pos_visual(self, anim, actual):
        if anim is None:
            return actual
        (ax, ay), (bx, by), p = anim
        k = ease_out(min(1.0, p))
        return (ax + (bx - ax) * k, ay + (by - ay) * k)

    def dibujar_panel(self, s):
        s.blit(self.panel, (0, 0))
        pygame.draw.line(s, (20, 14, 10), (PANEL_W, 0), (PANEL_W, ALTO), 4)
        pygame.draw.line(s, PIEDRA, (PANEL_W - 3, 0), (PANEL_W - 3, ALTO), 1)
        for i, linea in enumerate(("Escape del", "laberinto")):
            sombra = self.f_titulo.render(linea, True, (20, 14, 10))
            txt = self.f_titulo.render(linea, True, ORO)
            s.blit(sombra, (26, 30 + i * 38))
            s.blit(txt, (24, 28 + i * 38))
        # contador de turnos
        etiqueta = self.f_peque.render("TURNOS", True, CREMA_TENUE)
        s.blit(etiqueta, (26, 128))
        n = self.f_grande.render(str(self.turno), True, CREMA)
        s.blit(n, (24, 146))
        pygame.draw.line(s, PIEDRA, (24, 222), (PANEL_W - 24, 222), 1)
        for b in self.botones:
            b.dibujar(s, self.f_texto, self.f_peque, self.boton_activo(b))
        # mapa de niveles: tres tablillas (clicables o con teclas 1-3)
        y0 = 392
        s.blit(self.f_peque.render("CÁMARAS (1-3)", True, CREMA_TENUE), (26, y0))
        nombres = {1: "Búsqueda A*", 2: "Minimax alfa-beta", 3: "Agente lógico"}
        for i, n in enumerate((1, 2, 3)):
            r = self.rects_camaras[n]
            actual = n == self.nivel.numero
            hecho = n in self.completados
            hover = self.hover_camara == n and not actual
            base = PIEDRA_CLARA if actual else (mezclar(PIEDRA, PIEDRA_CLARA, 0.45) if hover else PIEDRA)
            pygame.draw.rect(s, base, r, border_radius=4)
            borde = ORO if actual else (mezclar(PIEDRA_OSC, ORO, 0.55) if hover else PIEDRA_OSC)
            pygame.draw.rect(s, borde, r, 2, border_radius=4)
            romano = ("I", "II", "III")[i]
            color = ORO if hecho else (CREMA if actual or hover else CREMA_TENUE)
            s.blit(self.f_media.render(romano, True, color), (r.x + 12, r.y + 10))
            s.blit(self.f_peque.render(nombres[n], True, color), (r.x + 58, r.y + 16))
            if hecho:
                pygame.draw.lines(s, ORO, False, [(r.right - 30, r.centery), (r.right - 24, r.centery + 6), (r.right - 14, r.centery - 6)], 3)

    def dibujar_tablero(self, s):
        marco = pygame.Rect(TABLERO_X - 14, TABLERO_Y - 66, TABLERO_LADO + 28, TABLERO_LADO + 80)
        sombra = pygame.Surface(marco.size, pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 110), sombra.get_rect(), border_radius=6)
        s.blit(sombra, (marco.x + 6, marco.y + 10))
        pygame.draw.rect(s, PIEDRA_OSC, marco, border_radius=6)
        s.blit(self.friso, (TABLERO_X - 12, TABLERO_Y - 62))
        # antorchas del friso
        for fx in (TABLERO_X + 60, TABLERO_X + TABLERO_LADO - 60):
            f = math.sin(self.t * 11 + fx) * 1.5
            halo = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 190, 90, 50), (30, 30), 28)
            s.blit(halo, (fx - 30, TABLERO_Y - 66))
            pygame.draw.circle(s, (240, 120, 40), (fx, int(TABLERO_Y - 38 + f)), 6)
            pygame.draw.circle(s, (255, 220, 120), (fx, int(TABLERO_Y - 39 + f)), 3)
        s.blit(self.superficie_tablero, (TABLERO_X, TABLERO_Y))
        # escalera de salida fuera del muro, junto a (10, 10)
        ex, ey = celda_a_px(self.nivel.salida)
        for k in range(5):
            pygame.draw.rect(s, mezclar(ORO_OSC, PIEDRA_CLARA, k / 5), (ex + CELDA // 2 + k * 5, ey - 22 + k * 3, 6, 44 - k * 6))
        # nivel 3: ruta de patrullaje y zona de detección
        if self.nivel.numero == 3:
            for p in PATRULLA_NIVEL_3:
                cx, cy = celda_a_px(p)
                pygame.draw.circle(s, (120, 80, 130), (int(cx), int(cy)), 4)
            ax, ay = self.pos_visual(self.anim_a, self.agente)
            capa = pygame.Surface((CELDA, CELDA), pygame.SRCALPHA)
            capa.fill((255, 200, 90, 46))
            for dx, dy in MOVIMIENTOS.values():
                c = (round(ax) + dx, round(ay) + dy)
                if self.nivel.libre(c):
                    cx, cy = celda_a_px(c)
                    s.blit(capa, (cx - CELDA / 2, cy - CELDA / 2))
        # personajes (el de más abajo se dibuja encima)
        jx, jy = celda_a_px(self.pos_visual(self.anim_j, self.jugador))
        gx, gy = celda_a_px(self.pos_visual(self.anim_a, self.agente))
        dibujos = [(jy, lambda: dibujar_explorador(s, jx, jy, self.t)),
                   (gy, lambda: GUARDIANES[self.nivel.numero](s, gx, gy, self.t))]
        for _, d in sorted(dibujos, key=lambda x: x[0]):
            d()
        # barra de estado bajo el tablero
        y = TABLERO_Y + TABLERO_LADO + 22
        titulo = self.f_media.render(f"Cámara {self.nivel.numero}: {self.nivel.nombre}", True, CREMA)
        s.blit(titulo, (TABLERO_X - 12, y))
        guardian = self.f_texto.render(NOMBRE_GUARDIAN[self.nivel.numero], True, CREMA_TENUE)
        s.blit(guardian, (TABLERO_X - 12, y + 30))
        msg = self.f_texto.render(self.mensaje, True, PELIGRO if self.estado == "derrota" else ORO)
        s.blit(msg, (TABLERO_X + TABLERO_LADO + 12 - msg.get_width(), y + 4))
        accion_texto = self.memoria.get("ultima_accion", "en espera")
        color_accion = PELIGRO if self.memoria.get("deteccion_logica") else CREMA_TENUE
        accion_sup = self.f_peque.render(f"Agente: {accion_texto}", True, color_accion)
        s.blit(accion_sup, (TABLERO_X + TABLERO_LADO + 12 - accion_sup.get_width(), y + 32))

    def dibujar_cierre(self, s):
        if self.estado not in ("victoria", "derrota", "final"):
            return
        k = ease_out(min(1.0, self.fin_t / 0.35))
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((12, 8, 6, int(170 * k)))
        s.blit(velo, (0, 0))
        subtitulo_victoria = (
            "Enter: siguiente cámara"
            if self.nivel.numero < 3 and (self.nivel.numero + 1) not in self.completados
            else "Enter: ir a la cámara pendiente"
        )
        textos = {
            "victoria": ("Escapaste de la cámara", subtitulo_victoria),
            "derrota": ("El guardián te atrapó", "Enter: reintentar · U: deshacer la última jugada"),
            "final": ("Saliste del laberinto", "Superaste las tres cámaras · Enter: jugar de nuevo"),
        }
        t1, t2 = textos[self.estado]
        color = PELIGRO if self.estado == "derrota" else ORO
        tablilla = pygame.Rect(0, 0, 560, 170)
        tablilla.center = (TABLERO_X + TABLERO_LADO // 2, ALTO // 2 + int((1 - k) * 24))
        cara = textura_piedra(tablilla.w, tablilla.h, PIEDRA, 77, grietas=5)
        cara.set_alpha(int(255 * k))
        s.blit(cara, tablilla)
        pygame.draw.rect(s, color, tablilla, 3, border_radius=4)
        a = self.f_grande.render(t1, True, color)
        b = self.f_texto.render(t2, True, CREMA)
        a.set_alpha(int(255 * k))
        b.set_alpha(int(255 * k))
        s.blit(a, a.get_rect(center=(tablilla.centerx, tablilla.y + 64)))
        s.blit(b, b.get_rect(center=(tablilla.centerx, tablilla.y + 122)))

    def dibujar(self):
        s = self.pantalla
        s.blit(self.fondo, (0, 0))
        self.dibujar_tablero(s)
        self.dibujar_panel(s)
        self.dibujar_cierre(s)
        self.presentar()

    # ---------------------------------------------------------- ventana
    def area_destino(self):
        """Rectángulo donde cabe el lienzo dentro de la ventana, sin deformarlo."""
        vw, vh = self.ventana.get_size()
        k = min(vw / ANCHO, vh / ALTO)
        w, h = int(ANCHO * k), int(ALTO * k)
        return pygame.Rect((vw - w) // 2, (vh - h) // 2, w, h)

    def a_lienzo(self, pos):
        r = self.area_destino()
        return ((pos[0] - r.x) * ANCHO / max(1, r.w), (pos[1] - r.y) * ALTO / max(1, r.h))

    def presentar(self):
        r = self.area_destino()
        self.ventana.fill((14, 10, 7))
        if r.size == (ANCHO, ALTO):
            self.ventana.blit(self.pantalla, r)
        else:
            self.ventana.blit(pygame.transform.smoothscale(self.pantalla, r.size), r)
        pygame.display.flip()

    def alternar_completa(self):
        self.completa = not self.completa
        if self.completa:
            self.ventana = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.ventana = pygame.display.set_mode(self.tam_ventana, pygame.RESIZABLE)

    def ejecutar(self, max_frames=None):
        frames = 0
        while max_frames is None or frames < max_frames:
            dt = self.reloj.tick(60) / 1000
            self.eventos()
            self.actualizar(dt)
            self.dibujar()
            frames += 1


if __name__ == "__main__":
    Juego().ejecutar()
