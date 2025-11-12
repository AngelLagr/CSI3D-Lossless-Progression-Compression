from collections import deque
from copy import deepcopy
import random
from typing import List, Optional, Set, Tuple
from .data_structures import Vertex, Face, Gate, Patch
from . import constants
from .obja_parser import ObjaReader, ObjaWriter

# ============================================================================
# MESH TOPOLOGY HELPERS
# ============================================================================

"""
    Manages mesh topology information: valences, adjacency, neighborhoods.
    
    TODO: Handle normal orientation and faces' vertices order.
"""
class MeshTopology:
    class State:
        def __init__(self):
            self.vertex_connections = dict() # Hash(Vertex) -> Set(Vertex)
            self.orientations = dict() # Hash(Edge: [Vertex_from, Vertex_to]) -> (3e Vertex de la face de gauche [from->to], 3e Vertex de la face de droite [to->from]) 
        
        # self has priority over other on orientations conflict
        def difference(self, other):
            diff = MeshTopology.State()
            different_vertex = set(self.vertex_connections.keys()).difference(set(other.vertex_connections.keys()))
            for fromV in different_vertex:
                diff.vertex_connections[fromV] = deepcopy(self.vertex_connections[fromV])
                for toV in self.vertex_connections[fromV]:
                    if toV not in diff.vertex_connections:
                        diff.vertex_connections[toV] = set()

                    diff.vertex_connections[toV].add(fromV)
                    diff.orientations[(fromV, toV)] = self.orientations[(fromV, toV)]
                    diff.orientations[(toV, fromV)] = self.orientations[(toV, fromV)]

            # repeat on the other side
            different_vertex = set(other.vertex_connections.keys()).difference(set(self.vertex_connections.keys()))
            for fromV in different_vertex:
                diff.vertex_connections[fromV] = other.vertex_connections[fromV]
                for toV in other.vertex_connections[fromV]:
                    if toV not in diff.vertex_connections:
                        diff.vertex_connections[toV] = set()
                    
                    diff.vertex_connections[toV].add(fromV)
                    if (fromV, toV) not in diff.orientations:
                        diff.orientations[(fromV, toV)] = other.orientations[(fromV, toV)]
                    if (toV, fromV) not in diff.orientations:
                        diff.orientations[(toV, fromV)] = other.orientations[(toV, fromV)]
            return diff


    @staticmethod
    def from_obj_file(file_path: str):
        reader = ObjaReader()
        mesh = MeshTopology()
        for elem in reader.parse_file(file_path):
            if isinstance(elem, Vertex):
                mesh.add_vertex(elem, [])
            elif isinstance(elem, Face):
                for edge in elem.edges():
                    mesh.add_edge(*edge)
                    mesh.set_orientation(edge, elem.next_vertex(edge))
        return mesh

    def __init__(self):
        self.active_state = MeshTopology.State()
        self.committed_states = deque()

    def commit(self):
        diff = self.active_state.difference(self.committed_states[-1])
        self.committed_states.append(deepcopy(self.active_state))
        return diff        

    def rollback(self):
        if len(self.committed_states) > 0:
            self.active_state = self.committed_states.pop()

    def add_vertex(self, x, y, z, connected_to: List[Vertex]):
        self.add_vertex(Vertex((x, y, z), self), connected_to)

    def add_vertex(self, vertex: Vertex, connected_to: List[Vertex]):
        if vertex not in self.active_state.vertex_connections:
            vertex.mesh = self
            self.active_state.vertex_connections[vertex] = set()
            for conn in connected_to:
                self.add_edge(vertex, conn)

    def can_remove_vertex(self, vertex: Vertex) -> bool:
        if vertex not in self.active_state.vertex_connections:
            return False
        return all(len(self.active_state.vertex_connections[neighbor]) > 3 for neighbor in self.active_state.vertex_connections[vertex])
    
    def remove_vertex(self, vertex: Vertex, force: bool = False):
        if self.can_remove_vertex(vertex) is False and not force:
            return
        
        for neighbor in self.active_state.vertex_connections[vertex]:
            self.active_state.vertex_connections[neighbor].remove(vertex)
            
            del self.active_state.orientations[(vertex, neighbor)]
            del self.active_state.orientations[(neighbor, vertex)]

        del self.active_state.vertex_connections[vertex]

    def add_edge(self, fromV: Vertex, toV: Vertex):
        if fromV not in self.active_state.vertex_connections or toV not in self.active_state.vertex_connections:
            return
        
        self.active_state.vertex_connections[fromV].add(toV)
        self.active_state.vertex_connections[toV].add(fromV)

        # Could add automatic detection of orientations, but a bit complex, just use set_orientations after

    def can_remove_edge(self, fromV: Vertex, toV: Vertex) -> bool:
        return (fromV in self.active_state.vertex_connections and
                toV in self.active_state.vertex_connections[fromV] and
                len(self.active_state.vertex_connections[fromV]) > 3 and
                len(self.active_state.vertex_connections[toV]) > 3)
    
    def remove_edge(self, fromV: Vertex, toV: Vertex, force: bool = False):
        if self.can_remove_edge(fromV, toV) is False and not force:
            return
        
        for face in self.get_connected_faces((fromV, toV)):
            del self.face_orientations[(face, fromV)]
            del self.face_orientations[(face, toV)]
            del self.face_orientations[(face, face.next_vertex((fromV, toV)))]

        self.active_state.vertex_connections[fromV].remove(toV)
        self.active_state.vertex_connections[toV].remove(fromV)

    def remove_edge(self, gate: Gate):
        self.remove_edge(gate.edge[0], gate.edge[1])

    def set_orientation(self, from_to: Tuple[Vertex, Vertex], third_vertex: Vertex) -> bool:
        fromV, toV = from_to
        common_neighbours = self.active_state.vertex_connections[fromV].intersection(self.active_state.vertex_connections[toV])
        if len(common_neighbours) not in {1, 2}:
            return False # Badly structured mesh, can't define the orientation
        
        other_vertex = next((v for v in common_neighbours if v != third_vertex), None)
        self.active_state.orientations[from_to] = (third_vertex, other_vertex)
        self.active_state.orientations[(toV, fromV)] = (other_vertex, third_vertex) 
        return True

    def get_connected_vertices(self, vertex: Vertex) -> Set[Vertex]:
        if vertex not in self.active_state.vertex_connections:
            return []
        
        return self.active_state.vertex_connections[vertex]

    # Return (None, None) if the edge is not oriented
    def get_oriented_vertices(self, oriented_edge: Tuple[Vertex, Vertex]) -> Tuple[Optional[Vertex], Optional[Vertex]]:
        if oriented_edge not in self.active_state.orientations:
            return (None, None)
        
        return self.active_state.orientations[oriented_edge]

    # Left face is the one in the orientation of from -> to, right is to -> from
    def get_oriented_faces(self, from_to: Tuple[Vertex, Vertex]) -> Tuple[Optional[Face], Optional[Face]]:
        oriented_vertices = self.get_oriented_vertices(from_to)
        left_vertex, right_vertex = oriented_vertices
        v1, v2 = from_to
        return (Face((v1, v2, left_vertex), self) if left_vertex is not None else None,\
                Face((v2, v1, right_vertex), self) if right_vertex is not None else None)

    def get_faces(self, fromV: Vertex) -> Set[Face]:
        if fromV not in self.active_state.vertex_connections:
            return []
        
        faces = set()
        valence = self.get_valence(fromV)
        neighbors = self.active_state.vertex_connections[fromV]
        for toV in neighbors:
            if valence == len(faces):
                break

            connected_faces = self.get_oriented_faces((fromV, toV))
            for face in connected_faces:
                #print(face, ":", hash(face))
                faces.add(face)

        return faces

    # Warning: Return the faces in a random order for the moment
    def get_patch(self, vertex: Vertex) -> Patch:
        if vertex not in self.active_state.vertex_connections:
            return None
        faces = self.get_faces(vertex)
        return Patch(vertex, faces, self)
    
    def get_valence(self, vertex: Vertex) -> int:
        return len(self.active_state.vertex_connections.get(vertex, set()))
    
    def get_vertices(self) -> Set[Vertex]:
        return self.active_state.vertex_connections.keys()

    # Get the first available gate in the mesh
    def get_random_gate(self) -> Gate:
        if len(self.active_state.vertex_connections) == 0:
            return None
        
        MAX_TRIALS = len(self.active_state.vertex_connections) * 2 # Arbituary upper limit
        for trial in range(MAX_TRIALS):
            v1 = random.sample(list(self.active_state.vertex_connections.keys()), 1)[0]
            if len(self.active_state.vertex_connections[v1]) == 0:
                continue

            v2 = random.sample(list(self.active_state.vertex_connections[v1]), 1)[0]
            adjacent_vertex = self.get_oriented_vertices((v1, v2))
            if adjacent_vertex[0] is not None and self.can_remove_vertex(adjacent_vertex[0]):
                return Gate((v1, v2), adjacent_vertex[0], self)
            elif adjacent_vertex[1] is not None and self.can_remove_vertex(adjacent_vertex[1]):
                return Gate((v2, v1), adjacent_vertex[1], self)

        return None
        
    # todelete : for debug purpose
    def export_to_obj(self, file_path: str):
        # Simple OBJ exporter (debug): write vertices and faces to an OBJ file.
        vertices = self.active_state.vertex_connections.keys()
        indices = dict()
        with open(file_path, 'w') as out:
            # write vertices
            current_index = 1
            for vertex in vertices:
                x, y, z = vertex.position
                out.write(f"v {x} {y} {z}\n")
                indices[vertex] = current_index
                current_index += 1


            # write faces (avoid duplicates)
            seen_faces = set()
            for vertex in vertices:
                faces = self.get_faces(vertex)
                for f in faces:
                    if f in seen_faces:
                        continue
                    seen_faces.add(f)
                    indices_l = [indices[vert] for vert in f.vertices]
                    out.write(f"f {indices_l[0]} {indices_l[1]} {indices_l[2]}\n")