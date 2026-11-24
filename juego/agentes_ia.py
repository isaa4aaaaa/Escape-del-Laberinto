# agentes_ia.py
import heapq
from niveles import TAM as N, PATRULLA_NIVEL_3 as RUTA_PATRULLAJE_N3

# Mismo orden que en la versión original (afecta el desempate entre rutas iguales)
acciones = {"izquierda": (-1, 0), "abajo": (0, -1), "arriba": (0, 1), "derecha": (1, 0)}

# ---------------------------------------------------------
# NIVEL 1: Busqueda A* (Adaptado de Actividad 3 y 4)
# ---------------------------------------------------------

def hacer_nodo(estado, padre, accion, costo_camino, profundidad):
    return {
        "estado": estado,
        "padre": padre,
        "accion": accion,
        "costo_camino": costo_camino,
        "profundidad": profundidad
    }

def expandir(nodo, problema):
    sucesores = []

    for accion, estado in problema["funcion_sucesora"](nodo["estado"]):
        nuevo_nodo = hacer_nodo(
            estado,
            nodo,
            accion,
            nodo["costo_camino"] + problema["costo_accion"](
                nodo["estado"],
                accion,
                estado
            ),
            nodo["profundidad"] + 1
        )
        sucesores.append(nuevo_nodo)

    return sucesores

def solucion(nodo):
    camino = []

    while nodo["padre"] is not None:
        camino.append(
            (nodo["padre"]["estado"], nodo["accion"])
        )
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
        prioridad, _, nodo = heapq.heappop(self.heap)
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
            sucesores = expandir(nodo, problema)
            frontera.put(sucesores)

    return None

def costo_accion(estado, accion, estado_sucesor):
    return 1

def obtener_movimiento_astar(pos_agente, pos_jugador, muros):
    # Definicion de funciones del problema con obstaculos (Reto Actividad 4)
    def sucesor_obstaculos(estado):
        x, y = estado
        sucesores = []
        for accion, (dx, dy) in acciones.items():
            nx, ny = x + dx, y + dy
            if 1 <= nx <= N and 1 <= ny <= N:
                if (nx, ny) not in muros:
                    sucesores.append((accion, (nx, ny)))
        return sucesores

    def test_objetivo(estado):
        return estado == pos_jugador

    problema = {
        "estado_inicial": pos_agente,
        "estado_objetivo": pos_jugador,
        "funcion_sucesora": sucesor_obstaculos,
        "test_objetivo": test_objetivo,
        "costo_accion": costo_accion
    }

    # Heuristica distancia Manhattan
    def h(nodo):
        x, y = nodo["estado"]
        x_G, y_G = pos_jugador
        return abs(x - x_G) + abs(y - y_G)

    # Funcion de evaluacion A*: f(n) = g(n) + h(n)
    def f_astar(nodo):
        return nodo["costo_camino"] + h(nodo)

    f = FronteraPrioridad(f_astar)
    sol = busqueda_grafo(problema, f)

    # El agente ejecuta unicamente el primer movimiento de la ruta calculada
    if sol is not None and len(sol) > 0:
        primera_accion = sol[0][1]
        dx, dy = acciones[primera_accion]
        nueva_pos = (pos_agente[0] + dx, pos_agente[1] + dy)
        return primera_accion, nueva_pos, sol

    return None, pos_agente, []


# ---------------------------------------------------------
# NIVEL 2: Minimax con Poda Alfa-Beta (Adaptado de Actividad 5)
# ---------------------------------------------------------

def test_terminal(estado):
    # Termina si el agente captura al jugador o el jugador llega a la salida
    if estado["pos_g"] == estado["pos_p"]:
        return True
    if estado["pos_p"] == estado["salida"]:
        return True
    return False

def utilidad(estado):
    if estado["pos_g"] == estado["pos_p"]:
        return 1
    elif estado["pos_p"] == estado["salida"]:
        return -1
    else:
        return 0

def eval_estado(estado):
    # Evaluacion de estados terminales
    if test_terminal(estado):
        return 100 * utilidad(estado)

    gx, gy = estado["pos_g"]
    px, py = estado["pos_p"]
    sx, sy = estado["salida"]

    dist_captura = abs(gx - px) + abs(gy - py)
    dist_escape = abs(px - sx) + abs(py - sy)

    # Positivo favorece a MAX (acercarse a P), negativo favorece a MIN (P cerca de salida)
    valor = (dist_escape * 2) - (dist_captura * 3)
    return valor

def movimientos_validos(posicion, muros):
    x, y = posicion
    validos = []
    for accion, (dx, dy) in acciones.items():
        nx, ny = x + dx, y + dy
        if 1 <= nx <= N and 1 <= ny <= N:
            if (nx, ny) not in muros:
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
            nuevo_estado = {
                "pos_g": nueva_pos,
                "pos_p": estado["pos_p"],
                "jugador": "MIN",
                "muros": muros,
                "salida": estado["salida"]
            }
            lista.append((accion, nuevo_estado))
    else:
        for accion, nueva_pos in movimientos_validos(estado["pos_p"], muros):
            nuevo_estado = {
                "pos_g": estado["pos_g"],
                "pos_p": nueva_pos,
                "jugador": "MAX",
                "muros": muros,
                "salida": estado["salida"]
            }
            lista.append((accion, nuevo_estado))

    return lista

def max_valor_ab_lim(estado, alfa, beta, profundidad):
    if test_terminal(estado):
        return eval_estado(estado)
    if profundidad == 0:
        return eval_estado(estado)

    v = -float('inf')
    for accion, s in sucesores(estado):
        v = max(v, min_valor_ab_lim(s, alfa, beta, profundidad - 1))
        if v >= beta:
            return v
        alfa = max(alfa, v)
    return v

def min_valor_ab_lim(estado, alfa, beta, profundidad):
    if test_terminal(estado):
        return eval_estado(estado)
    if profundidad == 0:
        return eval_estado(estado)

    v = float('inf')
    for accion, s in sucesores(estado):
        v = min(v, max_valor_ab_lim(s, alfa, beta, profundidad - 1))
        if v <= alfa:
            return v
        beta = min(beta, v)
    return v

def decision_alfa_beta_lim(pos_agente, pos_jugador, muros, salida, profundidad=4):
    estado = {
        "pos_g": pos_agente,
        "pos_p": pos_jugador,
        "jugador": "MAX",
        "muros": muros,
        "salida": salida
    }

    mejor_valor = -float('inf')
    mejor_accion = None
    mejor_pos = pos_agente

    alfa = -float('inf')
    beta = float('inf')

    for accion, s in sucesores(estado):
        # Evaluar el sucesor considerando que ya se realizo un movimiento
        v = min_valor_ab_lim(s, alfa, beta, profundidad - 1)

        if v > mejor_valor:
            mejor_valor = v
            mejor_accion = accion
            mejor_pos = s["pos_g"]

        alfa = max(alfa, mejor_valor)

    return mejor_accion, mejor_pos


# ---------------------------------------------------------
# NIVEL 3: Agente Basado en Conocimiento (Adaptado de Minas de Moria)
# ---------------------------------------------------------

def decir(BC, sentencia):
    return lambda m: BC(m) and sentencia(m)

def extender(p, valor, modelo):
    nuevo_modelo = modelo.copy()
    nuevo_modelo[p] = valor
    return nuevo_modelo

def comprobar_tv(BC, alfa, simbolos, modelo):
    if len(simbolos) == 0:
        if BC(modelo):
            return alfa(modelo)
        else:
            return True

    P = simbolos[0]
    resto = simbolos[1:]

    return (
        comprobar_tv(BC, alfa, resto, extender(P, True, modelo))
        and
        comprobar_tv(BC, alfa, resto, extender(P, False, modelo))
    )

def obtener_movimiento_logico(pos_agente, pos_jugador, muros, indice_patrulla):
    # Base de conocimiento inicial
    BC = lambda m: True

    direcciones = ["izquierda", "abajo", "arriba", "derecha"]
    simbolos = []

    gx, gy = pos_agente

    # 1. Incorporar reglas de inferencia y percepciones en las 4 celdas adyacentes
    for d in direcciones:
        dx, dy = acciones[d]
        nx, ny = gx + dx, gy + dy

        # Simbolos proposicionales:
        # P_<dir>: Se percibe al jugador en la celda adyacente <dir>
        # A_<dir>: Ejecutar accion de captura hacia <dir>
        simbolo_p = f"P_{d}"
        simbolo_a = f"A_{d}"
        simbolos.extend([simbolo_p, simbolo_a])

        # Regla en la BC: P_<dir> <-> A_<dir>
        BC = decir(BC, lambda m, sp=simbolo_p, sa=simbolo_a: m[sp] == m[sa])

        # Percepcion actual en esa celda adyacente
        jugador_detectado = ((nx, ny) == pos_jugador) and ((nx, ny) not in muros)

        if jugador_detectado:
            BC = decir(BC, lambda m, sp=simbolo_p: m[sp])
        else:
            BC = decir(BC, lambda m, sp=simbolo_p: not m[sp])

    # 2. Comprobar mediante tablas de verdad si BC implica alguna accion de captura (BC |= A_<dir>)
    accion_inferida = None
    for d in direcciones:
        alfa = lambda m, sa=f"A_{d}": m[sa]
        if comprobar_tv(BC, alfa, simbolos, {}):
            accion_inferida = d
            break

    # Si detecta al jugador e infiere la accion de captura, interrumpe el patrullaje
    if accion_inferida is not None:
        dx, dy = acciones[accion_inferida]
        nueva_pos = (gx + dx, gy + dy)
        return accion_inferida, nueva_pos, indice_patrulla, True

    # 3. Cuando no detecte al jugador, continuara su recorrido de patrullaje:
    # (8,9) -> (9,9) -> (9,8) -> (8,8) -> (8,9)
    siguiente_idx = (indice_patrulla + 1) % len(RUTA_PATRULLAJE_N3)
    nueva_pos = RUTA_PATRULLAJE_N3[siguiente_idx]

    dx = nueva_pos[0] - gx
    dy = nueva_pos[1] - gy

    accion_patrulla = "patrulla"
    for nombre, (ax, ay) in acciones.items():
        if (ax, ay) == (dx, dy):
            accion_patrulla = nombre

    return accion_patrulla, nueva_pos, siguiente_idx, False