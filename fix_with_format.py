# This script will fix the app.py file by rewriting the CSS section to use .format()
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the start of the CSS block
start_marker = "# Inject CSS for Card Buttons"
end_marker = "# Create 3 columns"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    # Construct the new CSS block using .format()
    # Note: In .format(), we still need {{ }} for literal braces, just like f-strings.
    # But it avoids f-string parser bugs/quirks.
    
    new_block = '''# Inject CSS for Card Buttons (Secondary Buttons on Main Page)
    css_template = """
    <style>
    /* Target ALL Secondary Buttons on Main Page (The 3 Cards) */
    .stButton > button[kind="secondary"] {{
        background-color: white;
        border: 2px solid transparent;
        border-radius: 24px;
        height: 180px !important;
        white-space: pre; /* Force no wrapping for the title */
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 0 10px;
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        border-color: var(--toss-blue);
        background-color: white;
        color: inherit;
    }}
    
    /* First Line Styling (Title) - Larger and Bolder */
    .stButton > button[kind="secondary"] p::first-line {{
        font-size: 22px;
        font-weight: 800;
        line-height: 2.0;
    }}
    
    /* Reset font size for subsequent lines (Description) */
    .stButton > button[kind="secondary"] p {{
        font-size: 16px;
        font-weight: 400;
        color: #191f28;
        line-height: 1.4;
        display: block;
        width: 100%;
        margin: 0;
    }}
    
    /* Center Align Metrics */
    div[data-testid="stMetric"] {{
        text-align: center;
        justify-content: center;
    }}
    
    div[data-testid="stMetricLabel"] {{
        justify-content: center;
    }}
    
    div[data-testid="stMetricValue"] {{
        justify-content: center;
    }}
    
    /* Column-specific overrides for Colors */
    div[data-testid="column"]:nth-of-type(1) .stButton > button[kind="secondary"] {{
        background-color: {staff_bg} !important;
        color: {staff_text} !important;
        border-color: {staff_border} !important;
    }}
    
    div[data-testid="column"]:nth-of-type(2) .stButton > button[kind="secondary"] {{
        background-color: {guest_bg} !important;
        color: {guest_text} !important;
        border-color: {guest_border} !important;
    }}
    
    div[data-testid="column"]:nth-of-type(3) .stButton > button[kind="secondary"] {{
        background-color: {sante_bg} !important;
        color: {sante_text} !important;
        border-color: {sante_border} !important;
    }}
    
    /* Hover overrides */
    div[data-testid="column"]:nth-of-type(1) .stButton > button[kind="secondary"]:hover {{
        background-color: {staff_bg} !important;
        color: {staff_text} !important;
        opacity: 0.9;
    }}
    div[data-testid="column"]:nth-of-type(2) .stButton > button[kind="secondary"]:hover {{
        background-color: {guest_bg} !important;
        color: {guest_text} !important;
        opacity: 0.9;
    }}
    div[data-testid="column"]:nth-of-type(3) .stButton > button[kind="secondary"]:hover {{
        background-color: {sante_bg} !important;
        color: {sante_text} !important;
        opacity: 0.9;
    }}
    </style>
    """
    
    st.markdown(css_template.format(
        staff_bg=staff_bg, staff_text=staff_text, staff_border=staff_border,
        guest_bg=guest_bg, guest_text=guest_text, guest_border=guest_border,
        sante_bg=sante_bg, sante_text=sante_text, sante_border=sante_border
    ), unsafe_allow_html=True)
    
'''
    
    new_content = content[:start_idx] + new_block + content[end_idx:]
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("✅ Rewrote app.py with .format()")

else:
    print("❌ Could not find markers")
