"""Agentes perseguidores: AQUÍ VAN SUS IMPLEMENTACIONES.

La interfaz llama a `mover_agente` después de cada movimiento del jugador.
Debe devolver la nueva posición (x, y) del agente: una celda vecina libre
(nivel.vecinos(pos_agente)) o la misma posición si decide quedarse.

Parámetros disponibles:
    nivel        -> objeto Nivel (niveles.py): .muros, .salida, .libre(p), .vecinos(p)
    pos_agente   -> (x, y) actual del agente
    pos_jugador  -> (x, y) actual del jugador
    memoria      -> dict persistente durante el nivel (p. ej. índice de patrullaje
                    del nivel 3). La interfaz lo copia para poder deshacer jugadas.

Mientras no estén implementados, los agentes se quedan quietos.
"""


def agente_a_estrella(nivel, pos_agente, pos_jugador, memoria):
    # TODO Nivel 1: A* con costo unitario y heurística Manhattan.
    #      Ejecutar sólo el primer paso de la ruta calculada.
    return pos_agente


def agente_alfa_beta(nivel, pos_agente, pos_jugador, memoria):
    # TODO Nivel 2: minimax con poda alfa-beta, agente = MAX, jugador = MIN,
    #      profundidad máxima de 4 movimientos individuales.
    return pos_agente


def agente_logico(nivel, pos_agente, pos_jugador, memoria):
    # TODO Nivel 3: patrullar niveles.PATRULLA_NIVEL_3; si el jugador está
    #      en una celda adyacente, inferir el movimiento de captura con la
    #      base de conocimiento (lógica proposicional).
    return pos_agente


AGENTES = {1: agente_a_estrella, 2: agente_alfa_beta, 3: agente_logico}


def mover_agente(nivel, pos_agente, pos_jugador, memoria):
    return AGENTES[nivel.numero](nivel, pos_agente, pos_jugador, memoria)
