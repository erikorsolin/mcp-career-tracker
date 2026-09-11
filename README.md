# CareerTracker MCP

Servidor [MCP](https://modelcontextprotocol.io) local que dá ao Claude Code memória persistente sobre a sua carreira: um glossário do domínio em que você atua e um diário de impacto no formato STAR, com geração de Brag Documents para reuniões de 1:1.

O servidor é **agnóstico a área, empresa e setor**. Ele só persiste e lê JSON. Quem especializa o sistema é o que fica ao redor dele:

| Camada | Responsabilidade | Onde vive |
|---|---|---|
| **Agente** | O "chapéu" da IA: papel, regras, fluxo, tom | `~/.claude/agents/` (nível de usuário, fora deste repositório) |
| **Servidor MCP** | Persistência genérica, sem regra de negócio | `server.py` |
| **Dados** | Vocabulário e histórico da sua área | `data/*.json` (ignorado pelo git) |

Trocar de setor ou de objetivo é trocar o agente e o glossário. O servidor não muda.

## Ferramentas

| Ferramenta | O que faz |
|---|---|
| `mapear_conceito_dominio(termo, definicao, importancia_estrategica)` | Grava um conceito no glossário. |
| `consultar_base_de_negocios()` | Retorna o glossário completo. |
| `registrar_impacto_diario(situacao, tarefa, acao, resultado, metrica_negocio)` | Anexa um registro STAR datado ao diário. |
| `gerar_brag_document(dias=30)` | Monta o relatório em Markdown dos últimos N dias. |

O servidor não valida métricas nem obriga a consulta ao glossário antes de um registro. Essas regras pertencem ao agente.

## Instalação (Ubuntu)

Requer Python 3.10+ e o [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code).

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
git clone https://github.com/erikorsolin/mcp-career-tracker.git
cd mcp-career-tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Registrando o servidor no Claude Code

Use caminhos absolutos para que o servidor funcione a partir de qualquer pasta.

```bash
claude mcp add --scope user career-tracker -- "$(pwd)/venv/bin/python" "$(pwd)/server.py"
```

Confira com `claude mcp list` ou, dentro de uma sessão, com `/mcp`.

Variáveis de ambiente opcionais (passe com `-e NOME=valor` no `claude mcp add`):

| Variável | Padrão | Função |
|---|---|---|
| `CAREER_TRACKER_DATA_DIR` | `data/` ao lado do `server.py` | Diretório dos JSONs (ex: uma pasta criptografada) |
| `CAREER_TRACKER_LOG_FILE` | `career_log.json` | Nome do diário STAR |
| `CAREER_TRACKER_DOMAIN_FILE` | `dominio_financeiro.json` | Nome do glossário |

> **Segurança:** os JSONs em `data/` contêm vocabulário interno e métricas da empresa. Estão no `.gitignore` e nunca devem ser versionados nem compartilhados.

## Criando o agente no nível de usuário

O agente não faz parte do servidor. Ele é um arquivo Markdown em `~/.claude/agents/`, disponível em todos os seus projetos, que sabe quando e como chamar as ferramentas acima.

Este repositório traz um exemplo pronto, um **Conselheiro Executivo de Carreira** para QA no setor financeiro com estratégia Dual-Track (profundidade técnica para a gerência de engenharia, impacto de negócio para a diretoria). Ele bloqueia registros sem métrica de negócio e sempre consulta o glossário antes de gravar.

```bash
mkdir -p ~/.claude/agents
cp examples/agents/conselheiro-executivo.md ~/.claude/agents/
```

Dentro de qualquer sessão do Claude Code:

```
Use o agente conselheiro-executivo: hoje reduzi o tempo da esteira de regressão de 4h para 12min.
```

Para adaptar a outra área ou objetivo, copie o exemplo, troque o papel e as regras, e mantenha as chamadas às quatro ferramentas. O `/agents` do Claude Code lista e edita os agentes instalados.

> Subagentes rodam em contexto próprio e devolvem um relatório ao final, sem diálogo intermediário. Se preferir o fluxo interativo (confirmar o registro antes de gravar, escolher a audiência do 1:1), carregue o mesmo arquivo na conversa principal:
> `claude --append-system-prompt "$(cat ~/.claude/agents/conselheiro-executivo.md)"`

## Alimentando o glossário

O glossário é o que faz o agente falar a língua da sua empresa. Construa na conversa (o agente chama `mapear_conceito_dominio` sozinho) ou parta do exemplo do setor financeiro:

```bash
cp examples/dominio_financeiro.exemplo.json data/dominio_financeiro.json
```

## Exemplos de uso

### Mapear o domínio

```
Você: Nossa empresa opera como BaaS e tem um motor de crédito white-label que
      os parceiros configuram com as próprias políticas de risco.

Agente: Mapeei dois conceitos:
        - BaaS: principal linha de receita recorrente.
        - Motor de crédito white-label: maior exposição a risco financeiro e regulatório.
```

### Bloqueio sem métrica

```
Você: Hoje criei 25 testes automatizados para o fluxo de análise de crédito.

Agente: Ainda não posso registrar. "Criei 25 testes" descreve esforço, não impacto.
        1. Se uma falha nesse fluxo chegasse em produção, qual seria o prejuízo?
        2. Quanto tempo a validação manual levava antes?
```

### Registro com métrica

```
Você: A validação manual levava 4h por release. Agora roda em 12min na esteira.
      Uma falha no fluxo de decisão de crédito gera inadimplência.

Agente: [consulta o glossário]
        - Situação: motor de crédito white-label validado manualmente a cada release.
        - Tarefa: garantir a integridade das políticas de risco antes do deploy.
        - Ação: suíte orientada a contrato sobre as políticas de risco, gerada com
          apoio de IA e integrada à esteira com execução paralela por parceiro.
        - Resultado: validação de 4h para 12min por release, cobertura contínua
          do componente de maior exposição a risco.
        - Métrica: redução de 95% no ciclo de validação + mitigação de risco
          de inadimplência.
        Confirma?

Você: Confirmo.

Agente: [registra o impacto] Registrado.
```

### Preparar o 1:1

```
Você: Gera meu brag document dos últimos 30 dias.

Agente: O 1:1 é com liderança técnica ou executiva?

Você: Gerente de Engenharia, hands-on.

Agente: [gera o relatório]
        # Brag Document - Últimos 30 dias
        ...
        ## Narrativa para o 1:1
        Temas: testes de contrato no motor de crédito, paralelização da esteira,
        aderência regulatória.
        Abertura: "Neste mês ataquei o gargalo da esteira com testes de contrato
        e execução paralela, reduzindo a exposição a risco do motor de crédito."
```

## Formato dos dados

`career_log.json` é uma lista de registros:

```json
{ "data": "2026-09-11T10:32:00", "situacao": "...", "tarefa": "...",
  "acao": "...", "resultado": "...", "metrica_negocio": "..." }
```

`dominio_financeiro.json` é um dicionário indexado pelo termo em minúsculas:

```json
{ "baas": { "termo_original": "BaaS", "definicao": "...",
            "importancia_estrategica": "...", "data_mapeamento": "..." } }
```

## Estrutura

```
mcp-career-tracker/
├── server.py                                # Servidor MCP agnóstico
├── requirements.txt
├── data/                                    # JSONs locais (ignorados pelo git)
└── examples/
    ├── agents/conselheiro-executivo.md      # Agente de exemplo, para ~/.claude/agents/
    └── dominio_financeiro.exemplo.json      # Glossário de exemplo, setor financeiro
```
