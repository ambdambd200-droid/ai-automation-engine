"""Add desktop MCP server to opencode config."""
import json

path = r'C:\Users\A\.config\opencode\opencode.jsonc'

with open(path, encoding='utf-8') as f:
    content = f.read()

data = json.loads(content)

data['mcp']['desktop'] = {
    'type': 'local',
    'command': [
        r'C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe',
        r'C:\Users\A\Desktop\Money\desktop_mcp_server.py',
    ],
    'enabled': True,
}

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')

print(f'Done. Desktop MCP server added to: {path}')
