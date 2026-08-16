import os
import shutil
import subprocess
from pathlib import Path

print("🧹 LIMPANDO SSD...")

# 1. TEMPORÁRIOS
print("  Removendo temporários...")
temp_dirs = [
    os.environ.get('TEMP', ''),
    os.environ.get('TMP', ''),
    'C:\\Windows\\Temp'
]
for pasta in temp_dirs:
    if os.path.exists(pasta):
        for item in Path(pasta).glob('*'):
            try:
                if item.is_file(): item.unlink()
                else: shutil.rmtree(item)
            except: pass

# 2. LIXEIRA
print("  Esvaziando lixeira...")
try:
    subprocess.run('rd /s /q C:\\$Recycle.bin', shell=True)
except:
    try:
        subprocess.run('powershell -command "Clear-RecycleBin -Force"', shell=True)
    except: pass

# 3. PREFETCH
print("  Limpando Prefetch...")
prefetch = 'C:\\Windows\\Prefetch'
if os.path.exists(prefetch):
    for item in Path(prefetch).glob('*'):
        try: item.unlink()
        except: pass

# 4. DOWNLOADS ANTIGOS (>30 dias)
print("  Removendo downloads antigos...")
downloads = Path(os.path.expanduser("~/Downloads"))
if downloads.exists():
    from datetime import datetime, timedelta
    limite = datetime.now() - timedelta(days=30)
    for item in downloads.glob('*'):
        if item.is_file():
            data = datetime.fromtimestamp(item.stat().st_mtime)
            if data < limite:
                try: item.unlink()
                except: pass

# 5. CACHE DO PIP
print("  Limpando cache do pip...")
venv_pip = Path('.venv') / ('Scripts' if os.name == 'nt' else 'bin') / ('pip.exe' if os.name == 'nt' else 'pip')
if venv_pip.exists():
    subprocess.run(f'"{venv_pip}" cache purge', shell=True)

# 6. REMOVE PACOTES FORA DO REQUIREMENTS.TXT
print("  Removendo pacotes não usados...")
req_file = Path('requirements.txt')
if req_file.exists():
    with open(req_file) as f:
        reqs = [linha.strip().split('=')[0].lower() for linha in f if linha.strip() and not linha.startswith('#')]
    
    if venv_pip.exists():
        import json
        result = subprocess.run(f'"{venv_pip}" list --format=json', shell=True, capture_output=True, text=True)
        if result.stdout:
            pacotes = json.loads(result.stdout)
            protegidos = ['pip', 'setuptools', 'wheel', 'virtualenv']
            for p in pacotes:
                nome = p['name'].lower()
                if nome not in reqs and nome not in protegidos:
                    print(f"    Removendo: {p['name']}")
                    subprocess.run(f'"{venv_pip}" uninstall {p["name"]} -y', shell=True)

print("✅ LIMPEZA CONCLUÍDA!")