#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script fixes the CSS block in app_fresh.py

with open('app_fresh.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the problematic CSS block
# The issue is that st.markdown(""" ... """) without f-string
# causes Python to try to parse the CSS as code

# Find the start of the CSS block
start_marker = '    # Static CSS (no variables, no f-string needed)\n    st.markdown("""'
end_marker = '    """, unsafe_allow_html=True)\n    \n    # Dynamic CSS'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    # Extract the CSS content
    css_block_start = start_idx + len(start_marker)
    css_content = content[css_block_start:end_idx]
    
    # Create new version using variable assignment
    new_block = '''    # Static CSS (no variables, no f-string needed)
    css_static = """'''
    new_block += css_content
    new_block += '    """'
    new_block += '\n    st.markdown(css_static, unsafe_allow_html=True)\n    \n    # Dynamic CSS'
    
    # Replace
    new_content = content[:start_idx] + new_block + content[end_idx + len(end_marker):]
    
    # Write to app.py
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully fixed app.py")
    print(f"Changed {len(content)} bytes to {len(new_content)} bytes")
else:
    print("❌ Could not find CSS block markers")
    print(f"Start found: {start_idx != -1}, End found: {end_idx != -1}")
