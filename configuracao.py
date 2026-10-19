# Centralização de configurações 

# Configurações Freechains
NOME_CADEIA: str = "#firewall-test"
ENDERECO_REMOTO: str = "10.0.1.222:8330"
ARQUIVO_DENUNCIAS: str = "denuncias.json"
CHAVE_PRIVADA: str = "/home/kali/henrxque"

# - Intervalo de refresh
# Tempo entre cada sincronização (em segundos)
# Para testes rápidos no laboratório, use 15 ou 30 segundos.
INTERVALO_SEGUNDOS: int = 20

# Configurações Fail2ban
DIRETORIO_ACTION: str = "/etc/fail2ban/action.d"


# Configurações UFW

# Configurações Sudoers
CAMINHO_SUDOERS: str = "/etc/sudoers.d/ufw_"
# - Permissões
CONTEUDO_SUDOERS: str= "ALL=(ALL) NOPASSWD: /usr/sbin/ufw"
