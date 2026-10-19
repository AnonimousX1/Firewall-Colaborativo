#!/usr/bin/env python3

import time
import subprocess
from datetime import datetime
from pathlib import Path

import main


def propagar_atualizacoes_rede(nome_cadeia: str, endereco_remoto: str) -> None:
    """
    O autor do projeto relatou que a função send não funciona infelizmente, por isto cada par deve buscas mudanças nos pares com recv
    Envia (sync send) os nossos novos posts e dislikes locais para o par remoto.
    
    """
    comando = ["freechains", "chain", nome_cadeia, "sync", "send", endereco_remoto]
    resultado = subprocess.run(comando, capture_output=True, text=True)

    if resultado.returncode == 0:
        print(f" -> Atualizações locais propagadas para {endereco_remoto} com sucesso!")
    else:
        print(f" -> Aviso ao propagar para {endereco_remoto}: {resultado.stderr.strip()}")


def executar_ciclo_orquestracao(
    nome_cadeia: str,
    endereco_remoto: str,
    caminho_arquivo_json: Path,
    chave_privada: Path
) -> None:
    """
    Executa as 3 etapas fundamentais do sistema na ordem correta.
    """
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n============================================================")
    print(f"[{agora}] INICIANDO CICLO DE ORQUESTRAÇÃO P2P")
    print(f"============================================================")

    # ETAPA 1: Sincroniza (recv/clone), valida blocos novos e gera/atualiza o denuncias.json
    main.consultar_cadeia_publica(nome_cadeia, endereco_remoto)

    # Verifica se o arquivo denuncias.json foi criado antes de seguir para as etapas 2 e 3
    if not caminho_arquivo_json.exists():
        print("Arquivo de denúncias ainda não existe. Aguardando próximo ciclo...")
        return

    # ETAPA 2: Avalia os perfis e aplica dislikes (action ou author) em novas infrações
    main.avaliar_punicoes(caminho_arquivo_json, nome_cadeia, chave_privada)

    # ETAPA 3: Lê as denúncias novas de colaboradores confiáveis e aplica no UFW local
    main.aplicar_bloqueios_cadeia_publica(caminho_arquivo_json)

    # # ETAPA 4: A avaliação de denuncias na “begs” da cadeia.
    main.avaliar_mendigos(nome_cadeia, chave_privada, recompensa_like = 10, min_reports_desafio = 50)

    # ETAPA 5: Propaga para a rede eventuais dislikes/posts que nosso nó gerou neste ciclo
    # Não funciona
    #propagar_atualizacoes_rede(nome_cadeia, endereco_remoto)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Ciclo finalizado com sucesso!")


def iniciar_daemon(
    nome_cadeia: str,
    endereco_remoto: str,
    caminho_arquivo_json: Path,
    chave_privada: Path,
    intervalo_segundos: int = 60
) -> None:
    """
    Mantém o orquestrador rodando continuamente em background/terminal.
    """
    print(f"Iniciando Orquestrador P2P na cadeia '{nome_cadeia}'...")
    print(f"Par remoto: {endereco_remoto} | Intervalo: {intervalo_segundos}s")
    print("Pressione Ctrl+C a qualquer momento para encerrar com segurança.\n")

    try:
        while True:
            try:
                executar_ciclo_orquestracao(
                    nome_cadeia=nome_cadeia,
                    endereco_remoto=endereco_remoto,
                    caminho_arquivo_json=caminho_arquivo_json,
                    chave_privada=chave_privada
                )
            except Exception as erro_ciclo:
                # Se der um erro inesperado num ciclo (ex: falha momentânea de rede),
                # o daemon mostra o erro mas NÃO morre; ele tenta de novo no próximo ciclo.z
                print(f"[ERRO NO CICLO] Ocorreu uma falha durante a execução: {erro_ciclo}")

            print(f"\nAguardando {intervalo_segundos} segundos até a próxima verificação...")
            time.sleep(intervalo_segundos)

    except KeyboardInterrupt:
        print("\n[ENCERRANDO] Sinal de interrupção (Ctrl+C) recebido. Orquestrador finalizado.")


if __name__ == "__main__":
    # ---- Configurações do Ambiente ----
    
    # Tempo entre cada sincronização (em segundos)
    # Para testes rápidos no laboratório, use 15 ou 30 segundos.
    INTERVALO_SEGUNDOS = 30


    NOME_CADEIA: str = "#firewall-test"
    ENDERECO_REMOTO: str = "10.0.1.222:8330"
    ARQUIVO_DENUNCIAS: Path = Path("denuncias.json")
    CHAVE_PRIVADA: Path = Path("/home/kali/henrxque")


    iniciar_daemon(
        nome_cadeia=NOME_CADEIA,
        endereco_remoto=ENDERECO_REMOTO,
        caminho_arquivo_json=ARQUIVO_DENUNCIAS,
        chave_privada=CHAVE_PRIVADA,
        intervalo_segundos=INTERVALO_SEGUNDOS
    )