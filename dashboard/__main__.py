"""
Entry point for running the dashboard as a module.

Usage:
    python -m dashboard.app
"""

import webbrowser
import threading
import time

def open_browser():
    """Open browser after a short delay to ensure server is ready."""
    time.sleep(1.5)
    webbrowser.open('http://localhost:8050')

if __name__ == '__main__':
    from dashboard.app import app
    
    print("=" * 60)
    print("BayesOpt Dashboard Starting")
    print("=" * 60)
    print(f"Opening browser to: http://localhost:8050")
    print("=" * 60)
    
    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run_server(debug=True, host='0.0.0.0', port=8050)
  
