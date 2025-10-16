import math


def offset_perpendicular(x1, y1, x2, y2, distancia):
    dx, dy = x2 - x1, y2 - y1
    long_v = math.hypot(dx, dy) or 1.0
    px, py = -dy / long_v, dx / long_v
    return px * distancia, py * distancia


def bezier_q_punto_y_tangente(p0, c, p2, t):
    (x0, y0), (xc, yc), (x2, y2) = p0, c, p2
    x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * xc + t ** 2 * x2
    y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * yc + t ** 2 * y2
    dx = 2 * (1 - t) * (xc - x0) + 2 * t * (x2 - xc)
    dy = 2 * (1 - t) * (yc - y0) + 2 * t * (y2 - yc)
    return x, y, dx, dy
