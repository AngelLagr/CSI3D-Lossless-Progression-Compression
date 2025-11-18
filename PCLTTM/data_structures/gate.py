from .vertex import Vertex
from typing import Tuple


class Gate:
    def __init__(self, edge: Tuple[Vertex, Vertex], front_vertex: Vertex, mesh=None):
        self.edge = edge  # (v_left, v_right)
        self.front_vertex = front_vertex
        self.mesh = mesh

    def to_face(self) -> "Face":
        from .face import Face
        return Face((self.edge[0], self.edge[1], self.front_vertex), self.mesh)

    def generate_patch(self) -> "Patch":
        if self.mesh is None:
            return None
        # Patch centered around the front vertex of this gate
        return self.mesh.get_patch(self.front_vertex)

    def __hash__(self):
        return hash((frozenset(self.edge), self.front_vertex))

    def __repr__(self):
        return f"Gate(edge={self.edge}, front_v={self.front_vertex})"
