"""Minimal stroked-path renderer for Lucide icons (ISC licensed SVGs).

Lucide ships each icon as a 24x24 SVG built from a handful of path/line/
circle/polyline primitives with round caps and joins. This parses just
enough of the SVG path grammar (M/L/H/V/C/S/Q/T/A/Z, absolute and relative)
to flatten those icons into polylines pygame can stroke, so icons don't
require a native SVG/cairo dependency.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pygame

ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"
VIEWBOX_SIZE = 24
ARC_STEPS = 16
CURVE_STEPS = 16

_TOKEN_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:e-?\d+)?")

_path_cache: dict[str, tuple[tuple[tuple[float, float], ...], ...]] = {}
_render_cache: dict[tuple[str, int, int, tuple[int, int, int]], pygame.Surface] = {}


def draw_icon(
    surface: pygame.Surface,
    rect: pygame.Rect,
    name: str,
    color: tuple[int, int, int],
    stroke_width: int | None = None,
    alpha: int = 255,
) -> None:
    """Draw a Lucide icon (by file stem, e.g. "x", "chevron-right") into rect."""
    width = max(1, rect.width)
    height = max(1, rect.height)
    line_width = stroke_width or max(1, round(rect.width * 0.09))

    key = (name, width, height, color)
    cached = _render_cache.get(key)
    if cached is None:
        cached = _render_icon(name, width, height, color, line_width)
        _render_cache[key] = cached

    if alpha < 255:
        faded = cached.copy()
        faded.set_alpha(alpha)
        surface.blit(faded, rect.topleft)
    else:
        surface.blit(cached, rect.topleft)


def _render_icon(
    name: str,
    width: int,
    height: int,
    color: tuple[int, int, int],
    line_width: int,
) -> pygame.Surface:
    subpaths = _load_subpaths(name)
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    scale = min(width, height) / VIEWBOX_SIZE

    radius = max(1, line_width // 2)
    for subpath in subpaths:
        points = [(x * scale, y * scale) for x, y in subpath]
        if len(points) < 2:
            continue
        pygame.draw.lines(image, color, False, points, line_width)
        for point in points:
            pygame.draw.circle(image, color, (round(point[0]), round(point[1])), radius)

    return image


def _load_subpaths(name: str) -> tuple[tuple[tuple[float, float], ...], ...]:
    cached = _path_cache.get(name)
    if cached is not None:
        return cached

    svg_text = (ICON_DIR / f"{name}.svg").read_text()
    subpaths: list[tuple[tuple[float, float], ...]] = []
    for path_d in re.findall(r'<path[^>]*\sd="([^"]+)"', svg_text):
        subpaths.extend(_flatten_path(path_d))

    result = tuple(subpaths)
    _path_cache[name] = result
    return result


def _flatten_path(d: str) -> list[tuple[tuple[float, float], ...]]:
    tokens = _TOKEN_RE.findall(d)
    index = 0

    def next_num() -> float:
        nonlocal index
        value = float(tokens[index])
        index += 1
        return value

    subpaths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    start = (0.0, 0.0)
    pos = (0.0, 0.0)
    command = ""

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
        # a bare number continues the previous command (implicit repeat)

        if command in "Mm":
            x, y = next_num(), next_num()
            if command == "m":
                x, y = pos[0] + x, pos[1] + y
            pos = (x, y)
            start = pos
            if current:
                subpaths.append(current)
            current = [pos]
            command = "L" if command == "M" else "l"
        elif command in "Ll":
            x, y = next_num(), next_num()
            if command == "l":
                x, y = pos[0] + x, pos[1] + y
            pos = (x, y)
            current.append(pos)
        elif command in "Hh":
            x = next_num()
            if command == "h":
                x = pos[0] + x
            pos = (x, pos[1])
            current.append(pos)
        elif command in "Vv":
            y = next_num()
            if command == "v":
                y = pos[1] + y
            pos = (pos[0], y)
            current.append(pos)
        elif command in "Cc":
            x1, y1, x2, y2, x, y = (next_num() for _ in range(6))
            if command == "c":
                x1, y1, x2, y2, x, y = x1 + pos[0], y1 + pos[1], x2 + pos[0], y2 + pos[1], x + pos[0], y + pos[1]
            current.extend(_cubic_points(pos, (x1, y1), (x2, y2), (x, y)))
            pos = (x, y)
        elif command in "Qq":
            x1, y1, x, y = (next_num() for _ in range(4))
            if command == "q":
                x1, y1, x, y = x1 + pos[0], y1 + pos[1], x + pos[0], y + pos[1]
            current.extend(_quadratic_points(pos, (x1, y1), (x, y)))
            pos = (x, y)
        elif command in "Aa":
            rx, ry, rot, large_arc, sweep, x, y = (next_num() for _ in range(7))
            if command == "a":
                x, y = x + pos[0], y + pos[1]
            current.extend(_arc_points(pos, rx, ry, rot, bool(large_arc), bool(sweep), (x, y)))
            pos = (x, y)
        elif command in "Zz":
            current.append(start)
            pos = start
        else:
            index += 1

    if current:
        subpaths.append(current)

    return [tuple(sp) for sp in subpaths]


def _cubic_points(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
) -> list[tuple[float, float]]:
    points = []
    for step in range(1, CURVE_STEPS + 1):
        t = step / CURVE_STEPS
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points


def _quadratic_points(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
) -> list[tuple[float, float]]:
    points = []
    for step in range(1, CURVE_STEPS + 1):
        t = step / CURVE_STEPS
        mt = 1 - t
        x = mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0]
        y = mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1]
        points.append((x, y))
    return points


def _arc_points(
    p0: tuple[float, float],
    rx: float,
    ry: float,
    x_axis_rotation: float,
    large_arc: bool,
    sweep: bool,
    p1: tuple[float, float],
) -> list[tuple[float, float]]:
    """Flatten an SVG elliptical arc via the spec's endpoint-to-center parameterization."""
    if rx == 0 or ry == 0 or p0 == p1:
        return [p1]

    phi = math.radians(x_axis_rotation)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)

    dx2, dy2 = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1p = cos_phi * dx2 + sin_phi * dy2
    y1p = -sin_phi * dx2 + cos_phi * dy2

    rx, ry = abs(rx), abs(ry)
    lam = (x1p**2) / (rx**2) + (y1p**2) / (ry**2)
    if lam > 1:
        scale = math.sqrt(lam)
        rx, ry = rx * scale, ry * scale

    sign = -1 if large_arc == sweep else 1
    numerator = max(0.0, rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2)
    denominator = rx**2 * y1p**2 + ry**2 * x1p**2
    coefficient = sign * math.sqrt(numerator / denominator) if denominator else 0.0
    cxp = coefficient * (rx * y1p) / ry
    cyp = -coefficient * (ry * x1p) / rx

    cx = cos_phi * cxp - sin_phi * cyp + (p0[0] + p1[0]) / 2
    cy = sin_phi * cxp + cos_phi * cyp + (p0[1] + p1[1]) / 2

    def angle(ux: float, uy: float, vx: float, vy: float) -> float:
        dot = ux * vx + uy * vy
        length = math.sqrt((ux**2 + uy**2) * (vx**2 + vy**2))
        result = math.acos(max(-1, min(1, dot / length))) if length else 0.0
        return -result if ux * vy - uy * vx < 0 else result

    theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    delta_theta = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and delta_theta > 0:
        delta_theta -= 2 * math.pi
    elif sweep and delta_theta < 0:
        delta_theta += 2 * math.pi

    points = []
    for step in range(1, ARC_STEPS + 1):
        t = theta1 + delta_theta * step / ARC_STEPS
        x = cx + rx * math.cos(t) * cos_phi - ry * math.sin(t) * sin_phi
        y = cy + rx * math.cos(t) * sin_phi + ry * math.sin(t) * cos_phi
        points.append((x, y))
    return points
