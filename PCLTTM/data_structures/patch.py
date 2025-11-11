from .vertex import Vertex
from typing import List, Tuple



class Patch:
    def __init__(self, center_vertex: Vertex, faces: List["Face"], mesh = None):
        self.center_vertex = center_vertex
        self.faces = faces
        self.mesh = mesh

    # Patch related functions
    
    def valence(self) -> int:
        return len(self.faces)
    
    def barycenter(self) -> Vertex:
        pass

    def local_coordinate_system(self):
        pass

    def is_oriented(self):
        return self.input_gate is not None

    def surrounding_vertices(self, starting_edge: Tuple[Vertex, Vertex]) -> List[Vertex]:
        if None in starting_edge:
            return []
        
        # local import to avoid circular import issues at module import time
        from .face import Face
        
        remaining_faces = set(self.faces)
        current_face = Face((starting_edge[0], starting_edge[1], self.center_vertex), self.mesh)
        key = hash(current_face)
        remaining_faces.discard(key)
        sequence = []
        current_vertex = starting_edge[0]
        while len(remaining_faces) > 0:
            face = next((f for f in remaining_faces if current_vertex in f.vertices and self.center_vertex in f.vertices), None)
            if face is None:
                break # Error: still some faces left, but no more connected faces
            
            next_vertex = face.next_vertex((current_vertex, self.center_vertex))
            sequence.append(next_vertex)
            current_vertex = next_vertex
            remaining_faces.remove(face)
        
        return sequence

    def surrounding_edges(self, starting_edge: Tuple[Vertex, Vertex]) -> List[Tuple[Vertex, Vertex]]:
        if None in starting_edge:
            return []
        
        edge_sequence = []
        current_vertex = starting_edge[0]
        for next_vertex in self.surrounding_vertices(starting_edge):
            edge_sequence.append((current_vertex, next_vertex))
            current_vertex = next_vertex
        
        return edge_sequence

    # Mesh related functions
    def output_gates(self, starting_edge: Tuple[Vertex, Vertex]) -> List["Gate"]:
        if None in starting_edge:
            return []
        
        # local import to avoid circular import issues at module import time
        from .gate import Gate
        
        output_gates = []
        for edge in self.surrounding_edges(starting_edge):
            faces = self.mesh.get_oriented_faces(edge)
            for face in faces:
                if self.center_vertex not in face.vertices:
                    next_vertex = face.next_vertex(edge)
                    output_gates.append(Gate(edge, next_vertex, self.mesh))
                    break
        
        return output_gates

    # Internal functions
    def __hash__(self):
        return hash(self.center_vertex)