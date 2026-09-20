"""Optional sound effects; game logic remains independent of the mixer."""
from .service import Audio, SilentAudio

__all__ = ["Audio", "SilentAudio"]
