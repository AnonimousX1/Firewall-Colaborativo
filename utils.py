import ipaddress

from datetime import datetime

def verifica_formato_ip(ip_alvo: str) -> bool:
    if not isinstance(ip_alvo, str):
        return False
    try:
        ipaddress.ip_address(ip_alvo)
        return True
    except ValueError:
        return False

def verificar_ip_privado(ip_alvo: str) -> bool:
    if not isinstance(ip_alvo, str):
        return False
    try:
        ip = ipaddress.ip_address(ip_alvo)
        return ip.is_private
    except ValueError:
        return False

def verifica_formato_timestamp(timestamp: str) -> bool:
    if not isinstance(timestamp, str):
        return False
    try:
        # fromisoformat lida nativamente com o output de str(datetime.now())
        datetime.fromisoformat(timestamp)
        return True
    except ValueError:
        return False

def calcular_percentil_puro(lista_valores: list[float], percentil: int) -> float:
    if not lista_valores:
        return 0.0
    lista_ordenada = sorted(lista_valores)
    # Acha a posição na lista usando regra de três simples
    indice = int((percentil / 100) * (len(lista_ordenada) - 1))
    return lista_ordenada[indice]


# ---- ambiente de testes