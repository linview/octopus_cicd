"""
Octopus - A flexible CICD infrastructure toolkit for test orchestration and container management
"""

from . import core
from . import dsl
from . import orchestration
from . import integrations
from . import utils

__version__ = "0.1.0"
__all__ = ["core", "dsl", "orchestration", "integrations", "utils"] 