class DecimationCode:
    def __init__(self):
        self.valence_code = -1
        self.residual = (0.0, 0.0, 0.0)
        self.target_vertex = None  # type: Vertex | None
        self.target_face = None    # type: Face | None

    def clean(self):
        target = self._target()
        if target is None or target.valence() != 6:
            return  # Nothing to clean
        else:
            self.valence_code = 3

    def _target(self):  # -> "Face | Vertex | None"
        if self.target_vertex is not None:
            return self.target_vertex
        elif self.target_face is not None:
            return self.target_face
        else:
            return None
