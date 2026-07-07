# spc_engine.py
# Statistical Process Control engine for crowd crush detection.
# Self-calibrates on the first 30 readings (~0.6 seconds at 50Hz).
# No training data required. Fully explainable to judges.
#
# Key parameters:
#   alpha:         EWMA smoothing factor (0=slow, 1=instant response)
#   ucl_sigma:     Control limit width in standard deviations (default: 3.0)
#   warmup_samples: Readings before alerts activate
#   ood_threshold: Mahalanobis distance for out-of-distribution detection

import numpy as np
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SPCConfig:
    alpha:          float = 0.3
    ucl_sigma:      float = 3.0
    warmup_samples: int   = 30
    ood_threshold:  float = 12.0


class CrushRiskEngine:
    """
    Processes a stream of 8-channel pressure readings and outputs a crush risk score.

    Usage:
        engine = CrushRiskEngine()
        result = engine.update([120, 340, 80, 560, 200, 410, 90, 300])
        print(result["risk"])   # 0–100
        print(result["alert"])  # True if risk > 60
    """

    def __init__(self, n_sensors: int = 8, config: SPCConfig = None):
        self.n           = n_sensors
        self.cfg         = config or SPCConfig()
        self.ewma        = np.zeros(n_sensors)
        self.ewma_var    = np.full(n_sensors, 0.01)
        self.history:    List[np.ndarray] = []
        self.sample_count = 0
        self.cov_inv:    Optional[np.ndarray] = None

    def update(self, pressure: List[int]) -> dict:
        """
        Process one sensor reading.

        Args:
            pressure: 8 integers, each 0–1023 (raw Arduino analogRead values)

        Returns dict with:
            risk     (int 0–100): crush risk score
            alert    (bool): risk > 60
            critical (bool): risk > 85
            ood      (bool): out-of-distribution → trigger cloud sync
            warmup   (bool): True during calibration phase
            sensors  (list): normalised sensor values (0.0–1.0)
        """
        if len(pressure) != self.n:
            raise ValueError(f"Expected {self.n} sensors, got {len(pressure)}")

        x = np.array(pressure, dtype=float) / 1023.0
        self.sample_count += 1

        # Compute z-scores and UCL violations using PREVIOUS mean and variance
        std        = np.sqrt(self.ewma_var + 1e-8)
        z_scores   = np.abs(x - self.ewma) / std
        violations = int(np.sum(z_scores > self.cfg.ucl_sigma))

        # Update EWMA and variance for the next reading
        delta         = x - self.ewma
        self.ewma     = self.cfg.alpha * x + (1 - self.cfg.alpha) * self.ewma
        self.ewma_var = (self.cfg.alpha * delta**2
                         + (1 - self.cfg.alpha) * self.ewma_var)

        if self.sample_count < self.cfg.warmup_samples:
            self.history.append(x.copy())
            return {
                "risk": 0, "alert": False, "critical": False,
                "ood": False, "warmup": True,
                "sensors": x.tolist(), "sample": self.sample_count
            }

        # Risk score: violation count drives 70%, magnitude drives 30%
        risk = int(min(100,
            (violations / self.n) * 70 +
            min(30, float(np.mean(z_scores)) * 10)
        ))


        # Out-of-distribution detection
        ood = False
        if len(self.history) >= 50 and self.cov_inv is not None:
            try:
                mu   = np.mean(self.history[-50:], axis=0)
                diff = x - mu
                maha = float(np.sqrt(max(0.0, diff @ self.cov_inv @ diff)))
                ood  = maha > self.cfg.ood_threshold
            except (np.linalg.LinAlgError, ValueError):
                ood = False

        # Maintain rolling history
        self.history.append(x.copy())
        if len(self.history) > 200:
            self.history = self.history[-100:]
        if self.sample_count % 50 == 0:
            self._recompute_covariance()

        return {
            "risk":       risk,
            "alert":      risk > 60,
            "critical":   risk > 85,
            "ood":        ood,
            "warmup":     False,
            "sensors":    x.tolist(),
            "ewma":       self.ewma.tolist(),
            "violations": violations,
            "z_scores":   z_scores.tolist()
        }

    def recalibrate(self, weights: dict) -> None:
        """Apply updated thresholds received from Cloud AI 100."""
        if "ucl_sigma" in weights:
            self.cfg.ucl_sigma = float(weights["ucl_sigma"])
        if "alpha" in weights:
            self.cfg.alpha = float(weights["alpha"])

    def _recompute_covariance(self) -> None:
        if len(self.history) < 10:
            return
        hist = np.array(self.history[-100:])
        try:
            cov = np.cov(hist.T) + np.eye(self.n) * 1e-6
            self.cov_inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            self.cov_inv = None
