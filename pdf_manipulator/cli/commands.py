"""Legacy CLI wrapper - redirects to new modular structure."""
import warnings
from .main import cli

warnings.warn(
    "Importing from pdf_manipulator.cli.commands is deprecated. "
    "Please import from pdf_manipulator.cli.main instead.",
    DeprecationWarning,
    stacklevel=2
)

# Maintain backward compatibility
__all__ = ['cli']