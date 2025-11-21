# -*- coding: utf-8 -*-
"""
Minimal end-to-end example using the frenet_local package.
Run with:  python -m frenet_local.examples.demo
"""

import numpy as np

from frenet_local.patch import Patch
from frenet_local.frame import FrenetFrame
from frenet_local.codec import LocalEncoder
from frenet_local.quant import Quantizer


def main():
    # Build a toy patch (slightly curved hexagon)
    verts = np.array([
        [ 1.0,  0.0,   0.02],
        [ 0.5,  0.866, 0.01],
        [-0.5,  0.866, 0.00],
        [-1.0,  0.0,  -0.01],
        [-0.5, -0.866, 0.00],
        [ 0.5, -0.866, 0.01],
    ], dtype=float)
    faces = np.array([
        [0, 1, 2],
        [0, 2, 3],
        [0, 3, 4],
        [0, 4, 5],
    ], dtype=int)
    patch = Patch(vertices=verts, faces=faces)

    # Gate edge (oriented): v0 -> v1
    gate = (verts[0], verts[1])

    # Build local frame (projected barycenter recommended)
    frame = FrenetFrame.from_patch_and_gate(patch, gate_edge=gate, project_barycenter=True)

    # A 3D point to encode (e.g., vertex to insert)
    vr = np.array([0.10, 0.05, 0.02], dtype=float)

    # Encode -> (alpha, beta, gamma)
    alpha, beta, gamma = LocalEncoder.encode(vr, frame)
    print("alpha, beta, gamma:", alpha, beta, gamma)

    # Optional: per-component quantization (e.g., 12-bit signed)
    Qa = Quantizer.fit([alpha], bits=12)
    Qb = Quantizer.fit([beta],  bits=12)
    Qg = Quantizer.fit([gamma], bits=12)

    qa = Quantizer.quantize([alpha], Qa)[0]
    qb = Quantizer.quantize([beta],  Qb)[0]
    qg = Quantizer.quantize([gamma], Qg)[0]

    alpha_hat = Quantizer.dequantize([qa], Qa)[0]
    beta_hat  = Quantizer.dequantize([qb], Qb)[0]
    gamma_hat = Quantizer.dequantize([qg], Qg)[0]

    # Decode -> reconstructed point
    vr_hat = LocalEncoder.decode(alpha_hat, beta_hat, gamma_hat, frame)
    print("reconstruction error ||vr - vr_hat|| =", np.linalg.norm(vr - vr_hat))


if __name__ == "__main__":
    main()
