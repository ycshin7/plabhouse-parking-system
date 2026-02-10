import sys

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where the CSS block starts (around "# Static CSS")
start_marker = "    # Static CSS"
end_marker = "    # Create 3 columns"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Could not find markers")
    sys.exit(1)

# Create new CSS block (simple, no f-string)
new_css = '''    # Static CSS
    st.markdown("""
    <style>
    .stButton > button[kind="secondary"] {
        background-color: white;
        border: 2px solid transparent;
        border-radius: 24px;
        height: 180px !important;
        white-space: pre;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 0 10px;
    }
    
    .stButton > button[kind="secondary"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        border-color: var(--toss-blue);
        background-color: white;
        color: inherit;
    }
    
    .stButton > button[kind="secondary"] p::first-line {
        font-size: 22px;
        font-weight: 800;
        line-height: 2.0;
    }
    
    .stButton > button[kind="secondary"] p {
        font-size: 13px !important;
        font-weight: 400 !important;
        color: #191f28 !important;
        line-height: 1.4 !important;
        display: block !important;
        width: 100% !important;
        margin: 0 !important;
    }
    
    div[data-testid="stMetric"] {
        text-align: center;
        justify-content: center;
    }
    
    div[data-testid="stMetricLabel"] {
        justify-content: center;
    }
    
    div[data-testid="stMetricValue"] {
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Dynamic CSS
    st.markdown(f"""
    <style>
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
    """, unsafe_allow_html=True)
    
'''

# Replace the section
new_content = content[:start_idx] + new_css + content[end_idx:]

# Write to new file
with open('app_fixed_final.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Created app_fixed_final.py")
print(f"Original size: {len(content)} bytes")
print(f"New size: {len(new_content)} bytes")
