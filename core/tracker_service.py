import time
import logging
from . import activity_monitor # Use explicit relative import
from . import data_store       # Use explicit relative import
# from .utils import get_os # Not strictly needed here if activity_monitor handles OS specifics

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeTrackerService:
    def __init__(self, check_interval=5, idle_threshold=300):
        """
        Initializes the Time Tracker Service.

        Args:
            check_interval (int): How often (in seconds) to check for active window changes.
            idle_threshold (int): Placeholder for future idle detection (not implemented in this version).
        """
        self.running = False
        self.check_interval = check_interval
        self.idle_threshold = idle_threshold # Placeholder for future use
        
        self.last_app_name = None
        self.last_window_title = None
        self.current_activity_start_time = None
        # self.last_active_time = time.time() # For more sophisticated idle detection

        # Initialize database (ensures tables are created)
        data_store.init_db()
        logger.info("TimeTrackerService initialized. Database connection established and tables ensured.")

    def _update_activity(self, app_name, window_title):
        """
        Logs the previously tracked activity and starts tracking the new one.
        If the app_name or window_title is None, it implies an issue fetching info, 
        so we might log an 'Unknown' state or simply reset.
        """
        current_time = time.time()

        # Log the previous activity if there was one
        if self.current_activity_start_time and self.last_app_name is not None:
            duration = int(current_time - self.current_activity_start_time)
            if duration > 0: # Log only if duration is meaningful
                logger.info(
                    f"Logging activity: App='{self.last_app_name}', "
                    f"Title='{self.last_window_title}', Duration={duration}s"
                )
                data_store.log_activity(self.last_app_name, self.last_window_title, duration)
        
        # Start tracking the new activity
        self.last_app_name = app_name if app_name is not None else "UnknownApp"
        self.last_window_title = window_title if window_title is not None else "UnknownTitle"
        self.current_activity_start_time = current_time
        # self.last_active_time = current_time # Reset idle timer

    def _handle_no_window_info(self):
        """Handles the case where no window information could be retrieved."""
        # If we were tracking something, log it as ending.
        # Then, log a special state like 'ScreenLocked' or 'NoFocus'.
        # For now, we'll treat it as a transition to an 'Unknown/Error' state.
        if self.last_app_name != "Unknown/Error": # Avoid repeatedly logging this state
            logger.warning("No active window information retrieved. Logging as Unknown/Error.")
            self._update_activity("Unknown/Error", "Could not retrieve window info")
        # Keep current_activity_start_time for this "Unknown/Error" state
        # until a valid window is detected again.

    def run(self):
        """Starts the main loop of the tracker service."""
        self.running = True
        logger.info(f"Time Tracker Service starting. Check interval: {self.check_interval}s.")
        
        # Initialize with the current window when the service starts
        try:
            app_name, window_title = activity_monitor.get_active_window_info()
            if app_name is not None: # Ensure we got valid info
                self._update_activity(app_name, window_title)
            else:
                # Handle cases where initial fetch might fail (e.g. immediately after login)
                logger.warning("Initial window fetch failed. Starting with 'Startup' state.")
                self._update_activity("Startup", "Initializing service")
        except Exception as e:
            logger.error(f"Error during initial window fetch: {e}. Starting with 'Startup' state.")
            self._update_activity("Startup", f"Initialization error: {e}")

        try:
            while self.running:
                current_app_name, current_window_title = activity_monitor.get_active_window_info()

                if current_app_name is None: # Indicates an issue or no discernible active window
                    self._handle_no_window_info()
                # Check if the active application or window title has changed
                elif current_app_name != self.last_app_name or current_window_title != self.last_window_title:
                    logger.debug(f"Activity changed: NewApp='{current_app_name}', NewTitle='{current_window_title}'")
                    self._update_activity(current_app_name, current_window_title)
                # else: Activity is the same, do nothing until next check
                
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Service interrupted by user (KeyboardInterrupt).")
        except Exception as e:
            logger.error(f"An unexpected error occurred in the service loop: {e}", exc_info=True)
        finally:
            # Log the final activity before exiting, if one was being tracked
            if self.running and self.current_activity_start_time and self.last_app_name is not None:
                 duration = int(time.time() - self.current_activity_start_time)
                 if duration > 0:
                    logger.info(
                        f"Logging final activity before stop: App='{self.last_app_name}', "
                        f"Title='{self.last_window_title}', Duration={duration}s"
                    )
                    data_store.log_activity(self.last_app_name, self.last_window_title, duration)
            self.running = False
            logger.info("Time Tracker Service stopped.")

    def stop(self):
        """Signals the service to stop its main loop."""
        logger.info("Stop signal received. Shutting down service...")
        self.running = False

if __name__ == '__main__': # For testing the service directly
    print("Running TimeTrackerService directly for testing (Ctrl+C to stop)...")
    # Ensure core modules are discoverable if run this way
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    # Re-import with adjusted path if necessary, though relative imports should work if invoked correctly
    # from core import activity_monitor, data_store

    service = TimeTrackerService(check_interval=3) # Check more frequently for testing
    service.run() 