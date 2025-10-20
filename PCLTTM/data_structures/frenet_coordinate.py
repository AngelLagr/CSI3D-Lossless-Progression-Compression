class FrenetCoordinates:
    def __init__(self, u: float, v: float, n: float):
        self.tangent_x = u
        self.tangent_y = v
        self.normal_z = n

    def apply(self, alpha: int, beta: int, gamma: int) -> np.ndarray:
        return (self.tangent_x * alpha, self.tangent_y * beta, self.normal_z * gamma)
