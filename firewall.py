#!/usr/bin/env python3

import sys
import subprocess
from datetime import datetime

# ---- Funções de bloqueio e desbloqueio de IP no UFW ----

def aplicar_bloqueio(
    ip_alvo: str,
    timestamp_epoch: str | None = None,
    motivo_fornecido: str | None = None
) -> tuple[str, datetime] | None:
    print(f"[{datetime.now()}] Iniciando bloqueio do IP {ip_alvo} no UFW...")
    
    comando = ["sudo", "ufw", "prepend", "deny", "from", ip_alvo, "to", "any"]
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print(f"IP {ip_alvo} bloqueado com sucesso. Saída: {resultado.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao bloquear o IP {ip_alvo}: {e.stderr.strip()}")
        return None
    except OSError as e:
        print(f"Erro ao executar o UFW para bloquear o IP {ip_alvo}: {e}")
        return None

    # Fallback nos parâmetros recebidos
    epoch = timestamp_epoch if timestamp_epoch else str(datetime.now().timestamp())
    motivo = motivo_fornecido if motivo_fornecido else "Bloqueio Manual/Desconhecido"
    
    try:
        dt_timestamp = datetime.fromtimestamp(float(epoch))
    except ValueError:
        dt_timestamp = datetime.now()

    return motivo, dt_timestamp

def aplicar_desbloqueio(ip_alvo: str) -> None:
    print(f"[{datetime.now()}] Removendo bloqueio do IP {ip_alvo} no UFW...")
    
    comando = ["sudo", "ufw", "delete", "deny", "from", ip_alvo, "to", "any"]
    
    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        #print(f"IP {ip_alvo} desbloqueado com sucesso. Saída: {resultado.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao desbloquear o IP {ip_alvo}: {e.stderr.strip()}")

if __name__ == "__main__":
    import main as freechains
    from pathlib import Path
    import configuracao

    if len(sys.argv) < 3:
        print("Uso: firewall_manager.py <ban|unban> <ip_alvo> [timestamp] [motivo]")
        sys.exit(1)
        
    acao = sys.argv[1]
    ip_alvo = sys.argv[2]
    
    if acao == "ban":
        # Extrai as tags do Fail2ban aqui, na raiz da execução por terminal
        t_epoch: str | None = sys.argv[3] if len(sys.argv) > 3 else None
        m_tag: str | None = sys.argv[4] if len(sys.argv) > 4 else None
        
        # Chamada com parâmetros e desestruturação correta correspondente ao return
        motivo: str
        dt_timestamp: datetime
        resultado_bloqueio = aplicar_bloqueio(ip_alvo, t_epoch, m_tag)
        if resultado_bloqueio is None:
            sys.exit(1)

        motivo, dt_timestamp = resultado_bloqueio
        print(f"IP {ip_alvo} bloqueado. Motivo: {motivo}, timestamp: {dt_timestamp}.")

        # ---- Configurações do Ambiente ----

        # Integração com aplicação
        # A variável NOME_CADEIA, pode mudar de acordo com a cadeia você está utilizando
        
        # Aqui você chama a função que já construiu no outro arquivo
        freechains.reportar_ip(configuracao.NOME_CADEIA, Path(configuracao.CHAVE_PRIVADA), ip_alvo, 1, motivo, dt_timestamp)

    elif acao == "unban":
        aplicar_desbloqueio(ip_alvo)
    else:
        print("Ação desconhecida. Use 'ban' ou 'unban'.")