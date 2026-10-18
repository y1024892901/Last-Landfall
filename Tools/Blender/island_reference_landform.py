"""Reference-driven bare island relief, in metres, with numpy broadcasting.

X runs left/right in the reference view; positive Y points toward the distant
main mountain.  This module deliberately does not define an island silhouette:
the caller clips this continuous surface against its irregular coastline.

Public interfaces:
    terrain_height(x, y) -> ndarray, or float for two scalar inputs
    terrain_fields(x, y) -> dict with height, slope_deg, rock_mask,
                            buildable_mask and valley_mask

There is no water, vegetation, sand, architecture, or radial shoreline fade.
"""

import numpy as np


def _smoothstep(low, high, value):
    t = np.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _smoothmax(first, second, radius=6.0):
    """Compact polynomial union; untouched when surfaces differ by >radius."""
    overlap = np.maximum(radius - np.abs(first - second), 0.0)
    return np.maximum(first, second) + overlap * overlap / (4.0 * radius)


def _noise(x, y, wavelength, seed=0.0):
    """Smooth deterministic value noise, approximately in [-1, 1]."""
    px, py = x / wavelength, y / wavelength
    ix, iy = np.floor(px), np.floor(py)
    tx, ty = px - ix, py - iy
    # Quintic interpolation also keeps small rock details smooth at cell edges.
    tx = tx * tx * tx * (tx * (tx * 6.0 - 15.0) + 10.0)
    ty = ty * ty * ty * (ty * (ty * 6.0 - 15.0) + 10.0)

    def lattice(a, b):
        value = np.sin(a * 127.1 + b * 311.7 + seed * 74.7) * 43758.5453
        return 2.0 * (value - np.floor(value)) - 1.0

    first = lattice(ix, iy) * (1.0 - tx) + lattice(ix + 1.0, iy) * tx
    second = lattice(ix, iy + 1.0) * (1.0 - tx) + lattice(ix + 1.0, iy + 1.0) * tx
    return first * (1.0 - ty) + second * ty


def _ridge_envelope(x, y, points, power=1.5, asymmetric=False, softness=0.0):
    """Absolute crest heights with varying widths along a branching ridge.

    Point tuples are (x, y, crest_height, flank_width).  Smooth interpolation
    between unequal crest heights makes several summits and saddles instead of
    a uniform tube.  The caller takes the maximum of individual ridge branches
    so their junctions do not inflate into additive piles.
    """
    result = np.zeros_like(x, dtype=np.float64)
    for first, second in zip(points[:-1], points[1:]):
        ax, ay, ah, aw = first
        bx, by, bh, bw = second
        dx, dy = bx - ax, by - ay
        along = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0.0, 1.0)
        distance = np.hypot(x - ax - along * dx, y - ay - along * dy)
        eased = along * along * (3.0 - 2.0 * along)
        crest = ah + (bh - ah) * eased
        width = aw + (bw - aw) * eased
        if asymmetric:
            # A steeper seaward rock face and broader inland shoulder.
            side = (dx * (y - ay) - dy * (x - ax)) / np.hypot(dx, dy)
            width = width * (0.72 + 0.44 * _smoothstep(-12.0, 12.0, side))
        profile = np.exp(-0.7 * np.power(distance / width, power))
        candidate = crest * profile
        result = _smoothmax(result, candidate, softness) if softness > 0.0 else np.maximum(result, candidate)
    return result


def _path_distance(x, y, points):
    result = np.full_like(x, 1.0e12, dtype=np.float64)
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        dx, dy = bx - ax, by - ay
        along = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0.0, 1.0)
        result = np.minimum(result, np.hypot(x - ax - along * dx, y - ay - along * dy))
    return result


# The dominant massif sits BEHIND the settlement lowland.  Its highest summit
# is left of centre.  The rear range loses height towards the right; there is
# no circular ridge around the player area.
REAR_RIDGES = (
    (
        (-1020.0, 410.0, 132.0, 145.0),
        (-780.0, 570.0, 203.0, 165.0),
        (-520.0, 750.0, 302.0, 185.0),
        (-330.0, 630.0, 340.0, 190.0),
        (-115.0, 635.0, 282.0, 172.0),
        (95.0, 560.0, 247.0, 158.0),
        (320.0, 530.0, 239.0, 155.0),
        (515.0, 405.0, 184.0, 138.0),
        (705.0, 375.0, 142.0, 125.0),
    ),
    # Unequal back-facing spurs keep the mountain silhouette broken.
    ((-520.0, 750.0, 302.0, 160.0), (-650.0, 925.0, 248.0, 140.0), (-780.0, 1100.0, 151.0, 115.0)),
    ((-330.0, 630.0, 340.0, 158.0), (-260.0, 885.0, 268.0, 138.0), (-125.0, 1120.0, 191.0, 125.0)),
    ((95.0, 560.0, 247.0, 138.0), (225.0, 790.0, 235.0, 135.0), (410.0, 990.0, 136.0, 110.0)),
    ((320.0, 530.0, 239.0, 135.0), (530.0, 760.0, 177.0, 125.0), (760.0, 900.0, 105.0, 105.0)),
    # Front-facing buttresses terminate ABOVE the lowland, never in a rim.
    ((-330.0, 630.0, 340.0, 135.0), (-460.0, 430.0, 225.0, 108.0), (-545.0, 260.0, 113.0, 90.0)),
    ((-780.0, 570.0, 203.0, 125.0), (-870.0, 360.0, 156.0, 120.0), (-790.0, 185.0, 100.0, 100.0)),
    ((95.0, 560.0, 247.0, 112.0), (225.0, 375.0, 161.0, 98.0), (370.0, 245.0, 100.0, 82.0)),
)


# Compact angular summits stand above the broad branching mountain shoulders.
# Tuple: x, y, summit height, X radius, Y radius, orientation in radians.
PEAKS = (
    (-330.0, 630.0, 440.0, 345.0, 350.0, -0.32),
    (-525.0, 755.0, 370.0, 290.0, 305.0, 0.32),
    (-105.0, 660.0, 328.0, 255.0, 250.0, -0.15),
    (110.0, 575.0, 286.0, 245.0, 250.0, 0.22),
    (350.0, 545.0, 253.0, 220.0, 235.0, -0.18),
    (850.0, 290.0, 184.0, 190.0, 175.0, 0.28),
)


def _angular_peaks(x, y):
    result = np.zeros_like(x)
    for px, py, peak, rx, ry, angle in PEAKS:
        dx, dy = x - px, y - py
        ca, sa = np.cos(angle), np.sin(angle)
        u, v = (dx * ca - dy * sa) / rx, (dx * sa + dy * ca) / ry
        azimuth = np.arctan2(v, u)
        radius = np.hypot(u, v)
        # Unequal facets produce rock planes and an uneven peak silhouette.
        radius *= 1.0 + 0.11 * np.cos(3.0 * azimuth + 0.4) + 0.065 * np.sin(5.0 * azimuth)
        # Compact the distant tail.  Adding a permanent 48 m foundation here
        # previously left all summit tails above the lowland's 54 m datum and
        # made a circular depression when the construction patch was flattened.
        cone = peak * np.exp(-1.42 * np.power(radius, 0.94))
        cone *= 1.0 - _smoothstep(1.10, 1.98, radius)
        result = np.maximum(result, cone)
    return result


# Separate hills and short ribs, with wide low saddles between them.  In the
# reference these read as distinct headlands, not a horseshoe retaining wall.
SIDE_RIDGES = (
    ((-1100.0, 140.0, 104.0, 112.0), (-930.0, 225.0, 162.0, 128.0), (-760.0, 240.0, 141.0, 115.0)),
    ((-1060.0, -400.0, 80.0, 105.0), (-850.0, -330.0, 154.0, 130.0), (-665.0, -410.0, 115.0, 113.0), (-590.0, -590.0, 78.0, 96.0)),
    ((-930.0, -530.0, 105.0, 90.0), (-1000.0, -690.0, 60.0, 82.0)),
    ((675.0, 215.0, 114.0, 102.0), (855.0, 285.0, 179.0, 132.0), (1035.0, 185.0, 123.0, 114.0)),
    ((610.0, -250.0, 99.0, 102.0), (790.0, -165.0, 139.0, 123.0), (965.0, -300.0, 106.0, 105.0), (1105.0, -440.0, 65.0, 90.0)),
    ((670.0, -415.0, 108.0, 107.0), (790.0, -605.0, 83.0, 100.0), (920.0, -680.0, 51.0, 85.0)),
)


FRONT_RIDGES = (
    # A long, low, forward-pointing rocky peninsula, with an asymmetric crest.
    ((25.0, -365.0, 73.0, 115.0), (90.0, -650.0, 112.0, 124.0),
     (180.0, -950.0, 86.0, 100.0), (250.0, -1210.0, 51.0, 74.0),
     (265.0, -1330.0, 34.0, 62.0)),
    # Two shorter toes fork off the peninsula; neither encloses the valley.
    ((90.0, -650.0, 112.0, 100.0), (340.0, -755.0, 80.0, 88.0), (565.0, -850.0, 41.0, 70.0)),
    ((180.0, -950.0, 86.0, 84.0), (-30.0, -975.0, 63.0, 75.0), (-235.0, -1075.0, 35.0, 60.0)),
)


FOOTHILL_RIDGES = (
    ((-600.0, 245.0, 120.0, 108.0), (-455.0, 185.0, 96.0, 92.0), (-365.0, 260.0, 72.0, 74.0)),
    ((490.0, 250.0, 126.0, 111.0), (390.0, 150.0, 99.0, 90.0), (435.0, 45.0, 74.0, 78.0)),
    ((-620.0, -365.0, 119.0, 112.0), (-465.0, -290.0, 89.0, 97.0), (-370.0, -335.0, 65.0, 79.0)),
    ((610.0, -315.0, 101.0, 104.0), (470.0, -260.0, 81.0, 90.0), (420.0, -365.0, 62.0, 72.0)),
)


EROSION_GULLIES = (
    (((-400.0, 690.0), (-500.0, 550.0), (-565.0, 425.0), (-620.0, 310.0), (-685.0, 165.0)), 48.0, 24.0),
    (((-280.0, 610.0), (-255.0, 505.0), (-180.0, 360.0), (-145.0, 235.0), (-55.0, 120.0)), 51.0, 25.0),
    (((-85.0, 615.0), (-30.0, 480.0), (55.0, 345.0), (70.0, 225.0)), 39.0, 23.0),
    (((255.0, 560.0), (345.0, 435.0), (430.0, 355.0), (485.0, 195.0), (530.0, 80.0)), 36.0, 25.0),
    (((-520.0, 720.0), (-625.0, 610.0), (-675.0, 480.0), (-765.0, 385.0)), 37.0, 21.0),
    (((-225.0, 745.0), (-140.0, 840.0), (-100.0, 990.0)), 34.0, 22.0),
    (((-455.0, 540.0), (-370.0, 420.0), (-335.0, 285.0)), 31.0, 20.0),
    (((110.0, 590.0), (160.0, 485.0), (245.0, 410.0)), 29.0, 19.0),
    (((-850.0, -280.0), (-790.0, -390.0), (-760.0, -515.0)), 11.0, 22.0),
    (((830.0, -195.0), (875.0, -330.0), (940.0, -435.0)), 10.0, 24.0),
    (((145.0, -720.0), (195.0, -880.0), (280.0, -1060.0)), 12.0, 17.0),
)


def _valley_weight(x, y):
    # An irregular, partial blend provides a connected valley. The expanded
    # The 900 x 630 m build core stays on the flat build datum, matching the
    # runtime placement ellipse. Blend back into natural terrain beyond it.
    meander = 48.0 * np.sin((y + 95.0) / 205.0)
    radius = np.sqrt(((x - meander) / 675.0) ** 2 + ((y + 75.0) / 487.5) ** 2)
    radius += 0.10 * _noise(x, y, 292.5, 87.0) + 0.055 * _noise(x, y, 142.5, 89.0)
    central = 0.76 * (1.0 - _smoothstep(0.62, 1.27, radius))
    core_radius = np.sqrt((x / 450.0) ** 2 + ((y + 80.0) / 315.0) ** 2)
    core = 1.0 - _smoothstep(1.0, 1.22, core_radius)
    central = np.maximum(central, core)

    # The south outlet continues through the front; a closed bowl cannot form.
    south = -y
    outlet_width = 180.0 - 55.0 * _smoothstep(350.0, 760.0, south)
    outlet_centre = -85.0 - 55.0 * _smoothstep(300.0, 700.0, south)
    lateral = 1.0 - _smoothstep(0.46, 1.19, np.abs(x - outlet_centre) / outlet_width)
    length = _smoothstep(180.0, 330.0, south) * (1.0 - _smoothstep(560.0, 815.0, south))
    return np.maximum(central, lateral * length)


def _height_array(x, y):
    # Keep the natural lowland at the same datum as the invisible build plane.
    # Its irregular far coastal foundation gently lowers toward the long toes.
    foundation_radius = np.hypot(0.80 * x, y + 75.0)
    base = 54.0 - 22.0 * _smoothstep(650.0, 1330.0, foundation_radius)
    base += 0.50 * _noise(x, y, 480.0, 4.0) + 0.20 * _noise(x, y, 195.0, 5.0)

    # Modest domain warping breaks straight procedural ridge centre lines.
    wx = x + 21.0 * _noise(x, y, 310.0, 13.0) + 8.0 * _noise(x, y, 125.0, 17.0)
    wy = y + 18.0 * _noise(x, y, 275.0, 23.0) + 7.0 * _noise(x, y, 110.0, 29.0)

    height = base.copy()
    for ridge in REAR_RIDGES:
        height = np.maximum(height, _ridge_envelope(wx, wy, ridge, power=1.50))
    height = np.maximum(height, _angular_peaks(x, y))
    for ridge in SIDE_RIDGES:
        height = np.maximum(height, _ridge_envelope(wx, wy, ridge, power=1.50))
    for ridge in FRONT_RIDGES:
        height = np.maximum(height, _ridge_envelope(wx, wy, ridge, power=1.50, asymmetric=True))

    # Inset ravines split rock buttresses on the flanks and drain downhill.
    incision = np.zeros_like(height)
    for points, depth, width in EROSION_GULLIES:
        distance = _path_distance(wx, wy, points)
        incision = np.maximum(incision, depth * np.exp(-0.5 * (distance / width) ** 2))
    raised = _smoothstep(55.0, 125.0, height)
    height -= incision * raised

    # Large-to-small relief: broad rock masses, facets, fractures, then restrained
    # surface break-up.  No noise is allowed to roughen the protected build core.
    mountain = _smoothstep(120.0, 350.0, height)
    roughness = (3.0 + 22.0 * mountain) * _smoothstep(59.0, 105.0, height)
    relief = (
        0.55 * _noise(wx, wy, 160.0, 31.0)
        + 0.30 * _noise(wx, wy, 76.0, 37.0)
        + 0.17 * _noise(wx, wy, 35.0, 41.0)
        + 0.085 * _noise(wx, wy, 15.5, 43.0)
        + 0.035 * _noise(wx, wy, 7.0, 47.0)
    )
    # Oblique seams add a consistent geological direction across the headlands.
    seam_phase = 0.064 * wx + 0.023 * wy + 2.2 * _noise(wx, wy, 88.0, 53.0)
    seams = -1.7 * np.power(0.5 + 0.5 * np.sin(seam_phase), 7.0)
    height += roughness * relief + seams * raised

    weight = _valley_weight(x, y)
    floor = 54.0 + 0.0005 * (y + 75.0) + 0.0008 * x
    floor += 0.35 * _noise(x, y, 295.0, 61.0)
    floor += 0.18 * _noise(x, y, 125.0, 67.0)
    # The central building patch has one agreed datum, with a gradual natural
    # transition into the surrounding gently rolling 54 +/- 1 m lowland.
    core_radius = np.sqrt((x / 450.0) ** 2 + ((y + 80.0) / 315.0) ** 2)
    core = 1.0 - _smoothstep(1.0, 1.22, core_radius)
    floor = floor * (1.0 - core) + 54.0 * core
    height = height * (1.0 - weight) + floor * weight

    # Four uneven, rounded low spurs merge softly with the valley edges.  Their
    # compact tails are already below the natural floor before the build core;
    # therefore no circular mask is needed to carve them away from that core.
    foothills = np.zeros_like(height)
    for ridge in FOOTHILL_RIDGES:
        foothills = _smoothmax(foothills, _ridge_envelope(wx, wy, ridge, power=1.70, softness=6.0), 6.0)
    height = _smoothmax(height, foothills, 6.0)
    return height, weight


def terrain_height(x, y):
    """Return bare land elevation; accepts scalars or broadcastable arrays."""
    xs, ys = np.broadcast_arrays(np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64))
    height, _ = _height_array(xs, ys)
    return float(height) if height.ndim == 0 else height


def terrain_fields(x, y):
    """Return height plus renderer/gameplay masks in the same coordinate shape.

    ``slope_deg`` uses a 3 m central difference.  ``rock_mask`` is a continuous
    artistic mask, not a material assignment.  ``buildable_mask`` is strongest
    on the broad central floor and falls to zero on terrain steeper than 7 deg.
    """
    xs, ys = np.broadcast_arrays(np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64))
    height, valley = _height_array(xs, ys)
    step = 3.0
    gx = (_height_array(xs + step, ys)[0] - _height_array(xs - step, ys)[0]) / (2.0 * step)
    gy = (_height_array(xs, ys + step)[0] - _height_array(xs, ys - step)[0]) / (2.0 * step)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    rock = _smoothstep(12.0, 37.0, slope)
    rock = np.maximum(rock, 0.65 * _smoothstep(240.0, 380.0, height))
    rock *= 1.0 - 0.85 * valley
    buildable = valley * (1.0 - _smoothstep(3.0, 7.0, slope))
    fields = {
        "height": height,
        "slope_deg": slope,
        "rock_mask": np.clip(rock, 0.0, 1.0),
        "buildable_mask": np.clip(buildable, 0.0, 1.0),
        "valley_mask": valley,
    }
    if height.ndim == 0:
        return {key: float(value) for key, value in fields.items()}
    return fields
