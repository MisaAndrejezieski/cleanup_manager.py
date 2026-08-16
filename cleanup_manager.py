#!/usr/bin/env python3
"""
Cleanup Manager - Tema Neon Pastel
Para programadores que amam estilo escuro com cores vibrantes
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

# Verifica o .venv
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

if not in_venv:
    print("❌ Ative o .venv primeiro!")
    print("   .venv\\Scripts\\activate")
    sys.exit(1)

# Importa as bibliotecas
try:
    from tkinter import messagebox, scrolledtext

    import customtkinter as ctk
except ImportError:
    print("📦 Instalando dependências...")
    subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter", "pillow"])
    from tkinter import messagebox, scrolledtext

    import customtkinter as ctk

# ============================================
# CORES NEON PASTEL
# ============================================

CORES = {
    # Fundos
    'bg_principal': '#0a0e1a',
    'bg_secundario': '#141b2d',
    'bg_terciario': '#1a2438',
    'bg_card': '#0f1629',
    
    # Textos
    'texto_principal': '#e0e6ff',
    'texto_secundario': '#8899cc',
    'texto_destaque': '#ffffff',
    
    # Neon
    'neon_azul': '#00d4ff',
    'neon_roxo': '#b06aff',
    'neon_rosa': '#ff6bcb',
    'neon_verde': '#00ff88',
    'neon_amarelo': '#ffe066',
    'neon_laranja': '#ff8c42',
    'neon_vermelho': '#ff4757',
    
    # Pastel
    'pastel_azul': '#7ec8e3',
    'pastel_roxo': '#c9b1ff',
    'pastel_rosa': '#ffb3d9',
    'pastel_verde': '#a8e6cf',
    'pastel_amarelo': '#ffe9a6',
    
    # Status
    'sucesso': '#00ff88',
    'erro': '#ff4757',
    'aviso': '#ffa502',
    'info': '#00d4ff',
}

# ============================================
# CLASSE PRINCIPAL COM TEMA NEON
# ============================================

class CleanupManagerGUI:
    def __init__(self):
        self.sistema = platform.system()
        self.is_windows = self.sistema == 'Windows'
        self.is_admin = self._verificar_admin()
        self.pacotes_protegidos = ['pip', 'setuptools', 'wheel', 'virtualenv', 'pipenv', 'poetry']
        
        self.diretorio_projeto = os.path.dirname(os.path.abspath(__file__))
        self.venv_local = os.path.join(self.diretorio_projeto, '.venv')
        self.esta_em_venv = in_venv
        
        self.config_file = os.path.join(self.diretorio_projeto, 'cleanup_config.json')
        self.config = self._carregar_config()
        
        self.espaco_liberado = 0
        self.limpando = False
        
        # Aplica o tema neon
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
        else:
            return os.geteuid() == 0
    
    def _carregar_config(self):
        config_padrao = {
            'modo_agressivo': False,
            'limpar_cache_pip': True,
            'remover_pycache': True,
            'remover_arquivos_temp': True,
            'esvaziar_lixeira': True,
            'limpar_prefetch': True,
            'remover_pacotes_nao_usados': True,
            'limpar_downloads': True,
            'dias_para_limpar': 30,
            'proteger_pacotes': self.pacotes_protegidos,
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in config_padrao.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                return config_padrao
        else:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_padrao, f, indent=2, ensure_ascii=False)
            return config_padrao
    
    def _salvar_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def log(self, mensagem, tipo="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Cores diferentes no log
        cores = {
            "SUCESSO": CORES['sucesso'],
            "ERRO": CORES['erro'],
            "AVISO": CORES['aviso'],
            "INFO": CORES['info'],
            "LIMPEZA": CORES['neon_rosa']
        }
        
        emojis = {
            "SUCESSO": "✅",
            "ERRO": "❌",
            "AVISO": "⚠️",
            "INFO": "✦",
            "LIMPEZA": "◆"
        }
        
        # Formata a mensagem com cores (para o ScrolledText)
        log_msg = f"[{timestamp}] {emojis.get(tipo, '')} {mensagem}\n"
        
        if hasattr(self, 'log_text'):
            # Insere com a cor apropriada
            cor = cores.get(tipo, CORES['texto_secundario'])
            self.log_text.insert("end", log_msg, (tipo,))
            self.log_text.see("end")
            self.janela.update()
        
        try:
            with open("cleanup_log.txt", 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{tipo}] {mensagem}\n")
        except:
            pass
    
    def _obter_tamanho_pasta(self, pasta):
        if not os.path.exists(pasta):
            return 0
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(pasta):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
            return round(total / (1024 * 1024), 2)
        except:
            return 0
    
    def _executar_comando(self, comando, shell=True):
        try:
            resultado = subprocess.run(
                comando, shell=shell, capture_output=True, text=True, encoding='utf-8'
            )
            return resultado.stdout, resultado.stderr, resultado.returncode
        except:
            return None, None, 1
    
    def limpar_arquivos_temporarios(self):
        if not self.is_windows:
            self.log("Apenas para Windows", "AVISO")
            return 0
        
        self.log("Iniciando limpeza de temporários...", "INFO")
        total_liberado = 0
        
        locais = []
        temp_user = os.environ.get('TEMP', '')
        if temp_user and os.path.exists(temp_user):
            locais.append(("Temp do usuário", temp_user))
        if os.path.exists("C:\\Windows\\Temp"):
            locais.append(("Temp do Windows", "C:\\Windows\\Temp"))
        
        for nome, local in locais:
            tamanho_antes = self._obter_tamanho_pasta(local)
            self.log(f"  {nome}: {tamanho_antes:.1f} MB", "INFO")
            
            try:
                for item in Path(local).glob('*'):
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                    except:
                        pass
                
                tamanho_depois = self._obter_tamanho_pasta(local)
                liberado = tamanho_antes - tamanho_depois
                total_liberado += liberado
                self.log(f"    ✓ Liberado: {liberado:.1f} MB", "SUCESSO")
            except Exception as e:
                self.log(f"    ✗ Erro: {e}", "ERRO")
        
        self.espaco_liberado += total_liberado
        self.log(f"Total: {total_liberado:.1f} MB", "SUCESSO")
        return total_liberado
    
    def limpar_cache_windows(self):
        if not self.is_windows:
            self.log("Apenas para Windows", "AVISO")
            return 0
        
        self.log("Iniciando limpeza de caches...", "INFO")
        total_liberado = 0
        
        caches = [("Prefetch", "C:\\Windows\\Prefetch")]
        
        for nome, local in caches:
            if not os.path.exists(local):
                continue
            
            tamanho_antes = self._obter_tamanho_pasta(local)
            self.log(f"  {nome}: {tamanho_antes:.1f} MB", "INFO")
            
            try:
                for item in Path(local).glob('*'):
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                    except:
                        pass
                
                tamanho_depois = self._obter_tamanho_pasta(local)
                liberado = tamanho_antes - tamanho_depois
                total_liberado += liberado
                self.log(f"    ✓ Liberado: {liberado:.1f} MB", "SUCESSO")
            except:
                pass
        
        self.espaco_liberado += total_liberado
        self.log(f"Total: {total_liberado:.1f} MB", "SUCESSO")
        return total_liberado
    
    def esvaziar_lixeira(self):
        if not self.is_windows:
            self.log("Apenas para Windows", "AVISO")
            return
        
        self.log("Esvaziando lixeira...", "INFO")
        try:
            self._executar_comando('rd /s /q C:\\$Recycle.bin')
            self.log("✓ Lixeira esvaziada!", "SUCESSO")
        except:
            try:
                self._executar_comando('powershell -command "Clear-RecycleBin -Force"')
                self.log("✓ Lixeira esvaziada!", "SUCESSO")
            except Exception as e:
                self.log(f"✗ Erro: {e}", "ERRO")
    
    def limpar_cache_pip(self):
        if not os.path.exists(self.venv_local):
            self.log("✗ .venv não encontrado!", "ERRO")
            return
        
        self.log("Limpando cache do pip...", "INFO")
        
        pip_exe = os.path.join(self.venv_local, 'Scripts', 'pip.exe') if self.is_windows else os.path.join(self.venv_local, 'bin', 'pip')
        
        if not os.path.exists(pip_exe):
            self.log("✗ Pip não encontrado!", "ERRO")
            return
        
        try:
            self._executar_comando(f'"{pip_exe}" cache purge')
            self.log("✓ Cache do pip limpo!", "SUCESSO")
            
            pycache_count = 0
            for pycache in Path(self.venv_local).rglob('__pycache__'):
                try:
                    shutil.rmtree(pycache)
                    pycache_count += 1
                except:
                    pass
            if pycache_count > 0:
                self.log(f"✓ Removidos {pycache_count} __pycache__", "SUCESSO")
        except Exception as e:
            self.log(f"✗ Erro: {e}", "ERRO")
    
    def remover_pacotes_nao_usados(self):
        if not os.path.exists(self.venv_local):
            self.log("✗ .venv não encontrado!", "ERRO")
            return
        
        self.log("Removendo pacotes não usados...", "INFO")
        
        pip_exe = os.path.join(self.venv_local, 'Scripts', 'pip.exe') if self.is_windows else os.path.join(self.venv_local, 'bin', 'pip')
        
        if not os.path.exists(pip_exe):
            self.log("✗ Pip não encontrado!", "ERRO")
            return
        
        stdout, _, _ = self._executar_comando(f'"{pip_exe}" list --format=json')
        if not stdout:
            self.log("✗ Não foi possível listar pacotes", "ERRO")
            return
        
        try:
            pacotes = json.loads(stdout)
            removidos = 0
            
            for pacote in pacotes:
                nome = pacote['name']
                if nome not in self.config['proteger_pacotes']:
                    self.log(f"  Removendo: {nome}", "INFO")
                    self._executar_comando(f'"{pip_exe}" uninstall {nome} -y')
                    removidos += 1
            
            self.log(f"✓ Removidos {removidos} pacotes!", "SUCESSO")
        except Exception as e:
            self.log(f"✗ Erro: {e}", "ERRO")
    
    def limpar_downloads(self):
        downloads = os.path.expanduser("~/Downloads")
        if not os.path.exists(downloads):
            self.log("Downloads não encontrado", "AVISO")
            return 0
        
        dias = self.config.get('dias_para_limpar', 30)
        self.log(f"Removendo arquivos com mais de {dias} dias...", "INFO")
        
        removidos = 0
        liberado = 0
        for item in Path(downloads).glob('*'):
            if item.is_file():
                idade = (datetime.now() - datetime.fromtimestamp(item.stat().st_mtime)).days
                if idade > dias:
                    try:
                        tamanho = item.stat().st_size / (1024 * 1024)
                        item.unlink()
                        removidos += 1
                        liberado += tamanho
                    except:
                        pass
        
        self.espaco_liberado += liberado
        self.log(f"✓ {removidos} arquivos ({liberado:.1f} MB)", "SUCESSO")
        return liberado
    
    def limpeza_completa(self):
        if self.limpando:
            self.log("⚠️ Limpeza em andamento!", "AVISO")
            return
        
        self.limpando = True
        self.btn_limpar.configure(state="disabled", text="✦ Limpando...")
        self.espaco_liberado = 0
        
        thread = threading.Thread(target=self._executar_limpeza_completa)
        thread.daemon = True
        thread.start()
    
    def _executar_limpeza_completa(self):
        try:
            self.log("◆" * 50, "LIMPEZA")
            self.log("🚀 INICIANDO LIMPEZA COMPLETA", "LIMPEZA")
            self.log("◆" * 50, "LIMPEZA")
            
            self.log("\n📁 1. Temporários...", "INFO")
            self.limpar_arquivos_temporarios()
            
            self.log("\n📁 2. Caches...", "INFO")
            self.limpar_cache_windows()
            
            self.log("\n📁 3. Lixeira...", "INFO")
            self.esvaziar_lixeira()
            
            self.log("\n📁 4. Pip cache...", "INFO")
            self.limpar_cache_pip()
            
            if self.config.get('remover_pacotes_nao_usados', True):
                self.log("\n📁 5. Removendo pacotes...", "INFO")
                self.remover_pacotes_nao_usados()
            
            if self.config.get('limpar_downloads', True):
                self.log("\n📁 6. Downloads...", "INFO")
                self.limpar_downloads()
            
            self.log("\n" + "◆" * 50, "LIMPEZA")
            self.log(f"✓ LIMPEZA CONCLUÍDA!", "SUCESSO")
            self.log(f"✦ Espaço liberado: {self.espaco_liberado:.1f} MB", "SUCESSO")
            self.log("◆" * 50, "LIMPEZA")
            
            self.label_espaco.configure(
                text=f"✦ Espaço liberado: {self.espaco_liberado:.1f} MB"
            )
            
            if self.espaco_liberado > 0:
                messagebox.showinfo(
                    "Limpeza Concluída",
                    f"✓ Limpeza finalizada!\n\n✦ Espaço liberado: {self.espaco_liberado:.1f} MB"
                )
            else:
                messagebox.showinfo(
                    "Limpeza Concluída",
                    "✓ Limpeza finalizada!\n\nNenhum espaço significativo foi liberado."
                )
            
        except Exception as e:
            self.log(f"✗ Erro: {e}", "ERRO")
            import traceback
            traceback.print_exc()
        
        finally:
            self.limpando = False
            self.btn_limpar.configure(state="normal", text="✦ Iniciar Limpeza Completa")
            self.progress_bar.set(0)
    
    def criar_interface(self):
        # Configuração da janela
        self.janela = ctk.CTk()
        self.janela.title("✦ Cleanup Manager - Neon Pastel")
        self.janela.geometry("950x720")
        self.janela.minsize(850, 650)
        self.janela.configure(fg_color=CORES['bg_principal'])
        
        # Frame principal
        self.frame_principal = ctk.CTkFrame(
            self.janela,
            fg_color=CORES['bg_secundario'],
            corner_radius=15
        )
        self.frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ===== CABEÇALHO =====
        header = ctk.CTkFrame(
            self.frame_principal,
            fg_color=CORES['bg_terciario'],
            corner_radius=10,
            height=80
        )
        header.pack(fill="x", padx=15, pady=(15, 10))
        header.pack_propagate(False)
        
        # Título com neon
        titulo = ctk.CTkLabel(
            header,
            text="✦ CLEANUP MANAGER",
            font=("JetBrains Mono", 24, "bold"),
            text_color=CORES['neon_azul']
        )
        titulo.pack(side="left", padx=20, pady=10)
        
        # Subtítulo
        subtitulo = ctk.CTkLabel(
            header,
            text="Limpeza Automatizada • SSD + Python",
            font=("JetBrains Mono", 12),
            text_color=CORES['texto_secundario']
        )
        subtitulo.pack(side="left", padx=10)
        
        # ===== STATUS =====
        self.frame_status = ctk.CTkFrame(
            self.frame_principal,
            fg_color=CORES['bg_terciario'],
            corner_radius=8
        )
        self.frame_status.pack(fill="x", padx=15, pady=5)
        
        # Status Admin
        status_admin = "⬡ Admin" if self.is_admin else "⬡ User"
        cor_admin = CORES['neon_verde'] if self.is_admin else CORES['neon_amarelo']
        self.label_admin = ctk.CTkLabel(
            self.frame_status,
            text=status_admin,
            text_color=cor_admin,
            font=("JetBrains Mono", 12, "bold")
        )
        self.label_admin.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        # Status Venv
        status_venv = "⬡ Venv Ativo" if self.esta_em_venv else "⬡ Venv Inativo"
        cor_venv = CORES['neon_verde'] if self.esta_em_venv else CORES['neon_vermelho']
        self.label_venv = ctk.CTkLabel(
            self.frame_status,
            text=status_venv,
            text_color=cor_venv,
            font=("JetBrains Mono", 12, "bold")
        )
        self.label_venv.grid(row=0, column=1, padx=15, pady=8, sticky="w")
        
        # Espaço liberado
        self.label_espaco = ctk.CTkLabel(
            self.frame_status,
            text="✦ 0.0 MB liberados",
            text_color=CORES['neon_roxo'],
            font=("JetBrains Mono", 12, "bold")
        )
        self.label_espaco.grid(row=0, column=2, padx=15, pady=8, sticky="w")
        
        self.frame_status.grid_columnconfigure(3, weight=1)
        
        # ===== BOTÕES =====
        self.frame_botoes = ctk.CTkFrame(
            self.frame_principal,
            fg_color=CORES['bg_terciario'],
            corner_radius=8
        )
        self.frame_botoes.pack(fill="x", padx=15, pady=8)
        
        # Botão principal - Limpeza Completa
        self.btn_limpar = ctk.CTkButton(
            self.frame_botoes,
            text="✦ Iniciar Limpeza Completa",
            command=self.limpeza_completa,
            font=("JetBrains Mono", 14, "bold"),
            height=45,
            fg_color=CORES['neon_roxo'],
            hover_color=CORES['pastel_roxo'],
            text_color=CORES['bg_principal'],
            corner_radius=10
        )
        self.btn_limpar.grid(row=0, column=0, columnspan=6, padx=5, pady=8, sticky="ew")
        
        # Botões secundários
        botoes = [
            ("⌘ Temp", self.limpar_arquivos_temporarios, CORES['neon_azul']),
            ("⌘ Cache", self.limpar_cache_windows, CORES['neon_azul']),
            ("⌘ Lixeira", self.esvaziar_lixeira, CORES['neon_azul']),
            ("⌘ Pip", self.limpar_cache_pip, CORES['neon_rosa']),
            ("⌘ Pacotes", self.remover_pacotes_nao_usados, CORES['neon_rosa']),
            ("⌘ Downloads", self.limpar_downloads, CORES['neon_amarelo']),
        ]
        
        for i, (texto, comando, cor) in enumerate(botoes):
            btn = ctk.CTkButton(
                self.frame_botoes,
                text=texto,
                command=comando,
                font=("JetBrains Mono", 11),
                height=32,
                fg_color=CORES['bg_principal'],
                hover_color=cor,
                text_color=cor,
                border_color=cor,
                border_width=1,
                corner_radius=8
            )
            btn.grid(row=1, column=i, padx=3, pady=5, sticky="ew")
        
        for i in range(6):
            self.frame_botoes.grid_columnconfigure(i, weight=1)
        
        # ===== PROGRESS BAR =====
        self.progress_bar = ctk.CTkProgressBar(
            self.frame_principal,
            progress_color=CORES['neon_roxo'],
            fg_color=CORES['bg_principal'],
            height=6,
            corner_radius=3
        )
        self.progress_bar.pack(fill="x", padx=15, pady=8)
        self.progress_bar.set(0)
        
        # ===== LOG =====
        label_log = ctk.CTkLabel(
            self.frame_principal,
            text="║ LOG DE EXECUÇÃO ║",
            font=("JetBrains Mono", 12, "bold"),
            text_color=CORES['neon_azul']
        )
        label_log.pack(pady=(8, 4))
        
        # Área de log com tema escuro
        self.log_text = scrolledtext.ScrolledText(
            self.frame_principal,
            wrap="word",
            font=("JetBrains Mono", 10),
            bg=CORES['bg_principal'],
            fg=CORES['texto_principal'],
            insertbackground=CORES['neon_azul'],
            relief="flat",
            height=14,
            bd=0,
            highlightthickness=0
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        
        # Configura cores das tags do log
        self.log_text.tag_config("SUCESSO", foreground=CORES['neon_verde'])
        self.log_text.tag_config("ERRO", foreground=CORES['neon_vermelho'])
        self.log_text.tag_config("AVISO", foreground=CORES['neon_amarelo'])
        self.log_text.tag_config("INFO", foreground=CORES['neon_azul'])
        self.log_text.tag_config("LIMPEZA", foreground=CORES['neon_rosa'])
        
        # ===== RODAPÉ =====
        rodape = ctk.CTkFrame(
            self.frame_principal,
            fg_color=CORES['bg_terciario'],
            corner_radius=8,
            height=40
        )
        rodape.pack(fill="x", padx=15, pady=(0, 10))
        rodape.pack_propagate(False)
        
        # Configurações
        self.btn_config = ctk.CTkButton(
            rodape,
            text="⚙ Config",
            command=self.abrir_configuracoes,
            font=("JetBrains Mono", 11),
            width=100,
            height=28,
            fg_color=CORES['bg_principal'],
            hover_color=CORES['neon_azul'],
            text_color=CORES['texto_secundario'],
            border_color=CORES['texto_secundario'],
            border_width=1,
            corner_radius=8
        )
        self.btn_config.pack(side="right", padx=15, pady=5)
        
        # Info
        info = ctk.CTkLabel(
            rodape,
            text="✦ Neon Pastel Theme v1.0 • Cleanup Manager",
            font=("JetBrains Mono", 10),
            text_color=CORES['texto_secundario']
        )
        info.pack(side="left", padx=15)
        
        # ===== MENSAGEM INICIAL =====
        self.log("✦ Cleanup Manager iniciado", "INFO")
        self.log(f"✦ Pasta: {self.diretorio_projeto}", "INFO")
        self.log(f"✦ Sistema: {self.sistema}", "INFO")
        self.log(f"✦ Venv: {'Ativo' if self.esta_em_venv else 'Inativo'}", "INFO")
        self.log("║" * 30, "INFO")
        self.log("✦ Pronto! Clique em 'Iniciar Limpeza Completa'", "INFO")
        
        # Fechar
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
        self.janela.mainloop()
    
    def abrir_configuracoes(self):
        janela_config = ctk.CTkToplevel(self.janela)
        janela_config.title("⚙ Configurações")
        janela_config.geometry("520x520")
        janela_config.resizable(False, False)
        janela_config.configure(fg_color=CORES['bg_principal'])
        janela_config.grab_set()
        
        frame = ctk.CTkFrame(
            janela_config,
            fg_color=CORES['bg_secundario'],
            corner_radius=15
        )
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text="⚙ CONFIGURAÇÕES",
            font=("JetBrains Mono", 18, "bold"),
            text_color=CORES['neon_azul']
        ).pack(pady=(15, 20))
        
        opcoes = [
            ("modo_agressivo", "◆ Modo Agressivo", self.config.get('modo_agressivo', False)),
            ("limpar_cache_pip", "◆ Limpar cache pip", self.config.get('limpar_cache_pip', True)),
            ("remover_pycache", "◆ Remover __pycache__", self.config.get('remover_pycache', True)),
            ("remover_arquivos_temp", "◆ Remover temporários", self.config.get('remover_arquivos_temp', True)),
            ("esvaziar_lixeira", "◆ Esvaziar lixeira", self.config.get('esvaziar_lixeira', True)),
            ("remover_pacotes_nao_usados", "◆ Remover pacotes", self.config.get('remover_pacotes_nao_usados', True)),
            ("limpar_downloads", "◆ Limpar Downloads", self.config.get('limpar_downloads', True)),
        ]
        
        checkboxes = {}
        for chave, texto, valor in opcoes:
            var = ctk.BooleanVar(value=valor)
            checkboxes[chave] = var
            cb = ctk.CTkCheckBox(
                frame,
                text=texto,
                variable=var,
                font=("JetBrains Mono", 12),
                text_color=CORES['texto_principal'],
                fg_color=CORES['neon_roxo'],
                hover_color=CORES['pastel_roxo'],
                border_color=CORES['texto_secundario'],
                checkmark_color=CORES['bg_principal']
            )
            cb.pack(anchor="w", pady=4, padx=20)
        
        ctk.CTkLabel(
            frame,
            text="Dias para manter Downloads:",
            font=("JetBrains Mono", 12),
            text_color=CORES['texto_secundario']
        ).pack(anchor="w", pady=(15, 4), padx=20)
        
        entry_dias = ctk.CTkEntry(
            frame,
            placeholder_text="30",
            width=100,
            font=("JetBrains Mono", 12),
            fg_color=CORES['bg_principal'],
            text_color=CORES['texto_principal'],
            border_color=CORES['texto_secundario']
        )
        entry_dias.insert(0, str(self.config.get('dias_para_limpar', 30)))
        entry_dias.pack(anchor="w", pady=(0, 15), padx=20)
        
        frame_botoes = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botoes.pack(fill="x", pady=15, padx=20)
        
        def salvar_config():
            for chave, var in checkboxes.items():
                self.config[chave] = var.get()
            try:
                self.config['dias_para_limpar'] = int(entry_dias.get())
            except:
                pass
            self._salvar_config()
            messagebox.showinfo("Sucesso", "✓ Configurações salvas!")
            janela_config.destroy()
        
        ctk.CTkButton(
            frame_botoes,
            text="💾 Salvar",
            command=salvar_config,
            font=("JetBrains Mono", 12, "bold"),
            height=35,
            fg_color=CORES['neon_verde'],
            hover_color=CORES['pastel_verde'],
            text_color=CORES['bg_principal'],
            corner_radius=10
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            frame_botoes,
            text="✗ Cancelar",
            command=janela_config.destroy,
            font=("JetBrains Mono", 12, "bold"),
            height=35,
            fg_color=CORES['neon_vermelho'],
            hover_color=CORES['pastel_rosa'],
            text_color=CORES['bg_principal'],
            corner_radius=10
        ).pack(side="right", padx=5, expand=True, fill="x")
    
    def _fechar(self):
        if self.limpando:
            if not messagebox.askyesno("Atenção", "Limpeza em andamento. Sair mesmo assim?"):
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