from typing import Tuple, List, Self

from constants import StateFlag, VertexTag
from face import Face
from patch import Patch

class Vertex():
    def __init__(self, position: Tuple[float, float, float], mesh = None):
        self.position = position
        self.state = StateFlag.Free
        self.tag = VertexTag.Default
        self.mesh = mesh

    # Mesh related functions
    def valence(self) -> int:
        return self.mesh.get_vertex_valence(self) if self.mesh else 0
    
    def generate_patch(self) -> List[Patch]:
        return self.mesh.get_patch(self) if self.mesh else []
    
    def connected_vertices(self) -> List[Self]:
        return self.mesh.get_connected_vertices(self) if self.mesh else []

    def connected_faces(self) -> List[Face]:
        return self.mesh.get_faces(self) if self.mesh else []
    
    def state_flag(self) -> StateFlag:
        return self.mesh.get_vertex_state(self) if self.mesh else StateFlag.Free
    
    def tag_flag(self) -> VertexTag:
        return self.mesh.get_vertex_tag(self) if self.mesh else VertexTag.Default

    # Internal functions
    def __hash__(self):
        return hash(self.position)
