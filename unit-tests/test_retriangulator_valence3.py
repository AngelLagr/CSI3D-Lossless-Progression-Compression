import pytest
from PCLTTM.data_structures.face import Face
from PCLTTM.data_structures.vertex import Vertex
from PCLTTM.retriangulator import Retriangulator
from PCLTTM.mesh import MeshTopology
from PCLTTM.data_structures.gate import Gate
from PCLTTM.data_structures.constants import RetriangulationTag


def is_face_oriented_correctly(face: Face) -> bool:
    v1, v2, v3 = face.vertices
    print("normale" , face)
    u = (
        v2.position[0] - v1.position[0],
        v2.position[1] - v1.position[1],
        v2.position[2] - v1.position[2],
    )
    v = (
        v3.position[0] - v1.position[0],
        v3.position[1] - v1.position[1],
        v3.position[2] - v1.position[2],
    )
    normal = (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )
    return normal[2] > 0  


@pytest.mark.parametrize(
    "left_tag,right_tag",
    [
        (RetriangulationTag.Plus, RetriangulationTag.Minus),
        (RetriangulationTag.Minus, RetriangulationTag.Plus),
        (RetriangulationTag.Plus, RetriangulationTag.Plus),
        (RetriangulationTag.Minus, RetriangulationTag.Minus),
    ],
)
def test_retriangulate_valence3_orientation(left_tag, right_tag):
    mesh = MeshTopology()

    L = Vertex((0.0, 0.0, 0.0))
    R = Vertex((1.0, 0.0, 0.0))
    V1 = Vertex((0.0, 1.0, 0.0))
    C = Vertex((0.2, 0.2, 0.0))  # centre

    mesh.add_vertex(L)
    mesh.add_vertex(V1)
    mesh.add_vertex(R)
    mesh.add_vertex(C)

    mesh.add_edge(C, L)
    mesh.add_edge(C, V1)
    mesh.add_edge(C, R)

    # Bord
    mesh.add_edge(L, R)
    mesh.add_edge(R, V1)
    mesh.add_edge(V1, L)

    mesh.set_orientation((R,C),L)
    mesh.set_orientation((R,V1),C)
    mesh.set_orientation((C,V1),L)

    gate = Gate((L, R), C, mesh)
    patch_oriented = [L, R, V1]

    assert mesh.get_patch(C).surrounding_vertices((L,R)) == patch_oriented
    r = Retriangulator()

    for v in patch_oriented:
        r.retriangulation_tags[v] = RetriangulationTag.Default

    r.retriangulation_tags[L] = left_tag
    r.retriangulation_tags[R] = right_tag

    resultat = r.retriangulate(
        mesh=mesh,
        valence=3,
        current_gate=gate,
        patch_oriented_vertex=patch_oriented,
    )

    assert resultat is True

    assert C not in mesh.active_state.vertex_connections

    left_vert, right_vert = mesh.get_oriented_vertices((L, R))
    assert left_vert is V1, "L'orientation de l'arête (L,R) n'a pas le bon 3e sommet"

    visited = set()
    for v in mesh.get_vertices():
        for face in mesh.get_faces(v):
            if face is None:
                continue
            key = frozenset(face.vertices)
            if key in visited:
                continue
            visited.add(key)

            assert is_face_oriented_correctly(face), "Face orientation is incorrect"
