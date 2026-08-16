#!/usr/bin/env python3
"""
Sistema de Limpeza Automatizada - SSD e Bibliotecas Python
Autor: Assistente IA
Versão: 1.0
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
    
    def _log(self, mensagem, tipo="INFO"):
        """Registra mensagens no log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{tipo}] {mensagem}"
        print(log_msg)
        
        with open(self.log_arquivo, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    
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
            diretorio_base = os.getcwd()
        
        self._log(f"🔍 Procurando ambientes virtuais em: {diretorio_base}", "INFO")
        
        venvs = []
        for root, dirs, files in os.walk(diretorio_base):
            # Pula diretórios de sistema e muito grandes
            if 'node_modules' in root or '.git' in root:
                continue
            
            if '.venv' in dirs:
                venv_path = os.path.join(root, '.venv')
                # Verifica se é realmente um ambiente virtual
                if self.is_windows:
                    python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
                    pip_exe = os.path.join(venv_path, 'Scripts', 'pip.exe')
                else:
                    python_exe = os.path.join(venv_path, 'bin', 'python')
                    pip_exe = os.path.join(venv_path, 'bin', 'pip')
                
                if os.path.exists(python_exe) or os.path.exists(pip_exe):
                    # Tenta obter informações do ambiente
                    info = self._obter_info_venv(venv_path)
                    venvs.append({
                        'caminho': venv_path,
                        'projeto': os.path.basename(root),
                        'python': python_exe if os.path.exists(python_exe) else None,
                        'pip': pip_exe if os.path.exists(pip_exe) else None,
                        'info': info
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
            if self.is_windows:
                python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
            else:
                python_exe = os.path.join(venv_path, 'bin', 'python')
            
            if os.path.exists(python_exe):
                stdout, _, _ = self._executar_comando(f'"{python_exe}" --version')
                if stdout:
                    info['python_version'] = stdout.strip()
            
            # Conta pacotes instalados
            if self.is_windows:
                pip_exe = os.path.join(venv_path, 'Scripts', 'pip.exe')
            else:
                pip_exe = os.path.join(venv_path, 'bin', 'pip')
            
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
    
    def limpar_venv(self, venv_info):
        """Limpa um ambiente virtual específico."""
        venv_path = venv_info['caminho']
        projeto = venv_info['projeto']
        
        self._log(f"\n📁 Limpando ambiente: {projeto} ({venv_path})", "INFO")
        print(f"  🐍 Python: {venv_info['info']['python_version']}")
        print(f"  📦 Pacotes: {venv_info['info']['pacotes_instalados']}")
        print(f"  💾 Tamanho: {venv_info['info']['tamanho']} MB")
        print(f"  📅 Criado em: {venv_info['info']['data_criacao']}")
        
        # Verifica se o pip existe
        if not venv_info['pip'] or not os.path.exists(venv_info['pip']):
            self._log("❌ Pip não encontrado neste ambiente!", "ERRO")
            return False
        
        # 1. Listar pacotes instalados
        self._log("  📋 Listando pacotes instalados...", "INFO")
        stdout, stderr, code = self._executar_comando(f'"{venv_info["pip"]}" list --format=json')
        if stdout:
            try:
                pacotes = json.loads(stdout)
                print(f"\n  📦 Pacotes instalados ({len(pacotes)}):")
                for pacote in pacotes[:10]:  # Mostra apenas os 10 primeiros
                    print(f"    - {pacote['name']} {pacote['version']}")
                if len(pacotes) > 10:
                    print(f"    ... e mais {len(pacotes) - 10} pacotes")
            except:
                pass
        
        # 2. Limpar cache do pip
        self._log("  🧹 Limpando cache do pip...", "INFO")
        self._executar_comando(f'"{venv_info["pip"]}" cache purge', capturar_saida=False)
        
        # 3. Remover arquivos __pycache__
        self._log("  🗑️ Removendo arquivos __pycache__...", "INFO")
        pycache_count = 0
        for pycache in Path(venv_path).rglob('__pycache__'):
            try:
                shutil.rmtree(pycache)
                pycache_count += 1
            except:
                pass
        print(f"    Removidos {pycache_count} diretórios __pycache__")
        
        # 4. Verificar dependências órfãs
        self._log("  🔍 Verificando dependências órfãs...", "INFO")
        
        # Tenta usar pip-autoremove
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
            pacotes_removiveis = [p for p in pacotes_instalados if p not in self.pacotes_protegidos]
            
            if pacotes_removiveis:
                print(f"\n  📋 Pacotes que podem ser removidos ({len(pacotes_removiveis)}):")
                for pacote in pacotes_removiveis[:20]:
                    print(f"    - {pacote}")
                if len(pacotes_removiveis) > 20:
                    print(f"    ... e mais {len(pacotes_removiveis) - 20} pacotes")
                
                # Pergunta se quer remover algum
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
        
        self._log(f"  ✅ Limpeza do ambiente '{projeto}' concluída!", "SUCESSO")
        return True
    
    def limpar_todos_venvs(self):
        """Limpa todos os ambientes virtuais encontrados."""
        if not self.venvs_encontrados:
            self._log("❌ Nenhum ambiente virtual encontrado para limpar.", "ERRO")
            return
        
        print(f"\n⚠️ Serão limpos {len(self.venvs_encontrados)} ambientes virtuais:")
        for venv in self.venvs_encontrados:
            print(f"  - {venv['projeto']} ({venv['info']['tamanho']} MB)")
        
        confirmacao = input("\n⚠️ Continuar? (s/N): ")
        if confirmacao.lower() != 's':
            return
        
        for venv in self.venvs_encontrados:
            self.limpar_venv(venv)
        
        self._log("✅ TODOS OS AMBIENTES FORAM LIMPOS!", "SUCESSO")
    
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
                    print(f"  {venv['projeto']}: {tamanho} MB")
                
                print(f"\n  Total ocupado por .venv: {total_venv:.1f} MB ({total_venv/1024:.2f} GB)")
            else:
                print("  Nenhum ambiente virtual encontrado.")
        
        except Exception as e:
            self._log(f"Erro na análise de espaço: {e}", "ERRO")
    
    # ========== FUNÇÃO PRINCIPAL ==========
    
    def menu_principal(self):
        """Exibe o menu principal e gerencia a interação."""
        print("\n" + "=" * 60)
        print("🚀 SISTEMA DE LIMPEZA AUTOMATIZADA v1.0")
        print("=" * 60)
        
        # Verifica se é administrador
        if not self.is_admin:
            print("\n⚠️ ATENÇÃO: Execute como Administrador para limpeza completa do sistema!")
        
        while True:
            print("\n📋 MENU PRINCIPAL")
            print("1. 🔍 Encontrar ambientes virtuais (.venv)")
            print("2. 🧹 Limpar ambiente virtual específico")
            print("3. 🚀 Limpar TODOS os ambientes virtuais")
            print("4. 💻 Limpar sistema (SSD - Temporários, Cache, etc)")
            print("5. 📊 Análise de espaço em disco")
            print("6. 🗑️ Limpar lixeira do sistema")
            print("0. ❌ Sair")
            
            opcao = input("\n👉 Escolha uma opção: ").strip()
            
            if opcao == "1":
                self.venvs_encontrados = self.encontrar_venvs()
                if self.venvs_encontrados:
                    print(f"\n✅ Encontrados {len(self.venvs_encontrados)} ambientes virtuais:")
                    for i, venv in enumerate(self.venvs_encontrados, 1):
                        print(f"  {i}. {venv['projeto']} - Python: {venv['info']['python_version']} - {venv['info']['tamanho']} MB")
                else:
                    print("❌ Nenhum ambiente virtual (.venv) encontrado.")
            
            elif opcao == "2":
                if not self.venvs_encontrados:
                    print("⚠️ Primeiro execute a opção 1 para encontrar os ambientes.")
                    continue
                
                print("\n📁 Ambientes virtuais disponíveis:")
                for i, venv in enumerate(self.venvs_encontrados, 1):
                    print(f"  {i}. {venv['projeto']} ({venv['info']['pacotes_instalados']} pacotes, {venv['info']['tamanho']} MB)")
                
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
                self.limpar_sistema()
            
            elif opcao == "5":
                self.analisar_espaco()
            
            elif opcao == "6":
                print("\n🗑️ Esvaziando lixeira...")
                if self.is_windows:
                    self._executar_comando('rd /s /q C:\\$Recycle.bin', capturar_saida=False)
                    print("✅ Lixeira esvaziada!")
                else:
                    print("⚠️ Função disponível apenas no Windows.")
            
            elif opcao == "0":
                print("\n👋 Saindo... Até logo!")
                break
            
            else:
                print("❌ Opção inválida. Tente novamente.")

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