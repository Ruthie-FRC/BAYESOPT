"""
Callback functions for the BayesOpt Dashboard.

Import this module after creating the app instance to register all callbacks.
"""

from dash import Input, Output, State, callback_context, ALL, MATCH, no_update
import dash
import dash_bootstrap_components as dbc
import json
from datetime import datetime

from dashboard_config import COEFFICIENT_DEFAULTS, COEFFICIENT_CONFIG

# Import layout functions - these will be needed by callbacks
# We'll handle the circular import by importing inside the callback registration function

def register_callbacks(app):
    """Register all callbacks with the Dash app."""
    from layouts import (
        create_dashboard_view, create_coefficients_view, create_workflow_view,
        create_graphs_view, create_settings_view, create_robot_status_view,
        create_notes_view, create_danger_zone_view, create_logs_view, create_help_view
    )
    
    # Callbacks start here
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
        except (json.JSONDecodeError, KeyError, TypeError):
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
         Output('root-container', 'data-theme'),
         Output('theme-toggle', 'children')],
        [Input('mode-toggle', 'n_clicks'),
         Input('theme-toggle', 'n_clicks')],
        [State('app-state', 'data')]
    )
    def update_app_state(mode_clicks, theme_clicks, state):
        """Update application state and theme."""
        ctx = callback_context
        if not ctx.triggered:
            return state, state.get('theme', 'light'), '🌙 Dark Mode'
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'mode-toggle':
            state['mode'] = 'advanced' if state['mode'] == 'normal' else 'normal'
        elif button_id == 'theme-toggle':
            # Toggle between light and dark theme
            state['theme'] = 'dark' if state.get('theme', 'light') == 'light' else 'light'
        
        # Update theme toggle button text
        theme_button_text = '☀️ Light Mode' if state.get('theme', 'light') == 'dark' else '🌙 Dark Mode'
        
        return state, state.get('theme', 'light'), theme_button_text
    
    
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
    
    
    # ============================================================================
    # Button Callback Functions
    # ============================================================================
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input('start-tuner-btn', 'n_clicks'),
         Input('stop-tuner-btn', 'n_clicks'),
         Input('run-optimization-btn', 'n_clicks'),
         Input('skip-coefficient-btn', 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_core_control_buttons(start_clicks, stop_clicks, run_clicks, skip_clicks, state):
        """Handle core control button clicks."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'start-tuner-btn':
            state['tuner_enabled'] = True
            print("✅ Tuner Started")
        elif button_id == 'stop-tuner-btn':
            state['tuner_enabled'] = False
            print("⛔ Tuner Stopped")
        elif button_id == 'run-optimization-btn':
            print("🔄 Running Optimization...")
            # In a real implementation, this would trigger the optimization
        elif button_id == 'skip-coefficient-btn':
            print("⏭️ Skipping to Next Coefficient")
            # In a real implementation, this would advance to the next coefficient
        
        return state
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input('prev-coeff-btn', 'n_clicks'),
         Input('next-coeff-btn', 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_coefficient_navigation(prev_clicks, next_clicks, state):
        """Handle coefficient navigation buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        coefficients = ['kDragCoefficient', 'kGravity', 'kShotHeight', 'kTargetHeight', 
                        'kShooterAngle', 'kShooterRPM', 'kExitVelocity']
        current_idx = coefficients.index(state['current_coefficient']) if state['current_coefficient'] in coefficients else 0
        
        if button_id == 'prev-coeff-btn':
            new_idx = (current_idx - 1) % len(coefficients)
            state['current_coefficient'] = coefficients[new_idx]
            print(f"⬅️ Previous Coefficient: {state['current_coefficient']}")
        elif button_id == 'next-coeff-btn':
            new_idx = (current_idx + 1) % len(coefficients)
            state['current_coefficient'] = coefficients[new_idx]
            print(f"➡️ Next Coefficient: {state['current_coefficient']}")
        
        return state
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input('fine-tune-up-btn', 'n_clicks'),
         Input('fine-tune-down-btn', 'n_clicks'),
         Input('fine-tune-left-btn', 'n_clicks'),
         Input('fine-tune-right-btn', 'n_clicks'),
         Input('fine-tune-reset-btn', 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_fine_tuning_buttons(up_clicks, down_clicks, left_clicks, right_clicks, reset_clicks, state):
        """Handle fine tuning control buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'fine-tune-up-btn':
            print("⬆️ Fine Tune Up")
        elif button_id == 'fine-tune-down-btn':
            print("⬇️ Fine Tune Down")
        elif button_id == 'fine-tune-left-btn':
            print("⬅️ Fine Tune Left")
        elif button_id == 'fine-tune-right-btn':
            print("➡️ Fine Tune Right")
        elif button_id == 'fine-tune-reset-btn':
            print("🔄 Fine Tune Reset")
        
        return state
    
    
    @app.callback(
        [Output({'type': 'coeff-slider', 'index': 'kDragCoefficient'}, 'value'),
         Output({'type': 'coeff-slider', 'index': 'kGravity'}, 'value'),
         Output({'type': 'coeff-slider', 'index': 'kShotHeight'}, 'value'),
         Output({'type': 'coeff-slider', 'index': 'kTargetHeight'}, 'value'),
         Output({'type': 'coeff-slider', 'index': 'kShooterAngle'}, 'value'),
         Output({'type': 'coeff-slider', 'index': 'kShooterRPM'}, 'value'),
         Output({'type': 'coeff-slider', 'index': 'kExitVelocity'}, 'value'),
         Output('app-state', 'data', allow_duplicate=True)],
        [Input('increase-all-btn', 'n_clicks'),
         Input('decrease-all-btn', 'n_clicks'),
         Input('reset-all-coeff-btn', 'n_clicks'),
         Input('copy-coeff-btn', 'n_clicks')],
        [State({'type': 'coeff-slider', 'index': 'kDragCoefficient'}, 'value'),
         State({'type': 'coeff-slider', 'index': 'kGravity'}, 'value'),
         State({'type': 'coeff-slider', 'index': 'kShotHeight'}, 'value'),
         State({'type': 'coeff-slider', 'index': 'kTargetHeight'}, 'value'),
         State({'type': 'coeff-slider', 'index': 'kShooterAngle'}, 'value'),
         State({'type': 'coeff-slider', 'index': 'kShooterRPM'}, 'value'),
         State({'type': 'coeff-slider', 'index': 'kExitVelocity'}, 'value'),
         State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_coefficient_bulk_actions(increase_clicks, decrease_clicks, reset_clicks, copy_clicks,
                                        drag_val, grav_val, shot_val, target_val, angle_val, rpm_val, velocity_val,
                                        state):
        """Handle bulk coefficient action buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Current values
        current_values = [drag_val, grav_val, shot_val, target_val, angle_val, rpm_val, velocity_val]
        
        if button_id == 'increase-all-btn':
            print("⬆️ Increasing All Coefficients by 10%")
            # Increase all coefficient values by 10%
            new_values = [v * 1.1 for v in current_values]
            return new_values + [state]
            
        elif button_id == 'decrease-all-btn':
            print("⬇️ Decreasing All Coefficients by 10%")
            # Decrease all coefficient values by 10%
            new_values = [v * 0.9 for v in current_values]
            return new_values + [state]
            
        elif button_id == 'reset-all-coeff-btn':
            print("🔄 Resetting All Coefficients to Defaults")
            # Reset all coefficients to defaults
            state['coefficient_values'] = {}
            default_values = [COEFFICIENT_DEFAULTS['kDragCoefficient'], COEFFICIENT_DEFAULTS['kGravity'], COEFFICIENT_DEFAULTS['kShotHeight'],
                             COEFFICIENT_DEFAULTS['kTargetHeight'], COEFFICIENT_DEFAULTS['kShooterAngle'], COEFFICIENT_DEFAULTS['kShooterRPM'],
                             COEFFICIENT_DEFAULTS['kExitVelocity']]
            return default_values + [state]
            
        elif button_id == 'copy-coeff-btn':
            print("📋 Copied Current Coefficient Values")
            # Log current values (in real implementation, would copy to clipboard)
            print(f"  kDragCoefficient: {drag_val}")
            print(f"  kGravity: {grav_val}")
            print(f"  kShotHeight: {shot_val}")
            print(f"  kTargetHeight: {target_val}")
            print(f"  kShooterAngle: {angle_val}")
            print(f"  kShooterRPM: {rpm_val}")
            print(f"  kExitVelocity: {velocity_val}")
            return current_values + [state]
        
        return current_values + [state]
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input({'type': 'coeff-slider', 'index': ALL}, 'value')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_coefficient_sliders(slider_values, state):
        """Handle coefficient slider changes."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        # Extract which slider was changed
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id:
            try:
                slider_data = json.loads(triggered_id)
                coeff_name = slider_data.get('index')
                if coeff_name:
                    # Get the value from the triggered slider
                    new_value = ctx.triggered[0]['value']
                    if 'coefficient_values' not in state:
                        state['coefficient_values'] = {}
                    state['coefficient_values'][coeff_name] = new_value
                    print(f"📊 {coeff_name} = {new_value}")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        return state
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input({'type': 'fine-inc', 'index': MATCH}, 'n_clicks'),
         Input({'type': 'fine-dec', 'index': MATCH}, 'n_clicks'),
         Input({'type': 'fine-inc-large', 'index': MATCH}, 'n_clicks'),
         Input({'type': 'fine-dec-large', 'index': MATCH}, 'n_clicks'),
         Input({'type': 'reset-coeff', 'index': MATCH}, 'n_clicks')],
        [State({'type': 'coeff-slider', 'index': MATCH}, 'value'),
         State({'type': 'coeff-slider', 'index': MATCH}, 'id'),
         State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_coefficient_fine_adjustments(inc_clicks, dec_clicks, inc_large_clicks, dec_large_clicks, reset_clicks,
                                            current_value, slider_id, state):
        """Handle fine adjustment buttons for individual coefficients."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Get coefficient name from the slider ID
        coeff_name = slider_id.get('index') if isinstance(slider_id, dict) else None
        if not coeff_name:
            return state
        
        # Use module-level configuration constants
        coeff_config = COEFFICIENT_CONFIG.get(coeff_name, {'step': 0.1, 'min': 0, 'max': 100})
        step = coeff_config['step']
        min_val = coeff_config['min']
        max_val = coeff_config['max']
        
        try:
            button_data = json.loads(triggered_id)
            button_type = button_data.get('type')
            
            new_value = current_value
            
            if button_type == 'fine-inc':
                new_value = min(current_value + step, max_val)
                print(f"➕ {coeff_name}: {current_value:.4f} → {new_value:.4f} (+{step})")
            elif button_type == 'fine-dec':
                new_value = max(current_value - step, min_val)
                print(f"➖ {coeff_name}: {current_value:.4f} → {new_value:.4f} (-{step})")
            elif button_type == 'fine-inc-large':
                new_value = min(current_value + (step * 10), max_val)
                print(f"➕➕ {coeff_name}: {current_value:.4f} → {new_value:.4f} (+{step * 10})")
            elif button_type == 'fine-dec-large':
                new_value = max(current_value - (step * 10), min_val)
                print(f"➖➖ {coeff_name}: {current_value:.4f} → {new_value:.4f} (-{step * 10})")
            elif button_type == 'reset-coeff':
                new_value = COEFFICIENT_DEFAULTS.get(coeff_name, current_value)
                print(f"🔄 Reset {coeff_name}: {current_value:.4f} → {new_value:.4f} (default)")
                # Remove from state overrides when resetting to default
                if 'coefficient_values' in state and coeff_name in state['coefficient_values']:
                    del state['coefficient_values'][coeff_name]
                # Store the new value in state
                state['coefficient_values'][coeff_name] = new_value
                return state
            
            # Update state with new value for all non-reset operations
            if 'coefficient_values' not in state:
                state['coefficient_values'] = {}
            state['coefficient_values'][coeff_name] = new_value
            
            return state
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error in fine adjustment: {e}")
            return state
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input({'type': 'jump-to-btn', 'index': ALL}, 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_jump_to_buttons(clicks, state):
        """Handle jump to coefficient buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id:
            try:
                button_data = json.loads(triggered_id)
                coeff_name = button_data.get('index')
                state['current_coefficient'] = coeff_name
                print(f"⤵️ Jumped to {coeff_name}")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        return state
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input('export-graphs-btn', 'n_clicks'),
         Input('refresh-graphs-btn', 'n_clicks'),
         Input('pause-graphs-btn', 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_graph_controls(export_clicks, refresh_clicks, pause_clicks, state):
        """Handle graph control buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'export-graphs-btn':
            print("📥 Exporting All Graphs...")
        elif button_id == 'refresh-graphs-btn':
            print("🔄 Refreshing Graph Data...")
        elif button_id == 'pause-graphs-btn':
            print("⏸️ Toggling Graph Auto-Update")
        
        return state
    
    
    @app.callback(
        [Output('graph-success-rate', 'style'),
         Output('graph-coefficient-history', 'style'),
         Output('graph-optimization-progress', 'style'),
         Output('graph-shot-distribution', 'style'),
         Output('graph-algorithm-comparison', 'style'),
         Output('graph-convergence', 'style'),
         Output('graph-heatmap', 'style'),
         Output('graph-velocity-dist', 'style')],
        [Input('graph-toggles', 'value')]
    )
    def toggle_graph_visibility(selected_graphs):
        """Toggle visibility of graphs based on checklist."""
        graph_ids = [
            'success_rate',
            'coefficient_history',
            'optimization_progress',
            'shot_distribution',
            'algorithm_comparison',
            'convergence',
            'heatmap',
            'velocity_dist'
        ]
        
        styles = []
        for graph_id in graph_ids:
            if graph_id in selected_graphs:
                styles.append({'display': 'block'})
            else:
                styles.append({'display': 'none'})
        
        return styles
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input('start-workflow-btn', 'n_clicks'),
         Input('skip-workflow-btn', 'n_clicks'),
         Input('prev-workflow-btn', 'n_clicks'),
         Input('reset-workflow-btn', 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_workflow_controls(start_clicks, skip_clicks, prev_clicks, reset_clicks, state):
        """Handle workflow control buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'start-workflow-btn':
            print("▶️ Starting Workflow from Beginning")
        elif button_id == 'skip-workflow-btn':
            print("⏭️ Skipping to Next in Workflow")
        elif button_id == 'prev-workflow-btn':
            print("⏮️ Going to Previous in Workflow")
        elif button_id == 'reset-workflow-btn':
            print("🔄 Resetting Workflow Progress")
        
        return state
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input({'type': 'backtrack', 'index': ALL}, 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_backtrack_buttons(clicks, state):
        """Handle backtrack coefficient buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id:
            try:
                button_data = json.loads(triggered_id)
                coeff_name = button_data.get('index')
                print(f"⏪ Backtracking to {coeff_name}")
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        return state
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input('save-session-btn', 'n_clicks'),
         Input('load-session-btn', 'n_clicks'),
         Input('export-session-btn', 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_session_management(save_clicks, load_clicks, export_clicks, state):
        """Handle session management buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'save-session-btn':
            print("💾 Saving Session...")
        elif button_id == 'load-session-btn':
            print("📁 Loading Session...")
        elif button_id == 'export-session-btn':
            print("📤 Exporting Session Data...")
        
        return state
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input('save-settings-btn', 'n_clicks'),
         Input('load-settings-btn', 'n_clicks'),
         Input('reset-settings-btn', 'n_clicks'),
         Input('set-baseline-btn', 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_settings_buttons(save_clicks, load_clicks, reset_clicks, baseline_clicks, state):
        """Handle settings management buttons."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'save-settings-btn':
            print("💾 Saving Settings...")
        elif button_id == 'load-settings-btn':
            print("📁 Loading Settings...")
        elif button_id == 'reset-settings-btn':
            print("🔄 Resetting Settings to Defaults...")
        elif button_id == 'set-baseline-btn':
            print("⭐ Setting Current Values as Baseline")
        
        return state
    
    
    @app.callback(
        [Output('notes-list', 'children'),
         Output('note-input', 'value')],
        [Input('add-note-btn', 'n_clicks')],
        [State('note-input', 'value'),
         State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_add_note(clicks, note_text, state):
        """Handle adding a new note."""
        if not clicks or not note_text:
            return dash.no_update, dash.no_update
        
        timestamp = datetime.now().strftime('%I:%M:%S %p')
        new_note = html.Div(
            className="card",
            style={'marginBottom': '8px', 'padding': '12px'},
            children=[
                html.Div(f"[{timestamp}]", style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                html.P(note_text, style={'margin': '4px 0 0 0'})
            ]
        )
        
        # Get current notes
        if 'notes' not in state:
            state['notes'] = []
        
        state['notes'].insert(0, {'time': timestamp, 'text': note_text})
        
        # Create list of note elements
        notes_elements = [
            html.Div(
                className="card",
                style={'marginBottom': '8px', 'padding': '12px'},
                children=[
                    html.Div(f"[{note['time']}]", style={'fontSize': '12px', 'color': 'var(--text-secondary)'}),
                    html.P(note['text'], style={'margin': '4px 0 0 0'})
                ]
            ) for note in state['notes']
        ]
        
        print(f"📝 Added Note: {note_text}")
        
        return notes_elements if notes_elements else [html.P("No notes yet", style={'fontStyle': 'italic', 'color': 'var(--text-secondary)'})], ""
    
    
    @app.callback(
        [Output('todos-list', 'children'),
         Output('todo-input', 'value')],
        [Input('add-todo-btn', 'n_clicks')],
        [State('todo-input', 'value'),
         State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_add_todo(clicks, todo_text, state):
        """Handle adding a new to-do item."""
        if not clicks or not todo_text:
            return dash.no_update, dash.no_update
        
        if 'todos' not in state:
            state['todos'] = []
        
        state['todos'].append({'text': todo_text, 'done': False})
        
        # Create list of todo elements
        todos_elements = [
            html.Div(
                className="card",
                style={'marginBottom': '8px', 'padding': '12px', 'display': 'flex', 'alignItems': 'center'},
                children=[
                    dbc.Checklist(
                        options=[{'label': todo['text'], 'value': 'done'}],
                        value=['done'] if todo.get('done', False) else [],
                        inline=True
                    )
                ]
            ) for todo in state['todos']
        ]
        
        print(f"✅ Added To-Do: {todo_text}")
        
        return todos_elements if todos_elements else [html.P("No to-dos yet", style={'fontStyle': 'italic', 'color': 'var(--text-secondary)'})], ""
    
    
    @app.callback(
        Output('app-state', 'data', allow_duplicate=True),
        [Input('reconfigure-base-btn', 'n_clicks'),
         Input('restore-defaults-btn', 'n_clicks'),
         Input('lock-config-btn', 'n_clicks'),
         Input('export-config-btn', 'n_clicks'),
         Input('import-config-btn', 'n_clicks'),
         Input('reset-data-btn', 'n_clicks'),
         Input('clear-pinned-btn', 'n_clicks'),
         Input('emergency-stop-btn', 'n_clicks'),
         Input('force-retune-btn', 'n_clicks')],
        [State('app-state', 'data')],
        prevent_initial_call=True
    )
    def handle_danger_zone_buttons(reconfig_clicks, restore_clicks, lock_clicks, export_clicks,
                                    import_clicks, reset_clicks, clear_clicks, emergency_clicks,
                                    retune_clicks, state):
        """Handle danger zone buttons with appropriate warnings."""
        ctx = callback_context
        if not ctx.triggered:
            return state
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'reconfigure-base-btn':
            print("⚙️ Reconfiguring Base Point...")
        elif button_id == 'restore-defaults-btn':
            print("🔄 Restoring Factory Defaults...")
        elif button_id == 'lock-config-btn':
            state['config_locked'] = not state.get('config_locked', False)
            status = "Locked" if state['config_locked'] else "Unlocked"
            print(f"🔐 Configuration {status}")
        elif button_id == 'export-config-btn':
            print("📤 Exporting Configuration...")
        elif button_id == 'import-config-btn':
            print("📥 Importing Configuration...")
        elif button_id == 'reset-data-btn':
            print("⚠️ Resetting All Tuning Data...")
            state['coefficient_values'] = {}
            state['shot_count'] = 0
            state['success_rate'] = 0.0
        elif button_id == 'clear-pinned-btn':
            print("🧹 Clearing All Pinned Data...")
        elif button_id == 'emergency-stop-btn':
            print("🔥 EMERGENCY STOP!")
            state['tuner_enabled'] = False
        elif button_id == 'force-retune-btn':
            print("🔄 Forcing Retune of Current Coefficient...")
        
        return state
    
    
    @app.callback(
        Output('mode-toggle', 'children'),
        [Input('app-state', 'data')]
    )
    def update_mode_toggle_label(state):
        """Update the mode toggle button label based on current mode."""
        if state.get('mode', 'normal') == 'normal':
            return "Switch to Advanced"
        else:
            return "Switch to Normal"
    
    
    @app.callback(
        [Output('coeff-display', 'children'),
         Output('shot-display', 'children'),
         Output('success-display', 'children')],
        [Input('app-state', 'data')]
    )
    def update_dashboard_displays(state):
        """Update the dashboard display values."""
        coeff = state.get('current_coefficient', 'kDragCoefficient')
        shots = state.get('shot_count', 0)
        success = state.get('success_rate', 0.0)
        
        return coeff, str(shots), f"{success:.1%}"
    
    
    @app.callback(
        [Output('status-bar-time', 'children'),
         Output('status-bar-shots', 'children'),
         Output('status-bar-success', 'children')],
        [Input('update-interval', 'n_intervals')],
        [State('app-state', 'data')]
    )
    def update_status_bar(n_intervals, state):
        """Update the status bar with current time and stats."""
        current_time = datetime.now().strftime('%I:%M:%S %p')
        shots = str(state.get('shot_count', 0))
        success = f"{state.get('success_rate', 0.0):.1%}"
        
        return current_time, shots, success
    
    
