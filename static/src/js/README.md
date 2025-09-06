# Frontend JavaScript Modules

This directory contains the core JavaScript functionality for the AI-First Software Engineering Maturity Assessment Framework.

## Architecture

The frontend is built using a modular ES6 class-based architecture with the following components:

### Core Modules

#### 1. Utils Module (`modules/utils.js`)
Common utilities and helper functions used across the application.

**Features:**
- Date/time formatting and relative time calculations
- Number and text formatting utilities
- Function utilities (debounce, throttle)
- UI helpers (toasts, alerts, confirmations)
- Form utilities (auto-save, validation, restore)
- Clipboard and file utilities
- Assessment-specific helpers
- Bootstrap component integration
- Local storage management
- Performance measurement tools

#### 2. Charts Module (`modules/charts.js`)
Comprehensive chart management using Chart.js for data visualization.

**Features:**
- Chart creation and lifecycle management
- Support for multiple chart types (line, bar, pie, doughnut, radar, scatter)
- Real-time data updates and auto-refresh
- Chart interaction (toggle types, export, configuration)
- Responsive design and window resize handling
- Loading states and error handling
- Pre-built chart types for DevIQ trends and maturity analysis

#### 3. Assessment Module (`modules/assessment.js`)
Assessment form interaction, validation, and submission management.

**Features:**
- Form validation with real-time feedback
- Auto-save functionality (every 30 seconds)
- Progress tracking and navigation
- Keyboard navigation (arrow keys, Ctrl+S)
- Response management and submission
- Unsaved changes warnings
- Assessment completion prompts
- Section-based navigation

#### 4. Dashboard Module (`modules/dashboard.js`)
Dashboard functionality with real-time updates and widget management.

**Features:**
- Widget lifecycle management
- Real-time data refresh (every 5 minutes)
- Chart rendering and integration
- Data filtering and sorting
- Export functionality
- Activity feed management
- Responsive layout handling
- Loading states and error recovery

#### 5. Comparison Module (`modules/comparison.js`)
Advanced assessment comparison functionality with visualization.

**Features:**
- Multi-assessment selection (up to 4 assessments)
- Side-by-side comparison interface
- Interactive charts (DevIQ trends, section radar)
- Statistical analysis and insights generation
- Export comparison results (PDF, Excel)
- Assessment ranking and benchmarking
- Keyboard shortcuts (Ctrl+A, Ctrl+C, Escape)
- Persistent selection storage
- Quick comparison from assessment cards

#### 6. Export Module (`modules/export.js`)
Comprehensive data export functionality for multiple formats.

**Features:**
- Multi-format support (PDF, Excel, CSV, JSON)
- Bulk export operations
- Progress tracking and monitoring
- Async export job handling
- Export history management
- File size validation and warnings
- Export cancellation support
- Download queue management
- Format-specific options and configuration
- Keyboard shortcuts (Ctrl+E, Ctrl+S)

#### 7. Search Module (`modules/search.js`)
Advanced search and filtering system with real-time results.

**Features:**
- Global search with autocomplete
- Real-time search suggestions
- Advanced filtering and faceted search
- Multiple sorting options
- Search result highlighting
- Search history and saved searches
- Context-aware search (assessments, questions, recommendations)
- Keyboard navigation (Ctrl+K, arrow keys, Enter, Escape)
- Search analytics and result tracking
- Advanced search modal with date ranges

#### 8. Main Application (`main.js`)
Application initialization, configuration, and global coordination.

**Features:**
- Module initialization and coordination
- Configuration management from server and meta tags
- Global event handling (AJAX, navigation, keyboard shortcuts)
- Error handling and reporting
- Page-specific initialization
- Network status monitoring
- Auto-save coordination
- Development tools and debugging

## Build System

### Building Assets

```bash
# Build all assets
npm run build

# Build JavaScript only
npm run build:js

# Clean dist directory
npm run clean
```

### Build Output

The build process creates:
- `dist/js/app.js` - Concatenated source files
- `dist/js/app.min.js` - Minified production bundle
- `dist/js/app.min.js.map` - Source map for debugging
- `dist/js/modules/` - Individual module files

### Build Statistics

The current build produces:
- **Original size:** ~108 KB
- **Minified size:** ~67 KB
- **Size reduction:** 38.2%

## Usage

### Development

Include individual modules for development:

```html
<!-- Core utilities (required first) -->
<script src="/static/src/js/modules/utils.js"></script>

<!-- Chart functionality (requires Chart.js) -->
<script src="/static/src/js/modules/charts.js"></script>

<!-- Assessment functionality -->
<script src="/static/src/js/modules/assessment.js"></script>

<!-- Dashboard functionality -->
<script src="/static/src/js/modules/dashboard.js"></script>

<!-- Main application -->
<script src="/static/src/js/main.js"></script>
```

### Production

Use the minified bundle:

```html
<script src="/static/dist/js/app.min.js"></script>
```

## Global Objects

The application exposes these global objects:

- `window.app` - Main application instance
- `window.utils` - Utility functions
- `window.chartManager` - Chart management (if Chart.js loaded)

## Configuration

Configuration can be provided via:

1. **Meta tags:**
```html
<meta name="app-debug" content="true">
<meta name="app-api-timeout" content="30000">
```

2. **Server endpoint:** `GET /api/config`

3. **Default values** in the application

## Page Types

The application automatically detects page types and initializes appropriate functionality:

- `page-assessment` - Assessment forms
- `page-dashboard` - Dashboard and analytics
- `page-admin` - Administrative functions

## Event System

The application uses a custom event system for module communication:

```javascript
// Listen for events
app.addEventListener('app:ready', (e) => {
    console.log('Application ready');
});

// Dispatch events
app.dispatchEvent('custom:event', { data: 'value' });
```

## Error Handling

Comprehensive error handling includes:
- Global error capture
- AJAX error handling
- Promise rejection handling
- Local error storage
- Optional error reporting

## Development Tools

In development mode (localhost), additional tools are available:

```javascript
// Access application instance
app.getConfig()

// Access modules
app.getModule('assessment')

// Utility functions
utils.showToast('Hello', 'success')
```

## Dependencies

- **Bootstrap 5** - UI framework
- **Chart.js** - Data visualization (optional)
- **Modern Browser** - ES6 support required

## Browser Support

- Chrome/Edge 80+
- Firefox 75+
- Safari 13+

## Performance

The application includes several performance optimizations:

- Debounced event handlers
- Throttled scroll/resize handlers
- Auto-pause when page hidden
- Efficient DOM manipulation
- Minimal re-renders

## Security

Security features include:

- CSRF token handling
- HTML sanitization
- Input validation
- XSS prevention
- Secure clipboard operations
