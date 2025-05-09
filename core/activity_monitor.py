import time
import platform
import logging
import psutil # Common dependency for process info

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_active_window_info_windows():
    """Gets active window information on Windows."""
    try:
        import win32gui
        import win32process

        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None # No foreground window

        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        process_name = "Unknown"
        try:
            process = psutil.Process(pid)
            process_name = process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.warning(f"Could not get process name for PID {pid} on Windows: {e}")

        window_title = win32gui.GetWindowText(hwnd)
        return process_name, window_title
    except ImportError:
        logger.error("pywin32 is not installed. Please install it for Windows support: pip install pywin32")
        return "Error: pywin32 not installed", "N/A"
    except Exception as e:
        logger.error(f"Error getting active window on Windows: {e}")
        return "Error", str(e)

def get_active_window_info_macos():
    """Gets active window information on macOS."""
    try:
        from AppKit import NSWorkspace
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, kCGWindowListExcludeDesktopElements

        logger.debug("Starting get_active_window_info_macos - PRAGMATIC APPROACH")

        # Get window list first - we'll use this as our primary source of truth
        options = kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements
        window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
        
        if not window_list:
            logger.warning("CGWindowListCopyWindowInfo returned an empty list or None.")
            return "Unknown", "No windows found"

        logger.debug(f"Found {len(window_list)} windows in the list.")
        
        # Filter for visible Layer 0 windows (user-interactive main windows)
        layer_0_windows = []
        for window in window_list:
            if window.get('kCGWindowLayer') == 0 and window.get('kCGWindowIsOnscreen'):
                layer_0_windows.append(window)
                
        if not layer_0_windows:
            logger.warning("No Layer 0 windows found in the window list.")
            # Try to use NSWorkspace as fallback
            workspace = NSWorkspace.sharedWorkspace()
            frontmost_app = workspace.frontmostApplication()
            if frontmost_app:
                app_name = frontmost_app.localizedName()
                return app_name, "No window title available (no Layer 0 windows)"
            else:
                return "Unknown", "No active application detected"
        
        # Sort Layer 0 windows by potential "frontmost" attributes
        # CGWindowListCopyWindowInfo gives windows in z-order, so first ones are likely frontmost
        # Log the first few windows for analysis
        logger.debug(f"Found {len(layer_0_windows)} Layer 0 windows. Looking for most likely active:")
        for i, window in enumerate(layer_0_windows[:5]): # Just log first 5 for brevity
            owner_pid = window.get('kCGWindowOwnerPID')
            owner_name = window.get('kCGWindowOwnerName', "(No Owner Name)")
            window_name = window.get('kCGWindowName', "(No Name Attribute)")
            window_alpha = window.get('kCGWindowAlpha', 1.0)
            window_bounds = window.get('kCGWindowBounds', {})
            logger.debug(f"  Candidate Window[{i}]: OwnerName='{owner_name}', OwnerPID={owner_pid}, Name='{window_name}', Alpha={window_alpha}, Bounds={window_bounds}")
        
        # Assume the first Layer 0 window is the active one (based on z-order)
        frontmost_window = layer_0_windows[0]
        app_name = frontmost_window.get('kCGWindowOwnerName', "Unknown App")
        
        # Choose the window title, prefer actual window name, or resort to common substitutions
        window_title = frontmost_window.get('kCGWindowName')
        
        if not window_title or window_title == "(No Name Attribute)":
            # Many apps don't set window titles - we'll use app name + "Window" as a reasonable fallback
            window_title = f"{app_name} Window" 
        
        logger.info(f"Selected frontmost window: App='{app_name}', Title='{window_title}'")
        return app_name, window_title

    except ImportError as e: 
        logger.error(f"Original ImportError during AppKit/Quartz import on macOS: {e}", exc_info=True)
        logger.error("This usually means pyobjc-core, pyobjc-framework-Cocoa, or pyobjc-framework-Quartz is not found.")
        return "Error: pyobjc import failed", "N/A"
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_active_window_info_macos: {e}", exc_info=True)
        return "Error", str(e)

def get_active_window_info_linux():
    """Gets active window information on Linux (X11)."""
    try:
        from Xlib import display, X
        
        d = display.Display()
        root = d.screen().root
        window_id_prop = d.intern_atom('_NET_ACTIVE_WINDOW')
        window_id_obj = root.get_full_property(window_id_prop, X.AnyPropertyType)

        if window_id_obj and window_id_obj.value:
            window_id = window_id_obj.value[0]
        else:
            logger.warning("Could not get _NET_ACTIVE_WINDOW ID on Linux.")
            return "Unknown", "No active window (X11 ID)"

        active_window = d.create_resource_object('window', window_id)
        if not active_window:
             return "Unknown", "No active window (X11 obj)"

        # Get window title
        title_prop_utf8 = d.intern_atom('_NET_WM_NAME')
        title_prop_legacy = d.intern_atom('WM_NAME')
        
        window_title_obj = active_window.get_full_property(title_prop_utf8, d.intern_atom('UTF8_STRING'))
        if not window_title_obj or not window_title_obj.value:
            window_title_obj = active_window.get_full_property(title_prop_legacy, X.AnyPropertyType) # Fallback

        window_title = "N/A (Title not found)"
        if window_title_obj and window_title_obj.value:
            if isinstance(window_title_obj.value, bytes):
                window_title = window_title_obj.value.decode('utf-8', 'replace')
            elif isinstance(window_title_obj.value, str):
                 window_title = window_title_obj.value
            else: # Sometimes it can be a list of bytes for some reason
                try:
                    window_title = b''.join(map(lambda x: x.to_bytes(1, 'little'), window_title_obj.value)).decode('utf-8', 'replace')
                except Exception:
                    window_title = str(window_title_obj.value) # Final fallback
        
        # Get process name via PID
        app_name = "Unknown"
        pid_prop = d.intern_atom('_NET_WM_PID')
        pid_obj = active_window.get_full_property(pid_prop, X.AnyPropertyType)
        if pid_obj and pid_obj.value:
            pid_val = pid_obj.value[0]
            try:
                process = psutil.Process(pid_val)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.warning(f"Could not get process name for PID {pid_val} on Linux: {e}")
        else:
            # Fallback: try WM_CLASS
            wm_class_obj = active_window.get_wm_class()
            if wm_class_obj and len(wm_class_obj) > 1:
                app_name = wm_class_obj[1] # Instance name

        return app_name, window_title
    except ImportError:
        logger.error("python-xlib is not installed. Install with: pip install python-xlib")
        return "Error: python-xlib not installed", "N/A"
    except (display.DisplayConnectionError, display.DisplayError) as e:
        logger.error(f"Cannot connect to X server or X11 error: {e}. This might be a Wayland session.")
        return "Error: X11 display issue", str(e)
    except Exception as e:
        logger.error(f"Error getting active window on Linux: {e}")
        return "Error", str(e)

def get_active_window_info():
    """Cross-platform function to get active window info."""
    os_type = platform.system().lower()
    logger.debug(f"Operating System detected: {os_type}")
    if "windows" in os_type:
        return get_active_window_info_windows()
    elif "darwin" in os_type:  # macOS
        return get_active_window_info_macos()
    elif "linux" in os_type:
        return get_active_window_info_linux()
    else:
        logger.warning(f"Unsupported OS: {os_type}")
        return "Unsupported OS", "N/A"

if __name__ == '__main__': # For basic testing of this module
    print("Attempting to get active window info for your OS...")
    current_os_type = platform.system().lower()
    if "windows" in current_os_type:
        print("OS: Windows. Ensure pywin32 and psutil are installed.")
    elif "darwin" in current_os_type:
        print("OS: macOS. Ensure pyobjc-core, pyobjc-framework-Cocoa, and psutil are installed.")
        print("NOTE: You might need to grant terminal/IDE Accessibility permissions for full functionality (System Settings > Privacy & Security > Accessibility).")
    elif "linux" in current_os_type:
        print("OS: Linux. Ensure python-xlib and psutil are installed. This works best on X11.")
    else:
        print(f"OS: {current_os_type} (Untested directly by this script's test block)")

    app, title = get_active_window_info()
    print(f"\nCurrent Active App: {app}")
    print(f"Current Window Title: {title}") 