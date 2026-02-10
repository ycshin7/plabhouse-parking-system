import re

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all emojis
emoji_pattern = re.compile("["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    u"\U00002702-\U000027B0"
    u"\U000024C2-\U0001F251"
    "]+", flags=re.UNICODE)

content = emoji_pattern.sub('', content)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Emojis removed successfully!")
