from collections import deque
from copy import deepcopy
from typing import Dict
import numpy as np
from PCLTTM import PCLTTM
from PCLTTM.data_structures.face import Face
from PCLTTM.data_structures.vertex import Vertex

def print_initial_model(steps):
    # Collect vertices
    vertices = sorted(steps.get_vertices())
    vertices_indices = {v: i + 1 for i, v in enumerate(vertices)}
    faces_indices = {}
    # ---- write vertices ----
    for v in vertices:
        x, y, z = v.position
        print(f"v {x} {y} {z}")

    # ---- collect unique faces preserving orientation ----
    # Use a mapping from frozenset(vertices) -> oriented tuple(vertices)
    # so we deduplicate faces while keeping the original vertex order

    for v in vertices:
        for face in steps.get_faces(v):
            if face is None or face in faces_indices:
                continue

            print("f " + " ".join(str(vertices_indices[v]) for v in face.vertices))
            faces_indices[face] = len(faces_indices) + 1
    
    return vertices_indices, faces_indices

def main():
    """
    Runs the program on the model given as parameter.
    """
    np.seterr(invalid='raise')
    model = PCLTTM()
    model.parse_file('example/crude_sphere_6.obj')

    steps = []
    for i in range(11):
        model_step = PCLTTM()
        model_step.parse_file(f'compression_step_{i+1}.obj')
        steps.append(model_step)
    

    vertex_idx, face_idx = print_initial_model(steps[-1].mesh)

    for i in reversed(range(1, len(steps))):
        #print(f"Compression step {i}:")

        compression_diffs = steps[i].mesh.active_state.compression_difference(steps[i - 1].mesh.active_state)
        #print("Vertices added/updated:", compression_diffs[0])
        #print("Edges removed:", compression_diffs[1])
        #print()

        face_to_remove = set()
        for edge, left_right in compression_diffs[1].items(): # edges to remove
            face_to_remove.add(Face((edge[0], edge[1], left_right[0])))
            face_to_remove.add(Face((edge[1], edge[0], left_right[1])))

        available_face_to_update = deque()
        for face in face_to_remove:
            available_face_to_update.append(face)

        vertex_to_add = sorted(compression_diffs[0].keys())
        for v in vertex_to_add: # vertices to update
            if v not in vertex_idx:
                print("v", v.position[0], v.position[1], v.position[2])
                vertex_idx[v] = len(vertex_idx) + 1

            patch = steps[i - 1].mesh.get_patch(v)
            for f in patch.faces:
                vertices_in_face = []
                for v in f.vertices:
                    if v not in vertex_idx:
                        print("v", v.position[0], v.position[1], v.position[2])
                        vertex_idx[v] = len(vertex_idx) + 1
                    vertices_in_face.append(str(vertex_idx[v]))
                        
                if available_face_to_update:
                    reused_face = available_face_to_update.pop()
                    reused_index = face_idx[reused_face]
                    print(f"ef {reused_index}", " ".join(vertices_in_face))
                    del face_idx[reused_face]
                    face_idx[f] = reused_index
                else:
                    print("f", " ".join(vertices_in_face)) 
                    face_idx[f] = len(face_idx) + 1

    print("Done.")


def temp(model):
    number_of_vertices = 0
    while number_of_vertices != len(model.mesh.vertices):
        model.compress()
        number_of_vertices = len(model.mesh.vertices)

    vertex_idx: Dict[Vertex, int] = {}
    
    face_idx: Dict[Face, int] = {}
    # When you writ "f x y z" in an OBJ file, you need: face_idx[Face((v_x, v_y, v_z))] = index_in_file

#     last_state = deepcopy(model.mesh.active_state)
#     while model.mesh.rollback():
#         diff = model.mesh.active_state.compression_difference(last_state)

#         face_to_remove = set()
#         for edge, left_right in diff[1].items(): # edges to remove
#             face_to_remove.add((edge[0], edge[1], left_right[0]))
#             face_to_remove.add((edge[1], edge[0], left_right[1]))

#         available_face_to_update = deque()
#         for face in face_to_remove:
#             available_face_to_update.append(face)
# `
#         vertex_to_add = sorted(diff[0].keys())`
#         for v in vertex_to_add: # vertices to update
#             print("v ", v.position[0], v.position[1], v.position[2])
#             vertex_idx[v] = len(vertex_idx) + 1

#             patch = model.mesh.get_patch[v]
#             for f in patch.faces:
#                 if available_face_to_update:
#                     print("ef ", face_idx[available_face_to_update.pop()], "v1 v2 v3")
#                 else:
#                     print("f v1 v2 v3")
        

#         last_state = deepcopy(model.mesh.active_state)


if __name__ == '__main__':
    main()