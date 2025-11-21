from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np


@dataclass
class QuantParams:
    """
    Quantization parameters for a single component.

    Attributes
    ----------
    offset : float
        Center of the quantization range (typically 0 for residuals).
    scale : float
        Multiplier mapping the floating range to the target integer range.
    bits  : int
        Bit depth used for signed integers (e.g., 10, 12).
    """
    offset: float
    scale: float
    bits: int


class Quantizer:
    """
    Minimal symmetric per-component quantizer.

    Methods
    -------
    fit(values, bits) -> QuantParams
        Fit offset/scale for signed range with given bit depth.
    quantize(values, params) -> np.ndarray[int32]
    dequantize(qvalues, params) -> np.ndarray[float64]
    """

    @staticmethod
    def fit(values: Sequence[float], bits: int) -> QuantParams:
        """
        Fit symmetric quantization parameters for given values and bit depth.

        We map values to signed integers in [-(2^(bits-1)-1), +(2^(bits-1)-1)].
        Offset defaults to 0 for residuals; scale is chosen from max absolute value.

        Parameters
        ----------
        values : sequence of float
            Floating values to be quantized (e.g., all alphas of a layer).
        bits : int
            Signed integer bit depth (>= 2).

        Returns
        -------
        QuantParams
        """
        if bits < 2:
            raise ValueError("bits must be >= 2")

        vmax = float(max(abs(min(values, default=0.0)),
                         abs(max(values, default=0.0))))
        qmax = (2 ** (bits - 1)) - 1
        scale = (qmax / vmax) if vmax > 1e-12 else 1.0
        return QuantParams(offset=0.0, scale=scale, bits=bits)

    @staticmethod
    def quantize(values: Sequence[float], params: QuantParams) -> np.ndarray:
        """
        Quantize floats -> int32 using params (offset, scale).
        """
        return np.round((np.asarray(values, dtype=float) - params.offset) * params.scale).astype(np.int32)

    @staticmethod
    def dequantize(qvalues: Sequence[int], params: QuantParams) -> np.ndarray:
        """
        Dequantize int -> float using params (offset, scale).
        """
        q = np.asarray(qvalues, dtype=np.int64)
        return (q.astype(np.float64) / params.scale) + params.offset
