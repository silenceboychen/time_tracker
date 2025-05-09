import platform

def get_os():
    """Detects the current operating system."""
    system = platform.system().lower()
    if "windows" in system:
        return "windows"
    elif "darwin" in system:  # macOS
        return "macos"
    elif "linux" in system:
        return "linux"
    return "unknown" 