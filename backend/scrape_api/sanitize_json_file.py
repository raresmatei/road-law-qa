import json
import re

# Read the original file
with open('../../output/36362.json', 'r', encoding='utf-8') as f:
    raw = f.read()

# Function to escape newlines and quotes in the text fields
def escape_text_fields(match):
    text_content = match.group(1)
    # Escape backslashes first
    text_content = text_content.replace('\\', '\\\\')
    # Escape quotes
    text_content = text_content.replace('"', '\\"')
    # Replace literal newlines with \n
    text_content = text_content.replace('\n', '\\n')
    return f'"text":"{text_content}"'

# Sanitize the raw string by escaping inside "text": "..."
sanitized = re.sub(
    r'"text":\s*"([^"]*?)"',
    escape_text_fields,
    raw,
    flags=re.DOTALL
)

# Parse and re-dump as pretty JSON
data = json.loads(sanitized)
with open('legislation_clean.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Preview the first object
print(json.dumps(data[0], ensure_ascii=False, indent=2))