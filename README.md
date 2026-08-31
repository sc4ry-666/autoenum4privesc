# autoenum4privesc
Ferramenta para enumeração de ambiente.
---
# 🔐 AutoEnum - Ferramenta de Autoenumeração

!Python

!Platform

!License

!Version

## 📋 Sobre a Ferramenta

**AutoEnum** é uma ferramenta avançada de segurança ofensiva projetada para automatizar o processo de enumeração de sistemas e identificação de vetores de escalação de privilégios. Desenvolvida para profissionais de pentest, red team e pesquisadores de segurança, a ferramenta realiza uma análise abrangente do sistema alvo, buscando configurações incorretas, binários vulneráveis e oportunidades de exploração.

### 🎯 Principais Características

- **Multi-plataforma**: Suporte completo para Linux e Windows
- **Enumeração abrangente**: Coleta informações detalhadas do sistema
- **Detecção automática**: Identifica vulnerabilidades conhecidas
- **Banco de exploits**: Referências para CVEs e exploits públicos
- **Relatórios detalhados**: Saída formatada e salvamento automático
- **Zero dependências**: Usa apenas bibliotecas padrão do Python

## 🚀 Funcionalidades

### Enumeração do Sistema

- ✅ Informações básicas (SO, kernel, arquitetura, hostname)
- ✅ Identificação do usuário atual e permissões
- ✅ Listagem de serviços em execução
- ✅ Análise de portas abertas e conexões
- ✅ Verificação de tarefas cron/agendadas
- ✅ Identificação de binários com SUID (Linux)
- ✅ Análise de capabilities do sistema (Linux)
- ✅ Verificação de configurações Docker

### Detecção de Vulnerabilidades

- 🔍 Identificação de versões vulneráveis de software
- 🔍 Busca automática por CVEs conhecidos
- 🔍 Análise de configurações sudo incorretas
- 🔍 Detecção de binários exploráveis
- 🔍 Verificação de grupos com privilégios especiais
- 🔍 Unquoted Service Paths (Windows)
- 🔍 AlwaysInstallElevated (Windows)
- 🔍 Hotfixes ausentes (Windows)

### Escalação de Privilégios

- ⚡ Identificação de vetores de escalação comuns
- ⚡ Sugestões de comandos para exploração
- ⚡ Detecção de binários SUID exploráveis
- ⚡ Análise de configurações Docker/LXC
- ⚡ Verificação de permissões sudo
- ⚡ Potato Attacks (Windows)
- ⚡ Análise de privilégios críticos

## 📦 Requisitos

### Sistema

- **Python 3.6+**
- **Linux** (recomendado para pentest)
- **Windows** (para testes em ambientes Windows)

### Bibliotecas Python

- **Nenhuma biblioteca externa necessária!**
- Apenas módulos da biblioteca padrão

## 🔧 Instalação

### Linux

`bash
# Clone o repositório
git clone <https://github.com/sc4ry-666/autoenum4privesc/>

# Entre no diretório
cd autoenum

# Torne o script executável
chmod +x autoenum.py

# Execute
python3 autoenum.py
`
