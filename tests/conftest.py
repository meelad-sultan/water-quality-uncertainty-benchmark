import copy

import numpy as np
import pytest

from wqub.config import load_config
from wqub.synth import make_synthetic


@pytest.fixture(scope="session")
def cfg():
    return load_config("configs/quick.yaml")


@pytest.fixture()
def cfg_copy(cfg):
    return copy.deepcopy(cfg)


@pytest.fixture(scope="session")
def small(cfg):
    return make_synthetic(cfg, np.random.default_rng(3))
