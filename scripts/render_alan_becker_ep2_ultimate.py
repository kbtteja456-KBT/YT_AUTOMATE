"""Educational Visual Animation Engine - Episode 2 Entrypoint.
Delegates to the approved modular Educational Visual Studio for Episode 2 (Python Data Types).
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.getcwd())
from scripts.render_educational_ep2_datatypes import render_episode_2

if __name__ == "__main__":
    render_episode_2()
