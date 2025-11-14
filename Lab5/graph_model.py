import heapq
import math

def validar_grafo_dirigido(matriz):
    n = len(matriz)
    for i in range(n):
        for j in range(i+1, n):
            a = matriz[i][j]
            b = matriz[j][i]
            if a != 0 and b != 0 and abs(a - b) < 1e-12:
                return (i, j)
    return None

def construir_adyacencias(matriz, dirigido):
    n = len(matriz)
    ady = [[] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            peso = matriz[i][j]
            if peso != 0:
                ady[i].append((j, peso))
    return ady

def dijkstra(adyacencias, indice_origen, indice_destino):
    n = len(adyacencias)
    dist = [float("inf")] * n
    previo = [-1] * n
    dist[indice_origen] = 0.0

    pq = [(0.0, indice_origen)]
    visitado = [False] * n

    while pq:
        d_actual, u = heapq.heappop(pq)
        if visitado[u]:
            continue
        visitado[u] = True
        if u == indice_destino:
            break
        for v, peso in adyacencias[u]:
            if peso < 0:
                # Dijkstra no admite pesos negativos.
                return float("inf"), [], True
            if dist[u] + peso < dist[v]:
                dist[v] = dist[u] + peso
                previo[v] = u
                heapq.heappush(pq, (dist[v], v))

    if dist[indice_destino] == float("inf"):
        return float("inf"), [], False

    camino = []
    nodo = indice_destino
    while nodo != -1:
        camino.append(nodo)
        nodo = previo[nodo]
    camino.reverse()
    return dist[indice_destino], camino, False

def bellman_ford(adyacencias, indice_origen):
    n = len(adyacencias)
    dist = [float("inf")] * n
    previo = [-1] * n
    dist[indice_origen] = 0

    for _ in range(n - 1):
        cambiado = False
        for u in range(n):
            for v, peso in adyacencias[u]:
                if dist[u] != float("inf") and dist[u] + peso < dist[v]:
                    dist[v] = dist[u] + peso
                    previo[v] = u
                    cambiado = True
        if not cambiado:
            break

    for u in range(n):
        for v, peso in adyacencias[u]:
            if dist[u] != float("inf") and dist[u] + peso < dist[v]:
                return None, None, True

    return dist, previo, False
