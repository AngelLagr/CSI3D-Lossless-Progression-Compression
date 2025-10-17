from data_structures.vertex import Vertex
from typing import Tuple


class Gate:
    def __init__(self, edge: Tuple[Vertex, Vertex], front_vertex: Vertex):
        self.edge = edge  # (v_left, v_right)
        self.front_vertex = front_vertex
    
    def __repr__(self):
        return f"Gate(edge={self.edge}, face={self.front_face_idx}, front_v={self.front_vertex_idx})"

