import math
from typing import List, Tuple

Vertex = Tuple[int, int, int]
Face = List[int]

# WARNING THIS HAS MANIFOLD VIOLATIONS


def generate_three_layer_sphere_int(n: int,
                                    height: int = 20,
                                    radius: int = 10,
                                    center: Vertex = (0, 0, 0)) -> Tuple[List[Vertex], List[Face]]:
    """
    Generates a 3-layer crude sphere:
      - top pole
      - upper ring (reduced radius)
      - middle ring (full radius)
      - lower ring (reduced radius)
      - bottom pole

    Fully triangulated, all integer vertices.
    """

    if n < 3:
        raise ValueError("n must be >= 3")

    cx, cy, cz = center

    # Vertical positions
    top_z    = cz + height // 2
    upper_z  = cz + height // 6
    middle_z = cz
    lower_z  = cz - height // 6
    bot_z    = cz - height // 2

    # Radii
    r_upper  = radius * 0.6   # slightly smaller
    r_middle = radius         # full radius
    r_lower  = radius * 0.6   # slightly smaller

    vertices: List[Vertex] = []
    faces: List[Face] = []

    # --- Poles ---
    top_index = len(vertices)
    vertices.append((cx, cy, top_z))

    # --- Rings ---
    upper_ring = []
    middle_ring = []
    lower_ring = []

    for i in range(n):
        theta = 2.0 * math.pi * i / n

        # Upper ring
        x = cx + int(round(r_upper * math.cos(theta)))
        y = cy + int(round(r_upper * math.sin(theta)))
        upper_ring.append(len(vertices))
        vertices.append((x, y, upper_z))

        # Middle ring (full width)
        x = cx + int(round(r_middle * math.cos(theta)))
        y = cy + int(round(r_middle * math.sin(theta)))
        middle_ring.append(len(vertices))
        vertices.append((x, y, middle_z))

        # Lower ring
        x = cx + int(round(r_lower * math.cos(theta)))
        y = cy + int(round(r_lower * math.sin(theta)))
        lower_ring.append(len(vertices))
        vertices.append((x, y, lower_z))

    # --- Bottom pole ---
    bottom_index = len(vertices)
    vertices.append((cx, cy, bot_z))

    # --------------------
    # Construct faces
    # --------------------

    # Top pole → upper ring
    for i in range(n):
        a = upper_ring[i]
        b = upper_ring[(i + 1) % n]
        faces.append([top_index, a, b])

    # Upper ring → middle ring
    for i in range(n):
        u1 = upper_ring[i]
        u2 = upper_ring[(i + 1) % n]
        m1 = middle_ring[i]
        m2 = middle_ring[(i + 1) % n]
        faces.append([u1, u2, m2])
        faces.append([u1, m2, m1])

    # Middle ring → lower ring
    for i in range(n):
        m1 = middle_ring[i]
        m2 = middle_ring[(i + 1) % n]
        l1 = lower_ring[i]
        l2 = lower_ring[(i + 1) % n]
        faces.append([m1, m2, l2])
        faces.append([m1, l2, l1])

    # Lower ring → bottom pole
    for i in range(n):
        a = lower_ring[i]
        b = lower_ring[(i + 1) % n]
        faces.append([bottom_index, b, a])

    return vertices, faces



def write_obj_file(filename: str, vertices: List[Vertex], faces: List[Face]) -> None:
    with open(filename, "w") as f:
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for face in faces:
            f.write("f " + " ".join(str(i + 1) for i in face) + "\n")
    print(f"✔ Written:", filename)


if __name__ == "__main__":
    verts, faces = generate_three_layer_sphere_int(n=12, height=20, radius=10)
    write_obj_file("crude_sphere.obj", verts, faces)
