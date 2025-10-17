from data_structures.vertex import Vertex
from typing import List



class Patch:
    def __init__(self, center_vertex: Vertex, faces: List[Vertex]):
        self.center_vertex = center_vertex
        self.faces: List[int] = []

    def valence(self) -> int:
        return len(self.faces)
