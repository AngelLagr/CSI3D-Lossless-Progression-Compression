from typing import List, Set, Tuple
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
        return mesh

    def __init__(self, model):
        self.state = MeshSnapshot()
        self.retriangulation_tags = dict() # Hash(Vertex) -> Retriangulation tag (+ or -)
        self.state_flags = dict() # Hash(Face|Vertex) -> State flag (e.g., CONQUERED, TO_BE_CONQUERED, FREE)
        self.current_transaction = None
        pass

    def transaction(self):
        if self.current_transaction is not None:
            self.current_transaction = MeshSnapshot()
        return self.current_transaction

    def commit(self):
        if self.current_transaction is not None:
            self.state.apply(self.current_transaction)
            self.current_transaction = None

    def rollback(self):
        if self.current_transaction is None:
            self.current_transaction = None

    def set_retriangulation_tag(self, vertex: Vertex, tag):
        if vertex in self.vertex_connections:
            self.retriangulation_tags[vertex] = tag

    def set_vertex_state(self, vertex: Vertex, flag):
        if vertex in self.vertex_connections:
            self.state_flags[vertex] = flag

    def set_face_state(self, face: Face, flag):
        if all(v in self.vertex_connections for v in face.vertices):
            self.state_flags[face] = flag


    def add_vertex(self, x, y, z, connected_to: List[Vertex]):
        self.add_vertex(Vertex((x, y, z), self), connected_to)

    def add_vertex(self, vertex: Vertex, connected_to: List[Vertex]):
        if vertex not in self.vertex_connections:
            self.vertex_connections[vertex] = set()
            for conn in connected_to:
                self.add_edge(vertex, conn)

    def can_remove_vertex(self, vertex: Vertex) -> bool:
        if vertex not in self.vertex_connections:
            return False
        return all(len(self.vertex_connections[neighbor]) > 3 for neighbor in self.vertex_connections[vertex])
    
    def remove_vertex(self, vertex: Vertex, force: bool = False):
        if self.can_remove_vertex(vertex) is False and not force:
            return
        
        for neighbor in self.vertex_connections[vertex]:
            self.vertex_connections[neighbor].remove(vertex)
            for face in self.get_connected_faces((vertex, neighbor)):
                del self.face_orientations[(face, vertex)]
                del self.face_orientations[(face, neighbor)]
                del self.face_orientations[(face, face.next_vertex((vertex, neighbor)))]

        del self.vertex_connections[vertex]

    def add_edge(self, fromV: Vertex, toV: Vertex):
        if fromV not in self.vertex_connections or toV not in self.vertex_connections:
            return
        
        self.vertex_connections[fromV].add(toV)
        self.vertex_connections[toV].add(fromV)

        for face in self.get_connected_faces((fromV, toV)):
            if (face, fromV) not in self.face_orientations:
                self.set_face_orientation(face, (fromV, toV))

    def can_remove_edge(self, fromV: Vertex, toV: Vertex) -> bool:
        return (fromV in self.vertex_connections and
                toV in self.vertex_connections[fromV] and
                len(self.vertex_connections[fromV]) > 3 and
                len(self.vertex_connections[toV]) > 3)
    
    def remove_edge(self, fromV: Vertex, toV: Vertex, force: bool = False):
        if self.can_remove_edge(fromV, toV) is False and not force:
            return
        
        for face in self.get_connected_faces((fromV, toV)):
            del self.face_orientations[(face, fromV)]
            del self.face_orientations[(face, toV)]
            del self.face_orientations[(face, face.next_vertex((fromV, toV)))]

        self.vertex_connections[fromV].remove(toV)
        self.vertex_connections[toV].remove(fromV)

    def remove_edge(self, gate: Gate):
        self.remove_edge(gate.edge[0], gate.edge[1])

    def set_face_orientation(self, face: Face, edge: Tuple[Vertex, Vertex]):
        next_vertex = face.next_vertex(edge)
        self.face_orientations[(face, edge[0])] = edge[1]
        self.face_orientations[(face, edge[1])] = next_vertex
        self.face_orientations[(face, next_vertex)] = edge[0]

    def get_connected_vertices(self, vertex: Vertex) -> Set[Vertex]:
        if vertex not in self.vertex_connections:
            return []
        return self.vertex_connections[vertex]

    def get_shared_neighbours(self, v1: Vertex, v2: Vertex) -> List[Vertex]:
        # v1 and v2 are Vertex objects; do not subscript them. Check membership
        # directly in the vertex_connections dict and return the intersection
        # of their neighbor sets (possibly empty).
        #if v1[0] not in self.vertex_connections or v2[1] not in self.vertex_connections:
        #    return []
        if v1 not in self.vertex_connections or v2 not in self.vertex_connections:
            return set()
        return self.vertex_connections[v1].intersection(self.vertex_connections[v2])

    def get_faces(self, vertex: Vertex) -> List[Face]:
        if vertex not in self.vertex_connections:
            return []
        faces = []
        seen = set()
        neighbors = self.vertex_connections[vertex]
        for a in neighbors:
            common_neighbors = neighbors.intersection(self.vertex_connections.get(a, set()))
            for b in common_neighbors:
                key = frozenset((vertex, a, b))
                if key in seen:
                    continue
                seen.add(key)
                faces.append(Face([vertex, a, b]))
        return faces

    def get_connected_faces(self, edge: Tuple[Vertex, Vertex]) -> Tuple[Face, Face]:
        v1, v2 = edge
        if v1 not in self.vertex_connections or v2 not in self.vertex_connections\
            or v1 not in self.vertex_connections[v2] or v2 not in self.vertex_connections[v1]:
            return []
        common_neighbors = self.get_shared_neighbours(v1, v2)
        return [Face([v1, v2, n]) for n in common_neighbors]

    # Warning: Return the faces in a random order for the moment
    def get_patch(self, vertex: Vertex) -> Patch:
        if vertex not in self.vertex_connections:
            return None
        faces = self.get_faces(vertex)
        return Patch(vertex, faces)
    
    def get_patch(self, gate: Gate) -> Patch:
        return self.get_patch(gate.front_vertex)
    
    # Get the first available gate in the mesh
    def get_initial_gate(self) -> Gate:
        for v in self.vertex_connections:
            neighbors = list(self.vertex_connections[v])
            if len(neighbors) < 2:
                continue
            
            for i in range(len(neighbors)):
                v1 = neighbors[i]
                v2 = neighbors[(i + 1) % len(neighbors)]
                if v1 in self.vertex_connections and v2 in self.vertex_connections[v1]:
                    self.set_retriangulation_tag(v1, constants.RetriangulationTag.Plus)
                    self.set_retriangulation_tag(v2, constants.RetriangulationTag.Minus)
                    return Gate((v1, v2), v)
        return None
        
    # todelete : for debug purpose
    def export_to_obj(self, file_path: str):
        # Simple OBJ exporter (debug): write vertices and faces to an OBJ file.
        vertices = list(self.vertex_connections.keys())
        vertex_indices = {v: i + 1 for i, v in enumerate(vertices)}  # OBJ indices start at 1

        with open(file_path, 'w') as out:
            # write vertices
            for v in vertices:
                x, y, z = v.position
                out.write(f"v {x} {y} {z}\n")

            # write faces (avoid duplicates)
            seen_faces = set()
            for v in vertices:
                faces = self.get_faces(v)
                for f in faces:
                    key = frozenset(f.vertices)
                    if key in seen_faces:
                        continue
                    seen_faces.add(key)
                    indices = [vertex_indices[vert] for vert in f.vertices]
                    out.write(f"f {indices[0]} {indices[1]} {indices[2]}\n")