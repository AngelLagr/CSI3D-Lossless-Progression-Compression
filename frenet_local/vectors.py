from __future__ import annotations
import numpy as np


def normalize(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """
    Return the unit vector of v. If ||v|| < eps, returns the zero vector.

    Parameters
    ----------
    v : np.ndarray
        Input vector (shape (..., 3)).
    eps : float
        Small epsilon to guard against division by zero.

    Returns
    -------
    np.ndarray
        Unit vector with same shape as v.
    """
    n = np.linalg.norm(v)
    if n < eps:
        return v * 0.0
    return v / n


def any_tangent_from_normal(n: np.ndarray) -> np.ndarray:
    """
    Build a stable tangent lying in the plane orthogonal to n.

    If n is close to X, use Y as auxiliary, otherwise use X.

    Parameters
    ----------
    n : (3,) np.ndarray
        Unit normal vector.

    Returns
    -------
    (3,) np.ndarray
        Unit tangent vector orthogonal to n.
    """
    aux = np.array([1.0, 0.0, 0.0], dtype=float)
    if abs(np.dot(aux, n)) > 0.9:
        aux = np.array([0.0, 1.0, 0.0], dtype=float)
    t = np.cross(n, aux)
    return normalize(t)
