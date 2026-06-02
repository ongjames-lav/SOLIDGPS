# Theme definitions for Streamlit

CSS_INJECTION = """
<style>
/* 1. DESIGN TOKENS & VARIABLES */
:root {
    /* Color Palette */
    --primary-color: #2563EB; /* Blue-600 */
    --primary-hover: #1D4ED8; /* Blue-700 */
    --background-base: #F8FAFC; /* Slate-50 */
    --surface-color: #FFFFFF;
    --text-main: #0F172A; /* Slate-900 */
    --text-muted: #64748B; /* Slate-500 */
    --border-color: #E2E8F0; /* Slate-200 */
    --success-color: #10B981;
    --warning-color: #F59E0B;
    --error-color: #EF4444;

    /* Spacing Scale (8px base) */
    --space-1: 0.5rem;   /* 8px */
    --space-2: 1rem;     /* 16px */
    --space-3: 1.5rem;   /* 24px */
    --space-4: 2rem;     /* 32px */

    /* Typography */
    --font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

    /* Borders & Shadows */
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);

    /* Motion */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* 2. GLOBAL STYLES & OVERRIDES */
html, body, [class*="css"] {
    font-family: var(--font-family);
    color: var(--text-main);
}

.stApp {
    background-color: var(--background-base);
}

/* 3. TYPOGRAPHY HIERARCHY */
h1 {
    font-size: clamp(2rem, 5vw, 3rem) !important;
    font-weight: 800 !important;
    letter-spacing: -0.025em !important;
    color: var(--text-main) !important;
    margin-bottom: var(--space-1) !important;
}

h2 {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    margin-top: var(--space-4) !important;
    margin-bottom: var(--space-2) !important;
}

h3 {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
}

/* 4. COMPONENT STYLING */
/* Dashboard Cards (Metrics) */
div[data-testid="stMetric"] {
    background: var(--surface-color);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: var(--space-3);
    box-shadow: var(--shadow-sm);
    transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}

div[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

div[data-testid="stMetricValue"] {
    font-size: 2.25rem !important;
    font-weight: 700 !important;
    color: var(--primary-color) !important;
}

/* Buttons */
.stButton > button {
    background-color: var(--primary-color) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    padding: var(--space-1) var(--space-3) !important;
    font-weight: 600 !important;
    transition: all var(--transition-fast) !important;
    width: 100%;
}

.stButton > button:hover {
    background-color: var(--primary-hover) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Expanders (Detailed Profiles) */
div[data-testid="stExpander"] {
    background: var(--surface-color);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-2);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

div[data-testid="stExpander"] > summary {
    padding: var(--space-2) var(--space-3);
    font-weight: 600;
    font-size: 1.1rem;
    transition: background-color var(--transition-fast);
}

div[data-testid="stExpander"] > summary:hover {
    background-color: var(--background-base);
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: var(--surface-color);
    border-right: 1px solid var(--border-color);
}

/* 5. RESPONSIVE DESIGN (BREAKPOINTS) */
/* Streamlit handles much of this, but we force layout adjustments for very small screens */
@media (max-width: 768px) {
    div[data-testid="stMetric"] {
        padding: var(--space-2);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
    }
}
</style>
"""
