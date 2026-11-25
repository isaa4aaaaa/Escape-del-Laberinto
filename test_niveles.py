"""Pruebas automatizadas de los tres niveles, agentes integrados y reglas de la pauta."""

from collections import deque
from copy import deepcopy

from juego.agentes import (
    decision_alfa_beta_lim,
    eval_estado,
    mover_agente,
    obtener_movimiento_astar,
    obtener_movimiento_logico,
)
from juego.niveles import PATRULLA_NIVEL_3, Nivel


def probar_nivel_1():
    print("=== PRUEBA NIVEL 1: BUSQUEDA A* ===")
    nivel = Nivel(1)
    pos_p = (1, 2)
    pos_g = nivel.inicio_agente
    accion, nueva_pos, ruta = obtener_movimiento_astar(pos_g, pos_p, nivel.muros)
    print(f"Posicion inicial G: {pos_g} -> Objetivo P: {pos_p}")
    print(f"Primer movimiento elegido por A*: {accion} -> Nueva pos G: {nueva_pos}")
    print(f"Longitud de la ruta optima calculada: {len(ruta)}")
    assert accion is not None, "Error: A* no encontro camino"
    assert nueva_pos in nivel.vecinos(pos_g), "Error: movimiento invalido en A*"

    memoria = {}
    pos_integrada = mover_agente(nivel, pos_g, pos_p, memoria)
    assert pos_integrada == nueva_pos
    assert "ultima_accion" in memoria and accion in memoria["ultima_accion"]
    print("Nivel 1 OK!\n")


def probar_nivel_2():
    print("=== PRUEBA NIVEL 2: MINIMAX CON PODA ALFA-BETA (Profundidad 4) ===")
    nivel = Nivel(2)
    pos_p = (2, 1)
    pos_g = nivel.inicio_agente
    accion, nueva_pos = decision_alfa_beta_lim(
        pos_g, pos_p, nivel.muros, nivel.salida, profundidad=4
    )
    print(f"Posicion G: {pos_g} | Posicion P: {pos_p}")
    print(f"Accion seleccionada por Alfa-Beta (prof=4): {accion} -> Nueva pos G: {nueva_pos}")
    assert accion is not None, "Error: Alfa-Beta no devolvio accion"
    assert nueva_pos in nivel.vecinos(pos_g), "Error: movimiento invalido en Alfa-Beta"

    # Verificar que captura inmediata tiene mayor puntaje que captura tardia
    est_captura = {
        "pos_g": (5, 5),
        "pos_p": (5, 5),
        "jugador": "MIN",
        "muros": nivel.muros,
        "salida": nivel.salida,
    }
    assert eval_estado(est_captura, profundidad=3) > eval_estado(est_captura, profundidad=1)

    # Verificar que elige captura inmediata cuando el jugador esta adyacente
    acc_cap, pos_cap = decision_alfa_beta_lim(
        (5, 5), (5, 6), nivel.muros, nivel.salida, profundidad=4
    )
    assert acc_cap == "arriba" and pos_cap == (5, 6)

    memoria = {}
    pos_integrada = mover_agente(nivel, pos_g, pos_p, memoria)
    assert pos_integrada == nueva_pos
    assert "ultima_accion" in memoria and accion in memoria["ultima_accion"]
    print("Nivel 2 OK!\n")


def probar_nivel_3():
    print("=== PRUEBA NIVEL 3: AGENTE BASADO EN CONOCIMIENTO ===")
    nivel = Nivel(3)
    pos_g = nivel.inicio_agente
    assert pos_g == PATRULLA_NIVEL_3[0] == (9, 9), "El guardian debe iniciar en (9, 9)"
    # Misma paridad inicial que P=(1,1) => paridad opuesta en el turno del agente
    assert sum(nivel.inicio_jugador) % 2 == sum(nivel.inicio_agente) % 2
    memoria = {}

    # Caso A: Jugador lejos -> inferencia BC |= A_patrullar y ciclo completo
    esperados = PATRULLA_NIVEL_3[1:] + [PATRULLA_NIVEL_3[0]]
    for esperado in esperados:
        siguiente = mover_agente(nivel, pos_g, (1, 2), memoria)
        print(f"  Patrullaje: {pos_g} -> {siguiente} | {memoria['ultima_accion']}")
        assert siguiente in nivel.vecinos(pos_g), "Movimiento de patrulla invalido"
        assert siguiente == esperado, f"Se esperaba {esperado}, se obtuvo {siguiente}"
        assert memoria["deteccion_logica"] is False
        assert "BC |= A_patrullar" in memoria["ultima_accion"]
        pos_g = siguiente

    # Caso B: Guardar copia de memoria (como hace Deshacer) y probar deteccion adyacente
    memoria_previa = deepcopy(memoria)
    assert pos_g == (9, 9)

    accion, nueva_pos, _, detectado = obtener_movimiento_logico(
        pos_g, (10, 9), nivel.muros, memoria["indice_patrulla"]
    )
    print(f"  Deteccion adyacente en (10,9): detectado={detectado}, accion={accion}, nueva_pos={nueva_pos}")
    assert detectado is True and nueva_pos == (10, 9) and accion == "derecha"

    pos_captura = mover_agente(nivel, pos_g, (10, 9), memoria)
    assert pos_captura == (10, 9)
    assert memoria["deteccion_logica"] is True
    assert "BC |= A_derecha" in memoria["ultima_accion"]
    assert memoria_previa["indice_patrulla"] == 0

    # Caso C: Comprobar por BFS que el nivel 3 sigue siendo resoluble con este patrullaje
    q = deque([(nivel.inicio_jugador, 0)])
    visit = {(nivel.inicio_jugador, 0)}
    resoluble = False
    while q and not resoluble:
        p, idx = q.popleft()
        g = PATRULLA_NIVEL_3[idx]
        for np in nivel.vecinos(p):
            if np == g:
                continue
            if np == nivel.salida:
                resoluble = True
                break
            if abs(np[0] - g[0]) + abs(np[1] - g[1]) == 1:
                continue
            nidx = (idx + 1) % len(PATRULLA_NIVEL_3)
            if np == PATRULLA_NIVEL_3[nidx]:
                continue
            if (np, nidx) not in visit:
                visit.add((np, nidx))
                q.append((np, nidx))
    assert resoluble, "Error: el nivel 3 no seria resoluble con la ruta actual"
    print("  Verificacion BFS: nivel 3 resoluble y con capturas activas!")
    print("Nivel 3 OK!\n")


if __name__ == "__main__":
    probar_nivel_1()
    probar_nivel_2()
    probar_nivel_3()
    print("TODAS LAS PRUEBAS PASARON CORRECTAMENTE.")
