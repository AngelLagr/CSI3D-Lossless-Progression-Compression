from vertex import Vertex
from face import Face
from typing import List



class Patch:
    def __init__(self, center_vertex: Vertex, faces: List[Face], mesh = None):
        self.center_vertex = center_vertex
        self.faces = faces
        self.mesh = mesh

    # Patch related functions
    # Should we include a function that generates the frenet coordinates around the center vertex?
    def valence(self) -> int:
        return len(self.faces)
    
    def barycenter(self) -> Vertex:
        pass

    # Mesh related functions

    # Internal functions
    def __hash__(self):
        return hash(self.center_vertex)