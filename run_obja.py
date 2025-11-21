import numpy as np
from PCLTTM import PCLTTM
import copy

# >>> AJOUTS IMPORTS POUR L'OBJA
from collections import deque
from typing import Dict, List, Tuple
from PCLTTM.data_structures.face import Face
from PCLTTM.data_structures.vertex import Vertex


# On definit une cle par face qui ne change pas si l'orientaion change
def face_key(face: Face) -> Tuple[Vertex, Vertex, Vertex]:
    return tuple(sorted(face.vertices, key=id))


def print_initial_model(mesh, output_file):
    # Collect vertices
    vertices = sorted(mesh.get_vertices())
    vertices_indices: Dict[Vertex, int] = {v: i + 1 for i, v in enumerate(vertices)}
    faces_indices: List[Tuple[Vertex, Vertex, Vertex], int] = []

    # ---- write vertices ----
    for v in vertices:
        x, y, z = v.position
        output_file.write(f"v {x} {y} {z}\n")

    # ---- collect unique faces preserving orientation ----
    # Use a mapping from frozenset(vertices) -> oriented tuple(vertices)
    # so we deduplicate faces while keeping the original vertex order

    for v in vertices:
        for face in mesh.get_faces(v):
            if face is None or face in faces_indices:
                print("Face to add already exists, skipping:", face)
                continue

            output_file.write(
                "f " + " ".join(str(vertices_indices[vtx]) for vtx in face.vertices) + "\n"
            )
            faces_indices.append(face)

    return vertices_indices, faces_indices


def main():
    """
    Runs the program on the model given as parameter.
    """
    np.seterr(invalid='raise')
    
    model = PCLTTM()
    model.parse_file('example/test_complete.obj')
    
    num_vertex = len(model.mesh.get_vertices()) if model.mesh is not None else 0
    iteration_compress = 0

    model_iter = copy.deepcopy(model)
    initial_gate = model_iter.mesh.get_random_gate()
    new_num_vertex = -1

    # Pour stocker les états successifs en mémoire
    steps = [copy.deepcopy(model_iter)]  # liste de PCLTTM après chaque compress()

    while new_num_vertex != num_vertex:
        
        iteration_compress += 1
        model_iter.compress(iteration_compress, initial_gate)
        model_iter.mesh.export_to_obj(f"compression_step_{iteration_compress}.obj")

        # état courant en mémoire
        steps.append(copy.deepcopy(model_iter))

        num_vertex = new_num_vertex
        new_num_vertex = len(model_iter.mesh.get_vertices())
        if new_num_vertex == 4:
            break
        model_iter = PCLTTM()
        model_iter.parse_file(f'compression_step_{iteration_compress}.obj')
        initial_gate = model_iter.mesh.get_random_gate()
        print(f"After iteration {iteration_compress}, number of vertices: {new_num_vertex}, old: {num_vertex}")
    
    print(f"After iteration {iteration_compress}, number of vertices: {new_num_vertex}, old: {num_vertex}")
    print("Compression complete.")

    # Génération de l'OBJA à partir des meshes en mémoire (steps), sans relire les fichiers
    if not steps:
        print("No compression steps recorded, OBJA not generated.")
        return

    with open('test_complete.obja', 'w') as output_file:
        # On considère que le dernier step est le plus compressé (comme avant)
        vertex_idx, face_idx = print_initial_model(steps[-1].mesh, output_file)
        print(f"Initial model: {len(vertex_idx)} vertices, {len(face_idx)} faces.")

        # On remonte les steps à l’envers pour simuler la décompression
        for i in reversed(range(1, len(steps))):
            # self = état plus compressé, previous = état plus détaillé
            print(f"Decompression step {i}:")
            compression_diffs = steps[i].mesh.active_state.compression_difference(steps[i - 1].mesh.active_state)

            vertex_diffs = compression_diffs[0]
            edge_diffs = compression_diffs[1]

            for edge, left_right in edge_diffs.items():  # edges to remove
                left_face = Face((edge[0], edge[1], left_right[0]))
                right_face = Face((edge[1], edge[0], left_right[1]))
                if left_face in face_idx:
                    left_face_idx = face_idx.index(left_face)
                    output_file.write(f"df {left_face_idx + 1}\n")
                    face_idx.remove(left_face)
                    print("Deleted left face:", left_face)
                else:
                    print("Left face to delete not found:", left_face)

                if right_face in face_idx:
                    right_face_idx = face_idx.index(right_face)
                    output_file.write(f"df {right_face_idx + 1}\n")
                    face_idx.remove(right_face)
                    print("Deleted right face:", right_face)
                else:
                    print("Right face to delete not found:", right_face)

            vertex_to_add = sorted(vertex_diffs.keys())
            for v in vertex_to_add:
                if v not in vertex_idx:
                    output_file.write(
                        f"v {v.position[0]} {v.position[1]} {v.position[2]}\n")
                    vertex_idx[v] = len(vertex_idx) + 1

                patch = steps[i - 1].mesh.get_patch(v)
                for f in patch.faces:
                    if f in face_idx:
                        print("Face to add already exists, skipping:", f)
                        continue  # face already exists
                    else:
                        print("Adding face:", f)
                    
                    vertices_in_face = []
                    for v_face in f.vertices:
                        if v_face not in vertex_idx:
                            output_file.write(f"v {v_face.position[0]} {v_face.position[1]} {v_face.position[2]}\n")
                            vertex_idx[v_face] = len(vertex_idx) + 1
                        vertices_in_face.append(str(vertex_idx[v_face]))
                    
                    output_file.write("f " + " ".join(vertices_in_face) + "\n")
                    face_idx.append(f)
                        

    print("Done.")


if __name__ == '__main__':
    main()
