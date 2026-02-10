
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

count_double = content.count('"""')
count_single = content.count("'''")

print(f'Triple double quotes: {count_double}')
print(f'Triple single quotes: {count_single}')

print('\nDouble positions:')
for m in re.finditer('"""', content):
    line = content[:m.start()].count('\n') + 1
    print(f'Line {line}')

print('\nSingle positions:')
for m in re.finditer("'''", content):
    line = content[:m.start()].count('\n') + 1
    print(f'Line {line}')
