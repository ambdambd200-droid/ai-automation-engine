import os, requests, winreg
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment') as reg:
    try:
        v, _ = winreg.QueryValueEx(reg, 'CEREBRAS_API_KEY')
        os.environ['CEREBRAS_API_KEY'] = v
    except FileNotFoundError:
        pass
key = os.environ.get('CEREBRAS_API_KEY', '')

models = ['gpt-oss-120b', 'zai-glm-4.7', 'gemma-4-31b', 'gpt-oss-20b', 'llama3.1-8b', 'llama-3.3-70b', 'llama-3.3-70b-instruct']
for m in models:
    r = requests.post('https://api.cerebras.ai/v1/chat/completions',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={
            'model': m,
            'messages': [{'role':'user','content':'Say hi'}],
            'max_tokens': 20,
        }, timeout=20)
    print(f'{m:30s}  {r.status_code}  {r.text[:120]}')
