"""Escenarios del proyecto (anexo del enunciado).

Coordenadas: (x, y) con (1, 1) en la esquina inferior izquierda y (10, 10)
en la superior derecha. La primera fila de texto corresponde a y = 10.
"""

TAM = 10

MAPAS = {
    1: [
        "....#..G.E",
        ".....#....",
        "..#.......",
        "......#...",
        "...#......",
        ".....##...",
        "..##......",
        "......#...",
        "...#..#...",
        "P..#......",
    ],
    2: [
        "......G..E",
        ".##...#...",
        "...#..#...",
        ".#.#......",
        ".#...##...",
        "...#......",
        "##.#.###..",
        "...#......",
        ".##..#..#.",
        "P....#....",
    ],
    3: [
        "......#..E",
        "......#G..",
        "....#.....",
        "......#...",
        "...#......",
        ".....#....",
        ".##..#....",
        ".....#....",
        "..##......",
        "P.........",
    ],
}

NOMBRES = {1: "Búsqueda A*", 2: "Minimax alfa-beta", 3: "Agente lógico"}

PATRULLA_NIVEL_3 = [(8, 9), (9, 9), (9, 8), (8, 8)]

MOVIMIENTOS = {"arriba": (0, 1), "abajo": (0, -1), "izquierda": (-1, 0), "derecha": (1, 0)}


class Nivel:
    def __init__(self, numero):
        self.numero = numero
        self.nombre = NOMBRES[numero]
        self.muros = set()
        for fila, linea in enumerate(MAPAS[numero]):
            y = TAM - fila
            for col, c in enumerate(linea):
                x = col + 1
                if c == "#":
                    self.muros.add((x, y))
                elif c == "P":
                    self.inicio_jugador = (x, y)
                elif c == "G":
                    self.inicio_agente = (x, y)
                elif c == "E":
                    self.salida = (x, y)

    def libre(self, pos):
        x, y = pos
        return 1 <= x <= TAM and 1 <= y <= TAM and pos not in self.muros

    def vecinos(self, pos):
        """Celdas libres alcanzables en un movimiento (arriba, abajo, izq., der.)."""
        x, y = pos
        return [(x + dx, y + dy) for dx, dy in MOVIMIENTOS.values() if self.libre((x + dx, y + dy))]
