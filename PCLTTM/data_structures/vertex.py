import numpy as np
from typing import Tuple, override

from constants import StateFlag, VertexTag
from globally_referencable import GlobalReference

class Vertex():
    def __init__(self, position: Tuple[float, float, float]):
        self.position = position
        self.state = StateFlag.Free
        self.tag = VertexTag.Default

    def valence(self) -> int:
        return len(self.adjacent_faces)
    
    def generate_patch(self):
        return None

    def __hash__(self):
        return hash(self.position)
