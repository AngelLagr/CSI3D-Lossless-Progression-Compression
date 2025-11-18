from typing import Tuple, List, Self, TYPE_CHECKING
from .constants import StateFlag, RetriangulationTag

if TYPE_CHECKING:
    from .data_structures import Face, Patch  # or proper imports


class Vertex:
    def __init__(self, position: Tuple[float, float, float], mesh=None):
        self.position = position
        self.mesh = mesh

    # Mesh related functions
    def valence(self) -> int:
        return self.mesh.get_valence(self) if self.mesh else 0

    def generate_patch(self) -> "Patch | None":
        return self.mesh.get_patch(self) if self.mesh else None

    def connected_vertices(self) -> List[Self]:
        return list(self.mesh.get_connected_vertices(self)) if self.mesh else []

    def connected_faces(self) -> List["Face"]:
        return list(self.mesh.get_faces(self)) if self.mesh else []

    # Internal functions
    def __lt__(self, other):
        return self.position < other.position

    def __hash__(self):
        return hash(self.position)

    def __eq__(self, other):
        return isinstance(other, Vertex) and self.position == other.position

    def __repr__(self):
        return "(" + ", ".join([str(pos) for pos in self.position]) + ")"
