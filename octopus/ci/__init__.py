"""
CI platform integration module
"""

from . import base, github, gitlab, jenkins

__all__ = ["base", "gitlab", "github", "jenkins"]
