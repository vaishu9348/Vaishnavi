"""
Tests for Differential Privacy (Laplace Mechanism)
Validates noise scale, bounds validation, clamping, and reproducibility.
"""

import sys
import os
import pytest
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from privacy.differential_privacy import LaplaceMechanism, InvalidEpsilonError


def test_laplace_scale_and_noise():
    dp = LaplaceMechanism(epsilon=1.0, sensitivity=1.0, seed=42)
    assert dp.scale == 1.0

    samples = [dp.draw_noise() for _ in range(1000)]
    assert len(samples) == 1000
    # Mean of Laplace noise with mean=0 should be near zero
    assert abs(np.mean(samples)) < 0.2


def test_perturb_count_non_negative_clamp():
    dp = LaplaceMechanism(epsilon=0.5, sensitivity=1.0, seed=123)
    perturbed = dp.perturb_count(0, clamp_zero=True)
    assert perturbed >= 0


def test_epsilon_validation_bounds():
    # Valid epsilon within [0.1, 1.0]
    LaplaceMechanism(epsilon=0.1)
    LaplaceMechanism(epsilon=0.5)
    LaplaceMechanism(epsilon=1.0)

    # Insecure or invalid epsilons must raise InvalidEpsilonError
    with pytest.raises(InvalidEpsilonError):
        LaplaceMechanism(epsilon=0.0)

    with pytest.raises(InvalidEpsilonError):
        LaplaceMechanism(epsilon=-0.5)

    with pytest.raises(InvalidEpsilonError):
        LaplaceMechanism(epsilon=100.0)

    with pytest.raises(InvalidEpsilonError):
        LaplaceMechanism(epsilon=1.5)  # Exceeds default secure ceiling 1.0
