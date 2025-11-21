from __future__ import annotations
from typing import Tuple
import numpy as np

from .frame import FrenetFrame


class LocalEncoder:
    """
    Encode and decode 3D points with respect to a Frenet-like local frame.

    API mirrors the paper's decomposition:
        vr = b + alpha * t1 + beta * t2 + gamma * n

    Methods
    -------
    encode(vr, frame) -> (alpha, beta, gamma)
    decode(alpha, beta, gamma, frame) -> vr_hat
    """

    @staticmethod
    def encode(vr: np.ndarray, frame: FrenetFrame) -> Tuple[float, float, float]:
        """
        Project a 3D point onto the local frame (alpha, beta, gamma).

        Parameters
        ----------
        vr : (3,) float array
            The 3D point to encode (e.g., vertex to be inserted).
        frame : FrenetFrame
            Local frame (b, t1, t2, n).

        Returns
        -------
        alpha, beta, gamma : floats
            Tangential (alpha,beta) and normal (gamma) coordinates of vr.
        """
        delta = vr - frame.b
        alpha = float(np.dot(delta, frame.t1))
        beta = float(np.dot(delta, frame.t2))
        gamma = float(np.dot(delta, frame.n))
        return alpha, beta, gamma

    @staticmethod
    def decode(alpha: float, beta: float, gamma: float, frame: FrenetFrame) -> np.ndarray:
        """
        Reconstruct a 3D point from local coordinates and a frame.

        Parameters
        ----------
        alpha, beta, gamma : float
            Local coordinates in the Frenet-like frame.
        frame : FrenetFrame
            Local frame (b, t1, t2, n).

        Returns
        -------
        vr_hat : (3,) float array
            Reconstructed 3D point: b + alpha t1 + beta t2 + gamma n
        """
        return frame.b + alpha * frame.t1 + beta * frame.t2 + gamma * frame.n
