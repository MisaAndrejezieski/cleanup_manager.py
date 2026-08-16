#!/usr/bin/env python3
"""
Cleanup Manager - Limpeza Automatizada
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

# ============================================
# VERIFICA .VENV
# ============================================

in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

if not in_venv:
    print("❌ Ative o .venv:")
    print("   .venv\\Scripts\\activate")
    print("   python cleanup_manager.py")
    sys.exit(1)

# ============================================
# INSTALA DEPENDÊNCIAS
# ============================================

def instalar_dependencias():
    dependencias = ['customtkinter', 'pillow']
    faltando = []
    
    for dep in dependencias:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            faltando.append(dep)
    
    if faltando:
        print(f"📦 Instalando: {', '.join(faltando)}...")
        for dep in faltando:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
        print("✅ Dependências instaladas!")

instalar_dependencias()

# ============================================
# IMPORTA
# ============================================

from tkinter import messagebox, scrolledtext

import customtkinter as ctk

# ============================================
# CORES
# ============================================

CORES = {
    'bg_principal': '#0a0e1a',
    'bg_secundario': '#141b2d',
    'bg_terciario': '#1a2438',
    'texto_principal': '#e0e6ff',
    'texto_secundario': '#8899cc',
    'neon_azul': '#00d4ff',
    'neon_roxo': '#b06aff',
    'neon_rosa': '#ff6bcb',
    'neon_verde': '#00ff88',
    'neon_amarelo': '#ffe066',
    'neon_vermelho': '#ff4757',
    'sucesso': '#00ff88',
    'erro': '#ff4757',
    'aviso': '#ffa502',
    'info': '#00d4ff',
}

# ============================================
# CLASSE PRINCIPAL
# ============================================

class CleanupManagerGUI:
    def __init__(self):
        self.is_windows = platform.system() == 'Windows'
        self.is_admin = self._verificar_admin()
        self.diretorio_projeto = os.path.dirname(os.path.abspath(__file__))
        self.venv_local = os.path.join(self.diretorio_projeto, '.venv')
        self.config_file = os.path.join(self.diretorio_projeto, 'cleanup_config.json')
        self.config = self._carregar_config()
        self.espaco_liberado = 0
        self.limpando = False
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.criar_interface()
    
    def _verificar_admin(self):
        if self.is_windows:
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        return os.geteuid() == 0
    
    def _carregar_config(self):
        padrao = {
            'remover_arquivos_temp': True,
            'esvaziar_lixeira': True,
            'limpar_prefetch': True,
            'limpar_cache_pip': True,
            'remover_pacotes_nao_usados': True,
            'limpar_downloads': True,
            'dias_para_limpar': 30,
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    for k, v in padrao.items():
                        if k not in config:
                            config[k] = v
                    return config
            except:
                return padrao
        else:
            with open(self.config_file, 'w') as f:
                json.dump(padrao, f, indent=2)
            return padrao
    
    def log(self, msg, tipo="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emojis = {"SUCESSO": "✓", "ERRO": "✗", "AVISO": "⚠", "INFO": "•", "LIMPEZA": "◆"}
        
        log_msg = f"[{timestamp}] {emojis.get(tipo, '')} {msg}\n"
        
        if hasattr(self, 'log_text'):
            self.log_text.insert("end", log_msg, (tipo,))
            self.log_text.see("end")
            self.janela.update()
        
        with open("cleanup_log.txt", 'a') as f:
            f.write(f"[{datetime.now()}] [{tipo}] {msg}\n")
    
    def _obter_tamanho(self, pasta):
        if not os.path.exists(pasta):
            return 0
        total = 0
        try:
            for root, dirs, files in os.walk(pasta):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
            return round(total / (1024 * 1024), 2)
        except:
            return 0
    
    def limpar_temp(self):
        if not self.is_windows:
            return 0
        self.log("Limpando temporários...", "INFO")
        total = 0
        locais = []
        if os.environ.get('TEMP'):
            locais.append(os.environ['TEMP'])
        if os.path.exists("C:\\Windows\\Temp"):
            locais.append("C:\\Windows\\Temp")
        
        for local in locais:
            antes = self._obter_tamanho(local)
            for item in Path(local).glob('*'):
                try:
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item, ignore_errors=True)
                except:
                    pass
            depois = self._obter_tamanho(local)
            total += antes - depois
        self.log(f"Liberado: {total:.1f} MB", "SUCESSO")
        self.espaco_liberado += total
        return total
    
    def limpar_cache(self):
        if not self.is_windows:
            return 0
        self.log("Limpando caches...", "INFO")
        total = 0
        if os.path.exists("C:\\Windows\\Prefetch"):
            antes = self._obter_tamanho("C:\\Windows\\Prefetch")
            for item in Path("C:\\Windows\\Prefetch").glob('*'):
                try:
                    if item.is_file():
                        item.unlink()
                except:
                    pass
            depois = self._obter_tamanho("C:\\Windows\\Prefetch")
            total += antes - depois
        self.log(f"Liberado: {total:.1f} MB", "SUCESSO")
        self.espaco_liberado += total
        return total
    
    def esvaziar_lixeira(self):
        if not self.is_windows:
            return
        self.log("Esvaziando lixeira...", "INFO")
        try:
            subprocess.run('rd /s /q C:\\$Recycle.bin', shell=True)
            self.log("Lixeira esvaziada!", "SUCESSO")
        except:
            try:
                subprocess.run('powershell -command "Clear-RecycleBin -Force"', shell=True)
                self.log("Lixeira esvaziada!", "SUCESSO")
            except Exception as e:
                self.log(f"Erro: {e}", "ERRO")
    
    def limpar_cache_pip(self):
        pip = os.path.join(self.venv_local, 'Scripts', 'pip.exe') if self.is_windows else os.path.join(self.venv_local, 'bin', 'pip')
        if not os.path.exists(pip):
            return
        self.log("Limpando cache do pip...", "INFO")
        try:
            subprocess.run(f'"{pip}" cache purge', shell=True)
            self.log("Cache do pip limpo!", "SUCESSO")
        except Exception as e:
            self.log(f"Erro: {e}", "ERRO")
    
    def remover_pacotes(self):
        pip = os.path.join(self.venv_local, 'Scripts', 'pip.exe') if self.is_windows else os.path.join(self.venv_local, 'bin', 'pip')
        if not os.path.exists(pip):
            return
        
        self.log("Removendo pacotes fora do requirements.txt...", "INFO")
        
        req_file = os.path.join(self.diretorio_projeto, 'requirements.txt')
        if not os.path.exists(req_file):
            self.log("❌ requirements.txt não encontrado!", "ERRO")
            return
        
        with open(req_file, 'r') as f:
            reqs = [l.strip().split('=')[0].split('>')[0].split('<')[0].strip().lower() 
                    for l in f if l.strip() and not l.startswith('#')]
        
        stdout, _ = subprocess.Popen(f'"{pip}" list --format=json', shell=True, stdout=subprocess.PIPE, text=True).communicate()
        if stdout:
            pacotes = json.loads(stdout)
            protegidos = ['pip', 'setuptools', 'wheel', 'virtualenv']
            removidos = 0
            
            for p in pacotes:
                nome = p['name'].lower()
                if nome not in reqs and nome not in protegidos:
                    self.log(f"  Removendo: {p['name']}", "INFO")
                    subprocess.run(f'"{pip}" uninstall {p["name"]} -y', shell=True)
                    removidos += 1
            
            self.log(f"✅ Removidos {removidos} pacotes!", "SUCESSO")
    
    def limpar_downloads(self):
        downloads = os.path.expanduser("~/Downloads")
        if not os.path.exists(downloads):
            return 0
        dias = self.config.get('dias_para_limpar', 30)
        self.log(f"Removendo arquivos com +{dias} dias...", "INFO")
        removidos = 0
        liberado = 0
        for item in Path(downloads).glob('*'):
            if item.is_file():
                idade = (datetime.now() - datetime.fromtimestamp(item.stat().st_mtime)).days
                if idade > dias:
                    try:
                        size = item.stat().st_size / (1024 * 1024)
                        item.unlink()
                        removidos += 1
                        liberado += size
                    except:
                        pass
        self.log(f"{removidos} arquivos ({liberado:.1f} MB)", "SUCESSO")
        self.espaco_liberado += liberado
        return liberado
    
    def limpeza_completa(self):
        if self.limpando:
            return
        self.limpando = True
        self.btn_limpar.configure(state="disabled", text="◆ Limpando...")
        self.espaco_liberado = 0
        thread = threading.Thread(target=self._executar_limpeza)
        thread.daemon = True
        thread.start()
    
    def _executar_limpeza(self):
        try:
            self.log("◆" * 40, "LIMPEZA")
            self.log("INICIANDO LIMPEZA COMPLETA", "LIMPEZA")
            self.log("◆" * 40, "LIMPEZA")
            
            self.limpar_temp()
            self.limpar_cache()
            self.esvaziar_lixeira()
            self.limpar_cache_pip()
            
            if self.config.get('remover_pacotes_nao_usados', True):
                self.remover_pacotes()
            
            if self.config.get('limpar_downloads', True):
                self.limpar_downloads()
            
            self.log("◆" * 40, "LIMPEZA")
            self.log(f"✅ LIMPEZA CONCLUÍDA!", "SUCESSO")
            self.log(f"Espaço liberado: {self.espaco_liberado:.1f} MB", "SUCESSO")
            self.log("◆" * 40, "LIMPEZA")
            
            self.label_espaco.configure(text=f"✦ {self.espaco_liberado:.1f} MB liberados")
            messagebox.showinfo("Concluído", f"✅ Limpeza finalizada!\n\n✦ {self.espaco_liberado:.1f} MB liberados")
            
        except Exception as e:
            self.log(f"Erro: {e}", "ERRO")
        finally:
            self.limpando = False
            self.btn_limpar.configure(state="normal", text="✦ Iniciar Limpeza Completa")
            self.progress_bar.set(0)
    
    def criar_interface(self):
        self.janela = ctk.CTk()
        self.janela.title("✦ Cleanup Manager")
        self.janela.geometry("950x700")
        self.janela.configure(fg_color=CORES['bg_principal'])
        
        main = ctk.CTkFrame(self.janela, fg_color=CORES['bg_secundario'], corner_radius=15)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        header = ctk.CTkFrame(main, fg_color=CORES['bg_terciario'], corner_radius=10, height=70)
        header.pack(fill="x", padx=15, pady=(15, 10))
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="✦ CLEANUP MANAGER", font=("JetBrains Mono", 22, "bold"), 
                    text_color=CORES['neon_azul']).pack(side="left", padx=20)
        ctk.CTkLabel(header, text="Limpeza Automatizada", font=("JetBrains Mono", 12),
                    text_color=CORES['texto_secundario']).pack(side="left", padx=10)
        
        status = ctk.CTkFrame(main, fg_color=CORES['bg_terciario'], corner_radius=8)
        status.pack(fill="x", padx=15, pady=5)
        
        cor_admin = CORES['neon_verde'] if self.is_admin else CORES['neon_amarelo']
        ctk.CTkLabel(status, text=f"⚡ {'Admin' if self.is_admin else 'User'}", 
                    text_color=cor_admin, font=("JetBrains Mono", 12, "bold")).grid(row=0, column=0, padx=15, pady=8)
        
        ctk.CTkLabel(status, text="✦ Venv Ativo", text_color=CORES['neon_verde'], 
                    font=("JetBrains Mono", 12, "bold")).grid(row=0, column=1, padx=15, pady=8)
        
        self.label_espaco = ctk.CTkLabel(status, text="✦ 0.0 MB liberados", 
                    text_color=CORES['neon_roxo'], font=("JetBrains Mono", 12, "bold"))
        self.label_espaco.grid(row=0, column=2, padx=15, pady=8)
        status.grid_columnconfigure(3, weight=1)
        
        botoes = ctk.CTkFrame(main, fg_color=CORES['bg_terciario'], corner_radius=8)
        botoes.pack(fill="x", padx=15, pady=8)
        
        self.btn_limpar = ctk.CTkButton(botoes, text="✦ Iniciar Limpeza Completa", 
                    command=self.limpeza_completa, font=("JetBrains Mono", 14, "bold"), height=45,
                    fg_color=CORES['neon_roxo'], hover_color=CORES['pastel_roxo'], 
                    text_color=CORES['bg_principal'], corner_radius=10)
        self.btn_limpar.grid(row=0, column=0, columnspan=6, padx=5, pady=8, sticky="ew")
        
        botoes_lista = [
            ("⌘ Temp", self.limpar_temp, CORES['neon_azul']),
            ("⌘ Cache", self.limpar_cache, CORES['neon_azul']),
            ("⌘ Lixeira", self.esvaziar_lixeira, CORES['neon_azul']),
            ("⌘ Pip", self.limpar_cache_pip, CORES['neon_rosa']),
            ("⌘ Pacotes", self.remover_pacotes, CORES['neon_rosa']),
            ("⌘ Downloads", self.limpar_downloads, CORES['neon_amarelo']),
        ]
        
        for i, (texto, cmd, cor) in enumerate(botoes_lista):
            btn = ctk.CTkButton(botoes, text=texto, command=cmd, font=("JetBrains Mono", 11), height=32,
                fg_color=CORES['bg_principal'], hover_color=cor, text_color=cor,
                border_color=cor, border_width=1, corner_radius=8)
            btn.grid(row=1, column=i, padx=3, pady=5, sticky="ew")
        
        for i in range(6):
            botoes.grid_columnconfigure(i, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(main, progress_color=CORES['neon_roxo'], 
                    fg_color=CORES['bg_principal'], height=6, corner_radius=3)
        self.progress_bar.pack(fill="x", padx=15, pady=8)
        self.progress_bar.set(0)
        
        ctk.CTkLabel(main, text="║ LOG ║", font=("JetBrains Mono", 12, "bold"), 
                    text_color=CORES['neon_azul']).pack(pady=(8, 4))
        
        self.log_text = scrolledtext.ScrolledText(main, wrap="word", font=("JetBrains Mono", 10),
                    bg=CORES['bg_principal'], fg=CORES['texto_principal'],
                    insertbackground=CORES['neon_azul'], relief="flat", height=14, bd=0)
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        
        self.log_text.tag_config("SUCESSO", foreground=CORES['neon_verde'])
        self.log_text.tag_config("ERRO", foreground=CORES['neon_vermelho'])
        self.log_text.tag_config("AVISO", foreground=CORES['neon_amarelo'])
        self.log_text.tag_config("INFO", foreground=CORES['neon_azul'])
        self.log_text.tag_config("LIMPEZA", foreground=CORES['neon_rosa'])
        
        rodape = ctk.CTkFrame(main, fg_color=CORES['bg_terciario'], corner_radius=8, height=40)
        rodape.pack(fill="x", padx=15, pady=(0, 10))
        rodape.pack_propagate(False)
        
        ctk.CTkLabel(rodape, text="✦ Cleanup Manager v1.0", 
                    font=("JetBrains Mono", 10), text_color=CORES['texto_secundario']).pack(side="left", padx=15)
        
        ctk.CTkButton(rodape, text="⚙ Config", command=self.abrir_config, font=("JetBrains Mono", 11), width=100, height=28,
                    fg_color=CORES['bg_principal'], hover_color=CORES['neon_azul'], text_color=CORES['texto_secundario'],
                    border_color=CORES['texto_secundario'], border_width=1, corner_radius=8).pack(side="right", padx=15)
        
        self.log("✦ Cleanup Manager iniciado", "INFO")
        self.log(f"✦ Projeto: {self.diretorio_projeto}", "INFO")
        self.log("✦ Pronto para limpeza", "INFO")
        
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
        self.janela.mainloop()
    
    def abrir_config(self):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("⚙ Config")
        janela.geometry("500x450")
        janela.configure(fg_color=CORES['bg_principal'])
        janela.grab_set()
        
        frame = ctk.CTkFrame(janela, fg_color=CORES['bg_secundario'], corner_radius=15)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="⚙ CONFIGURAÇÕES", font=("JetBrains Mono", 18, "bold"),
                    text_color=CORES['neon_azul']).pack(pady=(15, 20))
        
        opcoes = [
            ("remover_arquivos_temp", "◆ Remover temporários", self.config.get('remover_arquivos_temp', True)),
            ("esvaziar_lixeira", "◆ Esvaziar lixeira", self.config.get('esvaziar_lixeira', True)),
            ("limpar_prefetch", "◆ Limpar Prefetch", self.config.get('limpar_prefetch', True)),
            ("limpar_cache_pip", "◆ Limpar cache pip", self.config.get('limpar_cache_pip', True)),
            ("remover_pacotes_nao_usados", "◆ Remover pacotes", self.config.get('remover_pacotes_nao_usados', True)),
            ("limpar_downloads", "◆ Limpar Downloads", self.config.get('limpar_downloads', True)),
        ]
        
        checkboxes = {}
        for chave, texto, valor in opcoes:
            var = ctk.BooleanVar(value=valor)
            checkboxes[chave] = var
            cb = ctk.CTkCheckBox(frame, text=texto, variable=var, font=("JetBrains Mono", 12),
                text_color=CORES['texto_principal'], fg_color=CORES['neon_roxo'],
                hover_color=CORES['pastel_roxo'], border_color=CORES['texto_secundario'])
            cb.pack(anchor="w", pady=4, padx=20)
        
        ctk.CTkLabel(frame, text="Dias Downloads:", font=("JetBrains Mono", 12),
                    text_color=CORES['texto_secundario']).pack(anchor="w", pady=(15, 4), padx=20)
        
        entry = ctk.CTkEntry(frame, placeholder_text="30", width=100, font=("JetBrains Mono", 12),
            fg_color=CORES['bg_principal'], text_color=CORES['texto_principal'],
            border_color=CORES['texto_secundario'])
        entry.insert(0, str(self.config.get('dias_para_limpar', 30)))
        entry.pack(anchor="w", pady=(0, 15), padx=20)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15, padx=20)
        
        def salvar():
            for chave, var in checkboxes.items():
                self.config[chave] = var.get()
            try:
                self.config['dias_para_limpar'] = int(entry.get())
            except:
                pass
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            messagebox.showinfo("Sucesso", "✅ Configurações salvas!")
            janela.destroy()
        
        ctk.CTkButton(btn_frame, text="💾 Salvar", command=salvar, font=("JetBrains Mono", 12, "bold"), height=35,
            fg_color=CORES['neon_verde'], hover_color=CORES['pastel_verde'], text_color=CORES['bg_principal'],
            corner_radius=10).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(btn_frame, text="✗ Cancelar", command=janela.destroy, font=("JetBrains Mono", 12, "bold"), height=35,
            fg_color=CORES['neon_vermelho'], hover_color=CORES['pastel_rosa'], text_color=CORES['bg_principal'],
            corner_radius=10).pack(side="right", padx=5, expand=True, fill="x")
    
    def _fechar(self):
        if self.limpando and not messagebox.askyesno("Atenção", "Limpeza em andamento. Sair?"):
            return
        self.janela.destroy()
        sys.exit(0)

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    try:
        app = CleanupManagerGUI()
    except Exception as e:
        print(f"✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        input("Pressione Enter para sair...")