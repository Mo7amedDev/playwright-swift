import math 
def bezier_curve(t, points):
    """Compute the (x, y) position on a Bézier curve at t"""
    n = len(points) - 1  # Fix: The highest index should be n-1
    x = sum(math.comb(n, i) * (1 - t) ** (n - i) * t ** i * points[i][0] for i in range(n + 1))
    y = sum(math.comb(n, i) * (1 - t) ** (n - i) * t ** i * points[i][1] for i in range(n + 1))
    return x, y

 