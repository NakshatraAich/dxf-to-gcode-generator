# importing all libraries
from dataclasses import dataclass
from typing import Optional, Tuple
import math
import ezdxf
import matplotlib.pyplot as plt
import numpy as np
# importing all libraries

# defining the dxfsegment class
@dataclass
class DXFSegment:
    entity_type: str
    start: Optional[Tuple[float, float]] = None
    end: Optional[Tuple[float, float]] = None
    bulge: Optional[float] = 0.0
    center: Optional[Tuple[float, float]] = None
    radius: Optional[float] = None
# defining the dxfsegment class

# helper functions
def polar_to_cartesian(center, radius, angle_deg):
    angle_rad = math.radians(angle_deg)
    return (
        center[0] + radius * math.cos(angle_rad),
        center[1] + radius * math.sin(angle_rad)
    )

def cartesian_to_polar(x, y):
    r = math.hypot(x, y)
    theta = math.degrees(math.atan2(y, x)) 
    return theta 

def arc_from_bulge(p1, p2, bulge):
    """Returns arc points from bulge value."""
    if bulge == 0:
        return [p1, p2]

    x1, y1 = p1
    x2, y2 = p2
    chord = math.hypot(x2 - x1, y2 - y1)
    sagitta = (bulge * chord) / 2
    radius = ((chord / 2) ** 2 + sagitta ** 2) / (2 * abs(sagitta))
    
    # Midpoint of the chord
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2

    # Normal vector to chord
    dx = x2 - x1
    dy = y2 - y1
    nx = -dy
    ny = dx
    length = math.hypot(nx, ny)
    nx /= length
    ny /= length

    # Determine center direction by sign of bulge
    direction = 1 if bulge > 0 else -1
    cx = mx + direction * nx * (radius - abs(sagitta))
    cy = my + direction * ny * (radius - abs(sagitta))

    # Angles
    start_angle = math.atan2(y1 - cy, x1 - cx)
    end_angle = math.atan2(y2 - cy, x2 - cx)

    # Adjust for direction
    if bulge > 0 and end_angle < start_angle:
        end_angle += 2 * math.pi
    elif bulge < 0 and end_angle > start_angle:
        end_angle -= 2 * math.pi

    # Arc points
    angles = np.linspace(start_angle, end_angle, 50)
    arc_points = [(cx + radius * math.cos(a), cy + radius * math.sin(a)) for a in angles]
    return arc_points

def print_segments(segments):
    for i, seg in enumerate(segments, 1):
        print(f"{i}. Type: {seg.entity_type}")
        if seg.start:
            print(f"   Start:  ({seg.start[0]:.3f}, {seg.start[1]:.3f})")
        if seg.end:
            print(f"   End:    ({seg.end[0]:.3f}, {seg.end[1]:.3f})")
        if seg.bulge:
            print(f"   Bulge:  {seg.bulge:.3f}")
        if seg.center:
            print(f"   Center: ({seg.center[0]:.3f}, {seg.center[1]:.3f})")
        if seg.radius:
            print(f"   Radius: {seg.radius:.3f}")
        print()
# helper functions

# extraction function
def extract_dxf_segments(file_path):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    segments = []

    for entity in msp:
        etype = entity.dxftype()

        if etype == 'LINE':
            segments.append(DXFSegment(
                entity_type='LINE',
                start=(entity.dxf.start.x, entity.dxf.start.y),
                end=(entity.dxf.end.x, entity.dxf.end.y)
            ))

        elif etype in ['LWPOLYLINE', 'POLYLINE']:
            points = [(p[0], p[1]) for p in entity.get_points()]
            bulges = [p[4] if len(p) > 4 else 0.0 for p in entity.get_points()]
            for i in range(len(points) - 1):
                segments.append(DXFSegment(
                    entity_type='LWPOLYLINE',
                    start=points[i],
                    end=points[i+1],
                    bulge=bulges[i]
                ))
            if entity.closed:
                segments.append(DXFSegment(
                    entity_type='LWPOLYLINE',
                    start=points[-1],
                    end=points[0],
                    bulge=bulges[-1]
                ))

        elif etype == 'ARC':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            segments.append(DXFSegment(
                entity_type='ARC',
                center=center,
                radius=radius,
                start=polar_to_cartesian(center, radius, start_angle),
                end=polar_to_cartesian(center, radius, end_angle)
            ))

        elif etype == 'CIRCLE':
            segments.append(DXFSegment(
                entity_type='CIRCLE',
                center=(entity.dxf.center.x, entity.dxf.center.y),
                radius=entity.dxf.radius
            ))

    return segments
# extraction function

# plotting functions
def plot_segments(segments):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    for seg in segments:
        # Plot straight segments (LINE or polyline without bulge)
        if seg.entity_type in ['LINE', 'LWPOLYLINE'] and seg.bulge == 0:
            xs = [seg.start[0], seg.end[0]]
            ys = [seg.start[1], seg.end[1]]
            ax.plot(xs, ys, 'k-', markersize=0)
            ax.plot(xs, ys, 'ro', markersize=0)  # Mark vertices

        # Plot polyline arcs (with bulge)
        elif seg.entity_type == 'LWPOLYLINE' and seg.bulge != 0:
            arc_pts = arc_from_bulge(seg.start, seg.end, seg.bulge)
            xs, ys = zip(*arc_pts)
            ax.plot(xs, ys, 'b--', markersize=0)
            ax.plot([seg.start[0], seg.end[0]], [seg.start[1], seg.end[1]], 'ro', markersize=0)  # Vertices

        # Plot ARC entities
        elif seg.entity_type == 'ARC':
            start_angle = math.atan2(seg.start[1] - seg.center[1], seg.start[0] - seg.center[0])
            end_angle = math.atan2(seg.end[1] - seg.center[1], seg.end[0] - seg.center[0])
            if end_angle < start_angle:
                end_angle += 2 * math.pi
            angles = np.linspace(start_angle, end_angle, 50)
            xs = seg.center[0] + seg.radius * np.cos(angles)
            ys = seg.center[1] + seg.radius * np.sin(angles)
            ax.plot(xs, ys, 'g-', markersize=0)
            ax.plot([seg.start[0], seg.end[0]], [seg.start[1], seg.end[1]], 'ro')  # Vertices

        # Plot CIRCLE entities
        elif seg.entity_type == 'CIRCLE':
            theta = np.linspace(0, 2 * math.pi, 100)
            xs = seg.center[0] + seg.radius * np.cos(theta)
            ys = seg.center[1] + seg.radius * np.sin(theta)
            ax.plot(xs, ys, 'r-', markersize=0)
            # Optional: mark center
            ax.plot([seg.center[0]], [seg.center[1]], 'ro', markersize=0)  # Center as vertex

    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_title("DXF Geometry with Vertices")
    plt.show()

def plot_interpolated_points(points):
    xs, ys = zip(*points)
    plt.figure(figsize=(8, 8))
    
    # Plot all interpolated points
    plt.plot(xs, ys, 'ro', markersize=2, label="Interpolated Points")

    # Mark the first coordinate distinctly
    plt.plot(xs[0], ys[0], 'go', markersize=8, label="Start Point")  # Green circle

    plt.gca().set_aspect('equal')
    plt.grid(True)
    plt.title("Interpolated DXF Geometry")
    plt.legend()
    plt.show()

    return
# plotting functions

# interpolation functions
def interpolate_lines(start, end, step = 0.5):
    x0, y0 = start
    x1, y1 = end

    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)

    if length == 0 or step <= 0:
        return [start]

    num_steps = int(length // step)
    result = []

    for i in range(num_steps + 1):
        t = i * step / length
        x = x0 + t * dx
        y = y0 + t * dy
        result.append((x, y))

    if result[-1] != end:
        result.append(end)

    return result

def interpolate_arc_entity(center, radius, start_angle_deg, end_angle_deg, step=0.5):
    # Convert angles to radians
    start_angle = math.radians(start_angle_deg)
    end_angle = math.radians(end_angle_deg)

    # Ensure correct direction (counter-clockwise)
    if end_angle < start_angle:
        end_angle += 2 * math.pi

    angle_span = end_angle - start_angle
    arc_length = radius * angle_span
    num_points = max(int(arc_length // step), 2)

    angles = np.linspace(start_angle, end_angle, num_points)
    points = [(center[0] + radius * math.cos(a), center[1] + radius * math.sin(a)) for a in angles]
    return points

def interpolate_bulge_arc(p1, p2, bulge, step=1.0):
    """
    Returns interpolated arc points between p1 and p2 based on bulge.
    """
    if bulge == 0.0:
        return [p1, p2]

    x1, y1 = p1
    x2, y2 = p2
    chord = math.hypot(x2 - x1, y2 - y1)
    sagitta = (bulge * chord) / 2
    radius = ((chord / 2) ** 2 + sagitta ** 2) / (2 * abs(sagitta))

    # Midpoint of the chord
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2

    # Normal vector to chord
    dx = x2 - x1
    dy = y2 - y1
    nx = -dy
    ny = dx
    length = math.hypot(nx, ny)
    nx /= length
    ny /= length

    # Determine center direction by sign of bulge
    direction = 1 if bulge > 0 else -1
    cx = mx + direction * nx * (radius - abs(sagitta))
    cy = my + direction * ny * (radius - abs(sagitta))

    # Angles
    start_angle = math.atan2(y1 - cy, x1 - cx)
    end_angle = math.atan2(y2 - cy, x2 - cx)

    # Adjust for direction
    if bulge > 0 and end_angle < start_angle:
        end_angle += 2 * math.pi
    elif bulge < 0 and end_angle > start_angle:
        end_angle -= 2 * math.pi

    arc_length = abs(end_angle - start_angle) * radius
    n_steps = max(int(arc_length / step), 1)

    angles = np.linspace(start_angle, end_angle, n_steps + 1)
    arc_points = [(cx + radius * math.cos(a), cy + radius * math.sin(a)) for a in angles]
    return arc_points

def interpolate_segments(segments, step=10):
    interpolated_points = []

    for seg in segments:
        if seg.entity_type in ['LINE', 'LWPOLYLINE'] and seg.bulge == 0:
            pts = interpolate_lines(seg.start, seg.end, step)
            interpolated_points.extend(pts)

        elif seg.entity_type == 'LWPOLYLINE' and seg.bulge != 0:
            pts = interpolate_bulge_arc(seg.start, seg.end, seg.bulge, step)
            interpolated_points.extend(pts)

        elif seg.entity_type == 'ARC':
            start_angle = math.degrees(math.atan2(seg.start[1] - seg.center[1], seg.start[0] - seg.center[0]))
            end_angle = math.degrees(math.atan2(seg.end[1] - seg.center[1], seg.end[0] - seg.center[0]))
            # Handle angle wrapping
            if end_angle < start_angle:
                end_angle += 360
            pts = interpolate_arc_entity(seg.center, seg.radius, start_angle, end_angle, step)
            interpolated_points.extend(pts)

    return interpolated_points
# interpolation functions

# transformation functions
def shift_to_origin(points, new_origin =(216.50, 215.34)): #211.50, 92.032 #216.50, 215.34 #223.5,92.032
    if not points:
        return []

    origin_x, origin_y = points[0]
    shifted_points = [(x - origin_x + new_origin[0], y - origin_y + new_origin[1]) for x, y in points]
    return shifted_points

def mirror(points, axis='x'):
    if axis == 'x':
        return [(x, -y) for x, y in points]
    elif axis == 'y':
        return [(-x, y) for x, y in points]
    else:
        raise ValueError("Axis must be 'x' or 'y'")

def swap_axes(points):
    return [(y, x) for x, y in points]

def rotate_points(points, angle_deg):
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return [
        (x * cos_a - y * sin_a, x * sin_a + y * cos_a)
        for x, y in points
    ]

def reorder_path(points, start_point):
    if not points:
        return []

    # Find the index of the point closest to the desired start_point
    distances = [math.hypot(x - start_point[0], y - start_point[1]) for x, y in points]
    start_idx = distances.index(min(distances))

    # Reorder the list so it starts from the closest point
    return points[start_idx:] + points[:start_idx]
# transformation functions

# gcode generator
def generate_gcode(points):
    gcode = []

    # === Initialization ===
    gcode.append("; Initialize")
    gcode.append("G21 ; Set units to millimeters")
    gcode.append("G90 ; Use absolute positioning")
    gcode.append("G92 E0 ; Reset extruder")
    gcode.append("G1 Z70 F600 ; Lift Z to safe height")
    gcode.append("G1 X0 Y0 F1200 ; Safe Position to extrude")
    gcode.append("G4 P1000 ; Wait for system to stabilize")

    # === Prime the epoxy ===
    gcode.append("; Prime the syringe")
    gcode.append("G1 E1 F30 ; Slow prime to build pressure")
    gcode.append("G4 P1000 ; Let epoxy begin flowing")

    # === Dispense at each point ===
    ext = 60 # Start from primed value
    extrusion_per_point = 12.0  # Change this based on testing
    z_dispense = 9 #3 # Height to lower for epoxy drop

    # === Prime the epoxy ===
    for i in range(5):
        ext += 6
        gcode.append(f"G1 E{ext:.2f} F2000 ; Slowly extrude epoxy")
        gcode.append(f"G1 E{ext-(12):.2f} F2000 ; Slowly retract epoxy")
        gcode.append("G4 P300 ; Wait for 0.3 second")
        gcode.append("")

    gcode.append("G4 P3000 ; Pause")

    for x, y in points:
        gcode.append(f"; --- Move to ({x:.2f}, {y:.2f}) ---")
        gcode.append(f"G1 X{x:.2f} Y{y:.2f} F6000 ; Move to point")
        gcode.append(f"G1 Z{z_dispense:.2f} F6000 ; Lower to dispense height")

        ext += extrusion_per_point
        gcode.append(f"G1 E{ext} F2000")
        gcode.append(f"G1 E{ext-(extrusion_per_point*2)} F2000")
        gcode.append(f"G4 P200;")
        gcode.append(f"G1 Z{z_dispense+10} F6000 ; Lift the extruder")
        gcode.append("")

    # === Wrap up ===
    gcode.append("; Final actions")
    gcode.append("G1 Z40 F600 ; Raise nozzle safely")
    gcode.append("G1 X0 Y0 Z40 F3000; Reset")

    return "\n".join(gcode)
# gcode generator

if __name__ == "__main__":
    dxf_path = "C:\\Users\\mount\\Downloads\\GCodeGeneratorV3\\ext2.dxf"
    segments = extract_dxf_segments(dxf_path)
    plot_segments(segments)
    print_segments(segments)

    interpolated_points = interpolate_segments(segments, step=0.5)[::30]

    # === Transformations ===
    interpolated_points = reorder_path(interpolated_points, (67.50, 60.50))
    interpolated_points = shift_to_origin(interpolated_points)    

    # === Visualization ===
    plot_interpolated_points(interpolated_points)
    print(f"Interpolated point count: {len(interpolated_points)}")

    # === G-code Generation ===
    gcode = generate_gcode(interpolated_points)

    # file_path = "C:\\Users\\mount\\Downloads\\GCodeGeneratorV3\\male_inner_profile.gcode"
    file_path = "C:\\Users\\mount\\Downloads\\GCodeGeneratorV3\\female_outer_profile.gcode"
    with open(file_path, "w") as file:
        file.write(gcode)
        print(f"G-Code saved to {file_path}")
