from .gate import Gate
from .vertex import Vertex
from .face import Face
from typing import List, Tuple



class Patch:
    def __init__(self, center_vertex: Vertex, faces: List[Face], mesh = None):
        self.center_vertex = center_vertex
        self.faces = faces
        self.mesh = mesh
        self.input_gate = Gate()

    # Patch related functions
    # Should we include a function that generates the frenet coordinates around the center vertex?
    def valence(self) -> int:
        return len(self.faces)
    
    def barycenter(self) -> Vertex:
        pass

    def local_coordinate_system(self):
        pass

    def oriented_vertices(self) -> List[Vertex]:
        return self.oriented_vertices(self.gate.edge[0])

    def oriented_vertices(self, fromV: Vertex) -> List[Vertex]:
        if self.gate.edge[0] != fromV and self.gate.edge[1] != fromV:
            return []
        
        remaining_faces = set(self.faces)
        remaining_faces.remove(self.gate.to_face())
        sequence = []
        current_vertex = fromV
        while len(remaining_faces) > 0:
            face = next((f for f in remaining_faces if current_vertex in f.vertices and self.center_vertex in f.vertices), None)
            if face is None:
                break # Error: still some faces left, but no more connected faces
            
            next_vertex = face.next_vertex((current_vertex, self.center_vertex))
            sequence.append(next_vertex)
            current_vertex = next_vertex
            remaining_faces.remove(face)
        
        return sequence

    def oriented_edges(self, fromV: Vertex) -> List[Tuple[Vertex, Vertex]]:
        if self.gate.edge[0] != fromV and self.gate.edge[1] != fromV:
            return []
        
        edge_sequence = []
        current_vertex = fromV
        for next_vertex in self.oriented_vertices(fromV):
            edge_sequence.append((current_vertex, next_vertex))
            current_vertex = next_vertex
        
        return edge_sequence

    # Mesh related functions
    def output_gates(self, fromV: Vertex) -> List[Gate]:
        if self.gate.edge[0] != fromV and self.gate.edge[1] != fromV:
            return []
        
        edge_sequence = self.iterate_from(fromV)
        output_gates = []
        for edge in edge_sequence:
            faces = self.mesh.get_connected_faces(edge)
            for face in faces:
                if self.center_vertex not in face.vertices:
                    next_vertex = face.next_vertex(edge)
                    output_gates.append(Gate(edge, next_vertex, self.mesh))
                    break

    # Internal functions
    def __hash__(self):
        return hash(self.center_vertex)