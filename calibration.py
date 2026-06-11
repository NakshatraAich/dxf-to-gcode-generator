import random
import matplotlib.pyplot as plt
from math import sqrt
import ezdxf

def generate_points(size):
    points = []

    start = (0, 0)
    end = size

    for i in range(0, size[0]+1, 6):
        for j in range(0, size[1]+1, 6):
            coord = (i, j)
            points.append(coord)
    
    return points

def generate_points(StartX, StartY , EndX, EndY):

    points=[]

    for y in range(StartY, EndY+1, 20):
        for x in range(StartX, EndX+1, 20):
            points.append((x,y))
    
    return points

def spiral_pattern(points):
    size = int(sqrt(len(points)))  # Grid is size x size
    assert size * size == len(points), "Grid must be square"

    # Convert flat list of points to 2D matrix
    grid = [[None for _ in range(size)] for _ in range(size)]
    for point in points:
        x, y = point
        grid[y // 6][x // 6] = point  # Assuming step is 4 units

    # Start from center
    x = y = size // 2
    spiral = [grid[y][x]]

    dx = [1, 0, -1, 0]  # right, down, left, up
    dy = [0, 1, 0, -1]
    step = 1

    while len(spiral) < len(points):
        for direction in range(4):
            for _ in range(step):
                x += dx[direction]
                y += dy[direction]
                if 0 <= x < size and 0 <= y < size:
                    spiral.append(grid[y][x])
                    if len(spiral) == len(points):
                        break
            if direction == 1 or direction == 3:
                step += 1  # Increase step every two directions

    return spiral

def create_calibration_gcode(points):
    gcode = []
    gcode.append("G1 Z50 ; Raise for clearance")
    gcode.append("G92 E0 ; Raise for clearance")

    extrusion = 48
    dispense_z = 2
    safe_z = 60

    for i in points:
        gcode.append(f"G1 X{i[0]} Y{i[1]} F6000 ; Move to X:{i[0]} Y:{i[1]}")
        # gcode.append(f"G1 X100 Y100 F6000 ;")
        # gcode.append("G4 P5000; Pause")
        gcode.append(f"G1 Z{dispense_z} F6000 ; Lower the extruder")
        gcode.append(f"G1 E{extrusion} F2000")
        gcode.append(f"G1 E{extrusion-48} F2000")
        gcode.append(f"G4 P500;")
        gcode.append(f"G1 Z{safe_z} F6000 ; Lift the extruder")
        extrusion += 24

    return gcode

# points = generate_points(size = (48, 48))
# points = spiral_pattern(points)
# points = [(i + 100, j + 100) for i, j in points]

points = generate_points(120, 100, 160, 200)
gcode = create_calibration_gcode(points)

file_path = "C:\\Users\\mount\\Downloads\\GCodeGeneratorV3\\calibration.gcode"
with open(file_path, "w") as file:
    file.write("\n".join(gcode))
    print(f"G-Code saved to {file_path}")

# Plot the calibration path in visiting order
x_coords = [point[0] for point in points]
y_coords = [point[1] for point in points]

# Plotting
plt.figure(figsize=(6, 6))
plt.plot(x_coords, y_coords, color='blue', marker='o', linestyle='-')  # Lines between points
plt.title('Connected Calibration Path')
plt.xlabel('X Coordinate')
plt.ylabel('Y Coordinate')
plt.grid(True)
plt.axis('equal')
plt.show()

