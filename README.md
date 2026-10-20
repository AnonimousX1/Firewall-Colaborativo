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
5. **Crivo de Novatos (`list begs`):** Avalia mensagens pendentes na fila de mendicância. Um beg inválido aplica dislike ao autor e o desqualifica permanentemente do desafio; begs válidos posteriores não revertem essa decisão. Likes só são concedidos a autores que atinjam o mínimo de relatos válidos sem terem sido desqualificados.

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
| `configuracao.py` | Arquivo central de configurações do projeto, onde as variáveis globais (chaves, nomes de cadeia, caminhos e intervalos) são definidas para injeção de dependências. |
| `setup.py` | Script de configuração automatizada que ajusta permissões no arquivo sudoers para o UFW e cria a *action* de integração no diretório do Fail2ban. |
| `main.py` | Métodos do protocolo Freechains, publicação e busca de relatos, cálculo de taxas de erro, aplicação de moderação e crivo de novatos. |
| `orquestracao.py` | Daemon em loop contínuo que agenda e executa os ciclos de sincronização, punição e mitigação no firewall. |
| `firewall.py` | Integração via subprocesso com o UFW (`prepend deny` / `delete deny`) e ponto de entrada para ações disparadas pelo Fail2ban. |
| `utils.py` | Rotinas utilitárias de validação de rede (`ipaddress`), parsing de timestamps e funções de cálculo estatístico. |
| `denuncias.json` | Banco de estado local em disco para controle incremental de histórico, evitando reprocessamentos e repetição de comandos UFW. |

---

## a. Manual de Utilização da Aplicação

### Pré-requisitos

* Linux (Debian, Ubuntu, Kali Linux ou WSL2), Python 3.10 ou superior e `pip`.
* Freechains v0.20 instalado, com o daemon em execução e acessível pelo mesmo usuário que executará os scripts.
* UFW instalado. O usuário que executar os scripts precisa poder chamar `sudo ufw` sem interação.
* Um par de chaves SSH aceito pelo Freechains. O caminho da chave privada é configurado no projeto; o arquivo de chave pública correspondente também deve estar disponível.
* Fail2ban é necessário somente para a integração automática de banimento.

Inicie o daemon do Freechains antes de executar o projeto. Ajuste a porta conforme o ambiente e use a mesma porta no endereço remoto dos outros nós:

```bash
freechains daemon start --port=8330
```

### Configuração dos nós

Edite o bloco de configurações no final de `configuracao.py`:

* `NOME_CADEIA`: cadeia Freechains usada pelo nó, por exemplo `#firewall-test`.
* `ENDERECO_REMOTO`: endereço `IP:porta` do par usado para receber atualizações, por exemplo `10.0.1.222:8330`.
* `CHAVE_PRIVADA`: caminho da chave privada usada para assinar ações.
* `INTERVALO_SEGUNDOS`: intervalo entre ciclos; o padrão atual é `60` segundos.
* `ARQUIVO_DENUNCIAS`: mantenha `Path("denuncias.json")`. O processamento em `main.py` também usa esse nome relativo ao diretório atual.

Execute os scripts a partir da raiz do repositório para que o arquivo `denuncias.json` seja encontrado no local esperado. A chave pública correspondente deve estar disponível com o sufixo `.pub`.

### Configuração Automatizada do Ambiente (UFW e Fail2ban)

Para que o orquestrador consiga manipular o firewall e para que o Fail2ban consiga acionar o nosso projeto, execute o script de instalação automatizada na raiz do repositório:

```bash
sudo python3 setup.py
```

*(Nota: O script deve ser executado com `sudo` a partir do seu usuário comum do sistema, pois ele detecta o seu usuário para liberar as permissões exatas no UFW e criar as actions do Fail2ban).*

Retorno apos rotinas de `setup.py` funcionarem corretamente:

``` bash
freechains@freechains:~/Firewall-Colaborativo$ sudo python3 setup.py
Iniciando configuração automatizada...
 -> Usuário detectado: freechains
 -> Caminho do script: /home/freechains/Firewall-Colaborativo/firewall.py
 -> [OK] Regra do UFW adicionada ao sudoers.
 -> [OK] Action do Fail2ban (freechains_ufw.conf) criada.
 -> [OK] Serviço Fail2ban recarregado.

Configuração concluída com sucesso!
```

Após a execução com sucesso do script, basta habilitar a ação recém-criada na cadeia (jail) do Fail2ban que você deseja proteger.
Cadeias do Fail2ban ficam localizadas em `/etc/fail2ban/jail.local`.

Exemplo para habilitar testes de brute-force de SSH, no seu arquivo de configuração do Fail2ban:

```ini
[sshd]
enabled = true
action = %(action_)s
         freechains_ufw
```

Depois de adicionar a ação na jail, confira o status:

```bash
sudo fail2ban-client reload
sudo fail2ban-client status sshd
```

### Execução

Inicie o orquestrador a partir da raiz do projeto:

```bash
python3 orquestracao.py
```

Ele executará os ciclos continuamente, aguardando `INTERVALO_SEGUNDOS` entre eles. Encerre com `Ctrl+C`.

Para bloquear manualmente um IP no UFW e reportá-lo na cadeia, informe o timestamp Unix e o motivo:

```bash
python3 firewall.py ban 198.51.100.25 "$(date +%s)" "SSH brute force"
```

Para remover o bloqueio local do UFW:

```bash
python3 firewall.py unban 198.51.100.25
```

O comando `unban` remove somente a regra local; ele não publica uma ação de desbloqueio na cadeia.

---

## b. O que foi Implementado

* **Operações do substancias do Protocolo Freechains:** Rotinas de automação para clonagem incremental (`chains add clone`), recepção de blocos (`sync recv`), postagens normais e assistidas (`--beg`), likes e dislikes em ações e autores, além de leitura de metadados e inspeção de payloads.
* **Processamento Incremental Baseado em Deltas(Na minha cabeça se chama diferenças):** Mecanismo com verificação de conjuntos de hashes (`blocos_ja_vistos`), garantindo que apenas transações novas sejam processadas após a primeira carga, economizando I/O de disco e chamadas de subprocessos.
* **Prevenção de Reprocessamento e Punições Repetidas:** Controle de duplicação através das chaves `"aplicado_ufw"` e `"blocos_ja_punidos"` salvas em `denuncias.json`, impedindo duplicações de regras no UFW e evitando gastos de reputação com dislikes redundantes.
* **Reputação e Avaliação Ponderada:** Cálculo de taxa de erro individual considerando pesos de severidade (erros de formatação de timestamp, injeção de IPs privados ou payloads não-JSON), classificando autores entre "colaborador" e "infrator". Isso deu bastante trabalho !
* **Regras rígidas para entrada de colaboradores (`--beg`):** Rotina de triagem de mendigos que desqualifica o autor após qualquer payload defeituoso e exige volume mínimo de postagens legítimas para acolhimento de novos nós na cadeia.
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
* **JSON:** Formato estruturado para payloads de rede nas transações Freechains e para persistência do estado no nó.
