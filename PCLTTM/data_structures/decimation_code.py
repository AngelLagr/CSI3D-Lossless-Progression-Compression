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

    def _target(self) -> "Face|Vertex":
        if self.target_vertex != -1:
            return self.target_vertex
        elif self.target_face != -1:
            return self.target_face
        else:
            return None

