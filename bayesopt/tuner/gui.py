#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  BAYESIAN OPTIMIZATION TUNER - GUI WINDOW
  
  This creates a popup window when you double-click START_TUNER.bat
  The tuner runs on your LAPTOP and communicates with the robot via NetworkTables.
  
  The Java code on the RoboRIO will read coefficient updates from NetworkTables.
═══════════════════════════════════════════════════════════════════════════════
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bayesopt.tuner.config import TunerConfig
from bayesopt.tuner.tuner import BayesianTunerCoordinator


class TunerGUI:
    """
    GUI Window for the Bayesian Optimization Tuner.
    
    This window provides:
    - Status display (connected/disconnected)
    - Current coefficient being tuned
    - Shot count and progress
    - Log output
    - Start/Stop controls
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bayesian Optimization Tuner")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Set window icon (if available)
        try:
            self.root.iconbitmap(default='')
        # Ignore icon errors - icon is optional and may fail on some platforms
        except Exception:
            pass
        
        # State
        self.tuner = None
        self.config = None
        self.running = False
        self.connected = False
        self.log_queue = queue.Queue()
        self.update_thread = None
        
        # Build UI
        self._build_ui()
        
        # Start log consumer
        self._consume_logs()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Auto-start on launch
        self.root.after(100, self._auto_start)
    
    def _build_ui(self):
        """Build the GUI components."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # ═══════════════════════════════════════════════════════════════════
        # Header Section
        # ═══════════════════════════════════════════════════════════════════
        header_frame = ttk.LabelFrame(main_frame, text="Bayesian Optimization Tuner", padding="10")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        main_frame.columnconfigure(0, weight=1)
        
        # Status indicators
        status_frame = ttk.Frame(header_frame)
        status_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)
        
        # Connection status
        ttk.Label(status_frame, text="Connection:").grid(row=0, column=0, sticky="w")
        self.connection_label = ttk.Label(status_frame, text="Disconnected", foreground="red")
        self.connection_label.grid(row=0, column=1, sticky="w", padx=(5, 20))
        
        # Tuner status
        ttk.Label(status_frame, text="Status:").grid(row=0, column=2, sticky="w")
        self.status_label = ttk.Label(status_frame, text="Stopped", foreground="gray")
        self.status_label.grid(row=0, column=3, sticky="w", padx=(5, 20))
        
        # Current coefficient
        ttk.Label(status_frame, text="Tuning:").grid(row=0, column=4, sticky="w")
        self.coeff_label = ttk.Label(status_frame, text="--", foreground="blue")
        self.coeff_label.grid(row=0, column=5, sticky="w", padx=(5, 0))
        
        # ═══════════════════════════════════════════════════════════════════
        # Progress Section
        # ═══════════════════════════════════════════════════════════════════
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(1, weight=1)
        
        # Shot count
        ttk.Label(progress_frame, text="Shots:").grid(row=0, column=0, sticky="w")
        self.shots_label = ttk.Label(progress_frame, text="0 / 10")
        self.shots_label.grid(row=0, column=1, sticky="w", padx=(5, 20))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        progress_frame.columnconfigure(2, weight=1)
        
        # Mode indicator
        ttk.Label(progress_frame, text="Mode:").grid(row=0, column=3, sticky="w")
        self.mode_label = ttk.Label(progress_frame, text="--")
        self.mode_label.grid(row=0, column=4, sticky="w", padx=(5, 0))
        
        # ═══════════════════════════════════════════════════════════════════
        # Log Output Section
        # ═══════════════════════════════════════════════════════════════════
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="10")
        log_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        main_frame.rowconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Scrolled text widget for logs
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 9),
            state=tk.DISABLED,
            height=15
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure text tags for coloring
        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("warning", foreground="orange")
        self.log_text.tag_configure("error", foreground="red")
        
        # ═══════════════════════════════════════════════════════════════════
        # Control Buttons Section
        # ═══════════════════════════════════════════════════════════════════
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky="ew")
        
        # Start/Stop button
        self.start_button = ttk.Button(button_frame, text="Start Tuner", command=self._toggle_tuner)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # Clear log button
        clear_button = ttk.Button(button_frame, text="Clear Log", command=self._clear_log)
        clear_button.grid(row=0, column=1, padx=(0, 10))
        
        # Info label
        info_label = ttk.Label(
            button_frame, 
            text="Dashboard controls at /Tuning/BayesianTuner/ in NetworkTables",
            foreground="gray"
        )
        info_label.grid(row=0, column=2, sticky="e")
        button_frame.columnconfigure(2, weight=1)
    
    def _log(self, message, level="info"):
        """Add a message to the log queue."""
        self.log_queue.put((message, level))
    
    def _consume_logs(self):
        """Consume log messages from the queue and display them."""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                self.log_text.configure(state=tk.NORMAL)
                timestamp = time.strftime("%H:%M:%S")
                self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", level)
                self.log_text.see(tk.END)
                self.log_text.configure(state=tk.DISABLED)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._consume_logs)
    
    def _clear_log(self):
        """Clear the log output."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _auto_start(self):
        """Automatically start the tuner on launch."""
        self._log("═" * 60, "info")
        self._log("  BAYESIAN OPTIMIZATION TUNER", "info")
        self._log("  Runs on your laptop - connects to robot via NetworkTables", "info")
        self._log("═" * 60, "info")
        self._log("", "info")
        self._log("Starting automatically...", "info")
        self._toggle_tuner()
    
    def _toggle_tuner(self):
        """Start or stop the tuner."""
        if self.running:
            self._stop_tuner()
        else:
            self._start_tuner()
    
    def _start_tuner(self):
        """Start the tuner."""
        self._log("Loading configuration...", "info")
        
        try:
            self.config = TunerConfig()
            self._log(f"  ✓ Loaded {len(self.config.COEFFICIENTS)} coefficients", "success")
            self._log(f"  ✓ Tuning order: {self.config.TUNING_ORDER}", "success")
        except Exception as e:
            self._log(f"  ✗ ERROR loading configuration: {e}", "error")
            messagebox.showerror("Configuration Error", f"Failed to load configuration:\n{e}")
            return
        
        self._log("Initializing tuner...", "info")
        try:
            self.tuner = BayesianTunerCoordinator(self.config)
            self._log("  ✓ Tuner initialized", "success")
        except Exception as e:
            self._log(f"  ✗ ERROR initializing tuner: {e}", "error")
            return
        
        self._log("", "info")
        self._log("Connecting to robot via NetworkTables...", "info")
        self._log("  Make sure:", "info")
        self._log("  1. Robot is powered on", "info")
        self._log("  2. Laptop is connected to robot network", "info")
        self._log("  3. Robot code is running", "info")
        
        try:
            self.tuner.start()
            self.connected = self.tuner.nt_interface.is_connected()
            if self.connected:
                self.connection_label.configure(text="Connected", foreground="green")
                self._log("  ✓ Connected to NetworkTables!", "success")
            else:
                self._log("  ⚠ Connection pending...", "warning")
                self._log("  Will keep trying to connect...", "info")
        except Exception as e:
            self._log(f"  ⚠ Connection pending: {e}", "warning")
            self._log("  Will keep trying to connect...", "info")
        
        # Get log directory from coordinator's logger
        log_dir = self.tuner.data_logger.log_directory
        self._log(f"  ✓ Logs will be saved to: {log_dir}", "success")
        
        self._log("", "info")
        self._log("Dashboard Controls at /Tuning/BayesianTuner/:", "info")
        self._log("  • TunerEnabled - Toggle system on/off", "info")
        self._log("  • RunOptimization - Manual trigger (when autotune OFF)", "info")
        self._log("  • SkipToNextCoefficient - Skip (when auto-advance OFF)", "info")
        self._log("  • ManualControl/ - Adjust any coefficient", "info")
        self._log("  • FineTuning/ - Aim bias adjustment", "info")
        self._log("  • Backtrack/ - Re-tune earlier coefficients", "info")
        self._log("", "info")
        self._log("Tuner is now running!", "success")
        self._log("=" * 60, "info")
        
        # Update UI state
        self.running = True
        self.start_button.configure(text="Stop Tuner")
        self.status_label.configure(text="Running", foreground="green")
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        # Start UI update
        self._update_ui()
    
    def _stop_tuner(self):
        """Stop the tuner."""
        self._log("Stopping tuner...", "info")
        self.running = False
        
        if self.tuner:
            try:
                self.tuner.stop()
                self._log("  ✓ Tuner stopped and logs saved", "success")
            except Exception as e:
                self._log(f"  ✗ Error stopping tuner: {e}", "error")
        
        self.connected = False
        self.connection_label.configure(text="Disconnected", foreground="red")
        self.status_label.configure(text="Stopped", foreground="gray")
        self.start_button.configure(text="Start Tuner")
        self.coeff_label.configure(text="--")
        self.shots_label.configure(text="0 / 10")
        self.progress_bar['value'] = 0
        self.mode_label.configure(text="--")
        
        self._log("Tuner stopped.", "info")
    
    def _update_loop(self):
        """Background thread that runs the tuner update loop."""
        # BayesianTunerCoordinator runs its own thread, so we just keep the GUI alive
        # and check if we need to update connection status
        while self.running:
            try:
                if self.tuner and self.tuner.nt_interface:
                    # The tuner is running its own thread internally
                    # We just sleep here to keep the GUI thread responsive
                    pass
                time.sleep(0.5)
            except Exception as e:
                self._log(f"Error in update loop: {e}", "error")
                time.sleep(1)
    
    def _update_ui(self):
        """Update UI elements with current tuner state."""
        if not self.running:
            return
        
        if self.tuner:
            try:
                # Update current coefficient
                current_coeff = self.tuner.optimizer.get_current_coefficient_name()
                if current_coeff:
                    self.coeff_label.configure(text=current_coeff)
                else:
                    self.coeff_label.configure(text="--")
                
                # Update shot count using public methods
                shots = self.tuner.get_accumulated_shots_count()
                autotune, threshold = self.tuner.get_current_autotune_settings()
                self.shots_label.configure(text=f"{shots} / {threshold}")
                
                # Update progress bar
                progress = (shots / threshold * 100) if threshold > 0 else 0
                self.progress_bar['value'] = min(progress, 100)
                
                # Update mode
                self.mode_label.configure(text="Autotune" if autotune else "Manual")
                
                # Update connection status
                connected = self.tuner.nt_interface.is_connected()
                if connected != self.connected:
                    self.connected = connected
                    if connected:
                        self.connection_label.configure(text="Connected", foreground="green")
                    else:
                        self.connection_label.configure(text="Connecting...", foreground="orange")
            except Exception as e:
                # Log the exception to avoid silent failures in the UI update loop
                print(f"Exception in _update_ui: {e}", file=sys.stderr)
        
        # Schedule next update
        if self.running:
            self.root.after(200, self._update_ui)
    
    def _on_close(self):
        """Handle window close."""
        if self.running:
            if messagebox.askyesno("Confirm Exit", "Tuner is still running. Stop and exit?"):
                self._stop_tuner()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI tuner."""
    app = TunerGUI()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    
