from .vertex import Vertex
from typing import Tuple, TYPE_CHECKING


class Gate:
    def __init__(self, edge: Tuple[Vertex, Vertex], front_vertex: Vertex, mesh = None):
        self.edge = edge  # (v_left, v_right)
        self.front_vertex = front_vertex
        self.mesh = mesh
    
    # Gate related functions
    # Should we include a function that generates the frenet coordinates towards the front vertex?
    def to_face(self) -> "Face":
        # local import to avoid circular import issues at module import time
        from .face import Face
        return Face([self.edge[0], self.edge[1], self.front_vertex], self.mesh)

    # Mesh related functions
    def generate_patch(self) -> "Patch":
        return self.mesh.get_patch(self) if self.mesh else None

    # Internal functions
    def __hash__(self):
        return hash((frozenset(self.edge), self.front_vertex))

    def __repr__(self):
        return f"Gate(edge={self.edge}, face={self.front_face_idx}, front_v={self.front_vertex_idx})"

