from constants import StateFlag
from typing import Tuple


class Face:
    def __init__(self, vertices: Tuple[int, int, int]):
        self.index = index
        self.vertices = vertices  # (v1, v2, v3)
        self.state = StateFlag.Free
