"""
Application launching tools with configurable mapping.
"""

import subprocess
import shutil
from typing import Tuple
import config


def launch_app(app_name: str) -> Tuple[bool, str]:
    """
    Launch an application based on config.APPS or fallback to system start.
    """
    clean_name = app_name.strip().lower()
    
    # Check configured mapping
    command = config.APPS.get(clean_name)
    
    if not command:
        # Check partial / normalized matches
        for known_name, known_cmd in config.APPS.items():
            if known_name in clean_name or clean_name in known_name:
                command = known_cmd
                break

    if not command:
        # Fallback to direct Windows start command
        command = f'start "" "{clean_name}"'

    try:
        subprocess.Popen(command, shell=True)
        return True, f"Launched {app_name}"
    except Exception as e:
        return False, f"Failed to launch application '{app_name}': {e}"
