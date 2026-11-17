# main.py
import sys
import pygame
from escenarios import (
    N,
    acciones,
    cargar_escenario,
    cartesianas_a_pantalla,
    RUTA_PATRULLAJE_N3
)
from agentes_ia import (
    obtener_movimiento_astar,
    decision_alfa_beta_lim,
    obtener_movimiento_logico
)

# Constantes de la ventana y estetica estilo Mummy Maze
TAM_CELDA = 60
ANCHO_TABLERO = N * TAM_CELDA
ANCHO_PANEL = 320
ANCHO_VENTANA = ANCHO_TABLERO + ANCHO_PANEL
ALTO_VENTANA = N * TAM_CELDA

COLOR_ARENA_CLARA = (232, 205, 145)
COLOR_ARENA_OSCURA = (214, 184, 120)
COLOR_BORDE_CELDA = (168, 138, 82)
COLOR_MURO_BASE = (122, 88, 48)
COLOR_MURO_LUZ = (166, 126, 76)
COLOR_MURO_SOMBRA = (74, 51, 25)
COLOR_PANEL = (42, 32, 24)
COLOR_TEXTO = (245, 232, 199)
COLOR_DORADO = (255, 204, 51)
COLOR_PATRULLA = (70, 150, 210)

NOMBRES_NIVELES = {
    1: "Nivel 1: Busqueda A*",
    2: "Nivel 2: Minimax Alfa-Beta",
    3: "Nivel 3: Agente Logico (BC)"
}


class JuegoEscapeLaberinto:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Escape del Laberinto - Mummy Maze IA")
        self.pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
        self.reloj = pygame.time.Clock()
        self.fuente_titulo = pygame.font.SysFont("georgia", 20, bold=True)
        self.fuente_info = pygame.font.SysFont("consolas", 15)

        self.nivel_actual = 1
        self.iniciar_nivel(self.nivel_actual)

    def iniciar_nivel(self, nivel):
        datos = cargar_escenario(nivel)
        self.nivel_actual = nivel
        self.muros = datos["muros"]
        self.pos_p = datos["inicio_p"]
        self.pos_g = datos["inicio_g"]
        self.salida = datos["salida"]
        self.turno = 0
        self.estado_juego = "JUGANDO"
        self.ultima_accion_p = "-"
        self.ultima_accion_g = "-"
        self.ruta_astar = []
        self.indice_patrulla = 0
        self.deteccion_logica = False

    def mover_jugador(self, direccion):
        if self.estado_juego != "JUGANDO":
            return

        dx, dy = acciones[direccion]
        nx = self.pos_p[0] + dx
        ny = self.pos_p[1] + dy

        # Verificar limites del tablero 10x10 y obstaculos '#'
        if not (1 <= nx <= N and 1 <= ny <= N):
            return
        if (nx, ny) in self.muros:
            return

        # 1. El jugador humano realiza el primer movimiento
        self.pos_p = (nx, ny)
        self.ultima_accion_p = direccion
        self.turno += 1

        # Verificar si el jugador alcanzo la salida en (10, 10)
        if self.pos_p == self.salida:
            if self.nivel_actual < 3:
                self.estado_juego = "NIVEL_SUPERADO"
            else:
                self.estado_juego = "VICTORIA_TOTAL"
            return

        # Verificar si el jugador se movio hacia la celda del agente
        if self.pos_p == self.pos_g:
            self.estado_juego = "CAPTURADO"
            return

        # 2. Posteriormente, el agente ejecuta un movimiento
        self.ejecutar_turno_agente()

        # El agente gana cuando ocupa la misma celda que el jugador
        if self.pos_g == self.pos_p:
            self.estado_juego = "CAPTURADO"

    def ejecutar_turno_agente(self):
        if self.nivel_actual == 1:
            accion, nueva_pos, camino = obtener_movimiento_astar(
                self.pos_g, self.pos_p, self.muros
            )
            self.pos_g = nueva_pos
            self.ultima_accion_g = accion if accion else "sin ruta"
            self.ruta_astar = [estado for estado, _ in camino]

        elif self.nivel_actual == 2:
            accion, nueva_pos = decision_alfa_beta_lim(
                self.pos_g, self.pos_p, self.muros, self.salida, profundidad=4
            )
            self.pos_g = nueva_pos
            self.ultima_accion_g = accion if accion else "sin mov"
            self.ruta_astar = []

        elif self.nivel_actual == 3:
            accion, nueva_pos, nuevo_idx, detectado = obtener_movimiento_logico(
                self.pos_g, self.pos_p, self.muros, self.indice_patrulla
            )
            self.pos_g = nueva_pos
            self.indice_patrulla = nuevo_idx
            self.deteccion_logica = detectado
            if detectado:
                self.ultima_accion_g = f"{accion} (BC |= A_{accion})"
            else:
                self.ultima_accion_g = f"{accion} (Patrulla)"
            self.ruta_astar = []

    def dibujar_tablero(self):
        for x in range(1, N + 1):
            for y in range(1, N + 1):
                col, fila = cartesianas_a_pantalla(x, y)
                rect = pygame.Rect(col * TAM_CELDA, fila * TAM_CELDA, TAM_CELDA, TAM_CELDA)

                # Celdas de arena alternadas estilo Mummy Maze
                color_celda = COLOR_ARENA_CLARA if (x + y) % 2 == 0 else COLOR_ARENA_OSCURA
                pygame.draw.rect(self.pantalla, color_celda, rect)
                pygame.draw.rect(self.pantalla, COLOR_BORDE_CELDA, rect, 1)

                # Resaltar ruta de patrullaje en el Nivel 3
                if self.nivel_actual == 3 and (x, y) in RUTA_PATRULLAJE_N3:
                    pygame.draw.rect(self.pantalla, COLOR_PATRULLA, rect.inflate(-10, -10), 2)

                # Dibujar obstaculos '#' como muros de piedra egipcia
                if (x, y) in self.muros:
                    pygame.draw.rect(self.pantalla, COLOR_MURO_SOMBRA, rect)
                    pygame.draw.rect(self.pantalla, COLOR_MURO_BASE, rect.inflate(-6, -6))
                    pygame.draw.line(self.pantalla, COLOR_MURO_LUZ, rect.topleft, rect.topright, 3)
                    pygame.draw.line(self.pantalla, COLOR_MURO_LUZ, rect.topleft, rect.bottomleft, 3)

        # Dibujar salida 'E' en (10, 10) como escalera del templo
        col_e, fila_e = cartesianas_a_pantalla(*self.salida)
        rect_e = pygame.Rect(col_e * TAM_CELDA + 6, fila_e * TAM_CELDA + 6, TAM_CELDA - 12, TAM_CELDA - 12)
        pygame.draw.rect(self.pantalla, (60, 45, 20), rect_e, border_radius=6)
        for i in range(4):
            y_esc = rect_e.top + 8 + i * 10
            pygame.draw.line(self.pantalla, COLOR_DORADO, (rect_e.left + 6, y_esc), (rect_e.right - 6, y_esc), 3)

        # Dibujar Jugador Humano 'P' (Explorador)
        col_p, fila_p = cartesianas_a_pantalla(*self.pos_p)
        cx_p = col_p * TAM_CELDA + TAM_CELDA // 2
        cy_p = fila_p * TAM_CELDA + TAM_CELDA // 2
        pygame.draw.circle(self.pantalla, (40, 110, 180), (cx_p, cy_p + 4), 16)
        pygame.draw.circle(self.pantalla, (240, 200, 160), (cx_p, cy_p - 4), 11)
        pygame.draw.ellipse(self.pantalla, (160, 110, 50), (cx_p - 16, cy_p - 16, 32, 10))

        # Dibujar Agente Perseguidor 'G' (Momia Guardian)
        col_g, fila_g = cartesianas_a_pantalla(*self.pos_g)
        cx_g = col_g * TAM_CELDA + TAM_CELDA // 2
        cy_g = fila_g * TAM_CELDA + TAM_CELDA // 2
        pygame.draw.circle(self.pantalla, (235, 230, 210), (cx_g, cy_g), 18)
        for offset in (-8, 0, 8):
            pygame.draw.line(self.pantalla, (180, 170, 145), (cx_g - 15, cy_g + offset), (cx_g + 15, cy_g + offset), 2)
        pygame.draw.circle(self.pantalla, (220, 30, 30), (cx_g - 6, cy_g - 3), 3)
        pygame.draw.circle(self.pantalla, (220, 30, 30), (cx_g + 6, cy_g - 3), 3)

    def dibujar_panel(self):
        rect_panel = pygame.Rect(ANCHO_TABLERO, 0, ANCHO_PANEL, ALTO_VENTANA)
        pygame.draw.rect(self.pantalla, COLOR_PANEL, rect_panel)
        pygame.draw.line(self.pantalla, COLOR_DORADO, (ANCHO_TABLERO, 0), (ANCHO_TABLERO, ALTO_VENTANA), 3)

        x_txt = ANCHO_TABLERO + 16
        y_txt = 24

        titulo = self.fuente_titulo.render("ESCAPE DEL LABERINTO", True, COLOR_DORADO)
        self.pantalla.blit(titulo, (x_txt, y_txt))
        y_txt += 36

        sub = self.fuente_info.render(NOMBRES_NIVELES[self.nivel_actual], True, COLOR_TEXTO)
        self.pantalla.blit(sub, (x_txt, y_txt))
        y_txt += 38

        lineas = [
            f"Turno actual:   {self.turno}",
            f"Jugador (P):    {self.pos_p}",
            f"Guardian (G):   {self.pos_g}",
            f"Salida (E):     {self.salida}",
            "",
            f"Mov. Jugador:   {self.ultima_accion_p}",
            f"Mov. Agente:    {self.ultima_accion_g}",
            "",
            "--- CONTROLES ---",
            "Flechas / WASD : Mover (1 celda)",
            "Tecla R        : Reiniciar nivel",
            "Teclas 1, 2, 3 : Cambiar nivel",
        ]

        for linea in lineas:
            superficie = self.fuente_info.render(linea, True, COLOR_TEXTO)
            self.pantalla.blit(superficie, (x_txt, y_txt))
            y_txt += 24

        if self.estado_juego != "JUGANDO":
            y_txt += 20
            if self.estado_juego == "NIVEL_SUPERADO":
                msg1 = "¡NIVEL SUPERADO!"
                msg2 = "Presiona ESPACIO para avanzar"
                col_msg = (100, 240, 120)
            elif self.estado_juego == "VICTORIA_TOTAL":
                msg1 = "¡JUEGO COMPLETADO!"
                msg2 = "3 niveles superados (R reinicia)"
                col_msg = COLOR_DORADO
            else:
                msg1 = "¡AGENTE GANA (CAPTURA)!"
                msg2 = "Presiona R para reiniciar nivel"
                col_msg = (255, 90, 90)

            self.pantalla.blit(self.fuente_titulo.render(msg1, True, col_msg), (x_txt, y_txt))
            self.pantalla.blit(self.fuente_info.render(msg2, True, COLOR_TEXTO), (x_txt, y_txt + 28))

    def ejecutar(self):
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if evento.type == pygame.KEYDOWN:
                    if evento.key in (pygame.K_UP, pygame.K_w):
                        self.mover_jugador("arriba")
                    elif evento.key in (pygame.K_DOWN, pygame.K_s):
                        self.mover_jugador("abajo")
                    elif evento.key in (pygame.K_LEFT, pygame.K_a):
                        self.mover_jugador("izquierda")
                    elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                        self.mover_jugador("derecha")
                    elif evento.key == pygame.K_r:
                        self.iniciar_nivel(self.nivel_actual)
                    elif evento.key == pygame.K_SPACE and self.estado_juego == "NIVEL_SUPERADO":
                        self.iniciar_nivel(self.nivel_actual + 1)
                    elif evento.key == pygame.K_1:
                        self.iniciar_nivel(1)
                    elif evento.key == pygame.K_2:
                        self.iniciar_nivel(2)
                    elif evento.key == pygame.K_3:
                        self.iniciar_nivel(3)

            self.dibujar_tablero()
            self.dibujar_panel()
            pygame.display.flip()
            self.reloj.tick(30)


if __name__ == "__main__":
    JuegoEscapeLaberinto().ejecutar()