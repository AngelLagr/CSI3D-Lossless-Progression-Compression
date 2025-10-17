from data_structures import Vertex, Face, Gate, Patch

from obja_parser import ObjaReader, ObjaWriter

# ============================================================================
# MESH TOPOLOGY HELPERS
# ============================================================================

"""
    Manages mesh topology information: valences, adjacency, neighborhoods.
    
    This class precomputes and maintains:
    - Vertex valences (number of incident edges)
    - Vertex-face incidence lists
    - Edge-to-face mappings
    - Face-to-face adjacency
"""
class MeshTopology:
    @staticmethod
    def from_obj_file(file_path: str):
        reader = ObjaReader()
        mesh = MeshTopology()
        for elem in reader.parse_file(file_path):
            pass
        return mesh

    def __init__(self, model):
        self.vertex_faces = None  # For each vertex, list of incident face indices
        self.edge_to_face = None  # Maps oriented edge to face index
        self.face_adjacency = None  # For each face, set of adjacent faces
        
        self._compute_topology()


    def add_vertex(x, y, z, connected_to):
        pass
    def can_remove_vertex(vertex: Vertex) -> bool:
        return False
    def remove_vertex(vertex: Vertex):
        pass

    def add_edge(fromV: Vertex, toV: Vertex):
        pass
    def remove_edge(fromV: Vertex, toV: Vertex):
        pass
    def remove_edge(gate: Gate):
        pass

    def set_retriangulation_tag(vertex: Vertex, tag):
        pass
    def set_vertex_state(vertex: Vertex, flag):
        pass
    def set_face_state(face: Face, flag):
        pass

    def get_patch(vertex: Vertex) -> Patch:
        pass
    def get_patch(gate: Gate) -> Patch:
        pass
    def get_facing_vertex(gate: Gate) -> Vertex:
        pass