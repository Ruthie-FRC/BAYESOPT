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
from dash import dcc, html, Input, Output, State, callback_context, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for tuner imports
sys.path.insert(0, str(Path(__file__).parent.parent / "bayesopt" / "tuner"))

try:
    from config import TunerConfig
    from nt_interface import NetworkTablesInterface
    TUNER_AVAILABLE = True
except ImportError:
    TUNER_AVAILABLE = False
    print("Warning: Tuner modules not available. Dashboard will run in demo mode.")

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="BayesOpt Dashboard"
)

# Global state management
app_state = {
    'mode': 'normal',  # 'normal' or 'advanced'
    'theme': 'light',  # 'light' or 'dark'
    'more_features': False,
    'sidebar_collapsed': False,
    'tuner_enabled': False,
    'current_coefficient': 'kDragCoefficient',
    'coefficient_values': {},
    'notes': [],
    'todos': [],
    'selected_algorithm': 'gp',
    'graphs_visible': {
        'success_rate': True,
        'coefficient_history': True,
        'optimization_progress': True,
        'shot_distribution': False
    },
    'banner_dismissed': False,
    'config_locked': False,
    'shot_count': 0,
    'success_rate': 0.0,
    'connection_status': 'disconnected'
}

# GitHub-inspired CSS with pure white background and orange accents
CUSTOM_CSS = """
/* GitHub-Inspired Design System */
:root {
    /* Light theme (default) - Pure white with orange accents */
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #f0f0f0;
    --text-primary: #24292f;
    --text-secondary: #57606a;
    --text-tertiary: #656d76;
    --border-default: #d0d7de;
    --border-muted: #e8e8e8;
    
    /* Orange accent colors (team color) */
    --accent-primary: #FF8C00;
    --accent-hover: #E67E00;
    --accent-active: #CC7000;
    --accent-subtle: #FFF4E6;
    
    /* Semantic colors */
    --success: #1a7f37;
    --danger: #cf222e;
    --warning: #9a6700;
    --info: #0969da;
    
    /* Shadows */
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
    --shadow-md: 0 2px 6px rgba(0,0,0,0.08);
    --shadow-lg: 0 4px 12px rgba(0,0,0,0.12);
    
    /* Spacing (8px grid) */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    
    /* Typography */
    --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    --font-size-xs: 12px;
    --font-size-sm: 14px;
    --font-size-md: 16px;
    --font-size-lg: 20px;
    --font-size-xl: 24px;
}

[data-theme="dark"] {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --text-tertiary: #6e7681;
    --border-default: #30363d;
    --border-muted: #21262d;
    --accent-subtle: #1c1004;
}

body {
    font-family: var(--font-family);
    background-color: var(--bg-primary);
    color: var(--text-primary);
    margin: 0;
    padding: 0;
}

/* Top Navigation Bar */
.top-nav {
    height: 60px;
    background-color: var(--bg-primary);
    border-bottom: 1px solid var(--border-default);
    box-shadow: var(--shadow-sm);
    display: flex;
    align-items: center;
    padding: 0 var(--space-lg);
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
}

.top-nav-title {
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin-right: var(--space-xl);
}

/* Sidebar */
.sidebar {
    width: 240px;
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border-default);
    position: fixed;
    top: 60px;
    left: 0;
    bottom: 0;
    overflow-y: auto;
    transition: transform 200ms ease;
    z-index: 900;
}

.sidebar.collapsed {
    transform: translateX(-176px);
    width: 64px;
}

.sidebar-menu-item {
    padding: var(--space-sm) var(--space-md);
    color: var(--text-primary);
    text-decoration: none;
    display: flex;
    align-items: center;
    transition: all 150ms ease;
    cursor: pointer;
    font-size: var(--font-size-sm);
    border: none;
    background: none;
    width: 100%;
    text-align: left;
    border-left: 3px solid transparent;
}

.sidebar-menu-item:hover {
    background-color: var(--bg-tertiary);
    border-left-color: var(--accent-primary);
    padding-left: calc(var(--space-md) + 3px);
}

.sidebar-menu-item:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: -2px;
}

.sidebar-menu-item.active {
    background-color: var(--accent-subtle);
    color: var(--accent-primary);
    font-weight: 600;
    border-left-color: var(--accent-primary);
    border-left-width: 4px;
}

/* Main Content */
.main-content {
    margin-left: 240px;
    margin-top: 60px;
    margin-bottom: 32px; /* Space for status bar */
    padding: var(--space-md);
    transition: margin-left 200ms ease;
    min-height: calc(100vh - 92px);
    max-height: calc(100vh - 92px);
    overflow-y: auto;
}

.main-content.expanded {
    margin-left: 64px;
}

/* Breadcrumb */
.breadcrumb {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-sm) 0;
    margin-bottom: var(--space-md);
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
}

.breadcrumb-item {
    color: var(--text-secondary);
}

.breadcrumb-item.active {
    color: var(--text-primary);
    font-weight: 600;
}

.breadcrumb-separator {
    color: var(--text-tertiary);
}

/* Cards */
.card {
    background-color: var(--bg-primary);
    border: 1px solid var(--border-default);
    border-radius: 6px;
    padding: var(--space-sm);
    margin-bottom: var(--space-sm);
    box-shadow: var(--shadow-sm);
    transition: box-shadow 150ms ease;
}

.card:hover {
    box-shadow: var(--shadow-md);
}

.card-header {
    font-size: var(--font-size-md);
    font-weight: 600;
    margin-bottom: var(--space-sm);
    color: var(--text-primary);
    padding-bottom: var(--space-xs);
    border-bottom: 1px solid var(--border-muted);
}

/* Buttons */
.btn-primary {
    background-color: var(--accent-primary);
    color: white;
    border: none;
    padding: var(--space-sm) var(--space-md);
    border-radius: 6px;
    font-size: var(--font-size-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.btn-primary:hover {
    background-color: var(--accent-hover);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transform: translateY(-1px);
}

.btn-primary:active {
    background-color: var(--accent-active);
    transform: translateY(0);
}

.btn-primary:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}

.btn-secondary {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    border: 1px solid var(--border-default);
    padding: var(--space-sm) var(--space-md);
    border-radius: 6px;
    font-size: var(--font-size-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
}

.btn-secondary:hover {
    border-color: var(--text-secondary);
    background-color: var(--bg-secondary);
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.btn-secondary:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}

.btn-danger {
    background-color: var(--danger);
    color: white;
    border: none;
    padding: var(--space-sm) var(--space-md);
    border-radius: 6px;
    font-size: var(--font-size-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
}

.btn-danger:hover {
    background-color: #b91c1c;
    box-shadow: 0 2px 4px rgba(207,34,46,0.2);
}

.btn-danger:focus {
    outline: 2px solid var(--danger);
    outline-offset: 2px;
}

/* Tables */
.table-github {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--font-size-sm);
}

.table-github th {
    background-color: var(--bg-secondary);
    padding: var(--space-sm);
    text-align: left;
    font-weight: 600;
    border-bottom: 1px solid var(--border-default);
}

.table-github td {
    padding: var(--space-sm);
    border-bottom: 1px solid var(--border-muted);
}

/* Status Indicators */
.status-connected {
    color: var(--success);
}

.status-disconnected {
    color: var(--danger);
}

.status-paused {
    color: var(--warning);
}

/* Banner */
.banner {
    background-color: var(--accent-subtle);
    border: 1px solid var(--accent-primary);
    padding: var(--space-sm) var(--space-md);
    border-radius: 6px;
    margin-bottom: var(--space-md);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Animations */
@media (prefers-reduced-motion: no-preference) {
    .fade-in {
        animation: fadeIn 200ms ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
}

/* Input and Form Styling */
input[type="text"],
input[type="number"],
textarea,
select {
    background-color: var(--bg-primary);
    border: 1px solid var(--border-default);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: var(--font-size-sm);
    color: var(--text-primary);
    transition: all 150ms ease;
    width: 100%;
}

input:focus,
textarea:focus,
select:focus {
    border-color: var(--accent-primary);
    outline: none;
    box-shadow: 0 0 0 3px var(--accent-subtle);
}

input:disabled,
textarea:disabled,
select:disabled {
    background-color: var(--bg-secondary);
    color: var(--text-tertiary);
    cursor: not-allowed;
}

/* Loading States */
.loading {
    opacity: 0.6;
    pointer-events: none;
    position: relative;
}

.loading::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 20px;
    height: 20px;
    margin: -10px 0 0 -10px;
    border: 2px solid var(--accent-primary);
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Tooltip Styles */
.tooltip-text {
    visibility: hidden;
    background-color: var(--text-primary);
    color: var(--bg-primary);
    text-align: center;
    border-radius: 6px;
    padding: 5px 10px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity 150ms;
    font-size: var(--font-size-xs);
    white-space: nowrap;
}

.has-tooltip:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}

/* Responsive */
@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
    }
    
    .main-content {
        margin-left: 0;
    }
    
    .top-nav {
        padding: 0 var(--space-sm);
    }
}

/* Robot Game Styles */
#robot-game-container canvas {
    image-rendering: pixelated;
    image-rendering: crisp-edges;
}

/* Status Bar at Bottom */
.status-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 32px;
    background: linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-hover) 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 var(--space-md);
    font-size: var(--font-size-xs);
    z-index: 999;
    box-shadow: 0 -1px 3px rgba(0,0,0,0.1);
}

.status-bar-item {
    display: flex;
    align-items: center;
    gap: var(--space-xs);
}

.status-bar-separator {
    height: 16px;
    width: 1px;
    background-color: rgba(255,255,255,0.3);
    margin: 0 var(--space-sm);
}



/* Glowing recommendation button */
.btn-recommended {
    animation: glow-pulse 2s ease-in-out infinite;
    box-shadow: 0 0 10px rgba(255, 140, 0, 0.5);
}

@keyframes glow-pulse {
    0%, 100% {
        box-shadow: 0 0 10px rgba(255, 140, 0, 0.5);
    }
    50% {
        box-shadow: 0 0 20px rgba(255, 140, 0, 0.8), 0 0 30px rgba(255, 140, 0, 0.4);
    }
}

/* Orange Checkboxes and Switches */
.form-check-input {
    border-color: var(--border-default) !important;
    accent-color: var(--accent-primary) !important;
}

.form-check-input:checked {
    background-color: var(--accent-primary) !important;
    border-color: var(--accent-primary) !important;
}

.form-check-input:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px var(--accent-subtle) !important;
}

/* Orange Range Sliders */
input[type="range"] {
    accent-color: var(--accent-primary) !important;
}

input[type="range"]::-webkit-slider-thumb {
    background: var(--accent-primary) !important;
    border: 2px solid var(--accent-primary) !important;
}

input[type="range"]::-moz-range-thumb {
    background: var(--accent-primary) !important;
    border: 2px solid var(--accent-primary) !important;
}

input[type="range"]::-webkit-slider-runnable-track {
    background: linear-gradient(to right, 
        var(--accent-primary) 0%, 
        var(--accent-primary) var(--value, 50%), 
        var(--border-default) var(--value, 50%), 
        var(--border-default) 100%) !important;
}

input[type="range"]::-moz-range-track {
    background: var(--border-default) !important;
}

input[type="range"]::-moz-range-progress {
    background: var(--accent-primary) !important;
}

/* Dash Bootstrap Checklist Styling */
.checklist-input {
    accent-color: var(--accent-primary) !important;
}
"""

# Robot Game JavaScript
ROBOT_GAME_JS = """
// Simple Robot Runner Game (Chrome dino style)
class RobotGame {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.isRunning = false;
        this.score = 0;
        this.gameSpeed = 3;
        
        // Robot properties
        this.robot = {
            x: 50,
            y: 150,
            width: 30,
            height: 30,
            jumping: false,
            velocityY: 0,
            gravity: 0.6
        };
        
        // Obstacles
        this.obstacles = [];
        this.frameCount = 0;
        
        // Bind keyboard
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                if (!this.isRunning) {
                    this.start();
                } else {
                    this.jump();
                }
            }
        });
    }
    
    start() {
        this.isRunning = true;
        this.score = 0;
        this.obstacles = [];
        this.robot.y = 150;
        this.robot.velocityY = 0;
        this.robot.jumping = false;
        this.gameLoop();
    }
    
    jump() {
        if (!this.robot.jumping) {
            this.robot.velocityY = -12;
            this.robot.jumping = true;
        }
    }
    
    update() {
        // Update robot
        this.robot.velocityY += this.robot.gravity;
        this.robot.y += this.robot.velocityY;
        
        // Ground collision
        if (this.robot.y > 150) {
            this.robot.y = 150;
            this.robot.velocityY = 0;
            this.robot.jumping = false;
        }
        
        // Create obstacles
        this.frameCount++;
        if (this.frameCount % 120 === 0) {
            this.obstacles.push({
                x: 800,
                y: 160,
                width: 20,
                height: 40
            });
        }
        
        // Update obstacles
        this.obstacles = this.obstacles.filter(obs => {
            obs.x -= this.gameSpeed;
            
            // Check collision
            if (this.checkCollision(this.robot, obs)) {
                this.isRunning = false;
                return false;
            }
            
            // Remove off-screen obstacles
            if (obs.x + obs.width < 0) {
                this.score += 10;
                return false;
            }
            
            return true;
        });
        
        // Increase difficulty
        if (this.frameCount % 300 === 0) {
            this.gameSpeed += 0.2;
        }
    }
    
    checkCollision(rect1, rect2) {
        return rect1.x < rect2.x + rect2.width &&
               rect1.x + rect1.width > rect2.x &&
               rect1.y < rect2.y + rect2.height &&
               rect1.y + rect1.height > rect2.y;
    }
    
    draw() {
        // Clear canvas
        this.ctx.fillStyle = getComputedStyle(document.documentElement)
            .getPropertyValue('--bg-secondary').trim();
        this.ctx.fillRect(0, 0, 800, 200);
        
        // Draw ground
        this.ctx.strokeStyle = getComputedStyle(document.documentElement)
            .getPropertyValue('--border-default').trim();
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(0, 180);
        this.ctx.lineTo(800, 180);
        this.ctx.stroke();
        
        // Draw robot (simple geometric shape)
        this.ctx.fillStyle = getComputedStyle(document.documentElement)
            .getPropertyValue('--accent-primary').trim();
        
        // Robot body
        this.ctx.fillRect(this.robot.x, this.robot.y, this.robot.width, this.robot.height);
        
        // Robot head
        this.ctx.fillRect(this.robot.x + 5, this.robot.y - 10, 20, 10);
        
        // Robot eyes
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(this.robot.x + 8, this.robot.y - 7, 5, 5);
        this.ctx.fillRect(this.robot.x + 17, this.robot.y - 7, 5, 5);
        
        // Draw obstacles
        this.ctx.fillStyle = getComputedStyle(document.documentElement)
            .getPropertyValue('--danger').trim();
        this.obstacles.forEach(obs => {
            this.ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
        });
        
        // Update score display
        const scoreDiv = document.getElementById('game-score');
        if (scoreDiv) {
            scoreDiv.textContent = 'Score: ' + this.score;
        }
        
        // Game over message
        if (!this.isRunning && this.score > 0) {
            this.ctx.fillStyle = getComputedStyle(document.documentElement)
                .getPropertyValue('--text-primary').trim();
            this.ctx.font = '24px var(--font-family)';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('Game Over! Press SPACE to restart', 400, 100);
        }
    }
    
    gameLoop() {
        if (this.isRunning) {
            this.update();
        }
        this.draw();
        
        if (this.isRunning) {
            requestAnimationFrame(() => this.gameLoop());
        }
    }
}

// Initialize game when canvas is ready
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (document.getElementById('game-canvas')) {
            window.robotGame = new RobotGame('game-canvas');
        }
    }, 100);
});
"""

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


def create_top_nav():
    """Create the top navigation bar."""
    return html.Div(
        className="top-nav",
        children=[
            html.Div([
                html.Div("BayesOpt Dashboard", className="top-nav-title")
            ]),
            html.Div(
                style={'marginLeft': 'auto', 'display': 'flex', 'gap': '16px', 'alignItems': 'center'},
                children=[
                    # Connection status with icon
                    html.Div(id='connection-status', style={'display': 'flex', 'alignItems': 'center', 'gap': '8px'}, children=[
                        html.Span("● ", className="status-disconnected", style={'fontSize': '16px'}),
                        html.Div([
                            html.Div("Disconnected", style={'fontSize': '14px', 'fontWeight': '500'}),
                            html.Div("No robot", style={'fontSize': '11px', 'color': 'var(--text-tertiary)'})
                        ])
                    ]),
                    # Mode toggle
                    dbc.Button(
                        "Switch to Advanced",
                        id='mode-toggle',
                        className="btn-secondary",
                        size="sm",
                        title="Switch between Normal and Advanced modes"
                    ),
                ]
            )
        ]
    )


def create_sidebar():
    """Create the collapsible sidebar navigation."""
    return html.Div(
        id='sidebar',
        className="sidebar",
        children=[
            dbc.Button("☰", id='sidebar-toggle', className="btn-secondary", style={'margin': '8px'}),
            html.Hr(),
            html.Div([
                html.Button("Dashboard", id={'type': 'nav-btn', 'index': 'dashboard'}, className="sidebar-menu-item active"),
                html.Button("Coefficients", id={'type': 'nav-btn', 'index': 'coefficients'}, className="sidebar-menu-item"),
                html.Button("Order & Workflow", id={'type': 'nav-btn', 'index': 'workflow'}, className="sidebar-menu-item"),
                html.Button("Graphs & Analytics", id={'type': 'nav-btn', 'index': 'graphs'}, className="sidebar-menu-item"),
                html.Button("Settings", id={'type': 'nav-btn', 'index': 'settings'}, className="sidebar-menu-item"),
                html.Button("Robot Status", id={'type': 'nav-btn', 'index': 'robot'}, className="sidebar-menu-item"),
                html.Button("Notes & To-Do", id={'type': 'nav-btn', 'index': 'notes'}, className="sidebar-menu-item"),
                html.Button("Danger Zone", id={'type': 'nav-btn', 'index': 'danger'}, className="sidebar-menu-item"),
                html.Button("System Logs", id={'type': 'nav-btn', 'index': 'logs'}, className="sidebar-menu-item"),
                html.Button("Help", id={'type': 'nav-btn', 'index': 'help'}, className="sidebar-menu-item"),
            ])
        ]
    )


def create_robot_game_view():
    """Create the robot jumping game (appears when disconnected)."""
    return html.Div(
        id='robot-game-container',
        style={
            'display': 'none',  # Hidden by default, shown when disconnected
            'textAlign': 'center',
            'padding': '50px 0'
        },
        children=[
            html.Div(className="card", style={'maxWidth': '800px', 'margin': '0 auto'}, children=[
                html.Div("Robot Runner", className="card-header", style={'fontSize': '32px'}),
                html.P("Connection to robot lost. Press SPACE to play!", style={'fontSize': '16px', 'color': 'var(--text-secondary)'}),
                html.Canvas(
                    id='game-canvas',
                    width=800,
                    height=200,
                    style={
                        'border': '2px solid var(--border-default)',
                        'borderRadius': '6px',
                        'backgroundColor': 'var(--bg-secondary)',
                        'display': 'block',
                        'margin': '20px auto'
                    }
                ),
                html.Div(id='game-score', children="Score: 0", style={'fontSize': '24px', 'fontWeight': 'bold', 'color': 'var(--accent-primary)'}),
                html.P("Press SPACE to jump over obstacles!", style={'fontSize': '14px', 'marginTop': '10px'}),
                html.P("Game automatically appears when robot is disconnected", style={'fontSize': '12px', 'color': 'var(--text-tertiary)', 'fontStyle': 'italic'}),
            ])
        ]
    )


def create_dashboard_view():
    """Create the main dashboard view with quick actions."""
    return html.Div([
        # Robot game (shown when disconnected)
        create_robot_game_view(),
        
        # Breadcrumb navigation
        html.Div(className="breadcrumb", children=[
            html.Span("Home", className="breadcrumb-item"),
            html.Span("/", className="breadcrumb-separator"),
            html.Span("Dashboard", className="breadcrumb-item active"),
        ]),
        
        # Dismissible banner
        html.Div(
            id='keyboard-banner',
            className="banner",
            children=[
                html.Span("Tip: Press ? to view all keyboard shortcuts for faster control"),
                dbc.Button("✕", id='dismiss-banner', size="sm", className="btn-secondary", style={'marginLeft': 'auto'})
            ],
            style={'display': 'none' if app_state['banner_dismissed'] else 'flex'}
        ),
        
        # Main dashboard grid
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '12px', '@media (max-width: 768px)': {'gridTemplateColumns': '1fr'}}, children=[
            # Left column - Quick actions and status
            html.Div([
                # Quick actions card
                html.Div(className="card", children=[
                    html.Div("Quick Actions", className="card-header"),
                    html.P("Start tuning with a single click", style={'fontSize': '14px', 'color': 'var(--text-secondary)', 'marginBottom': '12px'}),
                    html.Div(style={'display': 'flex', 'flexDirection': 'column', 'gap': '8px'}, children=[
                        dbc.Button("Start Tuner (Ctrl+S)", id='start-tuner-btn', className="btn-primary", style={'width': '100%', 'padding': '10px'}),
                        dbc.Button("Stop Tuner (Ctrl+Q)", id='stop-tuner-btn', className="btn-danger", style={'width': '100%', 'padding': '10px'}),
                        dbc.Button("Run Optimization (Ctrl+O)", id='run-optimization-btn', className="btn-primary", style={'width': '100%', 'padding': '10px'}),
                        dbc.Button("Skip Coefficient (Ctrl+K)", id='skip-coefficient-btn', className="btn-secondary", style={'width': '100%', 'padding': '10px'}),
                    ])
                ]),
                
                # Current status card
                html.Div(className="card", children=[
                    html.Div("Current Status", className="card-header"),
                    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '12px'}, children=[
                        html.Div([
                            html.Label("Mode", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                            html.P(f"{app_state['mode'].title()}", id='mode-display', style={'fontSize': '16px', 'fontWeight': '600', 'margin': '2px 0'}),
                        ]),
                        html.Div([
                            html.Label("Coefficient", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                            html.P(f"{app_state['current_coefficient']}", id='coeff-display', style={'fontSize': '16px', 'fontWeight': '600', 'margin': '2px 0'}),
                        ]),
                        html.Div([
                            html.Label("Shot Count", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                            html.P(f"{app_state['shot_count']}", id='shot-display', style={'fontSize': '16px', 'fontWeight': '600', 'margin': '2px 0'}),
                        ]),
                        html.Div([
                            html.Label("Success Rate", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                            html.P(f"{app_state['success_rate']:.1%}", id='success-display', style={'fontSize': '16px', 'fontWeight': '600', 'margin': '2px 0', 'color': 'var(--success)'}),
                        ]),
                    ])
                ]),
            ]),
            
            # Right column - Navigation and fine tuning
            html.Div([
                # Coefficient navigation
                html.Div(className="card", children=[
                    html.Div("Coefficient Navigation", className="card-header"),
                    html.P("Navigate between coefficients", style={'fontSize': '14px', 'color': 'var(--text-secondary)', 'marginBottom': '12px'}),
                    html.Div(style={'display': 'flex', 'gap': '8px'}, children=[
                        dbc.Button("◀ Previous (Ctrl+←)", id='prev-coeff-btn', className="btn-secondary", style={'flex': '1', 'padding': '10px'}),
                        dbc.Button("Next ▶ (Ctrl+→)", id='next-coeff-btn', className="btn-secondary", style={'flex': '1', 'padding': '10px'}),
                    ])
                ]),
                
                # Fine tuning controls
                html.Div(className="card", children=[
                    html.Div("Fine Tuning Controls", className="card-header"),
                    html.P("Adjust current coefficient in small increments", style={'fontSize': '14px', 'color': 'var(--text-secondary)', 'marginBottom': '12px'}),
                    html.Div(style={'display': 'flex', 'flexDirection': 'column', 'gap': '8px', 'alignItems': 'center'}, children=[
                        dbc.Button("⬆ Up (Ctrl+↑)", id='fine-tune-up-btn', className="btn-secondary", style={'width': '160px', 'padding': '8px'}),
                        html.Div(style={'display': 'flex', 'gap': '8px', 'justifyContent': 'center', 'width': '100%'}, children=[
                            dbc.Button("← Left", id='fine-tune-left-btn', className="btn-secondary", style={'padding': '8px 12px'}),
                            dbc.Button("Reset", id='fine-tune-reset-btn', className="btn-secondary", style={'padding': '8px 16px'}),
                            dbc.Button("Right ➡", id='fine-tune-right-btn', className="btn-secondary", style={'padding': '8px 12px'}),
                        ]),
                        dbc.Button("⬇ Down (Ctrl+↓)", id='fine-tune-down-btn', className="btn-secondary", style={'width': '160px', 'padding': '8px'}),
                    ])
                ]),
            ]),
        ]),
    ])


def create_coefficients_view():
    """Create the comprehensive coefficients management view with ALL 7 parameters."""
    # All 7 coefficients with their actual ranges and defaults
    coefficients = {
        'kDragCoefficient': {'min': 0.001, 'max': 0.01, 'default': 0.003, 'step': 0.0001},
        'kGravity': {'min': 9.0, 'max': 10.0, 'default': 9.81, 'step': 0.01},
        'kShotHeight': {'min': 0.0, 'max': 3.0, 'default': 1.0, 'step': 0.01},
        'kTargetHeight': {'min': 0.0, 'max': 5.0, 'default': 2.5, 'step': 0.01},
        'kShooterAngle': {'min': 0, 'max': 90, 'default': 45, 'step': 1},
        'kShooterRPM': {'min': 0, 'max': 6000, 'default': 3000, 'step': 50},
        'kExitVelocity': {'min': 0, 'max': 30, 'default': 15, 'step': 0.1}
    }
    
    return html.Div([
        # Header with summary
        html.Div(className="card", children=[
            html.Div("All Coefficients - Real-Time Control", className="card-header"),
            html.P("Adjust all 7 shooting parameters with interactive sliders. Changes sync to robot in real-time."),
            html.Div(style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap', 'marginTop': '16px'}, children=[
                dbc.Button("⬆ Increase All 10%", id='increase-all-btn', className="btn-secondary", size="sm"),
                dbc.Button("⬇ Decrease All 10%", id='decrease-all-btn', className="btn-secondary", size="sm"),
                dbc.Button("Reset All to Defaults", id='reset-all-coeff-btn', className="btn-secondary", size="sm"),
                dbc.Button("Copy Current Values", id='copy-coeff-btn', className="btn-secondary", size="sm"),
            ])
        ]),
        
        # Individual coefficient cards with full controls
        html.Div([
            html.Div(className="card", style={'marginBottom': '12px', 'backgroundColor': 'var(--accent-subtle)' if coeff == 'kDragCoefficient' else 'var(--bg-primary)'}, children=[
                # Header row with coefficient name and jump button
                html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '12px'}, children=[
                    html.Div([
                        html.Span(coeff, style={'fontWeight': 'bold', 'fontSize': '16px'}),
                        html.Span(f" (Current: {params['default']})", style={'color': 'var(--text-secondary)', 'fontSize': '14px', 'marginLeft': '8px'}),
                    ]),
                    html.Div(style={'display': 'flex', 'gap': '4px'}, children=[
                        dbc.Button("⭐", id={'type': 'pin-coeff-btn', 'index': coeff}, size="sm", className="btn-secondary", title="Pin this value"),
                        dbc.Button("Jump to", id={'type': 'jump-to-btn', 'index': coeff}, size="sm", className="btn-primary")
                    ])
                ]),
                
                # Range info
                html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'fontSize': '12px', 'color': 'var(--text-secondary)', 'marginBottom': '8px'}, children=[
                    html.Span(f"Min: {params['min']}"),
                    html.Span(f"Default: {params['default']}"),
                    html.Span(f"Max: {params['max']}")
                ]),
                
                # Main slider
                dcc.Slider(
                    id={'type': 'coeff-slider', 'index': coeff},
                    min=params['min'],
                    max=params['max'],
                    value=params['default'],
                    step=params['step'],
                    marks={
                        params['min']: str(params['min']),
                        params['default']: {'label': str(params['default']), 'style': {'color': 'var(--accent-primary)'}},
                        params['max']: str(params['max'])
                    },
                    tooltip={'placement': 'bottom', 'always_visible': True}
                ),
                
                # Fine adjustment buttons
                html.Div(style={'display': 'flex', 'gap': '4px', 'marginTop': '12px', 'justifyContent': 'center'}, children=[
                    dbc.Button("--", id={'type': 'fine-dec-large', 'index': coeff}, size="sm", className="btn-secondary", title=f"-{params['step']*10}"),
                    dbc.Button("-", id={'type': 'fine-dec', 'index': coeff}, size="sm", className="btn-secondary", title=f"-{params['step']}"),
                    dbc.Button("Reset", id={'type': 'reset-coeff', 'index': coeff}, size="sm", className="btn-secondary"),
                    dbc.Button("+", id={'type': 'fine-inc', 'index': coeff}, size="sm", className="btn-secondary", title=f"+{params['step']}"),
                    dbc.Button("++", id={'type': 'fine-inc-large', 'index': coeff}, size="sm", className="btn-secondary", title=f"+{params['step']*10}"),
                ]),
                
                # Per-coefficient settings (Advanced mode)
                html.Div(id={'type': 'coeff-advanced-settings', 'index': coeff}, style={'display': 'none'}, children=[
                    html.Hr(),
                    html.Div("Per-Coefficient Settings", style={'fontWeight': 'bold', 'fontSize': '14px', 'marginBottom': '8px'}),
                    dbc.Checklist(
                        id={'type': 'coeff-overrides', 'index': coeff},
                        options=[
                            {'label': 'Override autotune settings', 'value': 'autotune_override'},
                            {'label': 'Override auto-advance settings', 'value': 'auto_advance_override'},
                            {'label': 'Lock this coefficient', 'value': 'locked'},
                            {'label': 'Skip in tuning order', 'value': 'skip'},
                        ],
                        value=[],
                        switch=True,
                        inline=False
                    ),
                    html.Div(id={'type': 'coeff-override-inputs', 'index': coeff}, style={'marginTop': '8px'}, children=[
                        html.Label("Custom shot threshold:", style={'fontSize': '12px'}),
                        dbc.Input(type="number", value=10, id={'type': 'coeff-threshold', 'index': coeff}, size="sm"),
                    ])
                ])
            ]) for coeff, params in coefficients.items()
        ]),
        
        # Pinned values section
        html.Div(className="card", children=[
            html.Div("📌 Pinned Values", className="card-header"),
            html.P("Save and quickly restore coefficient sets", style={'color': 'var(--text-secondary)'}),
            html.Div(id='pinned-values-list', children=[
                html.P("No pinned values yet. Click ⭐ on any coefficient to pin it.", style={'fontStyle': 'italic', 'color': 'var(--text-secondary)'})
            ])
        ]),
        
        # Coefficient history
        html.Div(className="card", children=[
            html.Div("Coefficient History", className="card-header"),
            html.Div(id='coefficient-history-table', children=[
                html.Table(className="table-github", children=[
                    html.Thead([
                        html.Tr([
                            html.Th("Timestamp"),
                            html.Th("Coefficient"),
                            html.Th("Old Value"),
                            html.Th("New Value"),
                            html.Th("Reason"),
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td("--:--:--"),
                            html.Td("--"),
                            html.Td("--"),
                            html.Td("--"),
                            html.Td("No history yet")
                        ])
                    ])
                ])
            ])
        ])
    ])


def create_graphs_view():
    """Create comprehensive graphs and analytics view with ALL visualizations."""
    return html.Div([
        # Graph controls
        html.Div(className="card", children=[
            html.Div("Graph Visibility & Controls", className="card-header"),
            html.P("Toggle individual graphs on/off to customize your view", style={'color': 'var(--text-secondary)'}),
            dbc.Checklist(
                id='graph-toggles',
                options=[
                    {'label': 'Shot Success Rate Over Time', 'value': 'success_rate'},
                    {'label': 'Coefficient Value History', 'value': 'coefficient_history'},
                    {'label': 'Optimization Progress by Coefficient', 'value': 'optimization_progress'},
                    {'label': 'Shot Distribution Analysis', 'value': 'shot_distribution'},
                    {'label': 'Algorithm Performance Comparison (Advanced)', 'value': 'algorithm_comparison'},
                    {'label': 'Convergence Plot (Advanced)', 'value': 'convergence'},
                    {'label': 'Heat Map - Distance vs Angle', 'value': 'heatmap'},
                    {'label': 'Shot Velocity Distribution', 'value': 'velocity_dist'},
                ],
                value=['success_rate', 'coefficient_history', 'optimization_progress'],
                switch=True
            ),
            html.Small("Success Rate Over Time: Track how success rate improves with each shot (hover to see coefficients)", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '4px'}),
            html.Small("Coefficient History: See how coefficient values change throughout optimization", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Optimization Progress: Bar chart showing tuning progress for each coefficient", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Shot Distribution: Analyze the spread and accuracy of your shots", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Algorithm Comparison: Compare performance of different ML algorithms (Advanced mode)", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Convergence Plot: Visualize how quickly the optimization converges (Advanced mode)", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Heat Map: 2D visualization of shot success by distance and angle", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Velocity Distribution: Histogram showing shot velocity patterns", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Hr(),
            html.Div(style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap'}, children=[
                dbc.Button("📥 Export All Graphs", id='export-graphs-btn', className="btn-secondary", size="sm"),
                dbc.Button("Refresh Data", id='refresh-graphs-btn', className="btn-secondary", size="sm"),
                dbc.Button("Pause Auto-Update", id='pause-graphs-btn', className="btn-secondary", size="sm"),
            ])
        ]),
        
        # Graph container with all visualizations
        html.Div(id='graphs-container', children=[
            # Shot Success Rate Over Time
            html.Div(id='graph-success-rate', className="card", children=[
                html.Div("Shot Success Rate Over Time", className="card-header"),
                html.Small("Hover over data points to see coefficient values used", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginBottom': '8px'}),
                dcc.Graph(
                    id='chart-success-rate',
                    figure=go.Figure(
                        data=[
                            go.Scatter(
                                x=[1,2,3,4,5,6,7,8,9,10],
                                y=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.78, 0.8, 0.82, 0.85],
                                mode='lines+markers',
                                name='Success Rate',
                                line={'color': '#FF8C00', 'width': 3},
                                marker={'size': 8},
                                customdata=[
                                    ['Drag: 0.003', 'Gravity: 9.81', 'Height: 1.0', 'Target: 2.4', 'Angle: 45', 'RPM: 5000', 'Velocity: 15'],
                                    ['Drag: 0.0032', 'Gravity: 9.80', 'Height: 1.02', 'Target: 2.4', 'Angle: 46', 'RPM: 5100', 'Velocity: 15.2'],
                                    ['Drag: 0.0035', 'Gravity: 9.81', 'Height: 1.05', 'Target: 2.4', 'Angle: 47', 'RPM: 5200', 'Velocity: 15.5'],
                                    ['Drag: 0.0038', 'Gravity: 9.82', 'Height: 1.08', 'Target: 2.4', 'Angle: 48', 'RPM: 5300', 'Velocity: 15.8'],
                                    ['Drag: 0.0040', 'Gravity: 9.81', 'Height: 1.10', 'Target: 2.4', 'Angle: 49', 'RPM: 5400', 'Velocity: 16.0'],
                                    ['Drag: 0.0042', 'Gravity: 9.80', 'Height: 1.12', 'Target: 2.4', 'Angle: 50', 'RPM: 5500', 'Velocity: 16.2'],
                                    ['Drag: 0.0043', 'Gravity: 9.81', 'Height: 1.14', 'Target: 2.4', 'Angle: 50', 'RPM: 5550', 'Velocity: 16.3'],
                                    ['Drag: 0.0044', 'Gravity: 9.81', 'Height: 1.15', 'Target: 2.4', 'Angle: 51', 'RPM: 5600', 'Velocity: 16.4'],
                                    ['Drag: 0.0045', 'Gravity: 9.81', 'Height: 1.16', 'Target: 2.4', 'Angle: 51', 'RPM: 5650', 'Velocity: 16.5'],
                                    ['Drag: 0.0046', 'Gravity: 9.81', 'Height: 1.17', 'Target: 2.4', 'Angle: 52', 'RPM: 5700', 'Velocity: 16.6'],
                                ],
                                hovertemplate='<b>Shot %{x}</b><br>' +
                                             'Success Rate: %{y:.1%}<br><br>' +
                                             '<b>Coefficients:</b><br>' +
                                             '%{customdata[0]}<br>' +
                                             '%{customdata[1]}<br>' +
                                             '%{customdata[2]}<br>' +
                                             '%{customdata[3]}<br>' +
                                             '%{customdata[4]}<br>' +
                                             '%{customdata[5]}<br>' +
                                             '%{customdata[6]}<br>' +
                                             '<extra></extra>'
                            )
                        ],
                        layout=go.Layout(
                            xaxis={'title': 'Shot Number', 'gridcolor': '#e8e8e8'},
                            yaxis={'title': 'Success Rate', 'range': [0, 1], 'gridcolor': '#e8e8e8'},
                            template='plotly_white',
                            hovermode='closest',
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                    )
                )
            ]),
            
            # Coefficient Value History
            html.Div(id='graph-coefficient-history', className="card", children=[
                html.Div("Coefficient Value History", className="card-header"),
                dcc.Graph(
                    id='chart-coeff-history',
                    figure=go.Figure(
                        data=[
                            go.Scatter(x=[1,2,3,4,5], y=[0.003, 0.0035, 0.004, 0.0045, 0.0042], 
                                      mode='lines+markers', name='kDragCoefficient', line={'color': '#FF8C00'}),
                            go.Scatter(x=[1,2,3,4,5], y=[9.81, 9.8, 9.82, 9.81, 9.81], 
                                      mode='lines+markers', name='kGravity', line={'color': '#0969da'}),
                            go.Scatter(x=[1,2,3,4,5], y=[1.0, 1.05, 1.1, 1.08, 1.09], 
                                      mode='lines+markers', name='kShotHeight', line={'color': '#1a7f37'}),
                        ],
                        layout=go.Layout(
                            xaxis={'title': 'Iteration'},
                            yaxis={'title': 'Coefficient Value'},
                            template='plotly_white',
                            hovermode='x unified',
                            legend={'orientation': 'h', 'y': -0.2}
                        )
                    )
                )
            ]),
            
            # Optimization Progress
            html.Div(id='graph-optimization-progress', className="card", children=[
                html.Div("Optimization Progress by Coefficient", className="card-header"),
                dcc.Graph(
                    id='chart-optimization-progress',
                    figure=go.Figure(
                        data=[
                            go.Bar(
                                x=['kDragCoefficient', 'kGravity', 'kShotHeight', 'kTargetHeight', 'kShooterAngle', 'kShooterRPM', 'kExitVelocity'],
                                y=[90, 85, 75, 60, 40, 20, 10],
                                marker={'color': ['#1a7f37', '#1a7f37', '#1a7f37', '#9a6700', '#FF8C00', '#cf222e', '#cf222e']},
                                text=['90%', '85%', '75%', '60%', '40%', '20%', '10%'],
                                textposition='auto'
                            )
                        ],
                        layout=go.Layout(
                            xaxis={'title': 'Coefficient'},
                            yaxis={'title': 'Optimization Progress (%)', 'range': [0, 100]},
                            template='plotly_white'
                        )
                    )
                )
            ]),
            
            # Shot Distribution
            html.Div(id='graph-shot-distribution', className="card", style={'display': 'none'}, children=[
                html.Div("Shot Distribution Analysis", className="card-header"),
                dcc.Graph(
                    id='chart-shot-distribution',
                    figure=go.Figure(
                        data=[
                            go.Scatter(
                                x=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
                                y=[2.3, 2.4, 2.5, 2.5, 2.6, 2.5, 2.4, 2.3, 2.2],
                                mode='markers',
                                marker={
                                    'size': 15,
                                    'color': [1, 1, 1, 0, 1, 1, 0, 1, 1],
                                    'colorscale': [[0, '#cf222e'], [1, '#1a7f37']],
                                    'showscale': True,
                                    'colorbar': {'title': 'Hit/Miss'}
                                },
                                text=['Hit', 'Hit', 'Hit', 'Miss', 'Hit', 'Hit', 'Miss', 'Hit', 'Hit'],
                                hovertemplate='Distance: %{x}m<br>Height: %{y}m<br>%{text}<extra></extra>'
                            )
                        ],
                        layout=go.Layout(
                            xaxis={'title': 'Shot Distance (m)'},
                            yaxis={'title': 'Target Height (m)'},
                            template='plotly_white'
                        )
                    )
                )
            ]),
            
            # Algorithm Performance Comparison (Advanced only)
            html.Div(id='graph-algorithm-comparison', className="card", style={'display': 'none'}, children=[
                html.Div("Algorithm Performance Comparison", className="card-header"),
                dcc.Graph(
                    id='chart-algorithm-comparison',
                    figure=go.Figure(
                        data=[
                            go.Bar(
                                x=['GP', 'RF', 'GBRT', 'ET', 'NN'],
                                y=[0.85, 0.82, 0.80, 0.78, 0.75],
                                marker={'color': '#FF8C00'},
                                text=['85%', '82%', '80%', '78%', '75%'],
                                textposition='auto'
                            )
                        ],
                        layout=go.Layout(
                            xaxis={'title': 'Algorithm'},
                            yaxis={'title': 'Success Rate', 'range': [0, 1]},
                            template='plotly_white'
                        )
                    )
                )
            ]),
            
            # Convergence Plot (Advanced only)
            html.Div(id='graph-convergence', className="card", style={'display': 'none'}, children=[
                html.Div("Convergence Plot", className="card-header"),
                dcc.Graph(
                    id='chart-convergence',
                    figure=go.Figure(
                        data=[
                            go.Scatter(
                                x=list(range(1, 31)),
                                y=[0.5, 0.48, 0.45, 0.43, 0.40, 0.38, 0.36, 0.35, 0.34, 0.33,
                                   0.32, 0.31, 0.30, 0.29, 0.285, 0.28, 0.275, 0.27, 0.268, 0.266,
                                   0.265, 0.264, 0.263, 0.262, 0.261, 0.260, 0.260, 0.260, 0.260, 0.260],
                                mode='lines+markers',
                                name='Best Value',
                                line={'color': '#1a7f37', 'width': 2}
                            )
                        ],
                        layout=go.Layout(
                            xaxis={'title': 'Iteration'},
                            yaxis={'title': 'Objective Function Value'},
                            template='plotly_white',
                            annotations=[{
                                'x': 25, 'y': 0.260,
                                'text': 'Converged',
                                'showarrow': True,
                                'arrowhead': 2
                            }]
                        )
                    )
                )
            ]),
            
            # Heat Map
            html.Div(id='graph-heatmap', className="card", style={'display': 'none'}, children=[
                html.Div("Heat Map - Distance vs Angle Success Rate", className="card-header"),
                dcc.Graph(
                    id='chart-heatmap',
                    figure=go.Figure(
                        data=[
                            go.Heatmap(
                                z=[[0.2, 0.4, 0.6, 0.8, 0.9],
                                   [0.3, 0.5, 0.7, 0.85, 0.95],
                                   [0.4, 0.6, 0.8, 0.9, 0.85],
                                   [0.5, 0.7, 0.85, 0.95, 0.8],
                                   [0.6, 0.8, 0.9, 0.9, 0.75]],
                                x=['30°', '35°', '40°', '45°', '50°'],
                                y=['1m', '2m', '3m', '4m', '5m'],
                                colorscale='RdYlGn',
                                text=[[0.2, 0.4, 0.6, 0.8, 0.9],
                                      [0.3, 0.5, 0.7, 0.85, 0.95],
                                      [0.4, 0.6, 0.8, 0.9, 0.85],
                                      [0.5, 0.7, 0.85, 0.95, 0.8],
                                      [0.6, 0.8, 0.9, 0.9, 0.75]],
                                texttemplate='%{text:.0%}',
                                textfont={'size': 12}
                            )
                        ],
                        layout=go.Layout(
                            xaxis={'title': 'Shooter Angle'},
                            yaxis={'title': 'Distance'},
                            template='plotly_white'
                        )
                    )
                )
            ]),
            
            # Velocity Distribution
            html.Div(id='graph-velocity-dist', className="card", style={'display': 'none'}, children=[
                html.Div("Shot Velocity Distribution", className="card-header"),
                dcc.Graph(
                    id='chart-velocity-dist',
                    figure=go.Figure(
                        data=[
                            go.Histogram(
                                x=[14.5, 14.8, 15.0, 15.2, 15.0, 14.9, 15.1, 15.3, 14.7, 15.0,
                                   15.2, 15.1, 14.9, 15.0, 15.1, 14.8, 15.2, 15.0, 14.9, 15.1],
                                nbinsx=20,
                                marker={'color': '#FF8C00'},
                                name='Exit Velocity'
                            )
                        ],
                        layout=go.Layout(
                            xaxis={'title': 'Exit Velocity (m/s)'},
                            yaxis={'title': 'Frequency'},
                            template='plotly_white',
                            showlegend=False
                        )
                    )
                )
            ]),
        ])
    ])


def create_workflow_view():
    """Create the order & workflow management view."""
    return html.Div([
        # Tuning Order Management
        html.Div(className="card", children=[
            html.Div("Tuning Order & Sequence", className="card-header"),
            html.P("Drag to reorder, click to enable/disable coefficients in the tuning sequence"),
            html.Div(id='tuning-order-list', children=[
                html.Div(className="card", style={'marginBottom': '8px', 'cursor': 'move', 'padding': '12px'}, children=[
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}, children=[
                        html.Div([
                            html.Span("1. ", style={'fontWeight': 'bold', 'marginRight': '8px'}),
                            html.Span("kDragCoefficient"),
                        ]),
                        html.Div(style={'display': 'flex', 'gap': '8px'}, children=[
                            dbc.Button("⬆", id={'type': 'move-up', 'index': 0}, size="sm", className="btn-secondary"),
                            dbc.Button("⬇", id={'type': 'move-down', 'index': 0}, size="sm", className="btn-secondary"),
                            dbc.Checklist(
                                id={'type': 'enable-coeff', 'index': 0},
                                options=[{'label': 'Enabled', 'value': 'enabled'}],
                                value=['enabled'],
                                switch=True,
                                inline=True
                            ),
                        ])
                    ])
                ]) for i in range(7)
            ])
        ]),
        
        # Workflow Controls
        html.Div(className="card", children=[
            html.Div("Workflow Controls", className="card-header"),
            html.Div(style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap'}, children=[
                dbc.Button("Start from Beginning", id='start-workflow-btn', className="btn-primary"),
                dbc.Button("Skip to Next", id='skip-workflow-btn', className="btn-secondary"),
                dbc.Button("Go to Previous", id='prev-workflow-btn', className="btn-secondary"),
                dbc.Button("Reset Progress", id='reset-workflow-btn', className="btn-secondary"),
            ])
        ]),
        
        # Current Workflow State
        html.Div(className="card", children=[
            html.Div("Current Workflow State", className="card-header"),
            html.Div(id='workflow-state', children=[
                html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '16px'}, children=[
                    html.Div([
                        html.Label("Current Coefficient:", style={'fontWeight': 'bold'}),
                        html.P("kDragCoefficient", id='current-coeff-display')
                    ]),
                    html.Div([
                        html.Label("Progress:", style={'fontWeight': 'bold'}),
                        html.P("1 of 7 (14%)", id='workflow-progress-display')
                    ]),
                    html.Div([
                        html.Label("Shots Collected:", style={'fontWeight': 'bold'}),
                        html.P("5 / 10", id='shots-collected-display')
                    ]),
                    html.Div([
                        html.Label("Estimated Time Remaining:", style={'fontWeight': 'bold'}),
                        html.P("~25 minutes", id='time-remaining-display')
                    ]),
                ])
            ])
        ]),
        
        # Backtrack Controls
        html.Div(className="card", children=[
            html.Div("Backtrack to Previous Coefficients", className="card-header"),
            html.P("Re-tune coefficients that may have been affected by later changes", style={'color': 'var(--text-secondary)'}),
            html.Div(style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap'}, children=[
                dbc.Button("← kDragCoefficient", id={'type': 'backtrack', 'index': 'kDragCoefficient'}, className="btn-secondary", size="sm"),
                dbc.Button("← kGravity", id={'type': 'backtrack', 'index': 'kGravity'}, className="btn-secondary", size="sm"),
                dbc.Button("← kShotHeight", id={'type': 'backtrack', 'index': 'kShotHeight'}, className="btn-secondary", size="sm"),
                dbc.Button("← kTargetHeight", id={'type': 'backtrack', 'index': 'kTargetHeight'}, className="btn-secondary", size="sm"),
                dbc.Button("← kShooterAngle", id={'type': 'backtrack', 'index': 'kShooterAngle'}, className="btn-secondary", size="sm"),
                dbc.Button("← kShooterRPM", id={'type': 'backtrack', 'index': 'kShooterRPM'}, className="btn-secondary", size="sm"),
                dbc.Button("← kExitVelocity", id={'type': 'backtrack', 'index': 'kExitVelocity'}, className="btn-secondary", size="sm"),
            ])
        ]),
        
        # Coefficient Interactions
        html.Div(className="card", children=[
            html.Div("Detected Coefficient Interactions", className="card-header"),
            html.P("Automatically detected dependencies between coefficients", style={'color': 'var(--text-secondary)'}),
            html.Div(id='interactions-display', children=[
                html.Table(className="table-github", children=[
                    html.Thead([
                        html.Tr([
                            html.Th("Coefficient 1"),
                            html.Th("Coefficient 2"),
                            html.Th("Interaction Strength"),
                            html.Th("Recommendation"),
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td("kShooterAngle"),
                            html.Td("kExitVelocity"),
                            html.Td(html.Div(style={'width': '100px', 'height': '20px', 'background': 'linear-gradient(to right, #1a7f37 80%, #e8e8e8 80%)'}, title="80% correlation")),
                            html.Td("Tune together")
                        ]),
                        html.Tr([
                            html.Td("kDragCoefficient"),
                            html.Td("kExitVelocity"),
                            html.Td(html.Div(style={'width': '100px', 'height': '20px', 'background': 'linear-gradient(to right, #FF8C00 60%, #e8e8e8 60%)'}, title="60% correlation")),
                            html.Td("Consider re-tuning")
                        ]),
                        html.Tr([
                            html.Td("kShotHeight"),
                            html.Td("kTargetHeight"),
                            html.Td(html.Div(style={'width': '100px', 'height': '20px', 'background': 'linear-gradient(to right, #9a6700 40%, #e8e8e8 40%)'}, title="40% correlation")),
                            html.Td("Monitor")
                        ]),
                    ])
                ])
            ])
        ]),
        
        # Tuning Session Management
        html.Div(className="card", children=[
            html.Div("Tuning Session Management", className="card-header"),
            html.Div([
                html.Label("Session Name:", style={'fontWeight': 'bold'}),
                dbc.Input(type="text", value="Competition Practice 2024", id='session-name', placeholder="Enter session name"),
                html.Br(),
                html.Label("Session Notes:", style={'fontWeight': 'bold'}),
                dbc.Textarea(id='session-notes', placeholder="Notes about this tuning session...", style={'height': '100px'}),
                html.Br(),
                html.Div(style={'display': 'flex', 'gap': '8px'}, children=[
                    dbc.Button("💾 Save Session", id='save-session-btn', className="btn-primary"),
                    dbc.Button("📁 Load Session", id='load-session-btn', className="btn-secondary"),
                    dbc.Button("📤 Export Session Data", id='export-session-btn', className="btn-secondary"),
                ])
            ])
        ]),
    ])


def create_settings_view():
    """Create the settings and configuration view with ALL options."""
    return html.Div([
        # Core Tuner Settings
        html.Div(className="card", children=[
            html.Div("Core Tuner Settings", className="card-header"),
            html.Div([
                dbc.Checklist(
                    id='tuner-toggles',
                    options=[
                        {'label': 'Enable Tuner', 'value': 'enabled'},
                        {'label': 'Auto-optimize', 'value': 'auto_optimize'},
                        {'label': 'Auto-advance', 'value': 'auto_advance'},
                        {'label': 'Manual mode', 'value': 'manual_mode'},
                        {'label': 'Match mode protection', 'value': 'match_protection'},
                    ],
                    value=['enabled'],
                    switch=True
                ),
                html.Small("Enable Tuner: Activate the Bayesian optimization system", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '4px'}),
                html.Small("Auto-optimize: Automatically run optimization after reaching shot threshold", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Small("Auto-advance: Automatically move to next coefficient when threshold reached", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Small("Manual mode: Require manual confirmation before applying coefficient changes", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Small("Match mode protection: Prevent tuning changes during competition matches", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Hr(),
                html.Label("Auto-optimize Shot Threshold", style={'fontWeight': 'bold'}),
                dbc.Input(type="number", value=10, id='auto-optimize-threshold', min=1, max=100),
                html.Br(),
                html.Label("Auto-advance Shot Threshold", style={'fontWeight': 'bold'}),
                dbc.Input(type="number", value=10, id='auto-advance-threshold', min=1, max=100),
                html.Br(),
                html.Label("Success Rate Threshold (%)", style={'fontWeight': 'bold'}),
                dbc.Input(type="number", value=80, id='success-threshold', min=0, max=100),
            ])
        ]),
        
        # Auto-Baseline Settings
        html.Div(className="card", children=[
            html.Div("Auto-Baseline Settings", className="card-header"),
            html.P("Automatically set optimal coefficients as new baseline", style={'fontSize': '14px', 'color': 'var(--text-secondary)'}),
            html.Div([
                dbc.Checklist(
                    id='auto-baseline-toggles',
                    options=[
                        {'label': 'Auto-set baseline when optimal detected', 'value': 'auto_baseline'},
                        {'label': 'Show recommendation (button glows when optimal)', 'value': 'recommend_baseline'},
                    ],
                    value=['recommend_baseline'],
                    switch=True
                ),
                html.Small("Auto-set: Immediately save coefficients as baseline when optimal performance is detected", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '4px'}),
                html.Small("Recommendation mode: Highlight the Set Baseline button when optimal, wait for your confirmation", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Hr(),
                html.Label("Optimal Detection Criteria", style={'fontWeight': 'bold', 'marginTop': '8px'}),
                html.Small("System considers coefficients optimal when:", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginBottom': '8px'}),
                
                html.Label("Minimum Success Rate (%)", style={'fontWeight': 'bold', 'fontSize': '14px'}),
                dbc.Input(type="number", value=85, id='baseline-success-threshold', min=50, max=100),
                html.Small("Success rate must exceed this value", style={'color': 'var(--text-secondary)'}),
                html.Br(), html.Br(),
                
                html.Label("Minimum Shot Count", style={'fontWeight': 'bold', 'fontSize': '14px'}),
                dbc.Input(type="number", value=20, id='baseline-shot-threshold', min=10, max=100),
                html.Small("Must have at least this many shots", style={'color': 'var(--text-secondary)'}),
                html.Br(), html.Br(),
                
                html.Label("Stability Window (shots)", style={'fontWeight': 'bold', 'fontSize': '14px'}),
                dbc.Input(type="number", value=5, id='baseline-stability-window', min=3, max=20),
                html.Small("Success rate must be stable over this many shots", style={'color': 'var(--text-secondary)'}),
                html.Br(), html.Br(),
                
                # Manual baseline button with glow capability
                html.Div(style={'marginTop': '16px', 'padding': '12px', 'backgroundColor': 'var(--accent-subtle)', 'borderRadius': '6px'}, children=[
                    html.Label("Manual Override", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '8px'}),
                    html.P("Click to set current coefficients as baseline now", style={'fontSize': '13px', 'color': 'var(--text-secondary)', 'marginBottom': '12px'}),
                    dbc.Button(
                        "Set Current as Baseline", 
                        id='set-baseline-btn', 
                        className="btn-primary",
                        style={'width': '100%', 'padding': '12px'}
                    ),
                    html.Small(id='baseline-recommendation', children="", style={'display': 'block', 'marginTop': '8px', 'color': 'var(--text-secondary)', 'fontStyle': 'italic'})
                ])
            ])
        ]),
        
        # Optimization Parameters
        html.Div(className="card", children=[
            html.Div("Optimization Parameters", className="card-header"),
            html.Div([
                html.Label("Initial Points", style={'fontWeight': 'bold'}),
                dbc.Input(type="number", value=5, id='n-initial-points', min=1, max=20),
                html.Small("Number of random points before optimization", style={'color': 'var(--text-secondary)'}),
                html.Br(), html.Br(),
                
                html.Label("Calls per Coefficient", style={'fontWeight': 'bold'}),
                dbc.Input(type="number", value=30, id='n-calls', min=5, max=100),
                html.Small("Maximum optimization iterations per coefficient", style={'color': 'var(--text-secondary)'}),
                html.Br(), html.Br(),
                
                html.Label("Acquisition Function", style={'fontWeight': 'bold'}),
                dbc.Select(
                    id='acquisition-function',
                    options=[
                        {'label': 'Expected Improvement (EI)', 'value': 'EI'},
                        {'label': 'Lower Confidence Bound (LCB)', 'value': 'LCB'},
                        {'label': 'Probability of Improvement (PI)', 'value': 'PI'},
                        {'label': 'Expected Improvement per Second (EIps)', 'value': 'EIps'},
                    ],
                    value='EI'
                ),
                html.Br(),
                
                html.Label("Exploration Factor (xi)", style={'fontWeight': 'bold'}),
                dbc.Input(type="number", value=0.01, id='xi', min=0, max=1, step=0.001),
                html.Small("Balance exploration vs exploitation", style={'color': 'var(--text-secondary)'}),
                html.Br(), html.Br(),
                
                html.Label("Convergence Threshold", style={'fontWeight': 'bold'}),
                dbc.Input(type="number", value=0.001, id='convergence-threshold', min=0.0001, max=0.1, step=0.0001),
                html.Small("Stop when improvement is below this", style={'color': 'var(--text-secondary)'}),
            ])
        ]),
        
        # NetworkTables Configuration
        html.Div(className="card", children=[
            html.Div("NetworkTables Configuration", className="card-header"),
            html.Div([
                html.Label("Robot IP / Team Number", style={'fontWeight': 'bold'}),
                dbc.Input(type="text", value="10.TE.AM.2", id='robot-ip', placeholder="10.TE.AM.2 or roborio-TEAM-frc.local"),
                html.Br(),
                
                html.Label("Table Path", style={'fontWeight': 'bold'}),
                dbc.Input(type="text", value="/Tuning/BayesianTuner", id='nt-table-path'),
                html.Br(),
                
                html.Label("Update Rate (Hz)", style={'fontWeight': 'bold'}),
                dbc.Input(type="number", value=10, id='nt-update-rate', min=1, max=50),
                html.Small("How often to sync with robot", style={'color': 'var(--text-secondary)'}),
                html.Br(), html.Br(),
                
                dbc.Checklist(
                    id='nt-toggles',
                    options=[
                        {'label': 'Require shot logged interlock', 'value': 'require_shot_logged'},
                        {'label': 'Require coefficients updated interlock', 'value': 'require_coeff_updated'},
                        {'label': 'Auto-reconnect on disconnect', 'value': 'auto_reconnect'},
                    ],
                    value=['require_shot_logged'],
                    switch=True
                ),
                html.Small("Shot logged interlock: Wait for robot confirmation before recording shot data", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '4px'}),
                html.Small("Coefficients updated interlock: Wait for robot confirmation that new values were applied", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Small("Auto-reconnect: Automatically attempt to reconnect to robot if connection is lost", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            ])
        ]),
        
        # Logging Configuration
        html.Div(className="card", children=[
            html.Div("Logging & Data Recording", className="card-header"),
            html.Div([
                dbc.Checklist(
                    id='logging-toggles',
                    options=[
                        {'label': 'Enable CSV shot logs', 'value': 'csv_logs'},
                        {'label': 'Enable JSON coefficient history', 'value': 'json_logs'},
                        {'label': 'Log all NetworkTables traffic', 'value': 'nt_traffic'},
                        {'label': 'Verbose debug logging', 'value': 'verbose'},
                        {'label': 'Log timestamps', 'value': 'timestamps'},
                        {'label': 'Log coefficient interactions', 'value': 'interactions'},
                    ],
                    value=['csv_logs', 'json_logs', 'timestamps'],
                    switch=True
                ),
                html.Small("CSV shot logs: Save individual shot results to CSV files for analysis", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '4px'}),
                html.Small("JSON coefficient history: Record all coefficient changes in JSON format", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Small("NetworkTables traffic: Log all communication between dashboard and robot", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Small("Verbose debug: Enable detailed debugging output for troubleshooting", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Small("Timestamps: Include precise timestamps in all log entries", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Small("Coefficient interactions: Log relationships between coefficient changes", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
                html.Hr(),
                
                html.Label("Log Directory", style={'fontWeight': 'bold'}),
                dbc.Input(type="text", value="tuner_logs/", id='log-directory'),
                html.Br(),
                
                html.Label("Log File Prefix", style={'fontWeight': 'bold'}),
                dbc.Input(type="text", value="bayesopt", id='log-prefix'),
            ])
        ]),
        
        # Advanced mode only - ML Algorithm Selection
        html.Div(id='advanced-settings', className="card", style={'display': 'none'}, children=[
            html.Div("ML Algorithm Selection", className="card-header"),
            dbc.Select(
                id='algorithm-selector',
                options=[
                    {'label': 'Gaussian Process (GP) - Recommended', 'value': 'gp'},
                    {'label': 'Random Forest (RF)', 'value': 'rf'},
                    {'label': 'Gradient Boosted Trees (GBRT)', 'value': 'gbrt'},
                    {'label': 'Extra Trees (ET)', 'value': 'et'},
                    {'label': 'Neural Network (NN)', 'value': 'nn'},
                    {'label': 'Support Vector Regression (SVR)', 'value': 'svr'},
                    {'label': 'K-Nearest Neighbors (KNN)', 'value': 'knn'},
                    {'label': 'Ridge Regression', 'value': 'ridge'},
                    {'label': 'Lasso Regression', 'value': 'lasso'},
                    {'label': 'Decision Trees', 'value': 'decision_tree'},
                    {'label': 'AdaBoost', 'value': 'adaboost'},
                ],
                value='gp'
            ),
            html.Br(),
            
            html.Div("Algorithm Hyperparameters", style={'fontWeight': 'bold', 'marginBottom': '8px'}),
            html.Div(id='algorithm-params', children=[
                html.Label("Kernel (for GP)"),
                dbc.Select(
                    id='gp-kernel',
                    options=[
                        {'label': 'RBF (Radial Basis Function)', 'value': 'rbf'},
                        {'label': 'Matern', 'value': 'matern'},
                        {'label': 'Rational Quadratic', 'value': 'rational_quadratic'},
                    ],
                    value='rbf'
                ),
                html.Br(),
                
                html.Label("Alpha (noise level)"),
                dbc.Input(type="number", value=1e-10, id='gp-alpha', step=1e-11),
                html.Br(),
                
                html.Label("Number of Restarts"),
                dbc.Input(type="number", value=10, id='gp-restarts', min=0, max=50),
            ]),
            
            html.Hr(),
            html.Div("Hybrid Strategies", className="card-header"),
            dbc.Checklist(
                id='hybrid-strategies',
                options=[
                    {'label': 'Ensemble Voting - Combine multiple algorithms', 'value': 'ensemble'},
                    {'label': 'Stacking (Meta-Learning) - Learn best combination', 'value': 'stacking'},
                    {'label': 'Transfer Learning - Use historical data', 'value': 'transfer'},
                    {'label': 'Adaptive Algorithm Selection - Auto-pick best', 'value': 'adaptive'},
                    {'label': 'Multi-Armed Bandit - Explore/exploit algorithms', 'value': 'bandit'},
                    {'label': 'Bayesian Model Averaging - Weight by probability', 'value': 'bma'},
                ],
                value=[],
                switch=True
            ),
            html.Small("Ensemble Voting: Combine predictions from multiple algorithms for better accuracy", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '4px'}),
            html.Small("Stacking: Use machine learning to find optimal algorithm combinations", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Transfer Learning: Apply knowledge from previous tuning sessions", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Adaptive Selection: Automatically choose the best-performing algorithm for your situation", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Multi-Armed Bandit: Balance trying new algorithms vs using known good ones", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Small("Bayesian Model Averaging: Weight algorithms based on their predicted probability of success", style={'color': 'var(--text-secondary)', 'display': 'block', 'marginTop': '2px'}),
            html.Br(),
            
            html.Div(id='ensemble-weights', style={'display': 'none'}, children=[
                html.Div("Ensemble Weights", style={'fontWeight': 'bold', 'marginBottom': '8px'}),
                html.Label("GP Weight"),
                dcc.Slider(id='weight-gp', min=0, max=1, step=0.1, value=0.4, marks={0: '0', 0.5: '0.5', 1: '1'}),
                html.Label("RF Weight"),
                dcc.Slider(id='weight-rf', min=0, max=1, step=0.1, value=0.3, marks={0: '0', 0.5: '0.5', 1: '1'}),
                html.Label("GBRT Weight"),
                dcc.Slider(id='weight-gbrt', min=0, max=1, step=0.1, value=0.3, marks={0: '0', 0.5: '0.5', 1: '1'}),
            ])
        ]),
        
        # Per-Coefficient Overrides
        html.Div(id='per-coeff-overrides', className="card", style={'display': 'none'}, children=[
            html.Div("Per-Coefficient Setting Overrides", className="card-header"),
            html.P("Override global settings for specific coefficients", style={'color': 'var(--text-secondary)'}),
            html.Div(id='coefficient-override-list', children=[
                html.Div(className="card", style={'marginBottom': '8px'}, children=[
                    html.Div("kDragCoefficient", style={'fontWeight': 'bold'}),
                    dbc.Checklist(
                        id={'type': 'coeff-override', 'index': 'kDragCoefficient'},
                        options=[
                            {'label': 'Override autotune settings', 'value': 'autotune'},
                            {'label': 'Override auto-advance settings', 'value': 'auto_advance'},
                        ],
                        value=[],
                        switch=True
                    ),
                ])
            ])
        ]),
        
        # More Features (Advanced + More Features only)
        html.Div(id='more-features-settings', className="card", style={'display': 'none'}, children=[
            html.Div("More Features (Experimental)", className="card-header"),
            dbc.Checklist(
                id='experimental-toggles',
                options=[
                    {'label': 'Enable performance profiling', 'value': 'profiling'},
                    {'label': 'Show raw NetworkTables values', 'value': 'raw_nt'},
                    {'label': 'Enable debug mode', 'value': 'debug'},
                    {'label': 'Show internal state', 'value': 'internal_state'},
                    {'label': 'Enable experimental algorithms', 'value': 'experimental_algos'},
                ],
                value=[],
                switch=True
            ),
        ]),
        
        # Save/Load Configuration
        html.Div(className="card", children=[
            html.Div("Configuration Management", className="card-header"),
            html.Div(style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap'}, children=[
                dbc.Button("💾 Save Settings", id='save-settings-btn', className="btn-primary"),
                dbc.Button("📁 Load Settings", id='load-settings-btn', className="btn-secondary"),
                dbc.Button("Reset to Defaults", id='reset-settings-btn', className="btn-secondary"),
            ])
        ])
    ])


def create_robot_status_view():
    """Create the robot status monitoring view."""
    return html.Div([
        # Breadcrumb navigation
        html.Div(className="breadcrumb", children=[
            html.Span("Home", className="breadcrumb-item"),
            html.Span("/", className="breadcrumb-separator"),
            html.Span("Robot Status", className="breadcrumb-item active"),
        ]),
        
        # Robot vital stats
        html.Div(className="card", children=[
            html.Div("Robot Vital Statistics", className="card-header"),
            html.P("Real-time monitoring of robot performance and health", style={'fontSize': '14px', 'color': 'var(--text-secondary)', 'marginBottom': '16px'}),
            html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 'gap': '16px'}, children=[
                html.Div(className="card", style={'padding': '12px'}, children=[
                    html.Label("Battery Voltage", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                    html.Div(id='robot-battery', children="12.4V", style={'fontSize': '24px', 'fontWeight': '600', 'color': 'var(--success)'}),
                    html.Small("Healthy", style={'color': 'var(--text-secondary)'})
                ]),
                html.Div(className="card", style={'padding': '12px'}, children=[
                    html.Label("CPU Usage", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                    html.Div(id='robot-cpu', children="34%", style={'fontSize': '24px', 'fontWeight': '600', 'color': 'var(--info)'}),
                    html.Small("Normal", style={'color': 'var(--text-secondary)'})
                ]),
                html.Div(className="card", style={'padding': '12px'}, children=[
                    html.Label("Memory Usage", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                    html.Div(id='robot-memory', children="128MB", style={'fontSize': '24px', 'fontWeight': '600', 'color': 'var(--info)'}),
                    html.Small("Normal", style={'color': 'var(--text-secondary)'})
                ]),
                html.Div(className="card", style={'padding': '12px'}, children=[
                    html.Label("CAN Utilization", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                    html.Div(id='robot-can', children="42%", style={'fontSize': '24px', 'fontWeight': '600', 'color': 'var(--success)'}),
                    html.Small("Healthy", style={'color': 'var(--text-secondary)'})
                ]),
                html.Div(className="card", style={'padding': '12px'}, children=[
                    html.Label("Loop Time", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                    html.Div(id='robot-loop-time', children="18ms", style={'fontSize': '24px', 'fontWeight': '600', 'color': 'var(--success)'}),
                    html.Small("On target", style={'color': 'var(--text-secondary)'})
                ]),
                html.Div(className="card", style={'padding': '12px'}, children=[
                    html.Label("Connection", style={'fontSize': '12px', 'color': 'var(--text-secondary)', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                    html.Div(id='robot-connection-time', children="Disconnected", style={'fontSize': '18px', 'fontWeight': '600', 'color': 'var(--danger)'}),
                    html.Small("No robot", style={'color': 'var(--text-secondary)'})
                ]),
            ])
        ]),
        
        # Robot performance graphs
        html.Div(className="card", children=[
            html.Div("Robot Performance Graphs", className="card-header"),
            html.P("Monitor robot-specific metrics over time", style={'fontSize': '14px', 'color': 'var(--text-secondary)', 'marginBottom': '16px'}),
            
            # Battery voltage over time
            dcc.Graph(
                id='robot-battery-graph',
                figure=go.Figure(
                    data=[
                        go.Scatter(
                            x=list(range(60)),
                            y=[12.4 + (i % 10) * 0.01 for i in range(60)],
                            mode='lines',
                            name='Battery Voltage',
                            line={'color': '#1a7f37', 'width': 2}
                        )
                    ],
                    layout=go.Layout(
                        title='Battery Voltage (Last 60s)',
                        xaxis={'title': 'Time (seconds ago)', 'autorange': 'reversed'},
                        yaxis={'title': 'Voltage (V)', 'range': [11, 13]},
                        template='plotly_white',
                        height=300
                    )
                )
            ),
            
            # CPU and Memory usage
            dcc.Graph(
                id='robot-resources-graph',
                figure=go.Figure(
                    data=[
                        go.Scatter(x=list(range(60)), y=[30 + (i % 20) for i in range(60)], 
                                  mode='lines', name='CPU %', line={'color': '#0969da'}),
                        go.Scatter(x=list(range(60)), y=[50 + (i % 15) for i in range(60)], 
                                  mode='lines', name='Memory %', line={'color': '#9a6700'}),
                    ],
                    layout=go.Layout(
                        title='CPU & Memory Usage (Last 60s)',
                        xaxis={'title': 'Time (seconds ago)', 'autorange': 'reversed'},
                        yaxis={'title': 'Usage (%)', 'range': [0, 100]},
                        template='plotly_white',
                        height=300
                    )
                )
            ),
        ]),
        
        # Robot logs
        html.Div(className="card", children=[
            html.Div("Robot Logs", className="card-header"),
            html.P("Real-time logs from robot code", style={'fontSize': '14px', 'color': 'var(--text-secondary)', 'marginBottom': '16px'}),
            html.Div(
                id='robot-logs-display',
                style={
                    'backgroundColor': 'var(--bg-secondary)',
                    'padding': '16px',
                    'borderRadius': '6px',
                    'fontFamily': 'monospace',
                    'fontSize': '12px',
                    'maxHeight': '400px',
                    'overflowY': 'auto',
                    'whiteSpace': 'pre-wrap'
                },
                children=[
                    html.Div(f"[{datetime.now().strftime('%H:%M:%S')}] Robot code initialized"),
                    html.Div(f"[{datetime.now().strftime('%H:%M:%S')}] Subsystems ready"),
                    html.Div(f"[{datetime.now().strftime('%H:%M:%S')}] Awaiting connection..."),
                    html.Div(f"[{datetime.now().strftime('%H:%M:%S')}] NetworkTables not connected", style={'color': 'var(--warning)'}),
                ]
            )
        ]),
        
        # Robot diagnostics
        html.Div(className="card", children=[
            html.Div("🔧 Robot Diagnostics", className="card-header"),
            html.Table(className="table-github", children=[
                html.Thead([
                    html.Tr([
                        html.Th("Component"),
                        html.Th("Status"),
                        html.Th("Temperature"),
                        html.Th("Current Draw"),
                        html.Th("Errors"),
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td("Left Drive Motor"),
                        html.Td(html.Span("●", style={'color': 'var(--success)'}) + " OK"),
                        html.Td("42°C"),
                        html.Td("3.2A"),
                        html.Td("0"),
                    ]),
                    html.Tr([
                        html.Td("Right Drive Motor"),
                        html.Td(html.Span("●", style={'color': 'var(--success)'}) + " OK"),
                        html.Td("41°C"),
                        html.Td("3.1A"),
                        html.Td("0"),
                    ]),
                    html.Tr([
                        html.Td("Shooter Motor"),
                        html.Td(html.Span("●", style={'color': 'var(--warning)'}) + " Warm"),
                        html.Td("58°C"),
                        html.Td("12.4A"),
                        html.Td("0"),
                    ]),
                    html.Tr([
                        html.Td("Intake Motor"),
                        html.Td(html.Span("●", style={'color': 'var(--success)'}) + " OK"),
                        html.Td("38°C"),
                        html.Td("2.1A"),
                        html.Td("0"),
                    ]),
                    html.Tr([
                        html.Td("Pneumatics"),
                        html.Td(html.Span("●", style={'color': 'var(--danger)'}) + " No Data"),
                        html.Td("--"),
                        html.Td("--"),
                        html.Td("1"),
                    ]),
                ])
            ])
        ]),
    ])


def create_notes_view():
    """Create the notes and to-do view."""
    return html.Div([
        html.Div(className="card", children=[
            html.Div("Add Note", className="card-header"),
            dbc.Textarea(id='note-input', placeholder="Enter your observation..."),
            dbc.Button("Add Note", id='add-note-btn', className="btn-primary", style={'marginTop': '8px'})
        ]),
        
        html.Div(className="card", children=[
            html.Div("Add To-Do Item", className="card-header"),
            dbc.Input(id='todo-input', placeholder="Enter task..."),
            dbc.Button("Add To-Do", id='add-todo-btn', className="btn-primary", style={'marginTop': '8px'})
        ]),
        
        html.Div(className="card", children=[
            html.Div("Recent Notes", className="card-header"),
            html.Div(id='notes-list', children=[
                html.P("No notes yet", style={'fontStyle': 'italic', 'color': 'var(--text-secondary)'})
            ])
        ]),
        
        html.Div(className="card", children=[
            html.Div("To-Do List", className="card-header"),
            html.Div(id='todos-list', children=[
                html.P("No to-dos yet", style={'fontStyle': 'italic', 'color': 'var(--text-secondary)'})
            ])
        ])
    ])


def create_danger_zone_view():
    """Create the danger zone view for sensitive operations."""
    return html.Div([
        html.Div(className="card", style={'borderColor': 'var(--danger)'}, children=[
            html.Div("Danger Zone", className="card-header", style={'color': 'var(--danger)'}),
            html.P("These operations can significantly affect your tuning data. Use with caution."),
            
            html.Hr(),
            html.Div("Configuration Operations", style={'fontWeight': 'bold', 'marginBottom': '8px'}),
            dbc.Button("Reconfigure Base Point", id='reconfigure-base-btn', className="btn-secondary", style={'marginBottom': '8px', 'width': '100%'}),
            dbc.Button("Restore Factory Defaults", id='restore-defaults-btn', className="btn-secondary", style={'marginBottom': '8px', 'width': '100%'}),
            dbc.Button("🔐 Lock Configuration", id='lock-config-btn', className="btn-secondary", style={'marginBottom': '8px', 'width': '100%'}),
            
            html.Hr(),
            html.Div("Data Management", style={'fontWeight': 'bold', 'marginBottom': '8px'}),
            dbc.Button("📤 Export Configuration", id='export-config-btn', className="btn-secondary", style={'marginBottom': '8px', 'width': '100%'}),
            dbc.Button("📥 Import Configuration", id='import-config-btn', className="btn-secondary", style={'marginBottom': '8px', 'width': '100%'}),
            
            html.Hr(),
            html.Div("Destructive Operations", style={'fontWeight': 'bold', 'marginBottom': '8px', 'color': 'var(--danger)'}),
            dbc.Button("Reset All Tuning Data", id='reset-data-btn', className="btn-danger", style={'marginBottom': '8px', 'width': '100%'}),
            dbc.Button("🧹 Clear All Pinned Data", id='clear-pinned-btn', className="btn-danger", style={'marginBottom': '8px', 'width': '100%'}),
            
            html.Hr(),
            html.Div("Emergency Controls", style={'fontWeight': 'bold', 'marginBottom': '8px', 'color': 'var(--danger)'}),
            dbc.Button("🔥 Emergency Stop", id='emergency-stop-btn', className="btn-danger", style={'marginBottom': '8px', 'width': '100%'}),
            dbc.Button("Force Retune Coefficient", id='force-retune-btn', className="btn-danger", style={'marginBottom': '8px', 'width': '100%'}),
        ])
    ])


def create_logs_view():
    """Create the system logs view."""
    return html.Div([
        html.Div(className="card", children=[
            html.Div("System Logs", className="card-header"),
            html.Div(
                id='logs-display',
                style={
                    'backgroundColor': 'var(--bg-secondary)',
                    'padding': '16px',
                    'borderRadius': '6px',
                    'fontFamily': 'monospace',
                    'fontSize': '12px',
                    'maxHeight': '500px',
                    'overflowY': 'auto'
                },
                children=[
                    html.Div(f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard initialized"),
                    html.Div(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for robot connection..."),
                ]
            )
        ])
    ])


def create_help_view():
    """Create the help and keyboard shortcuts view."""
    shortcuts = [
        ('Ctrl+S', 'Start Tuner'),
        ('Ctrl+Q', 'Stop Tuner'),
        ('Ctrl+O', 'Run Optimization'),
        ('Ctrl+K', 'Skip Coefficient'),
        ('Ctrl+←', 'Previous Coefficient'),
        ('Ctrl+→', 'Next Coefficient'),
        ('Ctrl+↑', 'Fine Tune Up'),
        ('Ctrl+↓', 'Fine Tune Down'),
        ('Ctrl+H', 'Toggle Sidebar'),
        ('Ctrl+M', 'Toggle Mode (Normal/Advanced)'),
        ('Ctrl+Shift+M', 'Toggle More Features'),
        ('?', 'Show All Shortcuts'),
    ]
    
    return html.Div([
        html.Div(className="card", children=[
            html.Div("Take a Tour", className="card-header"),
            html.P("New to the dashboard? Take an interactive tour to learn about all the features!"),
            dbc.Button(
                "Start Interactive Tour",
                id='start-tour-button',
                className="btn-primary",
                size="lg",
                style={'width': '100%', 'marginBottom': '10px'}
            ),
            html.P([
                "The tour will guide you through:",
                html.Ul([
                    html.Li("Quick Actions and controls"),
                    html.Li("All 7 coefficient sliders"),
                    html.Li("Graphs and visualizations"),
                    html.Li("Settings and configuration"),
                    html.Li("Robot status monitoring"),
                    html.Li("Advanced features"),
                ], style={'marginTop': '10px', 'marginBottom': '0'})
            ], style={'fontSize': '14px', 'color': 'var(--text-secondary)', 'marginBottom': '0'})
        ]),
        
        html.Div(className="card", children=[
            html.Div("Keyboard Shortcuts", className="card-header"),
            html.Table(className="table-github", children=[
                html.Thead([
                    html.Tr([
                        html.Th("Shortcut"),
                        html.Th("Action")
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(html.Code(shortcut)),
                        html.Td(action)
                    ]) for shortcut, action in shortcuts
                ])
            ])
        ]),
        
        html.Div(className="card", children=[
            html.Div("About", className="card-header"),
            html.P("BayesOpt Dashboard v1.0"),
            html.P("Comprehensive browser-based control system for the Bayesian Optimization Tuner."),
            html.P("Features: GitHub-inspired design, two-level mode system, keyboard shortcuts, and complete runtime control over all tuner settings.")
        ]),
        
        html.Div(className="card", children=[
            html.Div("Robot Runner Game", className="card-header"),
            html.P("When the robot is disconnected, a fun jumping game automatically appears!"),
            html.P("Press SPACE to jump over obstacles. Score points and challenge yourself during downtime."),
            html.P(html.Em("Like Chrome's dino game, but with a robot!"), style={'color': 'var(--text-secondary)'})
        ])
    ])


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


# Callbacks
@app.callback(
    Output('main-content', 'children'),
    Output('main-content', 'className'),
    [Input({'type': 'nav-btn', 'index': ALL}, 'n_clicks')],
    [State('sidebar', 'className')]
)
def update_view(clicks, sidebar_class):
    """Update the main content view based on sidebar navigation."""
    ctx = callback_context
    if not ctx.triggered:
        return create_dashboard_view(), 'main-content'
    
    # Determine which button was clicked
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == '':
        return create_dashboard_view(), 'main-content'
    
    try:
        button_data = json.loads(triggered_id)
        view = button_data.get('index', 'dashboard')
    except:
        return create_dashboard_view(), 'main-content'
    
    # Map view to content - use lazy evaluation to avoid errors
    try:
        view_functions = {
            'dashboard': create_dashboard_view,
            'coefficients': create_coefficients_view,
            'workflow': create_workflow_view,
            'graphs': create_graphs_view,
            'settings': create_settings_view,
            'robot': create_robot_status_view,
            'notes': create_notes_view,
            'danger': create_danger_zone_view,
            'logs': create_logs_view,
            'help': create_help_view
        }
        
        view_func = view_functions.get(view, create_dashboard_view)
        content = view_func()
    except Exception as e:
        print(f"Error rendering view {view}: {e}")
        content = create_dashboard_view()
    
    class_name = 'main-content expanded' if 'collapsed' in sidebar_class else 'main-content'
    
    return content, class_name


@app.callback(
    Output('sidebar', 'className'),
    [Input('sidebar-toggle', 'n_clicks')],
    [State('sidebar', 'className')]
)
def toggle_sidebar(n_clicks, current_class):
    """Toggle sidebar collapsed state."""
    if n_clicks:
        if 'collapsed' in current_class:
            return 'sidebar'
        else:
            return 'sidebar collapsed'
    return current_class


@app.callback(
    [Output('app-state', 'data'),
     Output('root-container', 'data-theme')],
    [Input('mode-toggle', 'n_clicks')],
    [State('app-state', 'data')]
)
def update_app_state(mode_clicks, state):
    """Update application state."""
    ctx = callback_context
    if not ctx.triggered:
        return state, 'light'
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'mode-toggle':
        state['mode'] = 'advanced' if state['mode'] == 'normal' else 'normal'
    
    return state, 'light'  # Always return light theme


@app.callback(
    Output('keyboard-banner', 'style'),
    [Input('dismiss-banner', 'n_clicks')]
)
def dismiss_banner(n_clicks):
    """Dismiss the keyboard shortcuts banner."""
    if n_clicks:
        return {'display': 'none'}
    return {'display': 'flex'}


@app.callback(
    Output('robot-game-container', 'style'),
    [Input('update-interval', 'n_intervals')],
    [State('app-state', 'data')]
)
def toggle_robot_game(n_intervals, state):
    """Show robot game when disconnected from robot."""
    if state.get('connection_status') == 'disconnected':
        return {'display': 'block', 'textAlign': 'center', 'padding': '50px 0'}
    return {'display': 'none'}


@app.callback(
    Output('main-content', 'children', allow_duplicate=True),
    [Input('start-tour-button', 'n_clicks')],
    [State('app-state', 'data')],
    prevent_initial_call=True
)
def start_tour(n_clicks, state):
    """Start the interactive tour of the dashboard."""
    if not n_clicks:
        return create_help_view()
    
    # Create tour overlay with step-by-step guide
    tour_steps = [
        {
            'title': 'Welcome to BayesOpt Dashboard!',
            'description': 'This interactive tour will show you all the powerful features at your fingertips. Click Next to continue.',
            'target': None
        },
        {
            'title': 'Dashboard Overview',
            'description': 'The main dashboard gives you quick access to start/stop tuning, run optimizations, and navigate coefficients.',
            'target': 'dashboard'
        },
        {
            'title': 'All 7 Coefficients',
            'description': 'Access interactive sliders for all 7 parameters: Drag Coefficient, Gravity, Shot Height, Target Height, Shooter Angle, RPM, and Exit Velocity.',
            'target': 'coefficients'
        },
        {
            'title': 'Graphs & Analytics',
            'description': 'Visualize success rates, coefficient history, optimization progress, and shot distributions with toggleable graphs.',
            'target': 'graphs'
        },
        {
            'title': 'Complete Settings Control',
            'description': 'Adjust ALL tuner settings in real-time: auto-optimize, auto-advance, ML algorithms, NetworkTables config, logging, and more!',
            'target': 'settings'
        },
        {
            'title': 'Robot Status Monitoring',
            'description': 'Monitor robot vitals: battery, CPU, memory, CAN utilization, and view robot-specific logs and graphs.',
            'target': 'robot-status'
        },
        {
            'title': 'Advanced Mode',
            'description': 'Switch to Advanced mode to access 11 ML algorithms, 6 hybrid strategies, and experimental features.',
            'target': 'mode-toggle'
        },
        {
            'title': 'Tour Complete!',
            'description': 'You\'re all set! Explore the dashboard and use keyboard shortcuts (press ?) for faster control. Click Dashboard to return.',
            'target': None
        }
    ]
    
    return html.Div([
        html.Div(className="tour-overlay", style={
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.7)',
            'zIndex': '2000',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center'
        }, children=[
            html.Div(className="tour-card", style={
                'backgroundColor': 'var(--bg-primary)',
                'borderRadius': '8px',
                'padding': '30px',
                'maxWidth': '500px',
                'boxShadow': '0 10px 40px rgba(0,0,0,0.3)'
            }, children=[
                html.H2("Welcome to the Tour!", style={'color': 'var(--accent-primary)', 'marginBottom': '20px'}),
                html.P("The interactive tour will guide you through all dashboard features step-by-step.", style={'marginBottom': '20px'}),
                html.P("Features you'll discover:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Ul([
                    html.Li("Quick Actions and main controls"),
                    html.Li("All 7 coefficient sliders with fine tuning"),
                    html.Li("Graphs and data visualizations"),
                    html.Li("Complete settings panel with 60+ options"),
                    html.Li("Robot status monitoring"),
                    html.Li("Advanced ML features"),
                    html.Li("Keyboard shortcuts"),
                ]),
                html.Div(style={'marginTop': '30px', 'display': 'flex', 'gap': '10px'}, children=[
                    dbc.Button("Start Tour", className="btn-primary", size="lg", href="#", style={'flex': '1'}),
                    dbc.Button("Skip Tour", className="btn-secondary", size="lg", href="#", style={'flex': '1'}),
                ])
            ])
        ])
    ])


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
