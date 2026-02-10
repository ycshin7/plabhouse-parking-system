
# Fix app.py by rewriting the CSS block with single quotes
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the block
start_marker = 'css_template = """'
end_marker = 'st.markdown(css_template.format('

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1:
    # We will replace the whole block with a simpler version
    # using single quotes and ensuring no weird characters
    
    new_block = "    # Inject CSS\n    css_template = '''\n"
    new_block += "    <style>\n"
    new_block += "    .stButton > button[kind=\"secondary\"] {{\n"
    new_block += "        background-color: white;\n"
    new_block += "        border: 2px solid transparent;\n"
    new_block += "        border-radius: 24px;\n"
    new_block += "        height: 180px !important;\n"
    new_block += "        white-space: pre;\n"
    new_block += "        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);\n"
    new_block += "        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);\n"
    new_block += "        display: flex;\n"
    new_block += "        flex-direction: column;\n"
    new_block += "        justify-content: center;\n"
    new_block += "        align-items: center;\n"
    new_block += "        text-align: center;\n"
    new_block += "        padding: 0 10px;\n"
    new_block += "    }}\n"
    new_block += "    .stButton > button[kind=\"secondary\"]:hover {{\n"
    new_block += "        transform: translateY(-4px);\n"
    new_block += "        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);\n"
    new_block += "        border-color: var(--toss-blue);\n"
    new_block += "        background-color: white;\n"
    new_block += "        color: inherit;\n"
    new_block += "    }}\n"
    new_block += "    .stButton > button[kind=\"secondary\"] p::first-line {{\n"
    new_block += "        font-size: 22px;\n"
    new_block += "        font-weight: 800;\n"
    new_block += "        line-height: 2.0;\n"
    new_block += "    }}\n"
    new_block += "    .stButton > button[kind=\"secondary\"] p {{\n"
    new_block += "        font-size: 16px;\n"
    new_block += "        font-weight: 400;\n"
    new_block += "        color: #191f28;\n"
    new_block += "        line-height: 1.4;\n"
    new_block += "        display: block;\n"
    new_block += "        width: 100%;\n"
    new_block += "        margin: 0;\n"
    new_block += "    }}\n"
    new_block += "    div[data-testid=\"stMetric\"] {{ text-align: center; justify-content: center; }}\n"
    new_block += "    div[data-testid=\"stMetricLabel\"] {{ justify-content: center; }}\n"
    new_block += "    div[data-testid=\"stMetricValue\"] {{ justify-content: center; }}\n"
    new_block += "    div[data-testid=\"column\"]:nth-of-type(1) .stButton > button[kind=\"secondary\"] {{ background-color: {staff_bg} !important; color: {staff_text} !important; border-color: {staff_border} !important; }}\n"
    new_block += "    div[data-testid=\"column\"]:nth-of-type(2) .stButton > button[kind=\"secondary\"] {{ background-color: {guest_bg} !important; color: {guest_text} !important; border-color: {guest_border} !important; }}\n"
    new_block += "    div[data-testid=\"column\"]:nth-of-type(3) .stButton > button[kind=\"secondary\"] {{ background-color: {sante_bg} !important; color: {sante_text} !important; border-color: {sante_border} !important; }}\n"
    new_block += "    div[data-testid=\"column\"]:nth-of-type(1) .stButton > button[kind=\"secondary\"]:hover {{ background-color: {staff_bg} !important; color: {staff_text} !important; opacity: 0.9; }}\n"
    new_block += "    div[data-testid=\"column\"]:nth-of-type(2) .stButton > button[kind=\"secondary\"]:hover {{ background-color: {guest_bg} !important; color: {guest_text} !important; opacity: 0.9; }}\n"
    new_block += "    div[data-testid=\"column\"]:nth-of-type(3) .stButton > button[kind=\"secondary\"]:hover {{ background-color: {sante_bg} !important; color: {sante_text} !important; opacity: 0.9; }}\n"
    new_block += "    </style>\n"
    new_block += "    '''\n\n"
    
    new_content = content[:start_idx] + new_block + content[end_idx:]
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Rewrote app.py with single quotes")
else:
    print("❌ Marker not found")
