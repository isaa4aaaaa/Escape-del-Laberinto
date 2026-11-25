# Escape del Laberinto

Videojuego por turnos en Python y PyGame en el que un jugador humano debe atravesar tres laberintos de `10 × 10` celdas desde `(1, 1)` hasta la salida `(10, 10)` evitando ser capturado por un agente inteligente distinto en cada cámara.

## Agentes implementados

1. **Cámara I — Búsqueda A\*** ([juego/agentes.py](juego/agentes.py)): recalcula la ruta óptima en cada turno con costo unitario y heurística de distancia Manhattan, ejecutando únicamente el primer paso.
2. **Cámara II — Minimax con poda alfa-beta** ([juego/agentes.py](juego/agentes.py)): búsqueda adversarial con el guardián como `MAX` y el jugador como `MIN`, profundidad máxima de 4 movimientos individuales y desempate por profundidad en estados terminales.
3. **Cámara III — Agente basado en conocimiento** ([juego/agentes.py](juego/agentes.py)): base de conocimiento en lógica proposicional evaluada por tablas de verdad que infiere tanto la acción de captura (`BC |= A_<dir>`) cuando el jugador entra en una de las 4 celdas adyacentes como la acción de patrullaje (`BC |= A_patrullar`).

> **Nota sobre la paridad en el Nivel 3:** para resolver la invariante de paridad entre `P=(1, 1)` (par) y `G=(8, 9)` (impar) bajo movimientos estrictos de 1 celda por turno —que impedía que ambos coincidieran a distancia Manhattan `1` en el turno del agente—, el guardián patrulla las mismas 4 celdas `{(8,9), (9,9), (9,8), (8,8)}` iniciando en `(9, 9)` en sentido antihorario (`(9,9) → (8,9) → (8,8) → (9,8) → (9,9)`). Esto habilita las capturas reales por adyacencia manteniendo el nivel resoluble.

## Requisitos e instalación

```bash
pip install -r requirements.txt
```

## Ejecución

Iniciar el videojuego:

```bash
python main.py
```

(También puede ejecutarse directamente con `python juego/interfaz.py`.)

Ejecutar las pruebas automatizadas de los tres niveles y agentes:

```bash
python test_niveles.py
```

## Controles

- **Flechas** o **WASD**: moverse 1 celda por turno
- **`1`, `2`, `3`** (o clic en las tablillas del panel lateral): cambiar de cámara
- **`U`**: deshacer última jugada
- **`R`**: reiniciar cámara actual
- **`Enter`** / **`Espacio`**: continuar a la siguiente cámara o reintentar
- **`F11`** (o `Alt + Enter`): pantalla completa
- **`Esc`**: salir de pantalla completa / cerrar el juego
