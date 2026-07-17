"""Compatibility wrapper for existing Vizard scripts.

Prefer `import goodnavigate` for new code. This module keeps older
`import GoodNavigate` scripts working after pip installation.
"""

from goodnavigate import *  # noqa: F401,F403
