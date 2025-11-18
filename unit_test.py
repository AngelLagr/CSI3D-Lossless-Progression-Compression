from typing import List
from PCLTTM import PCLTTM
from PCLTTM.data_structures.face import Face
from PCLTTM.data_structures.vertex import Vertex
import random

def test_vertex_ordering():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((1, 3, 4))
    v3 = Vertex((2, 1, 3))

    s1 = sorted({v1, v2, v3})
    s2 = sorted([v3, v2, v1])
    return s1 == s2

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

    return k1 == k2 and k2 == k3

def test_vertex_in_set():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((2, 2, 3))
    v3 = Vertex((1, 2, 3))

    s = set()
    s.add(v1)
    s.add(v2)
    s.add(v3)

    return len(s) == 2

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

    return len(s) == 2

def test_sampled_orientation(obj_file: str, sample_size: int) -> bool:
    # -------------------------------
    # 1. Load model
    # -------------------------------
    model = PCLTTM()
    model.parse_file(obj_file)

    # -------------------------------
    # 2. Read OBJ vertices & faces
    # -------------------------------
    vertices = []
    faces = []

    with open(obj_file, "r") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.split()
                x, y, z = map(float, parts[1:4])
                vertices.append((x, y, z))
            elif line.startswith("f "):
                parts = line.split()[1:]
                face_indices = [int(p.split(" ")[0]) for p in parts]
                faces.append(face_indices)

    # -------------------------------
    # 3. Sample some faces
    # -------------------------------
    sample_count = min(sample_size, len(faces))
    print(f"Sampling {sample_count} faces out of {len(faces)} total faces.")
    sampled_faces = random.sample(faces, sample_count)
    sampled_structured_faces: List[Face] = []

    for face in sampled_faces:
        face_vertices = []
        for idx in face:
            v = vertices[idx - 1]  # OBJ indices start at 1
            vertex_obj = Vertex((v[0], v[1], v[2]))
            face_vertices.append(vertex_obj)
        sampled_structured_faces.append(Face(tuple(face_vertices)))

    # -------------------------------
    # 4. Check orientation per face
    # -------------------------------
    for face in sampled_structured_faces:
        #print("Testing face:", face)

        # Iterate edges of the face: (v_from, v_to) -> third vertex
        n = len(face.vertices)
        for i in range(n):
            v_from = face.vertices[i]
            v_to = face.vertices[(i+1) % n]
            v_third_actual = face.vertices[(i+2) % n]

            # Model stores: edge -> (left_vertex, right_vertex)
            edge_key = (v_from, v_to)
            result = model.mesh.get_oriented_vertices(edge_key)

            # Check if left vertex matches the third vertex in the OBJ face
            if result[0] != v_third_actual:
                print(f"Orientation mismatch on face {face}: \n\tedge {edge_key}, \n\texpected {v_third_actual}, \n\tgot {result}")
                return False

    # All sampled faces passed orientation test
    return True

def test_vertices_connections(obj_file: str) -> bool:
    # -------------------------------
    # 1. Load model
    # -------------------------------
    model = PCLTTM()
    model.parse_file(obj_file)

    # -------------------------------
    # 2. Read OBJ vertices & faces
    # -------------------------------
    vertices = []
    connexions = dict()
    
    with open(obj_file, "r") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.split()
                x, y, z = map(float, parts[1:4])
                vertices.append(Vertex((x, y, z)))
            elif line.startswith("f "):
                parts = line.split()[1:]
                face_indices = [int(p.split(" ")[0]) for p in parts]
                for v_idx in face_indices:
                    vertex = vertices[v_idx - 1]
                    if vertex not in connexions:
                        connexions[vertex] = set()
                    for other_idx in face_indices:
                        if other_idx != v_idx:
                            connexions[vertex].add(vertices[other_idx - 1])
    
    difference_found = set(vertices).difference(model.mesh.active_state.vertex_connections.keys())
    if difference_found != set():
        print("Vertices missing in mesh connections:", difference_found)
        return False

    # -------------------------------
    # 3. Verify connections
    # -------------------------------
    has_found_difference = False
    for vertex, connexions in connexions.items():
        model_connexions = model.mesh.active_state.vertex_connections.get(vertex, set())
        difference = connexions.difference(model_connexions)
        if difference != set():
            print(f"Missing connections for vertex {vertex}: {difference}")
            has_found_difference = True

    return not has_found_difference

def test_parser(obj_file: str) -> bool:
    is_successful = True
    is_successful = test_vertices_connections(obj_file)
    is_successful = is_successful and test_sampled_orientation(obj_file, 10000000) # large number to test all faces
    return is_successful

def main():
    print("Vertex ordering: ", test_vertex_ordering())
    print("Face hashing: ", test_face_hashing())
    print("Vertex in set: ", test_vertex_in_set())
    print("Face in set: ", test_face_in_set())
    #print("Vertices connections test (crude_sphere.obj): ", test_vertices_connections('example/fixed_crude_sphere.obj'))
    #print("Orientation test (crude_sphere.obj): ", test_sampled_orientation('example/fixed_crude_sphere.obj', 10))
    print("Test parser (crude_sphere.obj): ", test_parser('example/crude_sphere.obj'))



if __name__ == '__main__':
    main()