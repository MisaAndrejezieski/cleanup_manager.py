#!/usr/bin/env python3
"""
Cleanup Manager - Limpeza Automatizada com GUI
Versão: 6.1 - Corrigido
"""

import os
import platform
import subprocess
import sys

# ============================================
# PARTE 1: VERIFICA E ATIVA O .VENV
# ============================================

def verificar_venv():
    """Verifica se está no .venv e mostra instruções"""
    
    # Já está no venv?
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ .venv já ativo")
        return True
    
    # Caminho do .venv
    diretorio = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(diretorio, '.venv')
    
    # Se não existe, cria
    if not os.path.exists(venv_path):
        print("📦 Criando .venv...")
        try:
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            print("✅ .venv criado!")
        except Exception as e:
            print(f"❌ Erro ao criar .venv: {e}")
            return False
    
    # Verifica se o Python do .venv existe
    is_windows = platform.system() == 'Windows'
    if is_windows:
        python_venv = os.path.join(venv_path, 'Scripts', 'python.exe')
        activate_script = os.path.join(venv_path, 'Scripts', 'activate')
    else:
        python_venv = os.path.join(venv_path, 'bin', 'python')
        activate_script = os.path.join(venv_path, 'bin', 'activate')
    
    if not os.path.exists(python_venv):
        print(f"❌ Python do .venv não encontrado: {python_venv}")
        return False
    
    print(f"🐍 Python do .venv: {python_venv}")
    print("⚠️ Execute o programa com o Python do .venv:")
    print(f'   "{python_venv}" "{__file__}"')
    print("")
    print("Ou ative o .venv e execute:")
    if is_windows:
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    print("   python cleanup_manager.py")
    
    return False

# ============================================
# PARTE 2: VERIFICA E INSTALA DEPENDÊNCIAS
# ============================================

def instalar_dependencias():
    """Instala as dependências necessárias"""
    
    dependencias = ['customtkinter', 'pillow']
    faltando = []
    
    # Verifica quais estão faltando
    for dep in dependencias:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            faltando.append(dep)
    
    if not faltando:
        return True
    
    print(f"📦 Instalando: {', '.join(faltando)}...")
    
    # Instala usando pip
    for dep in faltando:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"✅ {dep} instalado!")
        except Exception as e:
            print(f"❌ Erro ao instalar {dep}: {e}")
            return False
    
    print("✅ Todas as dependências instaladas!")
    return True

# ============================================
# PARTE 3: EXECUTA O PROGRAMA
# ============================================

def main():
    # Verifica o .venv
    if not verificar_venv():
        print("\n❌ Execute o comando abaixo e tente novamente:")
        diretorio = os.path.dirname(os.path.abspath(__file__))
        venv_path = os.path.join(diretorio, '.venv')
        is_windows = platform.system() == 'Windows'
        
        if is_windows:
            python_venv = os.path.join(venv_path, 'Scripts', 'python.exe')
            print(f'   "{python_venv}" cleanup_manager.py')
        else:
            python_venv = os.path.join(venv_path, 'bin', 'python')
            print(f'   {python_venv} cleanup_manager.py')
        sys.exit(1)
    
    # Instala dependências
    if not instalar_dependencias():
        print("❌ Falha ao instalar dependências")
        sys.exit(1)
    
    # Importa as bibliotecas e roda
    import json
    import shutil
    import threading
    from datetime import datetime
    from pathlib import Path
    from tkinter import messagebox, scrolledtext

    import customtkinter as ctk

    # ============================================
    # CLASSE PRINCIPAL (igual à anterior)
    # ============================================
    
    class CleanupManagerGUI:
        def __init__(self):
            self.sistema = platform.system()
            self.is_windows = self.sistema == 'Windows'
            self.is_admin = self._verificar_admin()
            self.pacotes_protegidos = ['pip', 'setuptools', 'wheel', 'virtualenv', 'pipenv', 'poetry']
            
            self.diretorio_projeto = os.path.dirname(os.path.abspath(__file__))
            self.venv_local = os.path.join(self.diretorio_projeto, '.venv')
            self.requirements_file = os.path.join(self.diretorio_projeto, 'requirements.txt')
            self.esta_em_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            
            self.config_file = os.path.join(self.diretorio_projeto, 'cleanup_config.json')
            self.config = self._carregar_config()
            
            self.espaco_liberado = 0
            self.limpando = False
            
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
                'pasta_ignoradas': ['node_modules', '.git', '__pycache__', '.pytest_cache']
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
            except Exception as e:
                self.log(f"Erro ao salvar config: {e}", "ERRO")
        
        def log(self, mensagem, tipo="INFO"):
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            emojis = {
                "SUCESSO": "✅",
                "ERRO": "❌",
                "AVISO": "⚠️",
                "INFO": "ℹ️",
                "LIMPEZA": "🧹"
            }
            
            log_msg = f"[{timestamp}] {emojis.get(tipo, '')} {mensagem}\n"
            
            if hasattr(self, 'log_text'):
                self.log_text.insert("end", log_msg)
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
                    comando, 
                    shell=shell, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8'
                )
                return resultado.stdout, resultado.stderr, resultado.returncode
            except Exception as e:
                return None, str(e), 1
        
        def limpar_arquivos_temporarios(self):
            if not self.is_windows:
                self.log("Esta função é apenas para Windows", "AVISO")
                return 0
            
            self.log("Iniciando limpeza de arquivos temporários...", "INFO")
            
            locais_temp = []
            temp_user = os.environ.get('TEMP', '')
            if temp_user and os.path.exists(temp_user):
                locais_temp.append(("Temp do usuário", temp_user))
            
            if os.path.exists("C:\\Windows\\Temp"):
                locais_temp.append(("Temp do Windows", "C:\\Windows\\Temp"))
            
            total_liberado = 0
            for nome, local in locais_temp:
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
                    self.log(f"    ✅ Liberado: {liberado:.1f} MB", "SUCESSO")
                except Exception as e:
                    self.log(f"    ❌ Erro em {nome}: {e}", "ERRO")
            
            self.espaco_liberado += total_liberado
            self.log(f"Total liberado em temporários: {total_liberado:.1f} MB", "SUCESSO")
            return total_liberado
        
        def limpar_cache_windows(self):
            if not self.is_windows:
                self.log("Esta função é apenas para Windows", "AVISO")
                return 0
            
            self.log("Iniciando limpeza de caches...", "INFO")
            
            caches = [
                ("Cache de pré-carregamento", "C:\\Windows\\Prefetch"),
            ]
            
            total_liberado = 0
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
                    self.log(f"    ✅ Liberado: {liberado:.1f} MB", "SUCESSO")
                except Exception as e:
                    self.log(f"    ❌ Erro: {e}", "ERRO")
            
            self.espaco_liberado += total_liberado
            self.log(f"Total liberado em caches: {total_liberado:.1f} MB", "SUCESSO")
            return total_liberado
        
        def esvaziar_lixeira(self):
            if not self.is_windows:
                self.log("Esta função é apenas para Windows", "AVISO")
                return
            
            self.log("Esvaziando lixeira...", "INFO")
            try:
                self._executar_comando('rd /s /q C:\\$Recycle.bin')
                self.log("✅ Lixeira esvaziada!", "SUCESSO")
            except:
                try:
                    self._executar_comando('powershell -command "Clear-RecycleBin -Force"')
                    self.log("✅ Lixeira esvaziada!", "SUCESSO")
                except Exception as e:
                    self.log(f"❌ Erro ao esvaziar lixeira: {e}", "ERRO")
        
        def limpar_cache_pip(self):
            if not os.path.exists(self.venv_local):
                self.log("❌ .venv local não encontrado!", "ERRO")
                return
            
            self.log(f"Limpando cache do pip em: {self.venv_local}", "INFO")
            
            pip_exe = os.path.join(self.venv_local, 'Scripts', 'pip.exe') if self.is_windows else os.path.join(self.venv_local, 'bin', 'pip')
            
            if not os.path.exists(pip_exe):
                self.log("❌ Pip não encontrado!", "ERRO")
                return
            
            try:
                self._executar_comando(f'"{pip_exe}" cache purge')
                self.log("✅ Cache do pip limpo!", "SUCESSO")
                
                pycache_count = 0
                for pycache in Path(self.venv_local).rglob('__pycache__'):
                    try:
                        shutil.rmtree(pycache)
                        pycache_count += 1
                    except:
                        pass
                if pycache_count > 0:
                    self.log(f"✅ Removidos {pycache_count} diretórios __pycache__", "SUCESSO")
            except Exception as e:
                self.log(f"❌ Erro: {e}", "ERRO")
        
        def remover_pacotes_nao_usados(self):
            if not os.path.exists(self.venv_local):
                self.log("❌ .venv local não encontrado!", "ERRO")
                return
            
            self.log("Removendo pacotes não usados...", "INFO")
            
            pip_exe = os.path.join(self.venv_local, 'Scripts', 'pip.exe') if self.is_windows else os.path.join(self.venv_local, 'bin', 'pip')
            
            if not os.path.exists(pip_exe):
                self.log("❌ Pip não encontrado!", "ERRO")
                return
            
            stdout, _, _ = self._executar_comando(f'"{pip_exe}" list --format=json')
            if not stdout:
                self.log("❌ Não foi possível listar pacotes", "ERRO")
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
                
                self.log(f"✅ Removidos {removidos} pacotes!", "SUCESSO")
            except Exception as e:
                self.log(f"❌ Erro: {e}", "ERRO")
        
        def limpar_downloads(self):
            downloads = os.path.expanduser("~/Downloads")
            if not os.path.exists(downloads):
                self.log("Pasta de Downloads não encontrada", "AVISO")
                return 0
            
            dias = self.config.get('dias_para_limpar', 30)
            self.log(f"Removendo arquivos com mais de {dias} dias da pasta Downloads...", "INFO")
            
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
            self.log(f"✅ Removidos {removidos} arquivos ({liberado:.1f} MB liberados)", "SUCESSO")
            return liberado
        
        def limpeza_completa(self):
            if self.limpando:
                self.log("⚠️ Uma limpeza já está em andamento!", "AVISO")
                return
            
            self.limpando = True
            self.btn_limpar.configure(state="disabled", text="🔄 Limpando...")
            self.espaco_liberado = 0
            
            thread = threading.Thread(target=self._executar_limpeza_completa)
            thread.daemon = True
            thread.start()
        
        def _executar_limpeza_completa(self):
            try:
                self.log("=" * 50, "INFO")
                self.log("🚀 INICIANDO LIMPEZA COMPLETA", "LIMPEZA")
                self.log("=" * 50, "INFO")
                
                self.log("\n📁 1. Limpando arquivos temporários...", "INFO")
                self.limpar_arquivos_temporarios()
                
                self.log("\n📁 2. Limpando caches...", "INFO")
                self.limpar_cache_windows()
                
                self.log("\n📁 3. Esvaziando lixeira...", "INFO")
                self.esvaziar_lixeira()
                
                self.log("\n📁 4. Limpando cache do pip...", "INFO")
                self.limpar_cache_pip()
                
                if self.config.get('remover_pacotes_nao_usados', True):
                    self.log("\n📁 5. Removendo pacotes não usados...", "INFO")
                    self.remover_pacotes_nao_usados()
                
                if self.config.get('limpar_downloads', True):
                    self.log("\n📁 6. Limpando Downloads antigos...", "INFO")
                    self.limpar_downloads()
                
                self.log("\n" + "=" * 50, "INFO")
                self.log(f"✅ LIMPEZA CONCLUÍDA!", "SUCESSO")
                self.log(f"💾 Total liberado: {self.espaco_liberado:.1f} MB", "SUCESSO")
                self.log("=" * 50, "INFO")
                
                self.label_espaco.configure(
                    text=f"💾 Espaço liberado: {self.espaco_liberado:.1f} MB"
                )
                
                if self.espaco_liberado > 0:
                    messagebox.showinfo(
                        "Limpeza Concluída",
                        f"✅ Limpeza finalizada!\n\n💾 Espaço liberado: {self.espaco_liberado:.1f} MB"
                    )
                else:
                    messagebox.showinfo(
                        "Limpeza Concluída",
                        "✅ Limpeza finalizada!\n\nNenhum espaço significativo foi liberado."
                    )
                
            except Exception as e:
                self.log(f"❌ Erro durante a limpeza: {e}", "ERRO")
                import traceback
                traceback.print_exc()
            
            finally:
                self.limpando = False
                self.btn_limpar.configure(state="normal", text="🚀 Iniciar Limpeza Completa")
                self.progress_bar.set(0)
        
        def criar_interface(self):
            self.janela = ctk.CTk()
            self.janela.title("🧹 Cleanup Manager - Limpeza Automatizada")
            self.janela.geometry("900x700")
            self.janela.minsize(800, 600)
            
            self.frame_principal = ctk.CTkFrame(self.janela)
            self.frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
            
            self.label_titulo = ctk.CTkLabel(
                self.frame_principal,
                text="🧹 Cleanup Manager",
                font=("Arial", 28, "bold")
            )
            self.label_titulo.pack(pady=(10, 5))
            
            self.label_subtitulo = ctk.CTkLabel(
                self.frame_principal,
                text="Sistema de Limpeza Automatizada para SSD e Bibliotecas Python",
                font=("Arial", 14)
            )
            self.label_subtitulo.pack(pady=(0, 15))
            
            # Status
            self.frame_status = ctk.CTkFrame(self.frame_principal)
            self.frame_status.pack(fill="x", padx=10, pady=10)
            
            status_admin = "✅ Administrador" if self.is_admin else "⚠️ Sem privilégios"
            cor_admin = "#00ff00" if self.is_admin else "#ffaa00"
            self.label_admin = ctk.CTkLabel(
                self.frame_status,
                text=f"🔒 {status_admin}",
                text_color=cor_admin,
                font=("Arial", 12)
            )
            self.label_admin.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            status_venv = "✅ Ativo" if self.esta_em_venv else "❌ Inativo"
            cor_venv = "#00ff00" if self.esta_em_venv else "#ff4444"
            self.label_venv = ctk.CTkLabel(
                self.frame_status,
                text=f"🐍 Venv: {status_venv}",
                text_color=cor_venv,
                font=("Arial", 12)
            )
            self.label_venv.grid(row=0, column=1, padx=10, pady=5, sticky="w")
            
            self.label_espaco = ctk.CTkLabel(
                self.frame_status,
                text="💾 Espaço liberado: 0.0 MB",
                font=("Arial", 12),
                text_color="#00aaff"
            )
            self.label_espaco.grid(row=0, column=2, padx=10, pady=5, sticky="w")
            
            self.frame_status.grid_columnconfigure(3, weight=1)
            
            # Botões
            self.frame_botoes = ctk.CTkFrame(self.frame_principal)
            self.frame_botoes.pack(fill="x", padx=10, pady=10)
            
            self.btn_limpar = ctk.CTkButton(
                self.frame_botoes,
                text="🚀 Iniciar Limpeza Completa",
                command=self.limpeza_completa,
                font=("Arial", 14, "bold"),
                height=45,
                fg_color="#2e7d32",
                hover_color="#1b5e20"
            )
            self.btn_limpar.grid(row=0, column=0, columnspan=6, padx=5, pady=5, sticky="ew")
            
            botoes = [
                ("🗑️ Temporários", self.limpar_arquivos_temporarios),
                ("🧹 Caches", self.limpar_cache_windows),
                ("🗑️ Lixeira", self.esvaziar_lixeira),
                ("🐍 Pip Cache", self.limpar_cache_pip),
                ("📦 Remover Pacotes", self.remover_pacotes_nao_usados),
                ("📥 Downloads", self.limpar_downloads),
            ]
            
            for i, (texto, comando) in enumerate(botoes):
                btn = ctk.CTkButton(
                    self.frame_botoes,
                    text=texto,
                    command=comando,
                    font=("Arial", 12),
                    height=35,
                    fg_color="#1a237e",
                    hover_color="#283593"
                )
                btn.grid(row=1, column=i, padx=3, pady=5, sticky="ew")
            
            for i in range(6):
                self.frame_botoes.grid_columnconfigure(i, weight=1)
            
            # Progress bar
            self.progress_bar = ctk.CTkProgressBar(self.frame_principal)
            self.progress_bar.pack(fill="x", padx=10, pady=10)
            self.progress_bar.set(0)
            
            # Log
            self.label_log = ctk.CTkLabel(
                self.frame_principal,
                text="📋 Log de Execução",
                font=("Arial", 14, "bold")
            )
            self.label_log.pack(pady=(10, 5))
            
            self.log_text = scrolledtext.ScrolledText(
                self.frame_principal,
                wrap="word",
                font=("Consolas", 10),
                bg="#1e1e1e",
                fg="#d4d4d4",
                height=15
            )
            self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            # Rodapé
            self.frame_rodape = ctk.CTkFrame(self.frame_principal)
            self.frame_rodape.pack(fill="x", padx=10, pady=(0, 10))
            
            self.btn_config = ctk.CTkButton(
                self.frame_rodape,
                text="⚙️ Configurações",
                command=self.abrir_configuracoes,
                font=("Arial", 12),
                width=120,
                height=30,
                fg_color="#37474f",
                hover_color="#455a64"
            )
            self.btn_config.pack(side="right", padx=10)
            
            # Mensagem inicial
            self.log("🚀 Cleanup Manager iniciado!", "INFO")
            self.log(f"Sistema: {self.sistema}", "INFO")
            self.log(f"Administrador: {'Sim' if self.is_admin else 'Não'}", "INFO")
            self.log(f"Venv ativo: {'Sim' if self.esta_em_venv else 'Não'}", "INFO")
            self.log("=" * 50, "INFO")
            self.log("Pronto! Clique em 'Iniciar Limpeza Completa'", "INFO")
            
            self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
            self.janela.mainloop()
        
        def abrir_configuracoes(self):
            janela_config = ctk.CTkToplevel(self.janela)
            janela_config.title("⚙️ Configurações")
            janela_config.geometry("500x500")
            janela_config.resizable(False, False)
            janela_config.grab_set()
            
            frame = ctk.CTkFrame(janela_config)
            frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(
                frame,
                text="⚙️ Configurações",
                font=("Arial", 20, "bold")
            ).pack(pady=(0, 20))
            
            opcoes = [
                ("modo_agressivo", "🔨 Modo Agressivo", self.config.get('modo_agressivo', False)),
                ("limpar_cache_pip", "🧹 Limpar cache do pip", self.config.get('limpar_cache_pip', True)),
                ("remover_pycache", "🗑️ Remover __pycache__", self.config.get('remover_pycache', True)),
                ("remover_arquivos_temp", "🗑️ Remover arquivos temporários", self.config.get('remover_arquivos_temp', True)),
                ("esvaziar_lixeira", "🗑️ Esvaziar lixeira", self.config.get('esvaziar_lixeira', True)),
                ("remover_pacotes_nao_usados", "📦 Remover pacotes não usados", self.config.get('remover_pacotes_nao_usados', True)),
                ("limpar_downloads", "📥 Limpar Downloads antigos", self.config.get('limpar_downloads', True)),
            ]
            
            checkboxes = {}
            for chave, texto, valor in opcoes:
                var = ctk.BooleanVar(value=valor)
                checkboxes[chave] = var
                cb = ctk.CTkCheckBox(
                    frame,
                    text=texto,
                    variable=var,
                    font=("Arial", 12)
                )
                cb.pack(anchor="w", pady=5)
            
            ctk.CTkLabel(
                frame,
                text="Dias para manter em Downloads:",
                font=("Arial", 12)
            ).pack(anchor="w", pady=(15, 5))
            
            entry_dias = ctk.CTkEntry(
                frame,
                placeholder_text="30",
                width=100
            )
            entry_dias.insert(0, str(self.config.get('dias_para_limpar', 30)))
            entry_dias.pack(anchor="w", pady=(0, 15))
            
            frame_botoes = ctk.CTkFrame(frame)
            frame_botoes.pack(fill="x", pady=20)
            
            def salvar_config():
                for chave, var in checkboxes.items():
                    self.config[chave] = var.get()
                
                try:
                    dias = int(entry_dias.get())
                    self.config['dias_para_limpar'] = dias
                except:
                    pass
                
                self._salvar_config()
                messagebox.showinfo("Sucesso", "✅ Configurações salvas com sucesso!")
                janela_config.destroy()
            
            ctk.CTkButton(
                frame_botoes,
                text="💾 Salvar",
                command=salvar_config,
                font=("Arial", 12),
                height=35,
                fg_color="#2e7d32",
                hover_color="#1b5e20"
            ).pack(side="left", padx=5, expand=True, fill="x")
            
            ctk.CTkButton(
                frame_botoes,
                text="❌ Cancelar",
                command=janela_config.destroy,
                font=("Arial", 12),
                height=35,
                fg_color="#c62828",
                hover_color="#b71c1c"
            ).pack(side="right", padx=5, expand=True, fill="x")
        
        def _fechar(self):
            if self.limpando:
                if not messagebox.askyesno("Atenção", "Uma limpeza está em andamento. Deseja sair mesmo assim?"):
                    return
            self.janela.destroy()
            sys.exit(0)
    
    # ============================================
    # RODA O PROGRAMA
    # ============================================
    
    try:
        app = CleanupManagerGUI()
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        input("Pressione Enter para sair...")

# ============================================
# PONTO DE ENTRADA
# ============================================

if __name__ == "__main__":
    main()