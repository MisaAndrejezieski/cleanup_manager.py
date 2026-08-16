#!/usr/bin/env python3
"""
Sistema de Limpeza Automatizada - SSD e Bibliotecas Python
Com suporte a auto-gerenciamento do .venv local
Versão: 2.0
"""

import glob
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class CleanupManager:
    def __init__(self):
        self.sistema = platform.system()
        self.is_windows = self.sistema == 'Windows'
        self.is_admin = self._verificar_admin()
        self.venvs_encontrados = []
        self.log_arquivo = "cleanup_log.txt"
        self.pacotes_protegidos = ['pip', 'setuptools', 'wheel', 'virtualenv', 'pipenv', 'poetry']
        
        # Detecta o diretório do projeto atual
        self.diretorio_projeto = os.path.dirname(os.path.abspath(__file__))
        self.venv_local = os.path.join(self.diretorio_projeto, '.venv')
        self.esta_em_venv = self._verificar_venv_ativo()
        
        # Arquivo de configuração
        self.config_file = os.path.join(self.diretorio_projeto, 'cleanup_config.json')
        self.config = self._carregar_config()
        
    def _verificar_admin(self):
        """Verifica se o programa está rodando com privilégios de administrador."""
        if self.is_windows:
            try:
                return os.getuid() == 0
            except AttributeError:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    
    def _verificar_venv_ativo(self):
        """Verifica se o programa está rodando dentro de um ambiente virtual."""
        # Verifica se está em um venv
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if in_venv:
            self._log(f"🔍 Programa rodando no ambiente virtual: {sys.prefix}", "INFO")
        
        return in_venv
    
    def _carregar_config(self):
        """Carrega ou cria arquivo de configuração."""
        config_padrao = {
            'auto_limpar_cache': True,
            'remover_pycache': True,
            'proteger_pacotes': self.pacotes_protegidos,
            'pasta_ignoradas': ['node_modules', '.git', '__pycache__', '.pytest_cache'],
            'ultima_limpeza': None,
            'versao': '2.0'
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Atualiza com novas chaves se necessário
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
        """Salva o arquivo de configuração."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"Erro ao salvar configuração: {e}", "ERRO")
    
    def _log(self, mensagem, tipo="INFO"):
        """Registra mensagens no log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{tipo}] {mensagem}"
        print(log_msg)
        
        try:
            with open(self.log_arquivo, 'a', encoding='utf-8') as f:
                f.write(log_msg + '\n')
        except:
            pass
    
    def _executar_comando(self, comando, shell=True, capturar_saida=True):
        """Executa um comando no sistema com tratamento de erro."""
        try:
            if capturar_saida:
                resultado = subprocess.run(
                    comando, 
                    shell=shell, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8'
                )
                return resultado.stdout, resultado.stderr, resultado.returncode
            else:
                subprocess.run(comando, shell=shell, check=False)
                return None, None, 0
        except Exception as e:
            self._log(f"Erro ao executar comando: {e}", "ERRO")
            return None, str(e), 1
    
    def _obter_pip_venv(self, venv_path):
        """Obtém o caminho do pip em um ambiente virtual."""
        if self.is_windows:
            pip_exe = os.path.join(venv_path, 'Scripts', 'pip.exe')
            python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:
            pip_exe = os.path.join(venv_path, 'bin', 'pip')
            python_exe = os.path.join(venv_path, 'bin', 'python')
        
        return pip_exe, python_exe
    
    # ========== FUNÇÕES DE LIMPEZA DO SISTEMA ==========
    
    def limpar_sistema(self):
        """Executa limpeza completa do sistema (SSD)."""
        self._log("🚀 INICIANDO LIMPEZA DO SISTEMA", "INFO")
        
        if not self.is_admin:
            self._log("⚠️ Algumas operações precisam de privilégios de administrador!", "AVISO")
        
        # 1. Limpeza de Disco do Windows
        if self.is_windows:
            self._log("📀 Executando Limpeza de Disco do Windows...", "INFO")
            stdout, stderr, code = self._executar_comando("cleanmgr /sagerun")
            if code != 0:
                self._log("⚠️ Limpeza de Disco não configurada. Execute 'cleanmgr' primeiro para configurar.", "AVISO")
        
        # 2. Arquivos temporários
        self._log("🗑️ Removendo arquivos temporários...", "INFO")
        
        # Temp do usuário
        if self.is_windows:
            temp_dir = os.environ.get('TEMP', '')
            if temp_dir:
                self._executar_comando(f'del /f /s /q "{temp_dir}\\*.*"', capturar_saida=False)
        
        # Windows Temp
        if self.is_windows:
            self._executar_comando('del /f /s /q "C:\\Windows\\Temp\\*.*"', capturar_saida=False)
        
        # 3. Lixeira
        self._log("🗑️ Esvaziando Lixeira...", "INFO")
        if self.is_windows:
            self._executar_comando('rd /s /q C:\\$Recycle.bin', capturar_saida=False)
        
        # 4. Pré-cache
        self._log("🧹 Limpando cache de pré-carregamento...", "INFO")
        if self.is_windows:
            self._executar_comando('del /f /s /q "C:\\Windows\\Prefetch\\*.*"', capturar_saida=False)
        
        # 5. Sombras de backup (opcional)
        resposta = input("\n⚠️ Remover todos os pontos de restauração do Windows? (s/N): ")
        if resposta.lower() == 's':
            self._log("💾 Removendo pontos de restauração...", "INFO")
            self._executar_comando('vssadmin delete shadows /all /quiet', capturar_saida=False)
        
        self._log("✅ LIMPEZA DO SISTEMA CONCLUÍDA!", "SUCESSO")
    
    # ========== FUNÇÕES DE GERENCIAMENTO DE VENV ==========
    
    def encontrar_venvs(self, diretorio_base=None):
        """Encontra todos os ambientes virtuais (.venv) no diretório e subdiretórios."""
        if diretorio_base is None:
            diretorio_base = self.diretorio_projeto
        
        self._log(f"🔍 Procurando ambientes virtuais em: {diretorio_base}", "INFO")
        
        venvs = []
        
        # Primeiro, verifica o .venv local do projeto
        if os.path.exists(self.venv_local):
            pip_exe, python_exe = self._obter_pip_venv(self.venv_local)
            if os.path.exists(python_exe) or os.path.exists(pip_exe):
                info = self._obter_info_venv(self.venv_local)
                venvs.append({
                    'caminho': self.venv_local,
                    'projeto': f"🔵 {os.path.basename(self.diretorio_projeto)} (LOCAL - ATUAL)",
                    'python': python_exe if os.path.exists(python_exe) else None,
                    'pip': pip_exe if os.path.exists(pip_exe) else None,
                    'info': info,
                    'is_local': True
                })
        
        # Depois, procura por outros .venv em subdiretórios
        for root, dirs, files in os.walk(diretorio_base):
            # Pula diretórios que devem ser ignorados
            if any(ignorado in root for ignorado in self.config['pasta_ignoradas']):
                continue
            
            # Pula o .venv local já encontrado
            if root == self.diretorio_projeto:
                continue
                
            if '.venv' in dirs:
                venv_path = os.path.join(root, '.venv')
                pip_exe, python_exe = self._obter_pip_venv(venv_path)
                
                if os.path.exists(python_exe) or os.path.exists(pip_exe):
                    info = self._obter_info_venv(venv_path)
                    venvs.append({
                        'caminho': venv_path,
                        'projeto': os.path.basename(root),
                        'python': python_exe if os.path.exists(python_exe) else None,
                        'pip': pip_exe if os.path.exists(pip_exe) else None,
                        'info': info,
                        'is_local': False
                    })
        
        self.venvs_encontrados = venvs
        return venvs
    
    def _obter_info_venv(self, venv_path):
        """Obtém informações sobre um ambiente virtual."""
        info = {
            'python_version': 'Desconhecida',
            'pacotes_instalados': 0,
            'tamanho': 0,
            'data_criacao': 'Desconhecida'
        }
        
        try:
            # Tenta obter versão do Python
            pip_exe, python_exe = self._obter_pip_venv(venv_path)
            
            if os.path.exists(python_exe):
                stdout, _, _ = self._executar_comando(f'"{python_exe}" --version')
                if stdout:
                    info['python_version'] = stdout.strip()
            
            # Conta pacotes instalados
            if os.path.exists(pip_exe):
                stdout, _, _ = self._executar_comando(f'"{pip_exe}" list --format=json')
                if stdout:
                    try:
                        pacotes = json.loads(stdout)
                        info['pacotes_instalados'] = len(pacotes)
                    except:
                        pass
            
            # Calcula tamanho
            info['tamanho'] = self._calcular_tamanho_pasta(venv_path)
            
            # Data de criação
            if os.path.exists(venv_path):
                info['data_criacao'] = datetime.fromtimestamp(
                    os.path.getctime(venv_path)
                ).strftime("%Y-%m-%d %H:%M:%S")
        
        except Exception as e:
            self._log(f"Erro ao obter info do venv: {e}", "ERRO")
        
        return info
    
    def _calcular_tamanho_pasta(self, pasta):
        """Calcula o tamanho de uma pasta em MB."""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(pasta):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
            return round(total / (1024 * 1024), 2)  # MB
        except:
            return 0
    
    def limpar_venv(self, venv_info, auto_mode=False):
        """Limpa um ambiente virtual específico."""
        venv_path = venv_info['caminho']
        projeto = venv_info['projeto']
        is_local = venv_info.get('is_local', False)
        
        if is_local:
            print("\n" + "="*60)
            print("🔵 GERENCIANDO AMBIENTE VIRTUAL LOCAL (ATUAL)")
            print("="*60)
        
        self._log(f"\n📁 Limpando ambiente: {projeto} ({venv_path})", "INFO")
        print(f"  🐍 Python: {venv_info['info']['python_version']}")
        print(f"  📦 Pacotes: {venv_info['info']['pacotes_instalados']}")
        print(f"  💾 Tamanho: {venv_info['info']['tamanho']} MB")
        print(f"  📅 Criado em: {venv_info['info']['data_criacao']}")
        
        if is_local:
            print(f"  🔄 Este é o ambiente virtual ATUAL do programa!")
        
        # Verifica se o pip existe
        if not venv_info['pip'] or not os.path.exists(venv_info['pip']):
            self._log("❌ Pip não encontrado neste ambiente!", "ERRO")
            return False
        
        # 1. Listar pacotes instalados
        if not auto_mode:
            self._log("  📋 Listando pacotes instalados...", "INFO")
            stdout, stderr, code = self._executar_comando(f'"{venv_info["pip"]}" list --format=json')
            if stdout:
                try:
                    pacotes = json.loads(stdout)
                    print(f"\n  📦 Pacotes instalados ({len(pacotes)}):")
                    # Mostra pacotes em colunas
                    for i, pacote in enumerate(pacotes):
                        print(f"    {pacote['name']} {pacote['version']}")
                        if i >= 20 and len(pacotes) > 20:
                            print(f"    ... e mais {len(pacotes) - 20} pacotes")
                            break
                except:
                    pass
        
        # 2. Limpar cache do pip
        if self.config.get('auto_limpar_cache', True):
            self._log("  🧹 Limpando cache do pip...", "INFO")
            self._executar_comando(f'"{venv_info["pip"]}" cache purge', capturar_saida=False)
        
        # 3. Remover arquivos __pycache__
        if self.config.get('remover_pycache', True):
            self._log("  🗑️ Removendo arquivos __pycache__...", "INFO")
            pycache_count = 0
            for pycache in Path(venv_path).rglob('__pycache__'):
                try:
                    shutil.rmtree(pycache)
                    pycache_count += 1
                except:
                    pass
            print(f"    Removidos {pycache_count} diretórios __pycache__")
        
        # 4. Verificar dependências órfãs (apenas se não for auto_mode)
        if not auto_mode:
            self._log("  🔍 Verificando dependências órfãs...", "INFO")
            
            stdout, stderr, code = self._executar_comando(f'"{venv_info["pip"]}" list')
            if stdout:
                linhas = stdout.strip().split('\n')[2:]  # Pula cabeçalho
                pacotes_instalados = []
                for linha in linhas:
                    if linha.strip():
                        partes = linha.split()
                        if partes:
                            pacotes_instalados.append(partes[0])
                
                # Mostra pacotes que podem ser removidos (exceto os protegidos)
                pacotes_protegidos = self.config.get('proteger_pacotes', self.pacotes_protegidos)
                pacotes_removiveis = [p for p in pacotes_instalados if p not in pacotes_protegidos]
                
                if pacotes_removiveis:
                    print(f"\n  📋 Pacotes que podem ser removidos ({len(pacotes_removiveis)}):")
                    for pacote in pacotes_removiveis[:20]:
                        print(f"    - {pacote}")
                    if len(pacotes_removiveis) > 20:
                        print(f"    ... e mais {len(pacotes_removiveis) - 20} pacotes")
                    
                    # Pergunta se quer remover algum
                    if not auto_mode:
                        resposta = input("\n  🤔 Deseja remover algum pacote específico? (s/N): ")
                        if resposta.lower() == 's':
                            pacote_remover = input("  Digite o nome do pacote a remover (ou 'todos'): ").strip()
                            
                            if pacote_remover.lower() == 'todos':
                                confirmacao = input(f"  ⚠️ Remover TODOS os {len(pacotes_removiveis)} pacotes? (s/N): ")
                                if confirmacao.lower() == 's':
                                    for p in pacotes_removiveis:
                                        self._log(f"    Removendo {p}...", "INFO")
                                        self._executar_comando(
                                            f'"{venv_info["pip"]}" uninstall {p} -y', 
                                            capturar_saida=False
                                        )
                            elif pacote_remover in pacotes_removiveis:
                                confirmacao = input(f"  ⚠️ Remover '{pacote_remover}'? (s/N): ")
                                if confirmacao.lower() == 's':
                                    self._executar_comando(
                                        f'"{venv_info["pip"]}" uninstall {pacote_remover} -y',
                                        capturar_saida=False
                                    )
                                    self._log(f"  ✅ {pacote_remover} removido!", "SUCESSO")
                            else:
                                print(f"  ❌ Pacote '{pacote_remover}' não encontrado ou está protegido.")
                else:
                    print("  ✅ Nenhum pacote removível encontrado!")
        
        # Atualiza data da última limpeza
        if is_local:
            self.config['ultima_limpeza'] = datetime.now().isoformat()
            self._salvar_config()
        
        self._log(f"  ✅ Limpeza do ambiente '{projeto}' concluída!", "SUCESSO")
        return True
    
    def limpar_todos_venvs(self, auto_mode=False):
        """Limpa todos os ambientes virtuais encontrados."""
        if not self.venvs_encontrados:
            self._log("❌ Nenhum ambiente virtual encontrado para limpar.", "ERRO")
            return
        
        # Separa o local dos outros
        locais = [v for v in self.venvs_encontrados if v.get('is_local', False)]
        outros = [v for v in self.venvs_encontrados if not v.get('is_local', False)]
        
        print(f"\n⚠️ Serão limpos {len(self.venvs_encontrados)} ambientes virtuais:")
        if locais:
            print("  🔵 LOCAL (ATUAL):")
            for venv in locais:
                print(f"    - {venv['projeto']} ({venv['info']['tamanho']} MB)")
        if outros:
            print("  📁 OUTROS PROJETOS:")
            for venv in outros:
                print(f"    - {venv['projeto']} ({venv['info']['tamanho']} MB)")
        
        if not auto_mode:
            confirmacao = input("\n⚠️ Continuar? (s/N): ")
            if confirmacao.lower() != 's':
                return
        
        # Primeiro limpa os outros, depois o local
        for venv in outros:
            self.limpar_venv(venv, auto_mode)
        
        for venv in locais:
            self.limpar_venv(venv, auto_mode)
        
        self._log("✅ TODOS OS AMBIENTES FORAM LIMPOS!", "SUCESSO")
    
    def limpar_venv_local(self):
        """Limpa especificamente o ambiente virtual local."""
        if not os.path.exists(self.venv_local):
            self._log("❌ Ambiente virtual local não encontrado!", "ERRO")
            return
        
        pip_exe, python_exe = self._obter_pip_venv(self.venv_local)
        if not os.path.exists(pip_exe):
            self._log("❌ Pip não encontrado no ambiente local!", "ERRO")
            return
        
        info = self._obter_info_venv(self.venv_local)
        venv_info = {
            'caminho': self.venv_local,
            'projeto': f"🔵 {os.path.basename(self.diretorio_projeto)} (LOCAL - ATUAL)",
            'python': python_exe,
            'pip': pip_exe,
            'info': info,
            'is_local': True
        }
        
        self.limpar_venv(venv_info)
    
    # ========== FUNÇÕES DE ANÁLISE ==========
    
    def analisar_espaco(self):
        """Analisa e mostra o espaço em disco."""
        try:
            if self.is_windows:
                total, usado, livre = shutil.disk_usage("C:")
            else:
                total, usado, livre = shutil.disk_usage("/")
            
            print("\n💾 ANÁLISE DE ESPAÇO EM DISCO")
            print("=" * 50)
            print(f"  Total:  {total // (2**30)} GB")
            print(f"  Usado:  {usado // (2**30)} GB")
            print(f"  Livre:  {livre // (2**30)} GB")
            print(f"  Uso:    {usado/total*100:.1f}%")
            
            # Análise de espaço em projetos
            print("\n📁 PROJETOS E AMBIENTES VIRTUAIS")
            print("=" * 50)
            
            if self.venvs_encontrados:
                total_venv = 0
                for venv in self.venvs_encontrados:
                    tamanho = venv['info']['tamanho']
                    total_venv += tamanho
                    local = "🔵 LOCAL" if venv.get('is_local', False) else "   "
                    print(f"  {local} {venv['projeto']}: {tamanho} MB")
                
                print(f"\n  Total ocupado por .venv: {total_venv:.1f} MB ({total_venv/1024:.2f} GB)")
            else:
                print("  Nenhum ambiente virtual encontrado.")
        
        except Exception as e:
            self._log(f"Erro na análise de espaço: {e}", "ERRO")
    
    def mostrar_status_venv_local(self):
        """Mostra o status do ambiente virtual local."""
        print("\n🔵 STATUS DO AMBIENTE VIRTUAL LOCAL")
        print("=" * 50)
        
        if not os.path.exists(self.venv_local):
            print("❌ Ambiente virtual local não encontrado!")
            print(f"   Caminho esperado: {self.venv_local}")
            return
        
        pip_exe, python_exe = self._obter_pip_venv(self.venv_local)
        
        print(f"  📁 Caminho: {self.venv_local}")
        print(f"  🐍 Python: {os.path.exists(python_exe)}")
        print(f"  📦 Pip: {os.path.exists(pip_exe)}")
        print(f"  🔄 Ativo: {'Sim' if self.esta_em_venv else 'Não'}")
        
        if self.esta_em_venv:
            print(f"  📍 Python atual: {sys.executable}")
        
        # Mostra última limpeza
        if self.config.get('ultima_limpeza'):
            ultima = datetime.fromisoformat(self.config['ultima_limpeza'])
            print(f"  🧹 Última limpeza: {ultima.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("  🧹 Última limpeza: Nunca realizada")
    
    # ========== FUNÇÃO PRINCIPAL ==========
    
    def menu_principal(self):
        """Exibe o menu principal e gerencia a interação."""
        print("\n" + "=" * 60)
        print("🚀 SISTEMA DE LIMPEZA AUTOMATIZADA v2.0")
        print("=" * 60)
        
        # Verifica se está em um venv
        if self.esta_em_venv:
            print("\n✅ Programa rodando em ambiente virtual")
            print(f"   📍 {sys.prefix}")
        else:
            print("\n⚠️ Programa NÃO está rodando em ambiente virtual")
            print("   Recomendado: ative o .venv antes de executar")
        
        # Verifica se é administrador
        if not self.is_admin:
            print("\n⚠️ ATENÇÃO: Execute como Administrador para limpeza completa do sistema!")
        
        # Mostra status do .venv local
        self.mostrar_status_venv_local()
        
        while True:
            print("\n📋 MENU PRINCIPAL")
            print("1. 🔍 Encontrar ambientes virtuais (.venv)")
            print("2. 🧹 Limpar ambiente virtual específico")
            print("3. 🚀 Limpar TODOS os ambientes virtuais")
            print("4. 🔵 Limpar AMBIENTE VIRTUAL LOCAL (ATUAL)")
            print("5. 💻 Limpar sistema (SSD - Temporários, Cache, etc)")
            print("6. 📊 Análise de espaço em disco")
            print("7. 🗑️ Limpar lixeira do sistema")
            print("8. ⚙️ Configurações")
            print("0. ❌ Sair")
            
            opcao = input("\n👉 Escolha uma opção: ").strip()
            
            if opcao == "1":
                self.venvs_encontrados = self.encontrar_venvs()
                if self.venvs_encontrados:
                    print(f"\n✅ Encontrados {len(self.venvs_encontrados)} ambientes virtuais:")
                    for i, venv in enumerate(self.venvs_encontrados, 1):
                        local = "🔵 LOCAL" if venv.get('is_local', False) else "   "
                        print(f"  {i}. {local} {venv['projeto']} - {venv['info']['pacotes_instalados']} pacotes, {venv['info']['tamanho']} MB")
                else:
                    print("❌ Nenhum ambiente virtual (.venv) encontrado.")
            
            elif opcao == "2":
                if not self.venvs_encontrados:
                    print("⚠️ Primeiro execute a opção 1 para encontrar os ambientes.")
                    continue
                
                print("\n📁 Ambientes virtuais disponíveis:")
                for i, venv in enumerate(self.venvs_encontrados, 1):
                    local = "🔵 LOCAL" if venv.get('is_local', False) else "   "
                    print(f"  {i}. {local} {venv['projeto']} ({venv['info']['pacotes_instalados']} pacotes, {venv['info']['tamanho']} MB)")
                
                try:
                    escolha = int(input("\nEscolha o número do ambiente a limpar: ")) - 1
                    if 0 <= escolha < len(self.venvs_encontrados):
                        self.limpar_venv(self.venvs_encontrados[escolha])
                    else:
                        print("❌ Opção inválida.")
                except ValueError:
                    print("❌ Digite um número válido.")
            
            elif opcao == "3":
                if not self.venvs_encontrados:
                    print("⚠️ Primeiro execute a opção 1 para encontrar os ambientes.")
                    continue
                self.limpar_todos_venvs()
            
            elif opcao == "4":
                self.limpar_venv_local()
            
            elif opcao == "5":
                self.limpar_sistema()
            
            elif opcao == "6":
                self.analisar_espaco()
            
            elif opcao == "7":
                print("\n🗑️ Esvaziando lixeira...")
                if self.is_windows:
                    self._executar_comando('rd /s /q C:\\$Recycle.bin', capturar_saida=False)
                    print("✅ Lixeira esvaziada!")
                else:
                    print("⚠️ Função disponível apenas no Windows.")
            
            elif opcao == "8":
                self.menu_configuracoes()
            
            elif opcao == "0":
                print("\n👋 Saindo... Até logo!")
                break
            
            else:
                print("❌ Opção inválida. Tente novamente.")
    
    def menu_configuracoes(self):
        """Menu de configurações do programa."""
        print("\n⚙️ CONFIGURAÇÕES")
        print("=" * 50)
        print(f"1. Auto-limpar cache do pip: {'✅' if self.config.get('auto_limpar_cache', True) else '❌'}")
        print(f"2. Remover __pycache__: {'✅' if self.config.get('remover_pycache', True) else '❌'}")
        print(f"3. Pacotes protegidos: {len(self.config.get('proteger_pacotes', []))} pacotes")
        print(f"4. Pastas ignoradas: {len(self.config.get('pasta_ignoradas', []))} pastas")
        print("0. Voltar")
        
        opcao = input("\n👉 Escolha uma opção: ").strip()
        
        if opcao == "1":
            self.config['auto_limpar_cache'] = not self.config.get('auto_limpar_cache', True)
            self._salvar_config()
            print("✅ Configuração atualizada!")
        elif opcao == "2":
            self.config['remover_pycache'] = not self.config.get('remover_pycache', True)
            self._salvar_config()
            print("✅ Configuração atualizada!")
        elif opcao == "3":
            print("\n📋 Pacotes protegidos atuais:")
            for p in self.config.get('proteger_pacotes', []):
                print(f"  - {p}")
            print("\n(Os pacotes protegidos NUNCA serão removidos)")
            input("Pressione Enter para continuar...")
        elif opcao == "4":
            print("\n📁 Pastas ignoradas atuais:")
            for p in self.config.get('pasta_ignoradas', []):
                print(f"  - {p}")
            print("\n(Estas pastas são ignoradas na busca por .venv)")
            input("Pressione Enter para continuar...")

# ========== PONTO DE ENTRADA ==========

def main():
    """Função principal do programa."""
    try:
        manager = CleanupManager()
        manager.menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()