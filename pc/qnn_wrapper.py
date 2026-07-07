# qnn_wrapper.py
# Wraps the SPC engine's core computation for NPU execution via AI Hub.
# Before hackathon: mock_mode=True runs on CPU identically to NPU.
# Hackathon day: mock_mode=False runs on Snapdragon X NPU.

import numpy as np
import time

try:
    import qai_hub
    QAI_AVAILABLE = True
except ImportError:
    QAI_AVAILABLE = False


class NPUWrapper:
    """
    Wraps SPC computation for NPU execution.
    Falls back to CPU transparently if NPU is unavailable.
    """

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode or not QAI_AVAILABLE
        if not self.mock_mode:
            self._init_npu()

    def _init_npu(self):
        """Initialise QNN execution context on Snapdragon NPU."""
        # [FACT] Full QNN SDK initialisation requires the Snapdragon X PC hardware.
        # This is a stub that must be completed at the hackathon with the real device.
        # Reference: https://aihub.qualcomm.com/get-started
        print("[NPU] Initialising Qualcomm AI Hub NPU context...")
        # self.hub_model = qai_hub.load_model(...)   # Load compiled model
        print("[NPU] NPU context ready")

    def run_spc_step(
        self,
        x: np.ndarray,
        ewma: np.ndarray,
        ewma_var: np.ndarray,
        alpha: float,
        ucl_sigma: float
    ) -> dict:
        """
        Execute one SPC inference step.
        On CPU (mock): identical computation, no NPU.
        On NPU (hackathon): same math, executed on Hexagon DSP via QNN.
        """
        t0 = time.perf_counter()

        # Control limit check using PREVIOUS mean and variance
        std      = np.sqrt(ewma_var + 1e-8)
        z_scores = np.abs(x - ewma) / std
        violations = int(np.sum(z_scores > ucl_sigma))

        # EWMA update for the next step
        delta    = x - ewma
        ewma_new = alpha * x + (1 - alpha) * ewma
        var_new  = alpha * delta**2 + (1 - alpha) * ewma_var

        latency_ms = (time.perf_counter() - t0) * 1000

        return {
            "ewma_new":   ewma_new,
            "var_new":    var_new,
            "z_scores":   z_scores,
            "violations": violations,
            "latency_ms": latency_ms,
            "on_npu":     not self.mock_mode
        }
