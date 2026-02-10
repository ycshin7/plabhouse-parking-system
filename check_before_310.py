with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check for unclosed strings or parentheses in first 310 lines
content_before = ''.join(lines[:310])

# Count triple quotes
triple_double = content_before.count('"""')
triple_single = content_before.count("'''")

print(f'Triple double quotes before line 310: {triple_double}')
print(f'Triple single quotes before line 310: {triple_single}')

if triple_double % 2 != 0:
    print('❌ ODD number of triple double quotes!')
if triple_single % 2 != 0:
    print('❌ ODD number of triple single quotes!')
