from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import numpy as np

from .patch import Patch
from .vectors import normalize, any_tangent_from_normal


@dataclass
class FrenetFrame:
    """
    Approximate local Frenet-like frame for a triangle patch.

    Attributes
    ----------
    b : (3,) float
        Frame origin (patch barycenter, optionally projected).
    t1 : (3,) float
        First tangent (unit). Projection of the gate edge onto the tangent plane.
    t2 : (3,) float
        Second tangent (unit). Computed as cross(n, t1).
    n : (3,) float
        Unit normal (area-weighted average normal of the patch).

    """
    b: np.ndarray
    t1: np.ndarray
    t2: np.ndarray
    n: np.ndarray

    @staticmethod
    def from_patch_and_gate(
        patch: Patch,
        gate_edge: Tuple[np.ndarray, np.ndarray],
        project_barycenter: bool = True,
    ) -> "FrenetFrame":
        """
        Build the approximate Frenet frame for a patch from a gate edge.

        Parameters
        ----------
        patch : Patch
            Local patch (vertices + faces).
        gate_edge : (a, c) tuple of (3,) arrays
            Oriented gate edge endpoints in 3D (left->right in the paper).
        project_barycenter : bool
            If True, project the barycenter onto the tangent plane (recommended).

        Returns
        -------
        FrenetFrame
            (b, t1, t2, n) as used to encode/decode local coordinates.
        """
        if patch.vertices.ndim != 2 or patch.vertices.shape[1] != 3:
            raise ValueError("Patch.vertices must be (N,3).")
        if patch.faces.ndim != 2 or patch.faces.shape[1] != 3:
            raise ValueError("Patch.faces must be (M,3) of indices.")

        b = patch.barycenter(project_to_plane=project_barycenter)
        n = patch.area_weighted_normal()

        a, c = gate_edge
        e = c - a
        # Project gate onto tangent plane: e_perp = e - (e·n) n
        e_perp = e - np.dot(e, n) * n
        t1 = normalize(e_perp)

        # Fallback if gate nearly parallel to n (projection collapses)
        if np.linalg.norm(t1) < 1e-12:
            t1 = any_tangent_from_normal(n)

        t2 = np.cross(n, t1)
        t2 = normalize(t2)

        # Re-orthogonalize t1 just in case (numerical safety)
        t1 = normalize(np.cross(t2, n))

        return FrenetFrame(b=b, t1=t1, t2=t2, n=n)
