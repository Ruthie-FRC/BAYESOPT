"""
CSS styles and JavaScript code for the BayesOpt Dashboard.
"""

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

/* Dark Mode - Bootstrap Components */
[data-theme="dark"] .modal-content {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .modal-header {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border-bottom-color: var(--border-default) !important;
}

[data-theme="dark"] .modal-body {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .modal-footer {
    background-color: var(--bg-tertiary) !important;
    border-top-color: var(--border-default) !important;
}

[data-theme="dark"] .dropdown-menu {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .dropdown-item {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .dropdown-item:hover,
[data-theme="dark"] .dropdown-item:focus {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .dropdown-divider {
    border-top-color: var(--border-default) !important;
}

[data-theme="dark"] .popover {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .popover-header {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border-bottom-color: var(--border-default) !important;
}

[data-theme="dark"] .popover-body {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .tooltip-inner {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .list-group-item {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .list-group-item:hover {
    background-color: var(--bg-tertiary) !important;
}

/* Dark Mode - Dash Dev Tools and Error Panels */
[data-theme="dark"] .dash-debug-menu__outer {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .dash-debug-menu__outer--expanded {
    background-color: var(--bg-secondary) !important;
}

[data-theme="dark"] .dash-debug-menu__popup {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
}

[data-theme="dark"] .dash-debug-menu__button {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .dash-debug-menu__button:hover {
    background-color: var(--bg-primary) !important;
}

[data-theme="dark"] .dash-debug-menu__button--selected {
    background-color: var(--bg-primary) !important;
    color: var(--accent-primary) !important;
}

[data-theme="dark"] .dash-debug-menu__content {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .dash-debug-menu__status,
[data-theme="dark"] .dash-debug-menu__version {
    color: var(--text-secondary) !important;
}

[data-theme="dark"] .dash-debug-menu__divider {
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .dash-error-card {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .dash-error-card--container {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .dash-error-card__topbar {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border-bottom-color: var(--border-default) !important;
}

[data-theme="dark"] .dash-error-card__content {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .dash-error-card__message {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .dash-error-card__list {
    background-color: var(--bg-secondary) !important;
}

[data-theme="dark"] .dash-fe-error-item {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .dash-fe-error-item:hover {
    background-color: var(--bg-tertiary) !important;
}

[data-theme="dark"] .dash-fe-error__title {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .dash-fe-error__timestamp {
    color: var(--text-tertiary) !important;
}

[data-theme="dark"] .dash-fe-error-top__group {
    color: var(--text-primary) !important;
}

/* Legacy dash dev tools classes */
[data-theme="dark"] ._dash-dev-tools {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] ._dash-dev-tools-tab {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] ._dash-dev-tools-tab._active {
    background-color: var(--bg-primary) !important;
}

[data-theme="dark"] ._dash-dev-tools-panel {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] ._dash-error {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] ._dash-error-menu {
    background-color: var(--bg-tertiary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] ._dash-error-card {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] ._dash-error-card__content {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

/* Dark Mode - Form Controls */
[data-theme="dark"] .form-control {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .form-control:focus {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 0.2rem rgba(255, 140, 0, 0.25) !important;
}

[data-theme="dark"] .form-control::placeholder {
    color: var(--text-tertiary) !important;
}

[data-theme="dark"] .form-select {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .form-select:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 0.2rem rgba(255, 140, 0, 0.25) !important;
}

[data-theme="dark"] option {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

/* Dark Mode - Alerts and Badges */
[data-theme="dark"] .alert {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .badge {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
}

/* Dark Mode - Accordions and Collapses */
[data-theme="dark"] .accordion-item {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .accordion-button {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .accordion-button:not(.collapsed) {
    background-color: var(--bg-primary) !important;
    color: var(--accent-primary) !important;
}

[data-theme="dark"] .accordion-body {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

/* Dark Mode - Offcanvas */
[data-theme="dark"] .offcanvas {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .offcanvas-header {
    border-bottom-color: var(--border-default) !important;
}

[data-theme="dark"] .offcanvas-footer {
    border-top-color: var(--border-default) !important;
}

/* Dark Mode - Nav Tabs and Pills */
[data-theme="dark"] .nav-tabs {
    border-bottom-color: var(--border-default) !important;
}

[data-theme="dark"] .nav-tabs .nav-link {
    color: var(--text-secondary) !important;
    border-color: transparent !important;
}

[data-theme="dark"] .nav-tabs .nav-link:hover {
    border-color: var(--border-default) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .nav-tabs .nav-link.active {
    background-color: var(--bg-primary) !important;
    color: var(--accent-primary) !important;
    border-color: var(--border-default) var(--border-default) var(--bg-primary) !important;
}

[data-theme="dark"] .nav-pills .nav-link {
    color: var(--text-secondary) !important;
}

[data-theme="dark"] .nav-pills .nav-link:hover {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .nav-pills .nav-link.active {
    background-color: var(--accent-primary) !important;
}

/* Dark Mode - Progress Bars */
[data-theme="dark"] .progress {
    background-color: var(--bg-tertiary) !important;
}

/* Dark Mode - Breadcrumbs */
[data-theme="dark"] .breadcrumb {
    background-color: var(--bg-secondary) !important;
}

[data-theme="dark"] .breadcrumb-item + .breadcrumb-item::before {
    color: var(--text-tertiary) !important;
}

/* Dark Mode - Pagination */
[data-theme="dark"] .page-link {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .page-link:hover {
    background-color: var(--bg-tertiary) !important;
    border-color: var(--border-default) !important;
    color: var(--accent-primary) !important;
}

[data-theme="dark"] .page-item.active .page-link {
    background-color: var(--accent-primary) !important;
    border-color: var(--accent-primary) !important;
}

[data-theme="dark"] .page-item.disabled .page-link {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-tertiary) !important;
}

/* Dark Mode - Spinners and Loading */
[data-theme="dark"] .spinner-border,
[data-theme="dark"] .spinner-grow {
    color: var(--accent-primary) !important;
}

/* Dark Mode - Close Buttons */
[data-theme="dark"] .btn-close {
    filter: invert(1) grayscale(100%) brightness(200%);
}

/* Dark Mode - Plotly Graphs */
[data-theme="dark"] .js-plotly-plot .plotly,
[data-theme="dark"] .js-plotly-plot .plotly .svg-container {
    background-color: var(--bg-primary) !important;
}

[data-theme="dark"] .modebar {
    background-color: var(--bg-secondary) !important;
}

[data-theme="dark"] .modebar-btn {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .modebar-btn:hover {
    background-color: var(--bg-tertiary) !important;
}

/* Dark Mode - Dash Core Components */
[data-theme="dark"] .Select-control {
    background-color: var(--bg-primary) !important;
    border-color: var(--border-default) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .Select-menu-outer {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .Select-option {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

[data-theme="dark"] .Select-option:hover {
    background-color: var(--bg-tertiary) !important;
}

[data-theme="dark"] .Select-value-label {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .Select-placeholder {
    color: var(--text-tertiary) !important;
}

/* Dark Mode - DatePicker */
[data-theme="dark"] .DateInput,
[data-theme="dark"] .DateRangePickerInput {
    background-color: var(--bg-primary) !important;
}

[data-theme="dark"] .DateInput_input,
[data-theme="dark"] .DateRangePickerInput_input {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .DayPicker {
    background-color: var(--bg-secondary) !important;
}

[data-theme="dark"] .CalendarMonth {
    background-color: var(--bg-secondary) !important;
}

[data-theme="dark"] .CalendarDay {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-muted) !important;
}

[data-theme="dark"] .CalendarDay:hover {
    background-color: var(--bg-tertiary) !important;
}

[data-theme="dark"] .CalendarDay__selected {
    background-color: var(--accent-primary) !important;
    color: white !important;
}

/* Dark Mode - Tabs Container */
[data-theme="dark"] .tab {
    background-color: var(--bg-secondary) !important;
    color: var(--text-secondary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .tab--selected {
    background-color: var(--bg-primary) !important;
    color: var(--accent-primary) !important;
    border-bottom-color: var(--accent-primary) !important;
}

[data-theme="dark"] .tab:hover {
    background-color: var(--bg-tertiary) !important;
}

/* Dark Mode - Textarea */
[data-theme="dark"] .dash-textarea {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

[data-theme="dark"] .dash-textarea:focus {
    border-color: var(--accent-primary) !important;
}

/* Dark Mode - Additional Global Overrides */
[data-theme="dark"] * {
    scrollbar-color: var(--bg-tertiary) var(--bg-primary) !important;
}

/* Force dark backgrounds on all containers */
[data-theme="dark"] div,
[data-theme="dark"] section,
[data-theme="dark"] article,
[data-theme="dark"] main {
    background-color: transparent !important;
}

/* Ensure main content area is dark */
[data-theme="dark"] #root-container,
[data-theme="dark"] #react-entry-point,
[data-theme="dark"] #_dash-app-content {
    background-color: var(--bg-primary) !important;
}

/* Dark mode for all white/light backgrounds */
[data-theme="dark"] [style*="background-color: rgb(255, 255, 255)"],
[data-theme="dark"] [style*="background-color: white"],
[data-theme="dark"] [style*="background-color: #fff"],
[data-theme="dark"] [style*="background-color: #ffffff"],
[data-theme="dark"] [style*="background-color: rgb(245, 246, 250)"],
[data-theme="dark"] [style*="background-color: #f5f6fa"],
[data-theme="dark"] [style*="background-color: #f6f8fa"] {
    background-color: var(--bg-primary) !important;
}

/* Dark mode for inline light gray backgrounds */
[data-theme="dark"] [style*="background-color: rgb(240, 240, 240)"],
[data-theme="dark"] [style*="background-color: #f0f0f0"],
[data-theme="dark"] [style*="background-color: #e8e8e8"],
[data-theme="dark"] [style*="background-color: rgb(232, 232, 232)"] {
    background-color: var(--bg-secondary) !important;
}

/* Ensure text color on forced dark backgrounds */
[data-theme="dark"] [style*="color: rgb(0, 0, 0)"],
[data-theme="dark"] [style*="color: black"],
[data-theme="dark"] [style*="color: #000"] {
    color: var(--text-primary) !important;
}

/* Dark mode for containers with explicit white background */
[data-theme="dark"] .container,
[data-theme="dark"] .container-fluid,
[data-theme="dark"] .row,
[data-theme="dark"] .col,
[data-theme="dark"] [class*="col-"] {
    background-color: transparent !important;
}

/* Ensure React components are dark */
[data-theme="dark"] ._dash-loading,
[data-theme="dark"] ._dash-loading-callback {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

/* Dark mode for any remaining light panels */
[data-theme="dark"] .panel,
[data-theme="dark"] .panel-default,
[data-theme="dark"] .panel-body,
[data-theme="dark"] .panel-heading {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

/* Dark mode for wells and jumbotrons */
[data-theme="dark"] .well,
[data-theme="dark"] .jumbotron {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

/* Dark mode for any divs with explicit inline styles */
[data-theme="dark"] div[style] {
    /* This will be overridden by more specific rules, but provides a base */
}

/* Dark mode for Bootstrap container backgrounds */
[data-theme="dark"] .bg-white,
[data-theme="dark"] .bg-light {
    background-color: var(--bg-primary) !important;
}

[data-theme="dark"] .bg-secondary {
    background-color: var(--bg-secondary) !important;
}

/* Dark mode for text colors */
[data-theme="dark"] .text-dark {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .text-muted {
    color: var(--text-secondary) !important;
}

/* Ensure borders are visible in dark mode */
[data-theme="dark"] .border,
[data-theme="dark"] [class*="border-"] {
    border-color: var(--border-default) !important;
}

/* Dark mode for any remaining card-like structures */
[data-theme="dark"] .card-body,
[data-theme="dark"] .card-header,
[data-theme="dark"] .card-footer {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
}

/* Force dark on layout containers */
[data-theme="dark"] [class*="layout"],
[data-theme="dark"] [class*="Layout"] {
    background-color: transparent !important;
}

/* Dark mode for dash-table components */
[data-theme="dark"] .dash-table-container {
    background-color: var(--bg-primary) !important;
}

[data-theme="dark"] .dash-spreadsheet {
    background-color: var(--bg-primary) !important;
}

[data-theme="dark"] .dash-spreadsheet-container {
    background-color: var(--bg-primary) !important;
}

[data-theme="dark"] .cell {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* Ensure all text inputs are dark */
[data-theme="dark"] input[type="text"],
[data-theme="dark"] input[type="email"],
[data-theme="dark"] input[type="password"],
[data-theme="dark"] input[type="search"],
[data-theme="dark"] input[type="tel"],
[data-theme="dark"] input[type="url"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}

/* Ultra-aggressive dark mode - catch all remaining light elements */
[data-theme="dark"] .banner,
[data-theme="dark"] [class*="banner"] {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border-color: var(--accent-primary) !important;
}

/* Force dark on all alert/info boxes */
[data-theme="dark"] [class*="alert"],
[data-theme="dark"] [class*="info"],
[data-theme="dark"] [class*="tip"],
[data-theme="dark"] [class*="warning"] {
    background-color: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
}

/* Dark mode for all remaining white/light inline backgrounds - more aggressive */
[data-theme="dark"] * {
    /* Catch-all for inline styles - will be overridden by more specific rules */
}

[data-theme="dark"] *:not(.btn):not(button):not([class*="accent"]) {
    /* Try to catch elements with inline background styles */
}

/* Force all divs with row/col to be transparent or dark */
[data-theme="dark"] .row > div,
[data-theme="dark"] .col > div,
[data-theme="dark"] [class*="col-"] > div {
    background-color: transparent !important;
}

/* Aggressive catch for Bootstrap utility classes */
[data-theme="dark"] .p-1, [data-theme="dark"] .p-2, [data-theme="dark"] .p-3,
[data-theme="dark"] .p-4, [data-theme="dark"] .p-5,
[data-theme="dark"] .m-1, [data-theme="dark"] .m-2, [data-theme="dark"] .m-3,
[data-theme="dark"] .m-4, [data-theme="dark"] .m-5 {
    background-color: transparent !important;
}

/* Force dark on any remaining card-like elements */
[data-theme="dark"] [style*="box-shadow"],
[data-theme="dark"] [style*="border-radius"] {
    background-color: var(--bg-secondary) !important;
}

/* Specific override for error panel background */
[data-theme="dark"] [class*="error"] > div,
[data-theme="dark"] [class*="Error"] > div {
    background-color: var(--bg-secondary) !important;
}

/* Override any remaining light backgrounds in error list */
[data-theme="dark"] [class*="error"] li,
[data-theme="dark"] [class*="error"] ul,
[data-theme="dark"] [class*="error"] div {
    background-color: transparent !important;
    color: var(--text-primary) !important;
}

/* Force dark on Quick Actions and Current Status cards */
[data-theme="dark"] h3,
[data-theme="dark"] h4,
[data-theme="dark"] h5 {
    color: var(--text-primary) !important;
}

/* Override for parent containers */
[data-theme="dark"] [class*="container"] > *,
[data-theme="dark"] [class*="wrapper"] > * {
    background-color: transparent !important;
}

/* Last resort - force dark on absolutely everything that's not a button or accent */
[data-theme="dark"] div:not([class*="btn"]):not([class*="button"]):not([class*="accent"]):not([class*="orange"]) {
    /* Only apply if it has a light background */
}

/* Specifically target light gray backgrounds #f0f0f0, #f5f6fa, etc */
[data-theme="dark"] [style*="#f0f0f0"],
[data-theme="dark"] [style*="#f5f6fa"],
[data-theme="dark"] [style*="#f6f8fa"],
[data-theme="dark"] [style*="#ffffff"],
[data-theme="dark"] [style*="#fff"],
[data-theme="dark"] [style*="rgb(240, 240, 240)"],
[data-theme="dark"] [style*="rgb(245, 246, 250)"],
[data-theme="dark"] [style*="rgb(246, 248, 250)"],
[data-theme="dark"] [style*="rgb(255, 255, 255)"] {
    background-color: var(--bg-secondary) !important;
}
"""

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
