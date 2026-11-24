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

Los algoritmos están en agentes_ia.py; aquí sólo se adaptan a la interfaz.
"""

from agentes_ia import decision_alfa_beta_lim, obtener_movimiento_astar, obtener_movimiento_logico


def agente_a_estrella(nivel, pos_agente, pos_jugador, memoria):
    # Nivel 1: A* (costo unitario, heurística Manhattan); sólo el primer paso.
    _, nueva_pos, _ = obtener_movimiento_astar(pos_agente, pos_jugador, nivel.muros)
    return nueva_pos


def agente_alfa_beta(nivel, pos_agente, pos_jugador, memoria):
    # Nivel 2: minimax con poda alfa-beta, profundidad 4 movimientos individuales.
    _, nueva_pos = decision_alfa_beta_lim(pos_agente, pos_jugador, nivel.muros, nivel.salida, profundidad=4)
    return nueva_pos


def agente_logico(nivel, pos_agente, pos_jugador, memoria):
    # Nivel 3: patrullaje + inferencia con lógica proposicional.
    indice = memoria.get("indice_patrulla", 0)
    _, nueva_pos, indice, _ = obtener_movimiento_logico(pos_agente, pos_jugador, nivel.muros, indice)
    memoria["indice_patrulla"] = indice
    return nueva_pos


AGENTES = {1: agente_a_estrella, 2: agente_alfa_beta, 3: agente_logico}


def mover_agente(nivel, pos_agente, pos_jugador, memoria):
    return AGENTES[nivel.numero](nivel, pos_agente, pos_jugador, memoria)
