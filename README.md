# Firewall P2P com Freechains

Protótipo experimental de compartilhamento de denúncias de IPs usando uma cadeia Freechains, com aplicação local de bloqueios pelo UFW. O projeto é voltado a aprendizado e testes em ambiente controlado; não deve ser tratado como uma solução pronta para produção.

## Objetivo

Permitir que nós de uma rede Freechains publiquem denúncias estruturadas, sincronizem relatos de um par remoto, avaliem o histórico dos autores e apliquem no firewall local os bloqueios selecionados pela lógica do projeto.

## Fluxo atual

O daemon executa periodicamente estas etapas:

1. Sincroniza a cadeia com o par remoto e analisa novas mensagens do tipo `post`.
2. Valida o JSON, o endereço IP e o timestamp dos relatos e atualiza os perfis em `denuncias.json`.
3. Avalia infrações dos autores e, quando possível, publica dislikes na cadeia.
4. Aplica no UFW os IPs de relatos válidos de autores classificados como colaboradores. Uma falha ao executar o bloqueio não é marcada como sucesso e pode ser tentada novamente no ciclo seguinte.
5. Avalia mensagens da fila `begs` segundo as regras configuradas no código.

Um relato publicado tem este formato:

```json
{
  "ip_malicioso": "203.0.113.10",
  "motivo": "Exemplo de motivo",
  "timestamp": "2026-10-18 12:30:00"
}
```

## Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Comandos Freechains, publicação e busca de relatos, análise de perfis, punições e aplicação de bloqueios recebidos. |
| `orquestracao.py` | Ciclo periódico que sincroniza a cadeia, avalia relatos e aciona o UFW. |
| `firewall.py` | Comandos locais de bloqueio e desbloqueio usando o UFW. |
| `utils.py` | Validação de IPs e timestamps e funções auxiliares. |
| `denuncias.json` | Estado local incremental dos perfis, denúncias e bloqueios já aplicados. |

## Pré-requisitos

- Linux ou WSL com uma distribuição Linux.
- Python 3.10 ou superior.
- CLI e daemon do Freechains instalados e configurados, com acesso à cadeia e ao par remoto.
- UFW instalado e permissões `sudo` para alterar regras de firewall.
- Fail2ban, somente se ele for usado para acionar o comando `firewall.py ban`.
- Chaves Freechains correspondentes; a consulta de reputação também precisa encontrar o arquivo `.pub` associado.

O código Python usa apenas a biblioteca padrão; não há dependências Python externas declaradas.

## Configuração

Antes de iniciar, ajuste no bloco principal de `orquestracao.py`:

- `NOME_CADEIA`: cadeia a consultar.
- `ENDERECO_REMOTO`: endereço e porta do par Freechains.
- `ARQUIVO_DENUNCIAS`: caminho do estado local.
- `CHAVE_PRIVADA`: caminho da chave usada para assinar ações.
- `INTERVALO_SEGUNDOS`: intervalo entre ciclos.

O código também contém limites experimentais, como a reputação mínima para publicar um relato como post regular e a quantidade mínima de reports para aprovar um autor na fila `begs`. Revise esses valores em `main.py` antes de qualquer experimento.

Execute os comandos a partir da pasta do projeto, pois `denuncias.json` é carregado por caminho relativo.

### Execução automatizada com `sudo`

O daemon pode precisar executar o UFW sem interação. No Debian ou Kali, edite o arquivo `sudoers` com `visudo`:

```bash
sudo visudo
```

Adicione uma regra para o usuário que executará o projeto, substituindo `seu_usuario` pelo nome correto:

```sudoers
seu_usuario ALL=(ALL) NOPASSWD: /usr/sbin/ufw
```

Essa regra permite que o usuário execute o UFW como administrador sem senha. Conceda-a somente a uma conta confiável: o acesso ao UFW permite alterar as regras de firewall da máquina.

## Execução

Inicie o daemon de orquestração:

```bash
python3 orquestracao.py
```

O daemon roda continuamente; use `Ctrl+C` para encerrá-lo.

Para administrar uma regra localmente:

```bash
python3 firewall.py ban 203.0.113.10 1792345800 "Exemplo de motivo"
python3 firewall.py unban 203.0.113.10
```

No comando `ban`, o timestamp e o motivo são opcionais. Após aplicar o bloqueio local com sucesso, o script também chama `reportar_ip` para publicar ou confirmar a denúncia na cadeia Freechains. Essa integração usa valores definidos diretamente em `firewall.py`: cadeia `#firewall-test` e chave `/home/kali/henrxque`; ajuste-os para o seu ambiente. O comando `unban` remove apenas a regra local e não publica uma atualização na cadeia.

## Limitações e segurança

- A configuração inicial de cadeia, par, chave e intervalo está fixa no código e deve ser ajustada para cada ambiente.
- A propagação explícita com `sync send` está desativada no orquestrador; a sincronização configurada usa `sync recv`.
- A validação estrutural de um relato não comprova que o IP seja malicioso. Relatos de autores classificados como colaboradores podem resultar em bloqueios automáticos no UFW local.
- Os critérios de reputação, punição e aprovação de `begs` são experimentais. Teste-os numa cadeia isolada e com regras de firewall que você possa reverter.
- `denuncias.json` contém o estado usado para evitar reprocessamento. Faça cópias antes de limpar ou alterar esse arquivo.
