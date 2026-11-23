"""OpenCV pipeline independent of the interface. All measurements use original pixels."""
from dataclasses import dataclass
from time import perf_counter
import cv2
import numpy as np

COLUMNS = ["coin_id", "center_x", "center_y", "area_px2", "perimeter_px", "equiv_diameter_px",
           "enclosing_diameter_px", "circularity", "width_px", "height_px", "touches_border", "diameter_mm", "area_mm2"]


@dataclass(frozen=True)
class Config:
    kernel_size: int = 3
    min_area: int = 150
    min_circularity: float = 0.0
    peak_spacing: float = 1.0
    mm_per_pixel: float = 0.0


def read_image(source):
    """Read Unicode filenames or uploaded bytes, rejecting undecodable data."""
    data = np.frombuffer(source, np.uint8) if isinstance(source, bytes) else np.fromfile(source, np.uint8)
    if not data.size:
        raise ValueError("Tệp ảnh rỗng.")
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Không đọc được ảnh JPG/PNG hợp lệ.")
    return image


def make_markers(mask, spacing):
    """Find local distance maxima with radius-aware nonmaximum suppression.

    Process each component separately so small isolated coins are not lost to a
    single global distance cutoff. Marker placement remains a heuristic.
    """
    distance = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    smooth = cv2.GaussianBlur(distance, (5, 5), 0)
    maxima = (smooth >= cv2.dilate(smooth, np.ones((3, 3), np.uint8)) - 1e-6) & (mask > 0)
    _, components = cv2.connectedComponents(mask)
    markers = np.zeros(mask.shape, np.int32)
    next_id = 2
    for component in range(1, int(components.max()) + 1):
        member = components == component
        local_max = float(smooth[member].max())
        peaks = np.uint8(maxima & member & (smooth >= 0.22 * local_max))
        n, plateaus = cv2.connectedComponents(peaks)
        candidates = []
        for label in range(1, n):
            ys, xs = np.where(plateaus == label)
            best = int(np.argmax(smooth[ys, xs]))
            y, x = int(ys[best]), int(xs[best])
            candidates.append((float(smooth[y, x]), y, x))
        if not candidates:
            y, x = np.unravel_index(np.argmax(np.where(member, smooth, -1)), mask.shape)
            candidates = [(float(smooth[y, x]), int(y), int(x))]
        accepted = []
        for radius, y, x in sorted(candidates, reverse=True):
            if all(np.hypot(x - xx, y - yy) > spacing * max(radius, rr) for rr, yy, xx in accepted):
                accepted.append((radius, y, x))
                markers[y, x] = next_id
                next_id += 1
    return distance, markers


def split_mask(clean, spacing):
    """Marker-controlled watershed; background is constrained by the mask."""
    _, cc = cv2.connectedComponents(clean)
    before = int(cc.max())
    distance, seeds = make_markers(clean, spacing)
    labels = cc.copy()
    if before:
        marker = seeds.copy()
        marker[clean == 0] = 1
        marker = cv2.copyMakeBorder(marker, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=1)
        terrain = cv2.cvtColor(cv2.copyMakeBorder(clean, 1, 1, 1, 1,
                              cv2.BORDER_CONSTANT, value=0), cv2.COLOR_GRAY2BGR)
        split = cv2.watershed(terrain, marker)[1:-1, 1:-1]
        labels = np.where((clean > 0) & (split > 1), split - 1, 0).astype(np.int32)
    return before, distance, seeds, labels


def mask_quality(labels, min_area):
    """Area-weighted contour roundness; a heuristic, not a confidence score."""
    weighted, total = 0.0, 0
    for region in np.unique(labels):
        if region <= 0:
            continue
        mask = np.uint8(labels == region) * 255
        area = cv2.countNonZero(mask)
        if area < min_area:
            continue
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(contour, True)
        quality = 4 * np.pi * cv2.contourArea(contour) / perimeter**2 if perimeter else 0
        weighted += area * quality
        total += area
    return weighted / total if total else 0.0


def recover_round_regions(blur, min_area):
    """Recover closed coin rims when intensity alone misses bright surfaces.

    Threshold the morphological gradient and inspect nested contours at three
    small closing scales. Convex hulls bridge rim/lettering gaps. Accept only
    well-supported round hulls and suppress nested duplicates. No circle Hough
    transform, trained model, or fixed object count is used.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    gradient = cv2.morphologyEx(blur, cv2.MORPH_GRADIENT, kernel)
    _, edges = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    candidates = []
    for size in (1, 3, 5):
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
        contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            perimeter = cv2.arcLength(hull, True)
            (x, y), radius = cv2.minEnclosingCircle(hull)
            if (hull_area < min_area or perimeter == 0 or radius < 3
                    or radius > min(blur.shape) * .48 or area / hull_area < .4):
                continue
            roundness = 4 * np.pi * hull_area / perimeter**2
            coverage = hull_area / (np.pi * radius**2)
            if roundness >= .85 and coverage >= .77:
                candidates.append((hull_area * roundness * coverage, x, y, radius, hull))
    accepted = []
    mask = np.zeros_like(blur)
    for candidate in sorted(candidates, key=lambda item: item[0], reverse=True):
        _, x, y, radius, hull = candidate
        if any(np.hypot(x - other[1], y - other[2]) < .8 * max(radius, other[3]) for other in accepted):
            continue
        accepted.append(candidate)
        cv2.drawContours(mask, [hull], -1, 255, cv2.FILLED)
    return mask, edges


def process(image, config=None):
    config = config or Config()
    if image is None or image.ndim != 3 or image.shape[2] != 3 or min(image.shape[:2]) < 3:
        raise ValueError("Ảnh phải có ba kênh BGR, kích thước tối thiểu 3×3.")
    if (config.kernel_size not in (1, 3, 5, 7) or config.min_area < 1 or config.peak_spacing <= 0
            or config.mm_per_pixel < 0 or not 0 <= config.min_circularity <= 1):
        raise ValueError("Tham số xử lý không hợp lệ.")
    start = perf_counter()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Auto assumes most border pixels are background.
    border = np.concatenate([binary[0], binary[-1], binary[:, 0], binary[:, -1]])
    if np.mean(border) > 127:
        binary = cv2.bitwise_not(binary)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (config.kernel_size,) * 2)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    clean = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    # Padding makes flood filling safe when a coin touches the original border.
    padded = cv2.copyMakeBorder(clean, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    flooded = padded.copy()
    cv2.floodFill(flooded, None, (0, 0), 255)
    clean = cv2.bitwise_or(padded, cv2.bitwise_not(flooded))[1:-1, 1:-1]
    n, cc, stats, _ = cv2.connectedComponentsWithStats(clean, connectivity=8)
    for label in range(1, n):
        if stats[label, cv2.CC_STAT_AREA] < config.min_area:
            clean[cc == label] = 0
    before, distance, seeds, labels = split_mask(clean, config.peak_spacing)
    quality = mask_quality(labels, config.min_area)
    recovered = False
    extra_steps = {}
    if before:
        rim_mask, rim_edges = recover_round_regions(blur, config.min_area)
        if quality < .72:
            rim_result = split_mask(rim_mask, config.peak_spacing)
            # Avoid replacing a whole scene with decorative fragments.
            enough_area = cv2.countNonZero(rim_mask) >= .5 * cv2.countNonZero(clean)
            if enough_area and mask_quality(rim_result[3], config.min_area) > quality + .12:
                clean = rim_mask
                before, distance, seeds, labels = rim_result
                recovered = True
        if not recovered:
            # An area-weighted scene score hides a single fragmented bright
            # coin among many good coins. Inspect each closed rim locally too.
            count, rim_labels, rim_stats, _ = cv2.connectedComponentsWithStats(rim_mask)
            repaired = clean.copy()
            for region in range(1, count):
                x, y, width, height, area = rim_stats[region]
                member = rim_labels[y:y + height, x:x + width] == region
                current = repaired[y:y + height, x:x + width]
                coverage = np.count_nonzero((current > 0) & member) / area
                if not .05 < coverage < .80:
                    continue
                local = np.uint8(member) * 255
                contours, _ = cv2.findContours(local, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                contour = max(contours, key=cv2.contourArea)
                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * cv2.contourArea(contour) / perimeter**2 if perimeter else 0
                # Do not fill an elongated cluster or a partial border object.
                if circularity < .8:
                    continue
                current[member] = 255
                recovered = True
            if recovered:
                clean = repaired
                before, distance, seeds, labels = split_mask(clean, config.peak_spacing)
        if recovered:
            extra_steps = {"Threshold trên gradient hình thái": rim_edges}
    output = image.copy()
    rows = []
    accepted_labels = np.zeros(clean.shape, np.int32)
    for region in np.unique(labels):
        if region <= 0:
            continue
        mask = np.uint8(labels == region) * 255
        area = int(cv2.countNonZero(mask))
        if area < config.min_area:
            continue
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        contour = max(contours, key=cv2.contourArea)
        perimeter = float(cv2.arcLength(contour, True))
        circularity = 4 * np.pi * cv2.contourArea(contour) / perimeter**2 if perimeter else 0.0
        if circularity < config.min_circularity:
            continue
        moments = cv2.moments(mask, binaryImage=True)
        cx, cy = moments["m10"] / area, moments["m01"] / area
        x, y, width, height = cv2.boundingRect(contour)
        _, radius = cv2.minEnclosingCircle(contour)
        diameter = 2 * np.sqrt(area / np.pi)
        touches = x == 0 or y == 0 or x + width == image.shape[1] or y + height == image.shape[0]
        coin_id = len(rows) + 1
        accepted_labels[mask > 0] = coin_id
        scale = config.mm_per_pixel
        rows.append(dict(zip(COLUMNS, [coin_id, round(cx, 2), round(cy, 2), area,
            round(perimeter, 2), round(diameter, 2), round(2 * radius, 2), round(circularity, 4),
            width, height, touches, round(diameter * scale, 3) if scale else None,
            round(area * scale**2, 3) if scale else None])))
        cv2.drawContours(output, [contour], -1, (70, 230, 70), 2)
        center = (round(cx), round(cy))
        cv2.circle(output, center, 3, (0, 0, 255), -1)
        for color, thickness in [((0, 0, 0), 4), ((0, 255, 255), 2)]:
            cv2.putText(output, str(coin_id), (center[0] + 7, center[1] - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, .7, color, thickness, cv2.LINE_AA)
    palette = np.random.default_rng(42).integers(50, 256, (len(rows) + 1, 3), dtype=np.uint8)
    palette[0] = 0
    seed_view = image.copy()
    for y, x in zip(*np.where(seeds > 1)):
        cv2.circle(seed_view, (int(x), int(y)), 5, (0, 0, 255), -1)
    return {"rows": rows, "count": len(rows), "before_count": before,
            "recovered_from_rims": recovered,
            "elapsed_ms": (perf_counter() - start) * 1000, "output": output,
            "steps": {"Ảnh xám": gray, "Gaussian Blur": blur, "Threshold": binary, **extra_steps,
                      ("Mask khôi phục từ đường viền" if recovered else "Morphology và lấp lỗ"): clean,
                      "Distance Transform": cv2.normalize(distance, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
                      "Marker (tâm đỏ)": seed_view, "Nhãn đối tượng": palette[accepted_labels]},
            "labels": accepted_labels}
