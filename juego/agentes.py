"""Agentes perseguidores del proyecto Escape del Laberinto.

Implementaciones integradas para los tres niveles:
- Nivel 1: Búsqueda A* con costo unitario y heurística Manhattan.
- Nivel 2: Minimax con poda alfa-beta (profundidad máxima de 4 movimientos individuales).
- Nivel 3: Agente basado en conocimiento (lógica proposicional + patrullaje cíclico).

La interfaz llama a `mover_agente(nivel, pos_agente, pos_jugador, memoria)`
después de cada movimiento del jugador. Cada agente devuelve la nueva posición
`(x, y)` (una celda vecina libre o la misma posición si decide quedarse) y
actualiza `memoria` con su estado interno y su última acción para la interfaz.
"""

import heapq

try:
    from juego.niveles import MOVIMIENTOS, PATRULLA_NIVEL_3, TAM
except ImportError:
    from niveles import MOVIMIENTOS, PATRULLA_NIVEL_3, TAM

ORDEN_DIRECCIONES = ("izquierda", "abajo", "arriba", "derecha")
ACCIONES = {d: MOVIMIENTOS[d] for d in ORDEN_DIRECCIONES}


# ---------------------------------------------------------
# NIVEL 1: Búsqueda A* (Adaptado de Actividad 3 y 4)
# ---------------------------------------------------------

def hacer_nodo(estado, padre, accion, costo_camino, profundidad):
    return {
        "estado": estado,
        "padre": padre,
        "accion": accion,
        "costo_camino": costo_camino,
        "profundidad": profundidad,
    }


def expandir(nodo, problema):
    sucesores = []
    for accion, estado in problema["funcion_sucesora"](nodo["estado"]):
        nuevo_nodo = hacer_nodo(
            estado,
            nodo,
            accion,
            nodo["costo_camino"]
            + problema["costo_accion"](nodo["estado"], accion, estado),
            nodo["profundidad"] + 1,
        )
        sucesores.append(nuevo_nodo)
    return sucesores


def solucion(nodo):
    camino = []
    while nodo["padre"] is not None:
        camino.append((nodo["padre"]["estado"], nodo["accion"]))
        nodo = nodo["padre"]
    camino.reverse()
    return camino


class FronteraPrioridad:
    def __init__(self, f):
        self.f = f
        self.heap = []
        self.contador = 0

    def pendientes(self):
        return len(self.heap)

    def get(self):
        _, _, nodo = heapq.heappop(self.heap)
        return nodo

    def put(self, nodos):
        for nodo in nodos:
            prioridad = self.f(nodo)
            heapq.heappush(self.heap, (prioridad, self.contador, nodo))
            self.contador += 1


def busqueda_grafo(problema, frontera):
    cerrado = set()
    frontera.put([hacer_nodo(problema["estado_inicial"], None, None, 0, 0)])

    while frontera.pendientes():
        nodo = frontera.get()

        if problema["test_objetivo"](nodo["estado"]):
            return solucion(nodo)

        if nodo["estado"] not in cerrado:
            cerrado.add(nodo["estado"])
            frontera.put(expandir(nodo, problema))

    return None


def costo_accion(estado, accion, estado_sucesor):
    return 1


def obtener_movimiento_astar(pos_agente, pos_jugador, muros):
    """Calcula la ruta óptima con A* (Manhattan) y devuelve el primer paso."""
    def sucesor_obstaculos(estado):
        x, y = estado
        sucesores = []
        for accion, (dx, dy) in ACCIONES.items():
            nx, ny = x + dx, y + dy
            if 1 <= nx <= TAM and 1 <= ny <= TAM and (nx, ny) not in muros:
                sucesores.append((accion, (nx, ny)))
        return sucesores

    def test_objetivo(estado):
        return estado == pos_jugador

    problema = {
        "estado_inicial": pos_agente,
        "estado_objetivo": pos_jugador,
        "funcion_sucesora": sucesor_obstaculos,
        "test_objetivo": test_objetivo,
        "costo_accion": costo_accion,
    }

    def h(nodo):
        x, y = nodo["estado"]
        x_g, y_g = pos_jugador
        return abs(x - x_g) + abs(y - y_g)

    def f_astar(nodo):
        return nodo["costo_camino"] + h(nodo)

    frontera = FronteraPrioridad(f_astar)
    sol = busqueda_grafo(problema, frontera)

    # El agente ejecuta únicamente el primer movimiento de la ruta calculada
    if sol:
        primera_accion = sol[0][1]
        dx, dy = ACCIONES[primera_accion]
        nueva_pos = (pos_agente[0] + dx, pos_agente[1] + dy)
        return primera_accion, nueva_pos, sol

    return None, pos_agente, []


# ---------------------------------------------------------
# NIVEL 2: Minimax con Poda Alfa-Beta (Adaptado de Actividad 5)
# ---------------------------------------------------------

def test_terminal(estado):
    if estado["pos_g"] == estado["pos_p"]:
        return True
    if estado["pos_p"] == estado["salida"]:
        return True
    return False


def utilidad(estado):
    if estado["pos_g"] == estado["pos_p"]:
        return 1
    if estado["pos_p"] == estado["salida"]:
        return -1
    return 0


def eval_estado(estado, profundidad=0):
    if test_terminal(estado):
        u = utilidad(estado)
        # Ponderar por profundidad restante: preferir capturas mas rapidas y retrasar escapes
        if u > 0:
            return 100 + profundidad
        if u < 0:
            return -100 - profundidad
        return 0

    gx, gy = estado["pos_g"]
    px, py = estado["pos_p"]
    sx, sy = estado["salida"]

    dist_captura = abs(gx - px) + abs(gy - py)
    dist_escape = abs(px - sx) + abs(py - sy)

    # Positivo favorece a MAX (acercarse a P), negativo favorece a MIN (P cerca de la salida)
    return (dist_escape * 2) - (dist_captura * 3)


def movimientos_validos(posicion, muros):
    x, y = posicion
    validos = []
    for accion, (dx, dy) in ACCIONES.items():
        nx, ny = x + dx, y + dy
        if 1 <= nx <= TAM and 1 <= ny <= TAM and (nx, ny) not in muros:
            validos.append((accion, (nx, ny)))
    return validos


def sucesores(estado):
    if test_terminal(estado):
        return []

    jugador = estado["jugador"]
    muros = estado["muros"]
    lista = []

    if jugador == "MAX":
        for accion, nueva_pos in movimientos_validos(estado["pos_g"], muros):
            lista.append(
                (
                    accion,
                    {
                        "pos_g": nueva_pos,
                        "pos_p": estado["pos_p"],
                        "jugador": "MIN",
                        "muros": muros,
                        "salida": estado["salida"],
                    },
                )
            )
    else:
        for accion, nueva_pos in movimientos_validos(estado["pos_p"], muros):
            lista.append(
                (
                    accion,
                    {
                        "pos_g": estado["pos_g"],
                        "pos_p": nueva_pos,
                        "jugador": "MAX",
                        "muros": muros,
                        "salida": estado["salida"],
                    },
                )
            )

    return lista


def max_valor_ab_lim(estado, alfa, beta, profundidad):
    if test_terminal(estado) or profundidad == 0:
        return eval_estado(estado, profundidad)

    v = -float("inf")
    for _, s in sucesores(estado):
        v = max(v, min_valor_ab_lim(s, alfa, beta, profundidad - 1))
        if v >= beta:
            return v
        alfa = max(alfa, v)
    return v


def min_valor_ab_lim(estado, alfa, beta, profundidad):
    if test_terminal(estado) or profundidad == 0:
        return eval_estado(estado, profundidad)

    v = float("inf")
    for _, s in sucesores(estado):
        v = min(v, max_valor_ab_lim(s, alfa, beta, profundidad - 1))
        if v <= alfa:
            return v
        beta = min(beta, v)
    return v


def decision_alfa_beta_lim(pos_agente, pos_jugador, muros, salida, profundidad=4):
    """Elige el mejor movimiento para MAX con poda alfa-beta limitada por profundidad."""
    estado = {
        "pos_g": pos_agente,
        "pos_p": pos_jugador,
        "jugador": "MAX",
        "muros": muros,
        "salida": salida,
    }

    mejor_valor = -float("inf")
    mejor_accion = None
    mejor_pos = pos_agente

    alfa = -float("inf")
    beta = float("inf")

    for accion, s in sucesores(estado):
        v = min_valor_ab_lim(s, alfa, beta, profundidad - 1)
        if v > mejor_valor:
            mejor_valor = v
            mejor_accion = accion
            mejor_pos = s["pos_g"]
        alfa = max(alfa, mejor_valor)

    return mejor_accion, mejor_pos


# ---------------------------------------------------------
# NIVEL 3: Agente Basado en Conocimiento (Lógica Proposicional)
# ---------------------------------------------------------

def decir(bc, sentencia):
    return lambda m: bc(m) and sentencia(m)


def extender(p, valor, modelo):
    nuevo_modelo = modelo.copy()
    nuevo_modelo[p] = valor
    return nuevo_modelo


def comprobar_tv(bc, alfa, simbolos, modelo):
    if not simbolos:
        if bc(modelo):
            return alfa(modelo)
        return True

    p = simbolos[0]
    resto = simbolos[1:]
    return comprobar_tv(bc, alfa, resto, extender(p, True, modelo)) and comprobar_tv(
        bc, alfa, resto, extender(p, False, modelo)
    )


def obtener_movimiento_logico(pos_agente, pos_jugador, muros, indice_patrulla):
    """Infiere captura (BC |= A_<dir>) o patrullaje (BC |= A_patrullar) con tablas de verdad."""
    bc = lambda m: True
    simbolos = []
    gx, gy = pos_agente

    # 1. Incorporar reglas de inferencia y percepciones en las 4 celdas adyacentes
    for d in ORDEN_DIRECCIONES:
        dx, dy = ACCIONES[d]
        nx, ny = gx + dx, gy + dy

        simbolo_p = f"P_{d}"
        simbolo_a = f"A_{d}"
        simbolos.extend([simbolo_p, simbolo_a])

        # Regla en la BC: P_<dir> <-> A_<dir>
        bc = decir(bc, lambda m, sp=simbolo_p, sa=simbolo_a: m[sp] == m[sa])

        # Percepción actual en esa celda adyacente
        jugador_detectado = (
            1 <= nx <= TAM
            and 1 <= ny <= TAM
            and (nx, ny) == pos_jugador
            and (nx, ny) not in muros
        )

        if jugador_detectado:
            bc = decir(bc, lambda m, sp=simbolo_p: m[sp])
        else:
            bc = decir(bc, lambda m, sp=simbolo_p: not m[sp])

    # Regla en la BC: (~P_izquierda & ~P_abajo & ~P_arriba & ~P_derecha) <-> A_patrullar
    simbolos.append("A_patrullar")
    bc = decir(
        bc,
        lambda m: (
            not m["P_izquierda"]
            and not m["P_abajo"]
            and not m["P_arriba"]
            and not m["P_derecha"]
        )
        == m["A_patrullar"],
    )

    # 2. Comprobar por tablas de verdad si BC implica alguna acción de captura
    accion_inferida = None
    for d in ORDEN_DIRECCIONES:
        alfa = lambda m, sa=f"A_{d}": m[sa]
        if comprobar_tv(bc, alfa, simbolos, {}):
            accion_inferida = d
            break

    if accion_inferida is not None:
        dx, dy = ACCIONES[accion_inferida]
        nueva_pos = (gx + dx, gy + dy)
        return accion_inferida, nueva_pos, indice_patrulla, True

    # 3. Comprobar por tablas de verdad si BC implica continuar patrullaje (BC |= A_patrullar)
    if comprobar_tv(bc, lambda m: m["A_patrullar"], simbolos, {}):
        siguiente_idx = (indice_patrulla + 1) % len(PATRULLA_NIVEL_3)
        nueva_pos = PATRULLA_NIVEL_3[siguiente_idx]

        dx = nueva_pos[0] - gx
        dy = nueva_pos[1] - gy
        accion_patrulla = "patrulla"
        for nombre, (ax, ay) in ACCIONES.items():
            if (ax, ay) == (dx, dy):
                accion_patrulla = nombre
                break

        return accion_patrulla, nueva_pos, siguiente_idx, False

    return None, pos_agente, indice_patrulla, False


# ---------------------------------------------------------
# Adaptadores para la interfaz gráfica (juego/interfaz.py)
# ---------------------------------------------------------

def agente_a_estrella(nivel, pos_agente, pos_jugador, memoria):
    accion, nueva_pos, camino = obtener_movimiento_astar(
        pos_agente, pos_jugador, nivel.muros
    )
    memoria["ruta_astar"] = [estado for estado, _ in camino]
    memoria["ultima_accion"] = f"A*: {accion}" if accion else "A*: sin ruta"
    return nueva_pos


def agente_alfa_beta(nivel, pos_agente, pos_jugador, memoria):
    accion, nueva_pos = decision_alfa_beta_lim(
        pos_agente, pos_jugador, nivel.muros, nivel.salida, profundidad=4
    )
    memoria["ultima_accion"] = f"Alfa-Beta: {accion}" if accion else "Alfa-Beta: quieto"
    return nueva_pos


def agente_logico(nivel, pos_agente, pos_jugador, memoria):
    indice = memoria.get("indice_patrulla", 0)
    accion, nueva_pos, nuevo_idx, detectado = obtener_movimiento_logico(
        pos_agente, pos_jugador, nivel.muros, indice
    )
    memoria["indice_patrulla"] = nuevo_idx
    memoria["deteccion_logica"] = detectado
    if detectado:
        memoria["ultima_accion"] = f"BC |= A_{accion} (captura)"
    else:
        memoria["ultima_accion"] = f"BC |= A_patrullar ({accion})"
    return nueva_pos


AGENTES = {1: agente_a_estrella, 2: agente_alfa_beta, 3: agente_logico}


def mover_agente(nivel, pos_agente, pos_jugador, memoria):
    return AGENTES[nivel.numero](nivel, pos_agente, pos_jugador, memoria)
