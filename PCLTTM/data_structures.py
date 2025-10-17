# ============================================================================
# DATA STRUCTURES
# ============================================================================

class Vertex:
    def __init__(self, index: int, position: np.ndarray):
        self.index = index
        self.position = position  # np.array([x, y, z])
        self.state = StateFlag.Free
        self.tag = VertexTag.Default
        self.adjacent_faces: Set[int] = set()  # Indices of adjacent faces
        self.adjacent_vertices: Set[int] = set()  # Indices of adjacent vertices

    def valence(self) -> int:
        return len(self.adjacent_faces)
    
    def generate_patch(self):
        return None
    
class Face:
    def __init__(self, index: int, vertices: Tuple[int, int, int]):
        self.index = index
        self.vertices = vertices  # (v1, v2, v3)
        self.state = StateFlag.Free

class Gate:
    def __init__(self, edge: Tuple[int, int], front_face_idx: int, front_vertex_idx: int):
        self.edge = edge  # (v_left, v_right)
        self.front_face_idx = front_face_idx
        self.front_vertex_idx = front_vertex_idx
    
    def __repr__(self):
        return f"Gate(edge={self.edge}, face={self.front_face_idx}, front_v={self.front_vertex_idx})"

class Patch:
    def __init__(self, center_vertex: int, valence: int):
        self.center_vertex = center_vertex
        self.valence = valence
        self.boundary_vertices: List[int] = []
        self.faces: List[int] = []

class DecimationCode:
    def __init__(self):
        self.valence_code = -1
        self.residual = (0, 0, 0)
        self.target_vertex = -1 # Mutually exclusive with target_face
        self.target_face = -1

    def clean(self):
        target = self._target()
        if target is None or target.valence() != 6:
            return  # Nothing to clean
        else:
            self.valence_code = 3

    def _target(self) -> Face|Vertex:
        if self.target_vertex != -1:
            return self.target_vertex
        elif self.target_face != -1:
            return self.target_face
        else:
            return None

class FrenetCoordinates:
    def __init__(self, u: float, v: float, n: float):
        self.tangent_x = u
        self.tangent_y = v
        self.normal_z = n

    def apply(self, alpha: int, beta: int, gamma: int) -> np.ndarray:
        return (self.tangent_x * alpha, self.tangent_y * beta, self.normal_z * gamma)
