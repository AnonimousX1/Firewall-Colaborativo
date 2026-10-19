# Firewall P2P com Freechains

Protótipo experimental para a disciplina de Sistemas Peer-to-Peer de compartilhamento descentralizado de denúncias de IPs maliciosos utilizando o protocolo de consenso e reputação do Freechains, integrando detecção via Fail2ban e aplicação local de regras de bloqueio com UFW. Projeto desenvolvido para a disciplina de Sistemas Peer-to-Peer.

---

## Objetivo

Permitir que múltiplos nós distribuídos em uma cadeia Freechains publiquem denúncias estruturadas, sincronizem relatos assincronamente através de fofoca (*gossip*), analisem o comportamento histórico e reputacional dos autores e reflitam automaticamente no firewall local (`ufw`) apenas os bloqueios validados por critérios de tolerância definidos pelo nó.

---

## Fluxo do Sistema

O daemon principal (`orquestracao.py`) opera em loop contínuo executando periodicamente o seguinte ciclo:

1. **Sincronização (`sync recv`):** Atualiza a cadeia local contra o par remoto especificado (ou realiza o clone automático caso a cadeia ainda não exista).


2. **Leitura Incremental e Validação:** Analisa apenas novos blocos do tipo `post`. Realiza a validação de formato JSON, checa a integridade e escopo de IPs públicos (rejeitando IPs privados) e valida formatos de timestamp, atualizando os perfis locais em `denuncias.json`.


3. **Avaliação Reputacional:** Calcula a taxa de erro ponderada individual de cada autor (`main.avaliar_punicoes`) e emite moderação (`dislike` na mensagem ou na chave pública do autor), respeitando a reputação atual do próprio nó avaliador.


4. **Aplicação no Firewall:** Lê as denúncias de colaboradores confiáveis e aciona o comando `sudo ufw prepend deny from <IP>` para regras ainda não aplicadas (`aplicado_ufw == False`).


5. **Crivo de Novatos (`list begs`):** Avalia mensagens pendentes na fila de mendicância. Aplica tolerância zero (dislike imediato no autor se houver payload malformado) ou concede `like` integrador caso o novato atinja o desafio mínimo de relatos válidos.



```json
{
  "ip_malicioso": "203.0.113.10",
  "motivo": "Fail2ban SSH brute-force",
  "timestamp": "2026-10-18 12:30:00"
}

```

---

## Estrutura de Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Métodos do protocolo Freechains, publicação e busca de relatos, cálculo de taxas de erro, aplicação de moderação e crivo de novatos. |
| `orquestracao.py` | Daemon em loop contínuo que agenda e executa os ciclos de sincronização, punição e mitigação no firewall. |
| `firewall.py` | Integração via subprocesso com o UFW (`prepend deny` / `delete deny`) e ponto de entrada para ações disparadas pelo Fail2ban. |
| `utils.py` | Rotinas utilitárias de validação de rede (`ipaddress`), parsing de timestamps e funções de cálculo estatístico. |
| `denuncias.json` | Banco de estado local em disco para controle incremental de histórico, evitando reprocessamentos e repetição de comandos UFW. |

---

## a. Manual de Utilização da Aplicação

### Pré-requisitos

* Sistema Operacional Linux (Debian, Ubuntu, Kali Linux ou WSL2).
* Python 3.10 ou superior (utiliza estritamente módulos padrão: `json`, `subprocess`, `ipaddress`, `pathlib`, `datetime`).
* Binário e daemon do Freechains instalados e em execução:


```bash
freechains daemon start --port=<porta que te convém>
```


* Pacote `ufw` instalado com permissão de execução via `sudo`.


* Par de chaves SSH (`ed25519`) gerado para assinatura no Freechains (`~/.freechains/` ou diretório personalizado).


* Fail2ban instalado para gatilhos dinâmicos de banimento via arquivo `firewall.py`.



### Configuração de Privilégios (Sudoers)

Como o orquestrador executa como daemon sem intervenção interativa, configure o `sudoers` para permitir a manipulação de regras do UFW sem solicitação de senha:

```bash
sudo visudo

```

Adicione a linha abaixo ao final do arquivo, substituindo `seu_usuario` pelo seu usuário do sistema:

```sudoers
seu_usuario ALL=(ALL) NOPASSWD: /usr/sbin/ufw

```

### Configuração dos Nós

No cabeçalho do arquivo `orquestracao.py` e em `main.py`, defina as configurações do seu ambiente:

* `NOME_CADEIA`: Nome da cadeia Freechains (ex: `#firewall-test` ou `#p2p`).


* `ENDERECO_REMOTO`: IP e porta do par que servirá as atualizações (ex: `10.0.1.222:8330`).


* `CHAVE_PRIVADA`: Caminho absoluto do arquivo da chave privada para assinatura das operações.


* `INTERVALO_SEGUNDOS`: Período de dormência entre ciclos do daemon.



### Execução

1. **Iniciar o Daemon do Orquestrador:**
Execute a aplicação a partir do diretório raiz onde os scripts estão localizados:
```bash
python3 orquestracao.py

```


O daemon rodará em segundo plano até ser interrompido por sinal de interrupção (`Ctrl+C`).


2. **Acionamento Manual ou via Fail2ban (`firewall.py`):**
Para aplicar um bloqueio pontual no UFW e propagá-lo para a cadeia P2P:


```bash
python3 firewall.py ban 198.51.100.25 1792345800 "SSH brute force"

```


Para remover um bloqueio local no UFW (apenas remove a regra local sem emitir post na cadeia):


```bash
python3 firewall.py unban 198.51.100.25

```



---

## b. O que foi Implementado

* **Operações do substancias do Protocolo Freechains:** Rotinas de automação para clonagem incremental (`chains add clone`), recepção de blocos (`sync recv`), postagens normais e assistidas (`--beg`), likes e dislikes em ações e autores, além de leitura de metadados e inspeção de payloads.


* **Processamento Incremental Baseado em Deltas(Na minha cabeça se chama diferenças):** Mecanismo com verificação de conjuntos de hashes (`blocos_ja_vistos`), garantindo que apenas transações novas sejam processadas após a primeira carga, economizando I/O de disco e chamadas de subprocessos.


* **Prevenção de Reprocessamento e Punições Repetidas:** Controle de duplicação através das chaves `"aplicado_ufw"` e `"blocos_ja_punidos"` salvas em `denuncias.json`, impedindo duplicações de regras no UFW e evitando gastos de reputação com dislikes redundantes.


* **Reputação e Avaliação Ponderada:** Cálculo de taxa de erro individual considerando pesos de severidade (erros de formatação de timestamp, injeção de IPs privados ou payloads não-JSON), classificando autores entre "colaborador" e "infrator". Isso deu bastante trabalho !


* **Regras rígidas para entrada de colaboradores (`--beg`):** Rotina de triagem de mendigos que impõe tolerância zero para payloads defeituosos e exige volume mínimo de postagens legítimas para acolhimento de novos nós na cadeia.


* **Automação do Firewall Local:** Mecanismo seguro de injeção de regras via `sudo ufw prepend deny`, priorizando bloqueios antes de regras permissivas e tratando códigos de erro para novas tentativas em caso de falha de execução.



---

## c. O que Não foi Implementado

* **Propagação Ativa via `sync send`:** Como a primitiva `send` apresentou problemas no daemon da versão do Freechains utilizada, a disseminação depende exclusivamente de rotinas de coleta (`sync recv`) disparadas por cada par receptor.


* **Validação de Veracidade da Ameaça:** A arquitetura valida rigorosamente o formato sintático (se é um IP público e se os campos existem), mas não possui mecanismo de desafio para atestar se o IP bloqueado representava, de fato, um ataque real.


* **Sistema Centralizado ou Rotativo de Logs em Disco:** As saídas e diagnósticos operam através de saidas no terminal do console do daemon, sem nenhum tipo de saida por arquivo. Que facilita a extração de logs quando executado por vários dias.

* **Mecanismo de Desbloqueio Dinâmico Distribuído:** A aplicação propaga banimentos na rede, mas não há consenso implementado para "perdão" ou expiração coordenada de IPs entre os pares (o desbloqueio "unban" precisa ser realizada localmente pelo por quem utiliza o projeto).


* **Bloqueio no UFW dos Próprios Pares Infratores:** O nó pune a chave pública do autor na camada do Freechains (via reputação), mas não bloqueia a comunicação de rede ou o IP de transporte do nó infrator no firewall local, que seria mais eficiente.



---

## d. Ferramentas Utilizadas

* **Freechains (v0.20):** Protocolo P2P baseado em árvores Git para consenso por reputação e publicação/assinatura descentralizada.


* **Python (3.10+):** Linguagem base para desenvolvimento de toda a camada lógica, parsing e automação, sem uso de bibliotecas de terceiros.


* **UFW (Uncomplicated Firewall):** Interface de manipulação de regras de filtragem de pacotes do kernel Linux.


* **Fail2ban:** Agente de detecção de intrusão baseado em logs utilizado para disparar gatilhos de banimento integrados ao ecossistema.


* **JSON:** Formato estruturado para payloads de rede nas transações Freechains e para persistência de estado local incremental no nó.