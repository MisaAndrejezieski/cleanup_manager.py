#!/usr/bin/env python3
"""
Sistema de Limpeza Automatizada - Versão que REALMENTE LIMPA!
Versão: 4.0 - AÇÃO DIRETA
"""

import os
import sys
import subprocess
import shutil
import glob
from pathlib import Path
import json
from datetime import datetime
import platform
import re

class CleanupManager:
    def __init__(self):
        self.sistema = platform.system()
        self.is_windows = self.sistema == 'Windows'
        self.is_admin = self._verificar_admin()
        self.log_arquivo = "cleanup_log.txt"
        self.pacotes_protegidos = ['pip', 'setuptools', 'wheel', 'virtualenv', 'pipenv', 'poetry']
        
        self.diretorio_projeto = os.path.dirname(os.path.abspath(__file__))
        self.venv_local = os.path.join(self.diretorio_projeto, '.venv')
        self.requirements_file = os.path.join(self.diretorio_projeto, 'requirements.txt')
        self.esta_em_venv = self._verificar_venv_ativo()
        
        self.config_file = os.path.join(self.diretorio_projeto, 'cleanup_config.json')
        self.config = self._carregar_config()
        
        # Estatísticas
        self.espaco_liberado = 0
        
    def _verificar_admin(self):
        if self.is_windows:
            try:
                return os.getuid() == 0
            except AttributeError:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    
    def _verificar_venv_ativo(self):
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        if in_venv:
            self._log(f"🔍 Rodando no ambiente virtual: {sys.prefix}", "INFO")
        return in_venv
    
    def _carregar_config(self):
        config_padrao = {
            'modo_agressivo': False,
            'limpar_cache_pip': True,
            'remover_pycache': True,
            'remover_arquivos_temp': True,
            'esvaziar_lixeira': True,
            'limpar_prefetch': True,
            'remover_pontos_restauracao': False,
            'remover_pacotes_nao_usados': True,
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
            self._log(f"Erro ao salvar config: {e}", "ERRO")
    
    def _log(self, mensagem, tipo="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{tipo}] {mensagem}"
        print(log_msg)
        try:
            with open(self.log_arquivo, 'a', encoding='utf-8') as f:
                f.write(log_msg + '\n')
        except:
            pass
    
    def _executar_comando(self, comando, shell=True, capturar_saida=True):
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
    
    def _obter_tamanho_pasta(self, pasta):
        """Retorna o tamanho da pasta em MB."""
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
    
    # ========== FUNÇÕES QUE REALMENTE LIMPAM ==========
    
    def limpar_arquivos_temporarios(self):
        """LIMPA arquivos temporários do Windows."""
        print("\n🗑️ LIMPANDO ARQUIVOS TEMPORÁRIOS")
        print("=" * 50)
        
        if not self.is_windows:
            print("⚠️ Esta função é apenas para Windows")
            return
        
        locais_temp = []
        
        # Temp do usuário
        temp_user = os.environ.get('TEMP', '')
        if temp_user and os.path.exists(temp_user):
            locais_temp.append(("Temp do usuário", temp_user))
        
        # Temp do Windows
        if os.path.exists("C:\\Windows\\Temp"):
            locais_temp.append(("Temp do Windows", "C:\\Windows\\Temp"))
        
        # Temp do sistema
        if os.path.exists("C:\\Windows\\System32\\Temp"):
            locais_temp.append(("Temp do Sistema", "C:\\Windows\\System32\\Temp"))
        
        total_liberado = 0
        for nome, local in locais_temp:
            print(f"\n  📁 {nome}: {local}")
            tamanho_antes = self._obter_tamanho_pasta(local)
            print(f"    Tamanho: {tamanho_antes} MB")
            
            try:
                # Remove arquivos
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
                print(f"    ✅ Liberado: {liberado:.2f} MB")
            except Exception as e:
                print(f"    ❌ Erro: {e}")
        
        self.espaco_liberado += total_liberado
        print(f"\n  ✅ Total liberado em temporários: {total_liberado:.2f} MB")
        return total_liberado
    
    def limpar_cache_windows(self):
        """LIMPA caches do Windows."""
        print("\n🧹 LIMPANDO CACHES DO WINDOWS")
        print("=" * 50)
        
        if not self.is_windows:
            print("⚠️ Esta função é apenas para Windows")
            return
        
        caches = [
            ("Cache de pré-carregamento", "C:\\Windows\\Prefetch"),
            ("Cache de fontes", "C:\\Windows\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache"),
            ("Cache de ícones", "C:\\Users\\" + os.getlogin() + "\\AppData\\Local\\IconCache.db"),
        ]
        
        total_liberado = 0
        for nome, local in caches:
            if not os.path.exists(local):
                continue
            
            print(f"\n  📁 {nome}: {local}")
            tamanho_antes = self._obter_tamanho_pasta(local)
            print(f"    Tamanho: {tamanho_antes} MB")
            
            try:
                if os.path.isfile(local):
                    os.remove(local)
                else:
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
                print(f"    ✅ Liberado: {liberado:.2f} MB")
            except Exception as e:
                print(f"    ❌ Erro: {e}")
        
        self.espaco_liberado += total_liberado
        print(f"\n  ✅ Total liberado em caches: {total_liberado:.2f} MB")
        return total_liberado
    
    def esvaziar_lixeira(self):
        """ESVAZIA a lixeira do Windows."""
        print("\n🗑️ ESVAZIANDO LIXEIRA")
        print("=" * 50)
        
        if not self.is_windows:
            print("⚠️ Esta função é apenas para Windows")
            return
        
        try:
            # Método 1: Comando direto
            self._executar_comando('rd /s /q C:\\$Recycle.bin', capturar_saida=False)
            print("  ✅ Lixeira esvaziada (método 1)")
        except:
            try:
                # Método 2: Usando o PowerShell
                self._executar_comando('powershell -command "Clear-RecycleBin -Force"', capturar_saida=False)
                print("  ✅ Lixeira esvaziada (método 2)")
            except:
                print("  ❌ Não foi possível esvaziar a lixeira")
    
    def limpar_cache_pip_venv(self, venv_path):
        """LIMPA o cache do pip em um ambiente virtual."""
        pip_exe = os.path.join(venv_path, 'Scripts', 'pip.exe') if self.is_windows else os.path.join(venv_path, 'bin', 'pip')
        
        if not os.path.exists(pip_exe):
            print(f"  ❌ Pip não encontrado em {venv_path}")
            return 0
        
        print(f"\n  🧹 Limpando cache do pip em: {venv_path}")
        
        try:
            # Limpa cache
            self._executar_comando(f'"{pip_exe}" cache purge', capturar_saida=False)
            print("    ✅ Cache do pip limpo!")
            
            # Remove arquivos .pyc
            pycache_count = 0
            for pycache in Path(venv_path).rglob('__pycache__'):
                try:
                    shutil.rmtree(pycache)
                    pycache_count += 1
                except:
                    pass
            if pycache_count > 0:
                print(f"    ✅ Removidos {pycache_count} diretórios __pycache__")
            
            return 1
        except Exception as e:
            print(f"    ❌ Erro: {e}")
            return 0
    
    def remover_pacotes_nao_usados(self, venv_path):
        """REMOVE pacotes não usados de um ambiente virtual."""
        pip_exe = os.path.join(venv_path, 'Scripts', 'pip.exe') if self.is_windows else os.path.join(venv_path, 'bin', 'pip')
        
        if not os.path.exists(pip_exe):
            print(f"  ❌ Pip não encontrado em {venv_path}")
            return 0
        
        print(f"\n  🗑️ Removendo pacotes não usados de: {venv_path}")
        
        # Lista todos os pacotes
        stdout, _, _ = self._executar_comando(f'"{pip_exe}" list --format=json')
        if not stdout:
            print("    ❌ Não foi possível listar pacotes")
            return 0
        
        try:
            pacotes = json.loads(stdout)
            nomes_pacotes = [p['name'] for p in pacotes]
            
            # Remove pacotes que não são protegidos
            removidos = 0
            for pacote in nomes_pacotes:
                if pacote not in self.config['proteger_pacotes']:
                    # Tenta remover com dependências
                    self._executar_comando(
                        f'"{pip_exe}" uninstall {pacote} -y',
                        capturar_saida=False
                    )
                    removidos += 1
                    print(f"    ✅ Removido: {pacote}")
            
            print(f"\n  ✅ Total removido: {removidos} pacotes")
            return removidos
        except Exception as e:
            print(f"    ❌ Erro: {e}")
            return 0
    
    def remover_projetos_antigos(self):
        """REMOVE pastas de projetos antigos que você não usa mais."""
        print("\n🗑️ REMOVENDO PROJETOS ANTIGOS")
        print("=" * 50)
        print("⚠️ Esta função analisa pastas de projetos e sugere remoção")
        
        # Pasta de projetos comum
        pastas_projetos = [
            os.path.expanduser("~/Documents/Projetos"),
            os.path.expanduser("~/Desktop/Projetos"),
            os.path.expanduser("~/Documents/Projects"),
            os.path.expanduser("~/Desktop/Projects"),
        ]
        
        projetos_encontrados = []
        for pasta in pastas_projetos:
            if os.path.exists(pasta):
                for item in os.listdir(pasta):
                    caminho = os.path.join(pasta, item)
                    if os.path.isdir(caminho) and not item.startswith('.'):
                        # Verifica se tem .venv ou .git
                        if os.path.exists(os.path.join(caminho, '.venv')) or \
                           os.path.exists(os.path.join(caminho, '.git')):
                            tamanho = self._obter_tamanho_pasta(caminho)
                            data_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
                            dias = (datetime.now() - data_mod).days
                            projetos_encontrados.append({
                                'nome': item,
                                'caminho': caminho,
                                'tamanho': tamanho,
                                'dias': dias,
                                'data': data_mod
                            })
        
        if not projetos_encontrados:
            print("  Nenhum projeto encontrado")
            return
        
        print(f"\n  📁 Encontrados {len(projetos_encontrados)} projetos:")
        for i, p in enumerate(projetos_encontrados, 1):
            print(f"  {i}. {p['nome']} - {p['tamanho']:.1f} MB - Última modificação: {p['dias']} dias atrás")
        
        # Pergunta qual remover
        escolha = input("\n  Número do projeto para remover (ou 0 para pular): ").strip()
        if escolha and escolha != '0':
            try:
                idx = int(escolha) - 1
                if 0 <= idx < len(projetos_encontrados):
                    projeto = projetos_encontrados[idx]
                    confirmacao = input(f"  ⚠️ Remover '{projeto['nome']}' ({projeto['tamanho']:.1f} MB)? (s/N): ")
                    if confirmacao.lower() == 's':
                        shutil.rmtree(projeto['caminho'])
                        self.espaco_liberado += projeto['tamanho']
                        print(f"  ✅ Projeto removido! Liberado: {projeto['tamanho']:.1f} MB")
            except:
                pass
    
    def limpar_downloads(self):
        """LIMPA a pasta de Downloads (arquivos antigos)."""
        print("\n📥 LIMPANDO DOWNLOADS")
        print("=" * 50)
        
        downloads = os.path.expanduser("~/Downloads")
        if not os.path.exists(downloads):
            print("  Pasta de Downloads não encontrada")
            return
        
        # Arquivos com mais de 30 dias
        dias = 30
        print(f"  Removendo arquivos com mais de {dias} dias...")
        
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
        print(f"  ✅ Removidos {removidos} arquivos ({liberado:.1f} MB liberados)")
    
    # ========== FUNÇÃO PRINCIPAL DE LIMPEZA ==========
    
    def limpeza_completa(self):
        """Executa limpeza completa de tudo."""
        print("\n" + "=" * 60)
        print("🧹 LIMPEZA COMPLETA DO SISTEMA")
        print("=" * 60)
        print("⚠️ ATENÇÃO: Esta ação irá limpar vários arquivos do sistema!")
        print("   - Arquivos temporários")
        print("   - Caches do Windows")
        print("   - Lixeira")
        print("   - Cache do pip")
        print("   - Pacotes Python não usados")
        print("   - Downloads antigos")
        print("=" * 60)
        
        resposta = input("\n⚠️ Continuar com a limpeza completa? (s/N): ")
        if resposta.lower() != 's':
            print("❌ Limpeza cancelada.")
            return
        
        print("\n🚀 INICIANDO LIMPEZA...")
        
        # 1. Limpa temporários
        self.limpar_arquivos_temporarios()
        
        # 2. Limpa caches
        self.limpar_cache_windows()
        
        # 3. Esvazia lixeira
        self.esvaziar_lixeira()
        
        # 4. Limpa o .venv local
        if os.path.exists(self.venv_local):
            self.limpar_cache_pip_venv(self.venv_local)
            if self.config.get('remover_pacotes_nao_usados', True):
                self.remover_pacotes_nao_usados(self.venv_local)
        
        # 5. Limpa Downloads
        self.limpar_downloads()
        
        # 6. Projetos antigos
        if self.config.get('modo_agressivo', False):
            self.remover_projetos_antigos()
        
        print("\n" + "=" * 60)
        print(f"✅ LIMPEZA CONCLUÍDA!")
        print(f"💾 Total liberado: {self.espaco_liberado:.1f} MB")
        print("=" * 60)
        
        # Salva log
        self._log(f"Limpeza completa finalizada. Liberado: {self.espaco_liberado:.1f} MB", "SUCESSO")
    
    def menu_principal(self):
        """Menu principal simplificado com ações diretas."""
        print("\n" + "=" * 60)
        print("🧹 SISTEMA DE LIMPEZA - VERSÃO QUE REALMENTE LIMPA!")
        print("=" * 60)
        
        if not self.is_admin:
            print("\n⚠️ ATENÇÃO: Execute como Administrador para limpar tudo!")
        
        while True:
            print("\n📋 MENU DE AÇÕES DIRETAS")
            print("1. 🚀 LIMPEZA COMPLETA (Tudo de uma vez)")
            print("2. 🗑️ Limpar arquivos temporários")
            print("3. 🧹 Limpar caches do Windows")
            print("4. 🗑️ Esvaziar lixeira")
            print("5. 🐍 Limpar cache do pip e .pyc")
            print("6. 📦 Remover pacotes Python não usados")
            print("7. 📥 Limpar Downloads antigos")
            print("8. ⚙️ Configurações (modo agressivo)")
            print("0. ❌ Sair")
            
            opcao = input("\n👉 Escolha uma opção: ").strip()
            
            if opcao == "1":
                self.limpeza_completa()
            elif opcao == "2":
                self.limpar_arquivos_temporarios()
            elif opcao == "3":
                self.limpar_cache_windows()
            elif opcao == "4":
                self.esvaziar_lixeira()
            elif opcao == "5":
                if os.path.exists(self.venv_local):
                    self.limpar_cache_pip_venv(self.venv_local)
                else:
                    print("❌ .venv local não encontrado")
            elif opcao == "6":
                if os.path.exists(self.venv_local):
                    self.remover_pacotes_nao_usados(self.venv_local)
                else:
                    print("❌ .venv local não encontrado")
            elif opcao == "7":
                self.limpar_downloads()
            elif opcao == "8":
                self.config['modo_agressivo'] = not self.config.get('modo_agressivo', False)
                self._salvar_config()
                print(f"✅ Modo agressivo: {'ON' if self.config['modo_agressivo'] else 'OFF'}")
                if self.config['modo_agressivo']:
                    print("   ⚠️ Modo agressivo: vai remover projetos antigos também!")
            elif opcao == "0":
                print("\n👋 Saindo...")
                break
            else:
                print("❌ Opção inválida")

def main():
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