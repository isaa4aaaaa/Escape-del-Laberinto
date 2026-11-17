# escenarios.py
# Representación de los escenarios 10x10 del Anexo (Semestre 2027-1)
# Convención del curso: (1, 1) es esquina inferior izquierda; (10, 10) es esquina superior derecha.

N = 10

acciones = {
    "izquierda": (-1, 0),
    "abajo": (0, -1),
    "arriba": (0, 1),
    "derecha": (1, 0)
}

MAPAS_ASCII = {
    1: [
        "....#..G.E",
        ".....#..#.",
        ".#........",
        "...#......",
        "..##......",
        "..........",
        "..##......",
        "#.........",
        "...#..#...",
        "P..#......"
    ],
    2: [
        ".....G...E",
        "..##...#..",
        "......#...",
        "...#.#....",
        ".#...##...",
        "...#......",
        ".##..#....",
        "......#...",
        ".##.......",
        "P....#...."
    ],
    3: [
        "#.......#E",  
        "#......G..",  
        "...#..#..#",  
        ".......#.#",  
        ".........#",  
        "........#.",
        "##.#.###..",  
        "...#......",  
        "...#..#...",  
        "P........."   
    ]
}

# Ruta cíclica de patrullaje del Nivel 3 especificada en el Anexo:
# (8,9) -> (9,9) -> (9,8) -> (8,8) -> (8,9)
RUTA_PATRULLAJE_N3 = [(8, 9), (9, 9), (9, 8), (8, 8)]


def cargar_escenario(nivel):
    """
    Convierte el mapa ASCII del nivel (1, 2 o 3) al sistema cartesiano (x, y)
    donde x in [1..10] (izquierda a derecha) e y in [1..10] (abajo hacia arriba).
    """
    filas = MAPAS_ASCII[nivel]
    muros = set()
    inicio_p = (1, 1)
    inicio_g = (8, 10)
    salida = (10, 10)

    for indice_fila, texto_fila in enumerate(filas):
        y = N - indice_fila  # fila 0 de arriba corresponde a y = 10
        for indice_col, celda in enumerate(texto_fila):
            x = indice_col + 1  # col 0 corresponde a x = 1
            if celda == '#':
                muros.add((x, y))
            elif celda == 'P':
                inicio_p = (x, y)
            elif celda == 'G':
                inicio_g = (x, y)
            elif celda == 'E':
                salida = (x, y)

    # En el Nivel 3 el guardián inicia su patrullaje en (8, 9) según el Anexo
    if nivel == 3:
        inicio_g = RUTA_PATRULLAJE_N3[0]
        for celda_patrulla in RUTA_PATRULLAJE_N3:
            muros.discard(celda_patrulla)

    return {
        "nivel": nivel,
        "ancho": N,
        "alto": N,
        "muros": muros,
        "inicio_p": inicio_p,
        "inicio_g": inicio_g,
        "salida": salida
    }


def cartesianas_a_pantalla(x, y):
    """Convierte (x, y) del curso [1..10] a (columna, fila) de Pygame [0..9]."""
    col = x - 1
    fila = N - y
    return col, fila