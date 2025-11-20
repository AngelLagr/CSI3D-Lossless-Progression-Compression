from typing import List
import random

from PCLTTM import PCLTTM
from PCLTTM.data_structures.face import Face
from PCLTTM.data_structures.vertex import Vertex

OBJ_FILE = "example/crude_sphere_12.obj"


# ---------------------------------------------------------------------------
# Tests de base : Vertex / Face / hashing / sets
# ---------------------------------------------------------------------------

def test_vertex_ordering():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((1, 3, 4))
    v3 = Vertex((2, 1, 3))

    s1 = sorted({v1, v2, v3})
    s2 = sorted([v3, v2, v1])

    assert s1 == s2


def test_face_hashing():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((1, 3, 4))
    v3 = Vertex((2, 1, 3))

    f1 = Face((v1, v2, v3))
    f2 = Face((v3, v2, v1))
    f3 = Face((v2, v1, v3))

    k1 = hash(f1)
    k2 = hash(f2)
    k3 = hash(f3)

    assert k1 == k2 == k3


def test_vertex_in_set():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((2, 2, 3))
    v3 = Vertex((1, 2, 3))

    s = set()
    s.add(v1)
    s.add(v2)
    s.add(v3)

    assert len(s) == 2


def test_face_in_set():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((1, 3, 4))
    v3 = Vertex((2, 1, 3))
    v4 = Vertex((4, 3, 1))

    f1 = Face((v1, v2, v3))
    f2 = Face((v2, v1, v4))
    f3 = Face((v3, v2, v1))
    f4 = Face((v2, v1, v3))

    s = set()
    s.add(f1)
    s.add(f2)
    s.add(f3)
    s.add(f4)

    assert len(s) == 2


# ---------------------------------------------------------------------------
# Tests parser + mesh : connexions and orientations
# ---------------------------------------------------------------------------

def test_sampled_orientation():
    """
    Vérifie que pour un sous-ensemble de faces de l'OBJ, l’orientation
    stockée dans model.mesh correspond bien à l'ordre des sommets dans le .obj.
    """
    obj_file = OBJ_FILE
    sample_size = 200

    # 1. Load model
    model = PCLTTM()
    model.parse_file(obj_file)

    # 2. Read OBJ vertices & faces
    vertices: List[tuple[float, float, float]] = []
    faces: List[list[int]] = []

    with open(obj_file, "r") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.split()
                x, y, z = map(float, parts[1:4])
                vertices.append((x, y, z))
            elif line.startswith("f "):
                parts = line.split()[1:]
                # gestion simple du format "i" ou "i/..."
                face_indices = [int(p.split("/")[0]) for p in parts]
                faces.append(face_indices)

    assert len(vertices) > 0
    assert len(faces) > 0

    # 3. Sample some faces
    sample_count = min(sample_size, len(faces))  
    print(f"Sampling {sample_count} faces out of {len(faces)} total faces.")
    sampled_faces = random.sample(faces, sample_count)
    sampled_structured_faces: List[Face] = []

    for face in sampled_faces:
        face_vertices = []
        for idx in face:
            x, y, z = vertices[idx - 1]  # OBJ indices start at 1
            vertex_obj = Vertex((x, y, z))
            face_vertices.append(vertex_obj)
        sampled_structured_faces.append(Face(tuple(face_vertices)))

    # 4. Check orientation per face
    for face in sampled_structured_faces:
        n = len(face.vertices)
        for i in range(n):
            v_from = face.vertices[i]
            v_to = face.vertices[(i + 1) % n]
            v_third_actual = face.vertices[(i + 2) % n]

            edge_key = (v_from, v_to)
            left_vertex, right_vertex = model.mesh.get_oriented_vertices(edge_key)

            # Check if left vertex matches the third vertex in the OBJ face
            assert left_vertex == v_third_actual, (
                f"Orientation mismatch on face {face}: "
                f"edge {edge_key}, expected {v_third_actual}, got {left_vertex, right_vertex}"
            )


def test_vertices_connections():
    """
    Vérifie que les connexions dans le mesh reconstruit correspondent
    aux adjacences des faces du .obj.
    """
    obj_file = OBJ_FILE

    model = PCLTTM()
    model.parse_file(obj_file)

    vertices: List[Vertex] = []
    connexions: dict[Vertex, set[Vertex]] = {}

    with open(obj_file, "r") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.split()
                x, y, z = map(float, parts[1:4])
                vertices.append(Vertex((x, y, z)))
            elif line.startswith("f "):
                parts = line.split()[1:]
                face_indices = [int(p.split("/")[0]) for p in parts]
                for v_idx in face_indices:
                    vertex = vertices[v_idx - 1]
                    if vertex not in connexions:
                        connexions[vertex] = set()
                    for other_idx in face_indices:
                        if other_idx != v_idx:
                            connexions[vertex].add(vertices[other_idx - 1])

    difference_found = set(vertices).difference(
        model.mesh.active_state.vertex_connections.keys()
    )
    assert difference_found == set(), f"Vertices missing in mesh connections: {difference_found}"

    # Verify connections
    for vertex, expected_conns in connexions.items():
        model_conns = model.mesh.active_state.vertex_connections.get(vertex, set())
        difference = expected_conns.difference(model_conns)
        assert difference == set(), f"Missing connections for vertex {vertex}: {difference}"


# ---------------------------------------------------------------------------
# Test de retriangulation global 
# ---------------------------------------------------------------------------

def test_retriangulation():
    from PCLTTM.data_structures.constants import StateFlag, RetriangulationTag

    model = PCLTTM()
    model.parse_file("./example/test_complete.obj")

    # Accès à la méthode "privée" via name mangling Python
    initial_gate = model._PCLTTM__initial_gate_for_test()

    assert initial_gate is not None, "Could not find an initial gate in the mesh."

    # Tag the two vertices of the initial gate
    v_plus, v_minus = initial_gate.edge
    model.retriangulator.retriangulation_tags[v_plus] = RetriangulationTag.Plus
    model.retriangulator.retriangulation_tags[v_minus] = RetriangulationTag.Minus

    left_vertex, right_vertex = initial_gate.edge
    center_vertex = initial_gate.front_vertex

    vertex_state = model.state_flags.get(center_vertex, StateFlag.Free)
    # valence is taken from the mesh topology
    valence = center_vertex.valence()

    print(
        valence, "valence", center_vertex,
        "state:", vertex_state, left_vertex, right_vertex
    )

    can_remove = model.mesh.can_remove_vertex(center_vertex)
    assert can_remove is True, "Center vertex should be removable"

    # Patch + retriangulation
    patch = model.mesh.get_patch(center_vertex)
    assert patch is not None and patch.valence() > 0, "Patch should not be null or empty in this test."

    out_gates = patch.output_gates(initial_gate.edge)
    print(len(out_gates), "gates in the patch")

    patch_vertices = patch.surrounding_vertices(initial_gate.edge)

    model.retriangulator.retriangulate(
        model.mesh, valence, initial_gate, patch_vertices
    )

    expected_vertex_count = 14
    actual_vertex_count = len(model.mesh.active_state.vertex_connections)
    assert actual_vertex_count == expected_vertex_count, (
        f"Expected {expected_vertex_count} vertices, got {actual_vertex_count}"
    )
