import os, winreg, requests
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment') as reg:
    try:
        v, _ = winreg.QueryValueEx(reg, 'GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = v
    except FileNotFoundError:
        pass
key = os.environ.get('GEMINI_API_KEY', '')
r = requests.get(f'https://generativelanguage.googleapis.com/v1beta/models?key={key}',
    timeout=15)
print('status', r.status_code)
if r.status_code == 200:
    data = r.json()
    for m in data.get('models', []):
        name = m.get('name', '')
        methods = m.get('supportedGenerationMethods', [])
        if 'generateContent' in methods:
            print(f"  {name:50s}  {','.join(methods)}")
