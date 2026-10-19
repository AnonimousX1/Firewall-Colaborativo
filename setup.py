#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def executar_setup():
    import configuracao
    # 1. Verifica se está rodando como root
    if os.geteuid() != 0:
        print("Erro: Este script precisa ser executado como root.")
        print("Use: sudo python3 setup.py")
        sys.exit(1)

    # 2. Identifica o usuário real que chamou o sudo (ex: freechains ou kali)
    usuario = os.environ.get("SUDO_USER")
    if not usuario or usuario == "root":
        print("Erro: Não foi possível determinar o usuário original.")
        print("Certifique-se de executar com 'sudo python3 setup.py' a partir do seu usuário comum.")
        sys.exit(1)

    # 3. Identifica dinamicamente o caminho absoluto do projeto
    diretorio_atual = Path(__file__).parent.resolve()
    caminho_firewall: Path = diretorio_atual / "firewall.py"

    if not caminho_firewall.exists():
        print(f"Erro: O arquivo {caminho_firewall} não foi encontrado na pasta atual!")
        sys.exit(1)

    print(f"Iniciando configuração automatizada...")
    print(f" -> Usuário detectado: {usuario}")
    print(f" -> Caminho do script: {caminho_firewall}")

    # 4. Configurar SUDOERS de forma segura (usando a pasta sudoers.d)
    caminho_sudoers: Path = Path(f"{configuracao.CAMINHO_SUDOERS}{usuario}")
    conteudo_sudoers: str = f"{usuario} {configuracao.CONTEUDO_SUDOERS}\n"
    
    try:
        caminho_sudoers.write_text(conteudo_sudoers)
        caminho_sudoers.chmod(0o440)  # O sudo exige essa permissão estrita
        print(" -> [OK] Regra do UFW adicionada ao sudoers.")
    except Exception as e:
        print(f" -> [ERRO] Falha ao configurar sudoers: {e}")

    # 5. Criar a Action do Fail2ban
    diretorio_action = Path(configuracao.DIRETORIO_ACTION)
    if not diretorio_action.exists():
        print(" -> [AVISO] Fail2ban não encontrado em /etc/fail2ban/. Instale-o primeiro.")
    else:
        caminho_action = diretorio_action / "freechains_ufw.conf"
        conteudo_action = f"""[Definition]

# Nao precisamos de comandos ao iniciar ou parar o servico para essa acao
actionstart =
actionstop =
actioncheck =

# O Fail2ban roda como root, mas força a execução do script Python com o seu usuário

# O Fail2ban injeta o IP malicioso na tag <ip>
actionban = sudo -u {usuario} /usr/bin/python3 {caminho_firewall} ban <ip> <time> <name>

# Executado automaticamente quando o tempo de banimento (bantime) expira
actionunban = sudo -u {usuario} /usr/bin/python3 {caminho_firewall} unban <ip>

[Init]
# Vazio
"""
        try:
            caminho_action.write_text(conteudo_action)
            print(" -> [OK] Action do Fail2ban (freechains_ufw.conf) criada.")
            
            # Tenta recarregar o Fail2ban para aplicar as mudanças
            subprocess.run(["fail2ban-client", "reload"], capture_output=True)
            print(" -> [OK] Serviço Fail2ban recarregado.")
        except Exception as e:
            print(f" -> [ERRO] Falha ao configurar Fail2ban: {e}")

    print("\nConfiguração concluída com sucesso!")

if __name__ == "__main__":
    executar_setup()