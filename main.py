#!/usr/bin/env python3

import subprocess
import json

from datetime import datetime
from pathlib import Path

# ---- Base do protocolo Freechains ----

def enviar_mensagem(nome_cadeia: str, mensagem: str, chave_privada: Path, beg: bool = False) -> None:
    comando = ["freechains", "chain", nome_cadeia, "post", "inline", mensagem, f"--sign={chave_privada}"]
    
    if beg:
        comando.append("--beg")
        
    try:
        subprocess.run(comando, check=True)
        print("Mensagem enviada com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao enviar mensagem: {e}")

def postar(nome_cadeia: str, chave_privada: Path, ip_alvo: str, motivo: str, timestamp: datetime) -> None:
    print(f"IP {ip_alvo}, reportado na rede Freechains com motivo: {motivo} às {timestamp}")

    # Cria o dicionário com as chaves e valores
    dados = {
        "ip_malicioso": ip_alvo,
        "motivo": motivo,
        "timestamp": str(timestamp) # Converte o datetime para string
    }
    payload_estruturado = json.dumps(dados)

    reputacao: int = consultar_reputacao(nome_cadeia, chave_privada) 

    if reputacao >= 500: # Coloquei esse valor só para testes mesmo, mas na prática, posso definir o valor que achar adequado.
        print(f"Sua reputação é {reputacao} na cadeia {nome_cadeia}. Enviando relato na cadeia principal...")
        enviar_mensagem(nome_cadeia, payload_estruturado, chave_privada)
    else:
        print(f"Sua reputação é {reputacao} na cadeia {nome_cadeia}. Enviando relato como mendigo.")
        enviar_mensagem(nome_cadeia, payload_estruturado, chave_privada, beg=True)

def clonar_cadeia(nome_cadeia: str, endereco_remoto: str) -> None:
    print(f"Cadeia '{nome_cadeia}' não existe localmente. Clonando de {endereco_remoto}...")
    comando = ["freechains", "chains", "add", nome_cadeia, "clone", endereco_remoto]

    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        print(f"Cadeia clonada com sucesso! ID: {resultado.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao clonar cadeia: {e.stderr.strip()}")

    
def sincronizar_cadeia(nome_cadeia: str, endereco_remoto: str) -> str | None:
    comando = ["freechains", "chain", nome_cadeia, "sync", "recv", endereco_remoto]
    
    # Rodamos SEM check=True primeiro para podermos inspecionar o resultado com calma
    resultado = subprocess.run(comando, capture_output=True, text=True)

    # Se returncode for 0, o comando funcionou de primeira!
    if resultado.returncode == 0:
        print("Sincronização concluída com sucesso!")
        return resultado.stdout.strip()

    # Se deu erro (returncode != 0), olhamos dentro de resultado.stderr
    if "not found" in resultado.stderr:
        clonar_cadeia(nome_cadeia, endereco_remoto)
        return None
    else:
        # Caso seja outro erro (ex: daemon desligado no outro PC ou IP inacessível)
        print(f"Erro ao sincronizar: {resultado.stderr.strip()}")
        return None

def like_mensagem(nome_cadeia: str, hash_mensagem: str, qtd_likes: int, chave_privada: Path, chave_publica: str = "", modo: str = "action", motivo: str = "") -> bool:
    import os
    
    caminho_pub_temp: Path | None = None

    if modo == "action":
        comando = [
            "freechains", "chain", nome_cadeia, "like", 
            str(qtd_likes), "action", hash_mensagem, 
            f"--sign={chave_privada}", f"--why={motivo}"
        ]
        print(f"Enviando {qtd_likes} like(s) para o bloco {hash_mensagem[:25]}...")
    else:
        # Salva a chave pública em um arquivo temporário .pub para o Freechains ler sem erro
        caminho_pub_temp = Path(f"/tmp/infrator_{os.getpid()}_temp.pub")
        caminho_pub_temp.write_text(chave_publica + "\n", encoding="utf-8")
        
        comando = [
            "freechains", "chain", nome_cadeia, "like", 
            str(qtd_likes), "author", str(caminho_pub_temp), 
            f"--sign={chave_privada}", f"--why={motivo}"
        ]
        print(f"Enviando {qtd_likes} like(s) para o AUTOR ({chave_publica[:15]}...)...")
    
    try:
        subprocess.run(comando, check=True)
        print(" -> Like enviado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f" -> Erro ao enviar like: {e}")
        return False
    finally:
        # Limpa o arquivo temporário se ele foi criado
        if caminho_pub_temp and caminho_pub_temp.exists():
            caminho_pub_temp.unlink(missing_ok=True)

def dislike_mensagem(nome_cadeia: str, hash_mensagem: str, qtd_dislikes: int, chave_privada: Path, chave_publica: str = "", modo: str = "action", motivo: str = "") -> bool:
    import os

    caminho_pub_temp: Path | None = None

    if modo == "action":
        comando = [
            "freechains", "chain", nome_cadeia, "dislike", 
            str(qtd_dislikes), "action", hash_mensagem, 
            f"--sign={chave_privada}", f"--why={motivo}"
        ]
        print(f"Enviando {qtd_dislikes} dislikes para o bloco {hash_mensagem[:15]}...")
    else:
        # Salva a chave pública em um arquivo temporário .pub para o Freechains ler sem erro
        caminho_pub_temp = Path(f"/tmp/infrator_{os.getpid()}_temp.pub")
        caminho_pub_temp.write_text(chave_publica + "\n", encoding="utf-8")
        
        comando = [
            "freechains", "chain", nome_cadeia, "dislike", 
            str(qtd_dislikes), "author", str(caminho_pub_temp), 
            f"--sign={chave_privada}", f"--why={motivo}"
        ]
        print(f"Enviando {qtd_dislikes} dislikes para o AUTOR ({chave_publica[:25]}...)...")
    
    try:
        subprocess.run(comando, check=True)
        print(" -> Dislike enviado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f" -> Erro ao enviar dislike: {e}")
        return False
    finally:
        # Limpa o arquivo temporário se ele foi criado
        if caminho_pub_temp and caminho_pub_temp.exists():
            caminho_pub_temp.unlink(missing_ok=True)

def revoke_mensagem(nome_cadeia: str, hash_mensagem: str, chave_privada: Path, motivo: str = "") -> None:
    comando = ["freechains", "chain", nome_cadeia, "revoke", "1000", hash_mensagem, f"--sign={chave_privada}", f"--why={motivo}"]
    
    try:
        subprocess.run(comando, check=True)
        print("Mensagem revogada com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao revogar mensagem: {e}")

def consultar_reputacao(nome_cadeia: str, chave: Path | str) -> int:
    """
    Consulta a reputação de um autor no Freechains.
    Aceita:
      - Path ou string de caminho para chave privada ou pública (ex: /home/kali/henrxque[.pub])
      - String de texto da chave pública SSH (ex: 'ssh-ed25519 AAAAC3Nz...')
    """
    import os

    arquivo_temporario: Path | None = None
    caminho_pub: Path

    # Caso 1: Foi passada a string do texto da chave SSH pura
    if isinstance(chave, str) and chave.startswith("ssh-"):
        # Cria arquivo temporário seguro com o PID do processo atual
        arquivo_temporario = Path(f"/tmp/reps_{os.getpid()}_temp.pub")
        arquivo_temporario.write_text(chave.strip() + "\n", encoding="utf-8")
        caminho_pub = arquivo_temporario

    # Caso 2: Foi passado um caminho de arquivo (Path ou str)
    else:
        caminho_pub = Path(chave)
        # Se apontou para a chave privada, redireciona para a .pub
        if caminho_pub.suffix != ".pub":
            caminho_pub = caminho_pub.with_suffix(".pub")

    comando = ["freechains", "chain", nome_cadeia, "reps", "author", str(caminho_pub)]

    try:
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
        resultado_inteiro = int(resultado.stdout.strip())
        return resultado_inteiro
    except subprocess.CalledProcessError as e:
        print(f"Erro ao consultar reputação: {e.stderr.strip() if e.stderr else e}")
        return 0
    except (ValueError, FileNotFoundError) as e:
        print(f"Erro ao processar chave pública: {e}")
        return 0
    finally:
        # Limpa o arquivo temporário se ele foi criado
        if arquivo_temporario and arquivo_temporario.exists():
            arquivo_temporario.unlink(missing_ok=True)

def obter_autor_bloco(nome_cadeia: str, hash_bloco: str) -> str:
    cmd = ["freechains", "chain", nome_cadeia, "get", "metadata", hash_bloco]
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    
    for linha in resultado.stdout.splitlines():
        if linha.startswith("sign "):
            # Remove a palavra "sign " do começo e pega o resto da linha (a chave SSH)
            # Isso tava dando um bug danado
            return linha.replace("sign ", "", 1).strip()
            
    return "Desconhecido"

def obter_metadados_bloco(nome_cadeia: str, hash_bloco: str) -> tuple[str, str]:
    """Retorna (autor_pubkey, tipo_acao) lendo os metadados do bloco uma única vez."""
    cmd = ["freechains", "chain", nome_cadeia, "get", "metadata", hash_bloco]
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    
    autor = "Desconhecido"
    acao = "desconhecida"
    
    for linha in resultado.stdout.splitlines():
        if linha.startswith("sign "):
            autor = linha.replace("sign ", "", 1).strip()
        elif linha.startswith("action "):
            acao = linha.replace("action ", "", 1).strip()
            
    return autor, acao

def buscar_mensagem2(nome_cadeia: str, palavra_chave: str) -> str | None:
    '''
    Esta função está funcioando corretamente de acordo com os proposito do protocolo Freechains.
    que é buscar mensagens na cadeia que contenham a palavra-chave fornecida.
    , mas está causando dificuldade de implementar da forma que estou imaginando.
    '''

    comando = ["freechains", "chain", nome_cadeia, "list", "order"]
    resultado_lista = subprocess.run(comando, capture_output=True, text=True)
    
    
    for linha in resultado_lista.stdout.splitlines():
        if not linha.strip():
            continue
        
        hash_bloco = linha.split()[0]
        
        cmd_payload = ["freechains", "chain", nome_cadeia, "get", "payload", hash_bloco]
        resultado_payload = subprocess.run(cmd_payload, capture_output=True, text=True)
        #print(f"Bloco: {hash_bloco}, Payload: {resultado_payload.stdout.strip()}")

        if palavra_chave.lower() in resultado_payload.stdout.lower():
            #print(f"Chave encontrada no bloco: {hash_bloco}")
            return hash_bloco
    return None

def buscar_mensagem(nome_cadeia: str, ip_alvo: str) -> str | None:
    comando = ["freechains", "chain", nome_cadeia, "list", "order"]
    resultado_lista = subprocess.run(comando, capture_output=True, text=True)

    for linha in resultado_lista.stdout.splitlines():
        if not linha.strip():
            continue

        hash_bloco = linha.split()[0]
        comando_payload = ["freechains", "chain", nome_cadeia, "get", "payload", hash_bloco]
        resultado_payload = subprocess.run(comando_payload, capture_output=True, text=True)
        if resultado_payload.returncode != 0:
            continue

        try:
            dados = json.loads(resultado_payload.stdout)
        except json.JSONDecodeError:
            continue

        if isinstance(dados, dict) and dados.get("ip_malicioso") == ip_alvo:
            return hash_bloco

    return None


# ---- Aplicação sobre o protocolo Freechains ----

def reportar_ip(nome_cadeia: str, chave_privada: Path, ip_alvo: str, qtd_likes:int, motivo: str, timestamp: datetime) -> None:

    # Verificar se alguém já reportou o mesmo IP na cadeia. Caso não haja reporte, caso contrário like na mensagem existente.
    hash_encontrado: str | None = buscar_mensagem(nome_cadeia, ip_alvo)
    if hash_encontrado is not None:
        print(f"IP {ip_alvo} já foi reportado na cadeia {nome_cadeia}.")
        
        reputacao: int = consultar_reputacao(nome_cadeia, chave_privada) # curtidas recebem um imposto de 10%
        if reputacao >= qtd_likes:
            like_mensagem(nome_cadeia, hash_encontrado, qtd_likes, chave_privada, motivo="Confirmando denuncia")
        else:
            print(f" -> Sua reputação ({reputacao}) é insuficiente para dar like de confirmação. Ação ignorada.")
        
        return
    else:
        print(f"IP {ip_alvo} ainda não foi reportado na cadeia {nome_cadeia}. Postando relato...")
        postar(nome_cadeia, chave_privada, ip_alvo, motivo, timestamp)

def consultar_cadeia_publica(caminho_arquivo: Path, nome_cadeia: str, endereco_remoto: str) -> None:
    import utils
    print("\n--- Consultando cadeia publica (Incremental) ---")

    sincronizar_cadeia(nome_cadeia, endereco_remoto)
    
    # 1. Carrega o histórico anterior (se já existir) para não começar do zero!
    if caminho_arquivo.exists():
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            perfis: dict[str, dict] = json.load(f)
    else:
        perfis = {}

    # Monta um conjunto (set) rápido com todos os hashes que já vimos no passado
    blocos_ja_vistos: set[str] = set()
    for info in perfis.values():
        blocos_ja_vistos.update(info.get("blocos_invalidos", []))
        for d in info.get("denuncias_validas", []):
            blocos_ja_vistos.add(d["bloco"])

    comando_listar = ["freechains", "chain", nome_cadeia, "list", "order"]
    resultado_lista = subprocess.run(comando_listar, capture_output=True, text=True)

    if resultado_lista.returncode != 0:
        erro = resultado_lista.stderr.strip() or resultado_lista.stdout.strip()
        print(f"Erro ao listar blocos locais da cadeia: {erro or 'falha sem detalhes'}")
        return

    peso_1, peso_2, peso_3 = 1, 2, 5
    novos_blocos_processados = 0
    
    for linha in resultado_lista.stdout.splitlines():
        if not linha.strip():
            continue

        hash_bloco = linha.split()[0]

        # Se já avaliamos este bloco na consulta anterior, pula!
        if hash_bloco in blocos_ja_vistos:
            continue

        autor_pubkey, tipo_acao = obter_metadados_bloco(nome_cadeia, hash_bloco)

        if tipo_acao != "post":
            continue
        
        novos_blocos_processados += 1

        if autor_pubkey not in perfis:
            perfis[autor_pubkey] = {
                "chave_publica": autor_pubkey,
                "nome_cadeia": nome_cadeia,
                "tipo_perfil": "colaborador",
                "contagem_punitiva": 0,
                "blocos_invalidos": [],
                "blocos_ja_punidos": [], # Guarda onde já demos dislike
                "denuncias_validas": []
            }
        
        cmd_payload = ["freechains", "chain", nome_cadeia, "get", "payload", hash_bloco]
        resultado_payload = subprocess.run(cmd_payload, capture_output=True, text=True)

        if resultado_payload.returncode != 0:
            continue

        payload_texto = resultado_payload.stdout.strip()
        
        try:
            dados_denuncia = json.loads(payload_texto)
            if not isinstance(dados_denuncia, dict):
                raise ValueError("payload JSON válido, mas não é um objeto")

            ip_malicioso = dados_denuncia.get("ip_malicioso")
            motivo = dados_denuncia.get("motivo", "Desconhecido")
            timestamp = dados_denuncia.get("timestamp", "Desconhecido")

            if not isinstance(ip_malicioso, str) or not utils.verifica_formato_ip(ip_malicioso):
                perfis[autor_pubkey]["contagem_punitiva"] += 1 * peso_3
                perfis[autor_pubkey]["blocos_invalidos"].append(hash_bloco)
            elif utils.verificar_ip_privado(ip_malicioso):
                perfis[autor_pubkey]["contagem_punitiva"] += 1 * peso_2
                perfis[autor_pubkey]["blocos_invalidos"].append(hash_bloco)
            elif not utils.verifica_formato_timestamp(timestamp):
                perfis[autor_pubkey]["contagem_punitiva"] += 1 * peso_1
                perfis[autor_pubkey]["blocos_invalidos"].append(hash_bloco)
            else:
                perfis[autor_pubkey]["denuncias_validas"].append({
                    "bloco": hash_bloco,
                    "ip_malicioso": ip_malicioso,
                    "motivo": motivo,
                    "timestamp": timestamp,
                    "aplicado_ufw": False  # Flag para saber se já foi pro UFW!
                })

        except ValueError as erro_json:
            print(f"Bloco novo {hash_bloco[:15]} com formato inválido: {erro_json}")
            perfis[autor_pubkey]["contagem_punitiva"] += 1
            perfis[autor_pubkey]["blocos_invalidos"].append(hash_bloco)

    # Atualiza a classificação de cada autor
    for _, info in perfis.items():
        pontos = info["contagem_punitiva"]
        acertos = len(info["denuncias_validas"])
        base = pontos + acertos
        taxa = (pontos / base) * 100 if base > 0 else 0.0
        info["tipo_perfil"] = "infrator" if (pontos > 2 and taxa > 35.0) else "colaborador"

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        # Dicas para entender os parametros
        # indent=4 deixa o arquivo bonito para leitura humana
        # ensure_ascii=False evita que acentos fiquem com códigos estranhos (ex: \u00e7)
        json.dump(perfis, f, indent=4, ensure_ascii=False)
        
    print(f"Consulta concluída! {novos_blocos_processados} novo(s) post(s) analisado(s).")

def avaliar_mendigos(caminho_arquivo: Path, nome_cadeia: str, chave_privada: Path, recompensa_like: int, min_reports_desafio: int) -> None:
    import utils
    import json
    import subprocess

    print("\n--- Avaliando fila de mendigos (--beg) ---")

    # 1. Carrega o estado persistente do denuncias.json (Removido o bloqueio prévio de reputação)
    if caminho_arquivo.exists():
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            perfis: dict[str, dict] = json.load(f)
    else:
        perfis = {}

    cmd_begs = ["freechains", "chain", nome_cadeia, "list", "begs"]
    resultado_begs = subprocess.run(cmd_begs, capture_output=True, text=True)

    # CORREÇÃO P2: Falha ao listar begs não é mais mascarada como fila vazia
    if resultado_begs.returncode != 0:
        print(f" -> Erro ao consultar fila de mendigos: {resultado_begs.stderr.strip()}")
        return

    candidatos: dict[str, dict] = {}
    modificou_json: bool = False

    for linha in resultado_begs.stdout.splitlines():
        hash_beg = linha.strip()
        if not hash_beg:
            continue

        autor_mendigo: str = obter_autor_bloco(nome_cadeia, hash_beg)
        if autor_mendigo == "Desconhecido":
            continue

        if autor_mendigo not in perfis:
            perfis[autor_mendigo] = {
                "chave_publica": autor_mendigo,
                "nome_cadeia": nome_cadeia,
                "tipo_perfil": "colaborador",
                "contagem_punitiva": 0,
                "blocos_invalidos": [],
                "blocos_ja_punidos": [],
                "denuncias_validas": [],
                "begs_reprovados": [],
                "begs_likes_enviados": [],
                "status_desafio": "pendente"
            }

        reprovados_persistidos: dict[str, dict] = perfis[autor_mendigo].setdefault("begs_reprovados", [])
        likes_enviados: dict[str, dict] = perfis[autor_mendigo].setdefault("begs_likes_enviados", [])

        if reprovados_persistidos and perfis[autor_mendigo].get("status_desafio") != "reprovado":
            perfis[autor_mendigo]["status_desafio"] = "reprovado"
            modificou_json = True

        if perfis[autor_mendigo].get("status_desafio") == "reprovado" and reprovados_persistidos:
            continue

        if hash_beg in reprovados_persistidos or hash_beg in likes_enviados:
            continue

        if autor_mendigo not in candidatos:
            candidatos[autor_mendigo] = {
                "begs_validos": [],
                "bloco_erro": None
            }

        if candidatos[autor_mendigo]["bloco_erro"] is not None:
            continue

        cmd_payload = ["freechains", "chain", nome_cadeia, "get", "payload", hash_beg]
        resultado_payload = subprocess.run(cmd_payload, capture_output=True, text=True)
        if resultado_payload.returncode != 0:
            continue

        # CORREÇÃO P1: Tratamento rigoroso de Payload e fuga de atributo
        try:
            dados = json.loads(resultado_payload.stdout.strip())
            
            if not isinstance(dados, dict):
                raise ValueError("Payload JSON válido, mas não é um objeto (dict)")
            
            ip_malicioso = dados.get("ip_malicioso")
            timestamp = dados.get("timestamp", "")

            if (
                isinstance(ip_malicioso, str)
                and
                utils.verifica_formato_ip(ip_malicioso) 
                and not utils.verificar_ip_privado(ip_malicioso) 
                and utils.verifica_formato_timestamp(timestamp)
            ):
                candidatos[autor_mendigo]["begs_validos"].append(hash_beg)
            else:
                print(f" -> Beg {hash_beg[:10]} de {autor_mendigo[:20]}... reprovado (IP/Timestamp fora do padrão)!")
                candidatos[autor_mendigo]["bloco_erro"] = hash_beg

        except (json.JSONDecodeError, ValueError, AttributeError) as erro_json:
            print(f" -> Beg {hash_beg[:10]} de {autor_mendigo[:20]}... reprovado ({erro_json})!")
            candidatos[autor_mendigo]["bloco_erro"] = hash_beg

    if not candidatos:
        print(" -> Nenhum novo mendigo pendente de avaliação.")
        if modificou_json:
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(perfis, f, indent=4, ensure_ascii=False)
        return

    # 2. Avaliação dos candidatos encontrados
    for autor_mendigo, status in candidatos.items():
        bloco_erro = status["bloco_erro"]
        lista_validos = status["begs_validos"]
        qtd_validos = len(lista_validos)

        ja_aprovado: bool
        ja_reprovado: bool

        if perfis[autor_mendigo].get("status_desafio") == "aprovado":
            ja_aprovado = True
        else:
            ja_aprovado = False
            
        if perfis[autor_mendigo].get("status_desafio") == "reprovado":
            ja_reprovado = True
        else:
            ja_reprovado = False

        # REGRA 1: Tolerância Zero -> Punição Local e (se possível) na Rede
        if bloco_erro is not None:
            print(f" -> [TOLERÂNCIA ZERO] Mendigo {autor_mendigo[:20]}... cometeu erro no beg {bloco_erro[:10]}!")
            perfis[autor_mendigo]["status_desafio"] = "reprovado"
            modificou_json = True

            reputacao_atual = consultar_reputacao(nome_cadeia, chave_privada)
            if reputacao_atual >= recompensa_like:
                sucesso = punicao_2(
                    bloco=bloco_erro,
                    nome_cadeia=nome_cadeia,
                    chave_privada=chave_privada,
                    chave_publica=autor_mendigo,
                    qtd_dislikes=recompensa_like,
                    motivo="Mendigo malicioso. Erro no periodo probatorio."
                )
                if sucesso:
                    perfis[autor_mendigo]["begs_reprovados"].append(bloco_erro)
                    perfis[autor_mendigo]["tipo_perfil"] = "infrator"
                    modificou_json = True
            else:
                print(f" -> Reputação insuficiente ({reputacao_atual}) para aplicar dislike na rede. Infrator desqualificado apenas no estado local.")

        elif ja_reprovado:
            print(f" -> [DESQUALIFICADO] Mendigo {autor_mendigo[:20]}... já errou no desafio. Likes não serão concedidos.")

        # REGRA 2: Atingiu o desafio de reports legítimos
        elif qtd_validos >= min_reports_desafio or ja_aprovado:
            
            if not ja_aprovado:
                print(f" -> [APROVADO] Mendigo {autor_mendigo[:20]}... completou o desafio ({qtd_validos}/{min_reports_desafio} válidos)!")
                perfis[autor_mendigo]["status_desafio"] = "aprovado"
                modificou_json = True
            else:
                print(f" -> [RETOMANDO] Mendigo {autor_mendigo[:20]}... já aprovado. Retomando likes pendentes ({qtd_validos} válidos).")

            for hash_valido in lista_validos:
                reputacao = consultar_reputacao(nome_cadeia, chave_privada)
                if reputacao < recompensa_like:
                    print(f" -> Reputação atual ({reputacao}) insuficiente para iniciar a transação do like ({recompensa_like}).")
                    if modificou_json:
                        with open(caminho_arquivo, "w", encoding="utf-8") as f:
                            json.dump(perfis, f, indent=4, ensure_ascii=False)
                    return

                sucesso_like = like_mensagem(
                    nome_cadeia=nome_cadeia,
                    hash_mensagem=hash_valido,
                    qtd_likes=recompensa_like,
                    chave_privada=chave_privada,
                    modo="action",
                    motivo=f"Desafio de {min_reports_desafio} reports concluido com sucesso"
                )
                
                if not sucesso_like:
                    reputacao_apos_falha = consultar_reputacao(nome_cadeia, chave_privada)
                    print(f" -> Freechains recusou o like. Reputação consultada após a falha: {reputacao_apos_falha}. A tentativa será retomada no próximo ciclo.")
                    if modificou_json:
                        with open(caminho_arquivo, "w", encoding="utf-8") as f:
                            json.dump(perfis, f, indent=4, ensure_ascii=False)
                    return

                likes_enviados.append(hash_valido)
                modificou_json = True

        # REGRA 3: Em progresso do desafio
        else:
            print(f" -> [EM DESAFIO] Mendigo {autor_mendigo[:20]}... possui {qtd_validos}/{min_reports_desafio} reports legítimos. Aguardando a meta.")

    # 3. Persiste no arquivo se houveram modificações concluídas com sucesso
    if modificou_json:
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(perfis, f, indent=4, ensure_ascii=False)
            

def avaliar_punicoes(caminho_arquivo: Path, nome_cadeia: str, chave_privada: Path) -> None:
    print("\n--- Relatório de Avaliação de Infratores---")

    # Verifica antes se o nosso próprio nó tem reputação para moderar a rede!
    reputacao: int = consultar_reputacao(nome_cadeia, chave_privada)
    if reputacao <= 0:
        print(f" -> Aviso: Sua chave ({chave_privada.name}) possui {reputacao} reps nesta cadeia.")
        print(" -> Punições na rede (dislike) ignoradas por falta de reputação. (O filtro local do UFW continua ativo!)")
        return
    
    with open(caminho_arquivo, 'r', encoding='utf-8') as denuncias_file:
        perfis: dict[str, dict] = json.load(denuncias_file)

    taxa_erro_baixa: float = 15.0
    taxa_erro_moderada: float = 35.0

    for autor, info in perfis.items():

        if autor == "Desconhecido":
            continue

        pontos_erro: int = info["contagem_punitiva"]
        qtd_acertos: int = len(info["denuncias_validas"])
        blocos_errados: list = info["blocos_invalidos"]

        # Se o autor nunca errou, pula direto
        if pontos_erro == 0:
            continue

        chave_publica_infrator: str = autor
        ultimo_bloco_invalido: str = blocos_errados[-1]
        
        blocos_punidos: list = info.setdefault("blocos_ja_punidos", [])

        # Se este último erro já recebeu punição em uma execução anterior, pula!
        if ultimo_bloco_invalido in blocos_punidos:
            print(f"Autor {autor[:25]}... sem novas infrações desde a última avaliação.")
            continue

        
        # Somamos os pontos de erro com os acertos para ter a base total
        base_total: int  = pontos_erro + qtd_acertos
        taxa_erro_percentual: float = (pontos_erro / base_total) * 100

        custo_dislike: int = int(round(taxa_erro_percentual))
        
        if custo_dislike <= 0:
            print(f" -> Reputação insuficiente para punir {autor[:8]}... no momento.")
            continue

        print(f"\nAutor: {autor[:25]}...")
        print(f" -> Acertos: {qtd_acertos} | Pontos Punitivos: {pontos_erro} | Taxa de Erro: {taxa_erro_percentual:.1f}%")

        # REGRA 1: Taxa de erro baixa (até 15%) OU apenas 1 deslize leve isolado
        if taxa_erro_percentual <= taxa_erro_baixa or pontos_erro <= 2:
            print(" -> Status:Dentro da margem de tolerância. Nenhuma punição aplicada.")
            
        # REGRA 2: Taxa de erro moderada (entre 15% e 50%)
        elif taxa_erro_baixa < taxa_erro_percentual <= taxa_erro_moderada:
            print(" -> Status: Poluição moderada. Aplicando dislike leve no último bloco inválido.")
            resultado: bool = punicao_1(ultimo_bloco_invalido, nome_cadeia, chave_privada, custo_dislike, "Possível autor malicioso. Taxa de denuncias incorretas moderada.")
            if resultado:
                blocos_punidos.append(ultimo_bloco_invalido)
        
        # REGRA 3: Taxa de erro crítica (acima de 35% das postagens são inválidas punimos o author)
        else:
            print(" -> Status: Comportamento malicioso! Taxa acima de 50%. Punindo carteira do autor.")
            resultado: bool = punicao_2(ultimo_bloco_invalido, nome_cadeia, chave_privada, chave_publica_infrator, custo_dislike, "Autor malicioso. Taxa de denuncias incorretas crítica.")
            if resultado:
                blocos_punidos.append(ultimo_bloco_invalido)

    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(perfis, f, indent=4, ensure_ascii=False)
        

def punicao_1(bloco: str, nome_cadeia: str, chave_privada: Path, qtd_dislikes: int, motivo: str) -> bool:
    return dislike_mensagem(
        nome_cadeia=nome_cadeia, 
        hash_mensagem=bloco, 
        qtd_dislikes=qtd_dislikes, 
        chave_privada=chave_privada, 
        modo="action", 
        motivo=motivo
    )


def punicao_2(bloco: str, nome_cadeia: str, chave_privada: Path, chave_publica: str, qtd_dislikes: int, motivo: str) -> bool:
    return dislike_mensagem(
        nome_cadeia=nome_cadeia, 
        hash_mensagem=bloco, 
        qtd_dislikes=qtd_dislikes, 
        chave_privada=chave_privada, 
        chave_publica=chave_publica, 
        modo="author",
        motivo=motivo
    )


'''
perfis[autor_pubkey] = {
                "chave_publica": autor_pubkey,
                "nome_cadeia": nome_cadeia,
                "tipo_perfil": "infrator", # Começa assumindo o pior

                "contagem_punitiva": 0,
                "blocos_invalidos": [],
                "denuncias_validas": [] # Lista para guardar múltiplos IPs reportados
            }

dados = {
        "ip": ip_alvo,
        "motivo": motivo,
        "timestamp": str(timestamp) # Converte o datetime para string
    }
'''

def aplicar_bloqueios_cadeia_publica(caminho_arquivo: Path) -> None:
    import firewall as ufw

    print("\n--- Aplicando NOVOS bloqueios denunciados na cadeia ---")

    with open(caminho_arquivo, 'r', encoding='utf-8') as denuncias_file:
        perfis: dict[str, dict] = json.load(denuncias_file)

    novos_bloqueios = 0

    # Percorre cada autor no arquivo denuncias.json
    for autor, info in perfis.items():
        if info["tipo_perfil"] == "infrator":
            print(f"Ignorando denúncias de {autor[:25]}... (Classificado como infrator)")
            continue
        
        # Percorre a LISTA de denúncias válidas daquele colaborador
        for denuncia in info["denuncias_validas"]:
            # Se já aplicamos no UFW na rodada passada, ignora!
            if denuncia.get("aplicado_ufw", False):
                continue

            ip_malicioso: str = denuncia["ip_malicioso"]
            motivo: str = denuncia["motivo"]
            
            # Chama o módulo do seu firewall sem a vírgula dupla
            resultado_bloqueio = ufw.aplicar_bloqueio(
                ip_malicioso,
                motivo_fornecido=f"P2P: {motivo}"
            )
            if resultado_bloqueio is None:
                continue

            # Marca como concluído para nunca mais repetir na próxima consulta
            denuncia["aplicado_ufw"] = True
            novos_bloqueios += 1
    
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(perfis, f, indent=4, ensure_ascii=False)

    print(f"Total de novos IPs bloqueados nesta rodada: {novos_bloqueios}")

if __name__ == "__main__":
    import configuracao
    # ---- Configurações do Ambiente ----

    CAMINHO_BASE_CHAVES_PATH: Path = Path(configuracao.CHAVE_PRIVADA)

    sincronizar_cadeia(configuracao.NOME_CADEIA, configuracao.ENDERECO_REMOTO)
    
    '''
    print(f"Reputação: {consultar_reputacao(configuracao.NOME_CADEIA, CAMINHO_BASE_CHAVES_PATH)}")
    enviar_mensagem(configuracao.NOME_CADEIA, "oioi", CAMINHO_BASE_CHAVES_PATH)
    consultar_cadeia_publica(CAMINHO_BASE_CHAVES_PATH, configuracao.NOME_CADEIA, configuracao.ENDERECO_REMOTO)
    print(f"Buscar mensagem: {buscar_mensagem(configuracao.NOME_CADEIA, "oioi")}")
    '''