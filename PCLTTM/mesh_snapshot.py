from collections import deque
from typing import List
from PCLTTM.data_structures.vertex import Vertex
from obja_parser import ObjaParser

class MeshSnapshot:
    @staticmethod
    def difference(lhs: 'MeshSnapshot', rhs: 'MeshSnapshot') -> 'MeshSnapshot':
        diff = MeshSnapshot()
        # ...
        return diff


    def __init__(self):
        self.vertex_connections = dict() # Hash(Vertex) -> Set(Vertex)
        self.face_orientations = dict() # Hash(Face, Vertex) -> Next Vertex in the face 
        self.updates = deque() 

    def restore(self):
        pass

    def save(self):
        pass

    def apply(self, other: 'MeshSnapshot'):
        difference = MeshSnapshot.difference(self, other)
        # Apply the difference to self
        self.updates.append(difference)

    def negative(self) -> 'MeshSnapshot':
        neg = MeshSnapshot()
        # ...
        return neg

    def add_vertex(self, vertex: Vertex, edges: List[Vertex]):
        pass

    def remove_vertex(self, vertex: Vertex):
        pass

    def add_edge(self, v1: Vertex, v2: Vertex):
        pass

    def remove_edge(self, v1: Vertex, v2: Vertex):
        pass

    def save_to_obj(self, file_path: str):
        pass
