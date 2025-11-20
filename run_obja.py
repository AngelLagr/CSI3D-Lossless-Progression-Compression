from copy import deepcopy
from typing import Dict
import numpy as np
from PCLTTM import PCLTTM
from PCLTTM.data_structures.face import Face
from PCLTTM.data_structures.vertex import Vertex

def main():
    """
    Runs the program on the model given as parameter.
    """
    np.seterr(invalid='raise')
    model = PCLTTM()
    model.parse_file('example/crude_sphere_6.obj')

    number_of_vertices = 0
    while number_of_vertices != len(model.mesh.vertices):
        model.compress()
        number_of_vertices = len(model.mesh.vertices)

    vertex_idx: Dict[Vertex, int] = {}
    
    face_idx: Dict[Face, int] = {}
    # When you write "f x y z" in an OBJ file, you need: face_idx[Face((v_x, v_y, v_z))] = index_in_file

    last_state = deepcopy(model.mesh.active_state)
    while model.mesh.rollback():
        diff = model.mesh.active_state.difference(last_state)

        face_to_remove = set()
        for edge, left_right in diff[1].items(): # edges to remove
            face_to_remove.add((edge[0], edge[1], left_right[0]))
            face_to_remove.add((edge[1], edge[0], left_right[1]))

        available_face_to_update = deque()
        for face in face_to_remove:
            available_face_to_update.append(face)
`
        vertex_to_add = sorted(diff[0].keys())`
        for v in vertex_to_add: # vertices to update
            print("v ", v.position[0], v.position[1], v.position[2])
            vertex_idx[v] = len(vertex_idx) + 1

            patch = model.mesh.get_patch[v]
            for f in patch.faces:
                if available_face_to_update:
                    print("ef ", face_idx[available_face_to_update.pop()], "v1 v2 v3")
                else:
                    print("f v1 v2 v3")
        

        last_state = deepcopy(model.mesh.active_state)


if __name__ == '__main__':
    main()