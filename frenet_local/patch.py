from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from .vectors import normalize


@dataclass
class Patch:
    """
    A light wrapper around a local triangle patch.

    Attributes
    ----------
    vertices : (N, 3) float array
        3D points of the patch (in world coordinates). 
    exemple : vertices = np.array([
        [1.0, 0.0, 0.0],   # sommet 0
        [0.0, 1.0, 0.0],   # sommet 1
        [0.0, 0.0, 1.0],   # sommet 2
    ])
    faces : (M, 3) int array
        Local triangle indices (0..N-1) forming the patch.
    faces = np.array([
        [0, 1, 2],
    ])
    """
    vertices: np.ndarray  # shape (N, 3)
    faces: np.ndarray     # shape (M, 3), dtype=int

    def area_weighted_normal(self) -> np.ndarray:
        """
        Compute the area-weighted average normal of the patch, normalized.

        Returns
        -------
        n : (3,) float array
            Unit-length area-weighted average normal.
        """
        acc = np.zeros(3, dtype=float)
        for f in self.faces:
            p, q, r = self.vertices[f[0]], self.vertices[f[1]], self.vertices[f[2]]
            n_f = np.cross(q - p, r - p)  # magnitude = 2 * area
            acc += n_f
        return normalize(acc)

    def barycenter(self, project_to_plane: bool = False) -> np.ndarray:
        """
        Compute the patch barycenter. Optionally project it onto the tangent plane.

        Parameters
        ----------
        project_to_plane : bool
            If True, project the arithmetic mean onto the plane defined by the
            area-weighted normal through an arbitrary reference vertex.

        Returns
        -------
        b : (3,) float array
            Barycenter (possibly projected) used as the origin of the local frame.
        """
        b_raw = np.mean(self.vertices, axis=0)
        if not project_to_plane:
            return b_raw

        n = self.area_weighted_normal()
        ref = self.vertices[0]
        dist = np.dot((b_raw - ref), n)
        b_proj = b_raw - dist * n
        return b_proj
