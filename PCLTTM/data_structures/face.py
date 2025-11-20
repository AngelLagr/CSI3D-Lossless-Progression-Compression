from .vertex import Vertex
from .constants import StateFlag
from typing import List, Tuple


class Face:
    def __init__(self, vertices: Tuple[Vertex, Vertex, Vertex], mesh=None):
        if vertices is None:
            print("Warning: Face created with None vertices")
            raise ValueError("Vertices must not be None")
        self.vertices = vertices  # (v1, v2, v3)
        self.mesh = mesh

    # Face related functions
    def edges(
        self,
    ) -> Tuple[Tuple[Vertex, Vertex], Tuple[Vertex, Vertex], Tuple[Vertex, Vertex]]:
        v1, v2, v3 = self.vertices
        return ((v1, v2), (v2, v3), (v3, v1))

    def next_vertex(self, edge: Tuple[Vertex, Vertex]) -> Vertex | None:
        if edge[0] not in self.vertices or edge[1] not in self.vertices:
            return None  # Invalid edge for this face

        return next(v for v in self.vertices if v != edge[0] and v != edge[1])

    def to_gate(self, direction_vertex: Vertex) -> "Gate | None":
        if direction_vertex not in self.vertices:
            return None  # Invalid direction vertex for this face

        v1, v2, v3 = self.vertices
        if direction_vertex == v1:
            edge = (v2, v3)
        elif direction_vertex == v2:
            edge = (v3, v1)
        else:
            edge = (v1, v2)

        # local import to avoid circular import issues at module import time
        from .gate import Gate
        return Gate(edge, direction_vertex, self.mesh)

    def contains(self, vertex: Vertex) -> bool:
        return vertex in self.vertices

    # Mesh related functions
    def state_flag(self) -> StateFlag:
        # NOTE: MeshTopology currently does NOT implement get_face_state.
        # This will only work if mesh is a type that defines that method.
        return self.mesh.get_face_state(self) if self.mesh else StateFlag.Free

    def output_gates(self, starting_edge: Tuple[Vertex, Vertex]) -> List["Gate"]:
        """
        For each boundary edge around the center vertex, find the face on
        the "outside" (the one that does *not* contain the center vertex)
        and create a Gate towards that outside vertex.

        This uses mesh.get_oriented_faces(edge), which should return (left_face, right_face).
        """
        if starting_edge is None or None in starting_edge:
            return []

        if starting_edge[0] not in self.vertices or starting_edge[1] not in self.vertices or self.mesh is None:
            return []

        # local import to avoid circular imports
        from .gate import Gate

        output_gates: List[Gate] = []

        next_vertex = self.next_vertex(starting_edge)

        #left_outward_face = next((
        #            f for f in self.mesh.get_oriented_faces((next_vertex, starting_edge[0]))
        #            if f != self
        #        ), None)
        #left_outward_vertex = left_outward_face.next_vertex((next_vertex, starting_edge[0])) if left_outward_face is not None else None
        #if left_outward_vertex is not None:
        #    output_gates.append(Gate((next_vertex, starting_edge[0]), left_outward_vertex, self.mesh))
        #else:
        #    print("Warning: oriented left face's outward vertex is the center vertex itself.")

        #right_outward_face = next((
        #            f for f in self.mesh.get_oriented_faces((starting_edge[1], next_vertex))
        #            if f != self
        #        ), None)
        #right_outward_vertex = right_outward_face.next_vertex((starting_edge[1], next_vertex)) if right_outward_face is not None else None
        #if left_outward_vertex is not None:
        #    output_gates.append(Gate((next_vertex, starting_edge[1]), right_outward_vertex, self.mesh))


        left_edge = (starting_edge[0], next_vertex)
        oriented_faces = self.mesh.get_oriented_faces(left_edge)
        if oriented_faces[0] is not None:
            output_gates.append(Gate(left_edge, oriented_faces[0].next_vertex(left_edge), self.mesh))

        right_edge = (next_vertex, starting_edge[1])
        oriented_faces = self.mesh.get_oriented_faces(right_edge)
        if oriented_faces[0] is not None:
            output_gates.append(Gate(right_edge, oriented_faces[0].next_vertex(right_edge), self.mesh))
        
        return output_gates

    # Internal functions
    def __lt__(self, other):
        return self.vertices < other.vertices

    def __hash__(self):
        # Order-independent hash
        return hash(frozenset(self.vertices))

    def __eq__(self, other):
        return isinstance(other, Face) and set(self.vertices) == set(other.vertices)

    def __repr__(self):
        return "(" + ", ".join([str(v) for v in self.vertices]) + ")"
