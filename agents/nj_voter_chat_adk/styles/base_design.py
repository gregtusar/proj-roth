"""
Uber Base Design System implementation for Streamlit
Based on Base Web: https://baseweb.design/
"""

def get_base_css():
    """Returns CSS implementing Uber's Base design system"""
    return """
    <style>
    /* Import Uber Move font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Base Design System Color Palette */
    :root {
        /* Primary Colors */
        --uber-black: #000000;
        --uber-white: #FFFFFF;
        --uber-green: #276EF1;  /* Primary blue from Base */
        --wolf-blue: #3B5D7C;  /* Blue from wolf icon background */
        
        /* Grayscale */
        --gray-50: #F6F6F6;
        --gray-100: #EEEEEE;
        --gray-200: #E2E2E2;
        --gray-300: #CBCBCB;
        --gray-400: #AFAFAF;
        --gray-500: #757575;
        --gray-600: #545454;
        --gray-700: #333333;
        --gray-800: #1F1F1F;
        --gray-900: #141414;
        
        /* Semantic Colors */
        --primary: #276EF1;
        --primary-hover: #1E5FD8;
        --secondary: #F3F3F3;
        --success: #03703C;
        --warning: #FFC043;
        --error: #D44333;
        --info: #276EF1;
        
        /* Spacing */
        --spacing-xs: 4px;
        --spacing-sm: 8px;
        --spacing-md: 16px;
        --spacing-lg: 24px;
        --spacing-xl: 32px;
        --spacing-xxl: 48px;
        
        /* Border Radius */
        --radius-sm: 4px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-full: 9999px;
        
        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main app container */
    .stApp {
        background-color: var(--gray-50);
    }
    
    /* Headers with Uber style */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        color: var(--wolf-blue);
        letter-spacing: -0.02em;
    }
    
    h1 {
        font-size: 36px;
        line-height: 44px;
        font-weight: 700;
        color: var(--wolf-blue);
    }
    
    h2 {
        font-size: 28px;
        line-height: 36px;
        color: var(--wolf-blue);
    }
    
    h3 {
        font-size: 24px;
        line-height: 32px;
        color: var(--wolf-blue);
    }
    
    /* Streamlit specific overrides */
    .stButton > button {
        background-color: var(--uber-black);
        color: var(--uber-white);
        border: none;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        border-radius: var(--radius-md);
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
        width: 100%;
        margin-top: var(--spacing-sm);
    }
    
    .stButton > button:hover {
        background-color: var(--gray-800);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Primary button style */
    .primary-button > button {
        background-color: var(--primary);
        color: var(--uber-white);
    }
    
    .primary-button > button:hover {
        background-color: var(--primary-hover);
    }
    
    /* Text input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--uber-white);
        border: 2px solid var(--gray-200);
        border-radius: var(--radius-md);
        padding: 12px 16px;
        font-size: 16px;
        transition: all 0.2s ease;
        color: var(--gray-900);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(39, 110, 241, 0.1);
        outline: none;
    }
    
    /* Labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        color: var(--gray-700);
        font-size: 14px;
        font-weight: 500;
        margin-bottom: var(--spacing-xs);
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: var(--uber-white);
        border-radius: var(--radius-lg);
        padding: var(--spacing-md);
        margin-bottom: var(--spacing-md);
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--gray-100);
    }
    
    /* User messages */
    .stChatMessage[data-testid="user-message"] {
        background-color: var(--gray-50);
        border-left: 4px solid var(--primary);
    }
    
    /* Assistant messages */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: var(--uber-white);
        border-left: 4px solid var(--gray-300);
    }
    
    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: var(--uber-white);
        border-right: 1px solid var(--gray-200);
    }
    
    .css-1d391kg .stButton > button,
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent;
        color: var(--gray-700);
        border: 1px solid var(--gray-200);
        font-weight: 400;
    }
    
    .css-1d391kg .stButton > button:hover,
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: var(--gray-50);
        border-color: var(--gray-300);
    }
    
    /* Cards and containers */
    .stContainer {
        background-color: var(--uber-white);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--gray-100);
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background-color: var(--uber-white);
        border: 1px solid var(--gray-200);
        padding: var(--spacing-md);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: var(--gray-600);
        font-size: 14px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: var(--gray-900);
        font-size: 32px;
        font-weight: 600;
    }
    
    /* Success/Error/Warning messages */
    .stSuccess {
        background-color: #E6F4EA;
        color: var(--success);
        border-left: 4px solid var(--success);
        border-radius: var(--radius-md);
        padding: var(--spacing-md);
    }
    
    .stError {
        background-color: #FCE8E6;
        color: var(--error);
        border-left: 4px solid var(--error);
        border-radius: var(--radius-md);
        padding: var(--spacing-md);
    }
    
    .stWarning {
        background-color: #FEF7E0;
        color: #7A4510;
        border-left: 4px solid var(--warning);
        border-radius: var(--radius-md);
        padding: var(--spacing-md);
    }
    
    .stInfo {
        background-color: #E8F0FE;
        color: #1A73E8;
        border-left: 4px solid var(--info);
        border-radius: var(--radius-md);
        padding: var(--spacing-md);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--gray-50);
        border: 1px solid var(--gray-200);
        border-radius: var(--radius-md);
        font-weight: 500;
        color: var(--gray-900);
    }
    
    .streamlit-expanderHeader:hover {
        background-color: var(--gray-100);
    }
    
    /* Tables */
    .stDataFrame {
        border: 1px solid var(--gray-200);
        border-radius: var(--radius-md);
        overflow: hidden;
    }
    
    .stDataFrame thead tr th {
        background-color: var(--gray-50);
        color: var(--gray-700);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.05em;
        padding: var(--spacing-md);
    }
    
    .stDataFrame tbody tr {
        border-bottom: 1px solid var(--gray-100);
    }
    
    .stDataFrame tbody tr:hover {
        background-color: var(--gray-50);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: var(--primary);
        border-radius: var(--radius-full);
    }
    
    .stProgress {
        background-color: var(--gray-200);
        border-radius: var(--radius-full);
        height: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid var(--gray-200);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--gray-600);
        font-weight: 500;
        padding: var(--spacing-sm) var(--spacing-md);
        background-color: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        margin-bottom: -2px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--gray-900);
        background-color: var(--gray-50);
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--primary);
        border-bottom-color: var(--primary);
    }
    
    /* Code blocks */
    .stCodeBlock {
        background-color: var(--gray-900);
        border-radius: var(--radius-md);
        padding: var(--spacing-md);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--primary);
    }
    
    /* Custom utility classes */
    .uber-card {
        background: var(--uber-white);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--gray-100);
        margin-bottom: var(--spacing-lg);
    }
    
    .uber-title {
        font-size: 32px;
        font-weight: 700;
        color: var(--gray-900);
        margin-bottom: var(--spacing-md);
        letter-spacing: -0.02em;
    }
    
    .uber-subtitle {
        font-size: 18px;
        color: var(--gray-600);
        margin-bottom: var(--spacing-lg);
    }
    
    /* Animations */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-slide-in {
        animation: slideIn 0.3s ease-out;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        h1 {
            font-size: 28px;
            line-height: 36px;
        }
        
        h2 {
            font-size: 24px;
            line-height: 32px;
        }
        
        .uber-card {
            padding: var(--spacing-md);
        }
    }
    </style>
    """

def apply_base_design():
    """Apply Base design system to the current Streamlit app"""
    import streamlit as st
    st.markdown(get_base_css(), unsafe_allow_html=True)

def create_uber_card(title, content, subtitle=None):
    """Create an Uber-style card component"""
    import streamlit as st
    
    card_html = f"""
    <div class="uber-card animate-slide-in">
        <div class="uber-title">{title}</div>
        {f'<div class="uber-subtitle">{subtitle}</div>' if subtitle else ''}
        <div>{content}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def create_metric_card(label, value, delta=None, delta_color="normal"):
    """Create an Uber-style metric card"""
    import streamlit as st
    
    delta_html = ""
    if delta:
        color = {
            "normal": "var(--gray-600)",
            "positive": "var(--success)",
            "negative": "var(--error)"
        }.get(delta_color, "var(--gray-600)")
        
        delta_html = f'<div style="color: {color}; font-size: 14px; margin-top: 4px;">{delta}</div>'
    
    card_html = f"""
    <div class="uber-card" style="padding: var(--spacing-md);">
        <div style="color: var(--gray-600); font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">
            {label}
        </div>
        <div style="color: var(--gray-900); font-size: 32px; font-weight: 600; margin-top: 8px;">
            {value}
        </div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)