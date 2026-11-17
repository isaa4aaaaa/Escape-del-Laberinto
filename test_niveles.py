# test_niveles.py
from escenarios import cargar_escenario, RUTA_PATRULLAJE_N3
from agentes_ia import (
    obtener_movimiento_astar,
    decision_alfa_beta_lim,
    obtener_movimiento_logico
)

def probar_nivel_1():
    print("=== PRUEBA NIVEL 1: BUSQUEDA A* ===")
    esc = cargar_escenario(1)
    # Jugador se mueve de (1,1) a (1,2)
    pos_p = (1, 2)
    pos_g = esc["inicio_g"]  # (8, 10)
    accion, nueva_pos, ruta = obtener_movimiento_astar(pos_g, pos_p, esc["muros"])
    print("Posicion inicial G:", pos_g, "-> Objetivo P:", pos_p)
    print("Primer movimiento elegido por A*:", accion, "-> Nueva pos G:", nueva_pos)
    print("Longitud de la ruta optima calculada:", len(ruta))
    assert accion is not None, "Error: A* no encontro camino"
    print("Nivel 1 OK!\n")

def probar_nivel_2():
    print("=== PRUEBA NIVEL 2: MINIMAX CON PODA ALFA-BETA (Profundidad 4) ===")
    esc = cargar_escenario(2)
    pos_p = (2, 1)
    pos_g = esc["inicio_g"]  # (6, 10)
    accion, nueva_pos = decision_alfa_beta_lim(
        pos_g, pos_p, esc["muros"], esc["salida"], profundidad=4
    )
    print("Posicion G:", pos_g, "| Posicion P:", pos_p)
    print("Accion seleccionada por Alfa-Beta (prof=4):", accion, "-> Nueva pos G:", nueva_pos)
    assert accion is not None, "Error: Alfa-Beta no devolvio accion"
    print("Nivel 2 OK!\n")

def probar_nivel_3():
    print("=== PRUEBA NIVEL 3: AGENTE BASADO EN CONOCIMIENTO ===")
    esc = cargar_escenario(3)
    pos_g = RUTA_PATRULLAJE_N3[0]  # (8, 9)
    idx_patrulla = 0

    # Caso A: Jugador lejos en (1, 2) -> El agente debe patrullar a (9, 9)
    accion, nueva_pos, idx_patrulla, detectado = obtener_movimiento_logico(
        pos_g, (1, 2), esc["muros"], idx_patrulla
    )
    print("Caso 1 (Jugador lejos en (1,2)):")
    print("  Detectado:", detectado, "| Accion:", accion, "| Nueva pos G:", nueva_pos)
    assert detectado == False and nueva_pos == (9, 9), "Error en patrullaje"

    # Caso B: Jugador adyacente a (9, 9) en una celda libre, por ejemplo (9, 8) -> Debe inferir 'abajo' y capturar
    pos_g = nueva_pos  # (9, 9)
    pos_p_adyacente = (9, 8)
    accion, nueva_pos, idx_patrulla, detectado = obtener_movimiento_logico(
        pos_g, pos_p_adyacente, esc["muros"], idx_patrulla
    )
    print("Caso 2 (Jugador adyacente en (9,8)):")
    print("  Detectado:", detectado, "| Accion inferida:", accion, "| Nueva pos G:", nueva_pos)
    assert detectado == True and nueva_pos == pos_p_adyacente, "Error en inferencia de captura"
    print("Nivel 3 OK!\n")

if __name__ == "__main__":
    probar_nivel_1()
    probar_nivel_2()
    probar_nivel_3()
    print("TODAS LAS PRUEBAS PASARON CORRECTAMENTE.")