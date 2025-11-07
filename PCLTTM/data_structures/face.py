from PCLTTM.data_structures.gate import Gate
from data_structures.vertex import Vertex
from constants import StateFlag
from typing import Tuple


class Face:
    def __init__(self, vertices: Tuple[Vertex, Vertex, Vertex], mesh = None):
        self.vertices = vertices  # (v1, v2, v3)
        self.mesh = mesh

    # Face related functions
    def edges(self) -> Tuple[Tuple[Vertex, Vertex], Tuple[Vertex, Vertex], Tuple[Vertex, Vertex]]:
        v1, v2, v3 = self.vertices
        return ((v1, v2), (v2, v3), (v3, v1))

    def vertices(self):
        return self.vertices
    
    def next_vertex(self, edge: Tuple[Vertex, Vertex]) -> Vertex:
        if edge[0] not in self.vertices or edge[1] not in self.vertices:
            return None # Invalid edge for this face
        
        return next(v for v in self.vertices if v != edge[0] and v != edge[1])
    
    def to_gate(self, direction_vertex: Vertex) -> Gate:
        if direction_vertex not in self.vertices:
            return None  # Invalid direction vertex for this face
        
        v1, v2, v3 = self.vertices
        if direction_vertex == v1:
            edge = (v2, v3)
        elif direction_vertex == v2:
            edge = (v3, v1)
        else:
            edge = (v1, v2)
        
        return Gate(edge, direction_vertex, self.mesh)

    # Mesh related functions
    def state_flag(self) -> StateFlag:
        return self.mesh.get_face_state(self) if self.mesh else StateFlag.Free
    

    # Internal functions
    def __hash__(self):
        return hash(frozenset(self.vertices))