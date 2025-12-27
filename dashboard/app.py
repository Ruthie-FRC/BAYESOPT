"""
Comprehensive Browser-Based Dashboard for Bayesian Optimization Tuner.

This dashboard provides complete control over the tuning system with:
- GitHub-inspired professional design (pure white with orange accents)
- Two-level mode system (Normal/Advanced)
- Dark/Light theme toggle
- Collapsible sidebar navigation
- Keyboard shortcuts
- Real-time monitoring
- Advanced ML algorithm selection
- Danger Zone for sensitive operations
- Productivity features (Notes & To-Do)
- Optional visualizations
"""

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for tuner imports
sys.path.insert(0, str(Path(__file__).parent.parent / "bayesopt" / "tuner"))

# Check if tuner modules are available
try:
    from config import TunerConfig
    from nt_interface import NetworkTablesInterface
    TUNER_AVAILABLE = True
except ImportError:
    TUNER_AVAILABLE = False
    print("Warning: Tuner modules not available. Dashboard will run in demo mode.")

# Import dashboard modules
from dashboard_config import get_initial_app_state
from styles import CUSTOM_CSS, ROBOT_GAME_JS
from layouts import (
    create_top_nav, create_sidebar, create_dashboard_view, create_help_view
)

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="BayesOpt Dashboard"
)

# Global state management
app_state = get_initial_app_state()

# Inject custom CSS and JavaScript
app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>{CUSTOM_CSS}</style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
        <script>{ROBOT_GAME_JS}</script>
    </body>
</html>
'''

# Main layout
app.layout = html.Div(
    id='root-container',
    **{'data-theme': 'light'},  # Default theme, updated by callback
    children=[
        dcc.Store(id='app-state', data=app_state),
        dcc.Interval(id='update-interval', interval=1000),  # Update every second
        
        create_top_nav(),
        create_sidebar(),
        
        html.Div(
            id='main-content',
            className="main-content",
            children=[create_dashboard_view()]
        ),
        
        # Bottom status bar with real-time info
        html.Div(className="status-bar", children=[
            html.Div(className="status-bar-item", children=[
                html.Span("Time: "),
                html.Span(id='status-bar-time', children=datetime.now().strftime('%I:%M:%S %p'))
            ]),
            html.Div(className="status-bar-separator"),
            html.Div(className="status-bar-item", children=[
                html.Span("Date: "),
                html.Span(id='status-bar-date', children=datetime.now().strftime('%B %d, %Y'))
            ]),
            html.Div(className="status-bar-separator"),
            html.Div(className="status-bar-item", children=[
                html.Span("Battery: "),
                html.Span(id='status-bar-battery', children="--V")
            ]),
            html.Div(className="status-bar-separator"),
            html.Div(className="status-bar-item", children=[
                html.Span("Connection: "),
                html.Span(id='status-bar-signal', children="Disconnected")
            ]),
            html.Div(className="status-bar-separator"),
            html.Div(className="status-bar-item", children=[
                html.Span("Shots: "),
                html.Span(id='status-bar-shots', children="0")
            ]),
            html.Div(className="status-bar-separator"),
            html.Div(className="status-bar-item", children=[
                html.Span("Success: "),
                html.Span(id='status-bar-success', children="0.0%")
            ]),
        ]),
        
        # Hidden div for keyboard shortcut modal
        dbc.Modal(
            id='shortcuts-modal',
            children=[
                dbc.ModalHeader("Keyboard Shortcuts"),
                dbc.ModalBody(create_help_view()),
            ],
            size='lg'
        )
    ]
)

# Register all callbacks
from callbacks import register_callbacks
register_callbacks(app)

# Main execution
if __name__ == '__main__':
    import webbrowser
    import threading
    
    print("=" * 60)
    print("BayesOpt Dashboard Starting")
    print("=" * 60)
    print(f"Opening browser to: http://localhost:8050")
    print(f"Tuner integration: {'Available' if TUNER_AVAILABLE else 'Demo mode'}")
    print("=" * 60)
    
    # Open browser after a short delay to ensure server is ready
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open('http://localhost:8050')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(debug=True, host='0.0.0.0', port=8050)
