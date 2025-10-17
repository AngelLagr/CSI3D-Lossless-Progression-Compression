from data_structures.vertex import Vertex
from constants import StateFlag
from typing import Tuple


class Face:
    def __init__(self, vertices: Tuple[Vertex, Vertex, Vertex]):
        self.vertices = vertices  # (v1, v2, v3)
        self.state = StateFlag.Free

    def edges(self) -> Tuple[Tuple[Vertex, Vertex], Tuple[Vertex, Vertex], Tuple[Vertex, Vertex]]:
        v1, v2, v3 = self.vertices
        return ((v1, v2), (v2, v3), (v3, v1))
    
    def vertices(self):
        return self.vertices
    
    def __hash__(self):
        return hash(self.vertices)