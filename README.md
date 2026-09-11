# CareerTracker MCP

Servidor [MCP](https://modelcontextprotocol.io) local que funciona como um **oráculo de tudo o que você faz dentro de uma organização**: entregas e seus impactos, decisões, feedbacks, compromissos, o glossário do negócio e as pessoas com quem você trabalha.

O escopo é **uma empresa**, não a carreira inteira. A ideia é facilitar relatórios, reuniões com a gerência e a diretoria, o crescimento dentro da empresa e o entendimento do modelo de negócio.

Cada registro é um arquivo Markdown. A pasta `data/` pode ser aberta no [Obsidian](https://obsidian.md) para ver o grafo da organização.

> Guia completo com exemplos de cada caso de uso: [`doc/casos-de-uso.md`](doc/casos-de-uso.md)

## Uso no dia a dia

Você só precisa fazer três coisas, sempre em linguagem natural:

1. **Contar o que aconteceu.** O Claude decide se é entrega, decisão, feedback, compromisso, conceito ou pessoa.
2. **Perguntar.** "O que já fiz na API de Integrações?", "Por que trocamos de provedor de autenticação?"
3. **Pedir um documento.** "Prepara meu 1:1", "Relatório do trimestre", "Dossiê para promoção".

```
Você:   hoje a diretoria decidiu contratar um segundo provedor de autenticação por risco de indisponibilidade
Claude: registrei como decisão, ligada a [[Provedor de autenticação]] e [[Portal do Cliente]].

Você:   terminei o monitoramento sintético do provedor de autenticação, ainda não tenho números
Claude: registrei a entrega como "aguardando métrica". Ela fica nas pendências até ter o número.

Você:   prepara meu 1:1 de amanhã com a liderança técnica
Claude: [busca entregas, decisões, feedbacks e compromissos do período e monta a pauta]
```

## Como funciona

| Camada | Responsabilidade | Onde vive |
|---|---|---|
| **Skill** | Como a IA usa o servidor: papel, regras (ex: métrica obrigatória), fluxo, tom | `~/.claude/skills/` (fora deste repositório) |
| **Servidor MCP** | Grava, busca e liga registros. Sem regra de negócio | `server.py` |
| **Dados** | Os fatos da sua empresa, um `.md` por registro | `data/` (ignorado pelo git) |

O servidor é agnóstico a área, empresa e setor. Para trocar de contexto, troque a skill e a pasta de dados.

## Ferramentas

| Ferramenta | O que faz |
|---|---|
| `registrar(tipo, titulo, conteudo, ...)` | Cria um registro. Tipos: `entrega`, `decisao`, `feedback`, `compromisso`, `conceito`, `pessoa`. Aceita `data` passada, `metrica`, `relacionados`, `prazo`, `pessoa`, `categoria`, `aliases`, `tags`. |
| `atualizar(id, ...)` | Altera só os campos informados. `acrescentar` adiciona uma seção datada sem apagar o histórico. Renomear um conceito ou pessoa corrige os links em todos os registros. |
| `buscar(texto, tipo, de, ate, status, relacionado, detalhado, limite)` | Consulta com filtros combináveis. `relacionado="Portal do Cliente"` traz tudo que cita o Portal do Cliente. |
| `pendencias()` | Entregas aguardando métrica, compromissos em aberto (vencidos e próximos) e termos citados sem página no glossário. |

Regras do próprio servidor, que valem com ou sem a skill:
- entrega sem `metrica` fica com status `aguardando_metrica`;
- conceitos e pessoas não são sobrescritos (nem por alias);
- `[[portal]]` é gravado como `[[Portal do Cliente|portal]]`, para que aliases e variações de maiúsculas resolvam no Obsidian.

## Prompts (relatórios prontos)

Modelos que orientam a IA a buscar os dados certos e montar o documento. No Claude Code, digite `/` e procure por `career-tracker`:

| Prompt | Argumentos | Resultado |
|---|---|---|
| `preparar_1on1` | `audiencia` (`tecnica`/`executiva`), `dias` | Três temas de impacto, abertura, compromissos, ponto de desenvolvimento e pedidos |
| `relatorio_periodo` | `de`, `ate`, `audiencia` | Resumo executivo, resultados por tema, decisões e impacto a medir |
| `dossie_promocao` | `nivel_alvo` | Tabela competência x evidência, lacunas e narrativa de promoção |
| `briefing_stakeholder` | `pessoa` | O que a pessoa valoriza, histórico, entregas relacionadas e compromissos |

Exemplo: `/mcp__career-tracker__preparar_1on1 executiva 30`

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

Confira com `claude mcp list` ou, dentro de uma sessão, com `/mcp`. Depois de atualizar o `server.py`, reconecte o servidor pelo `/mcp`.

Variável de ambiente opcional (passe com `-e NOME=valor` no `claude mcp add`):

| Variável | Padrão | Função |
|---|---|---|
| `CAREER_TRACKER_DATA_DIR` | `data/` ao lado do `server.py` | Pasta dos registros (ex: uma pasta criptografada) |

> **Segurança:** os arquivos em `data/` contêm informação interna da empresa. A pasta inteira está no `.gitignore`. Não a coloque em sincronização de nuvem pessoal (Obsidian Sync, Google Drive, Dropbox) sem checar a política da empresa.

## Instalando a skill

A skill ensina o Claude a usar o servidor: quando registrar cada tipo de fato, como escrever uma entrega em STAR, quando exigir métrica e como montar um 1:1. Este repositório traz um exemplo, o **Conselheiro Executivo de Carreira**, para quem trabalha com tecnologia.

```bash
mkdir -p ~/.claude/skills
cp -r examples/skills/conselheiro-executivo ~/.claude/skills/
```

A skill fica disponível em todos os seus projetos e pode ser usada de dois jeitos:

- **Automático:** conte uma entrega, decisão, feedback ou compromisso, ou peça um 1:1. O Claude carrega a skill pela descrição dela.
- **Explícito:**
  ```
  /conselheiro-executivo hoje reduzi o tempo de deploy de 40min para 8min
  ```

A skill roda na **conversa principal**. Por isso o Claude consegue perguntar a métrica que falta, mostrar o rascunho da entrega e esperar sua confirmação antes de gravar. Um subagente não serviria aqui: ele roda em contexto separado e só devolve um relatório final, sem pausar para perguntar nada.

Para outra área, copie a pasta, troque `name` e `description` no `SKILL.md` e ajuste o papel e as regras.

## Visualizando no Obsidian

1. Instale o [Obsidian](https://obsidian.md) (no Ubuntu: `.deb`, AppImage ou `flatpak install flathub md.obsidian.Obsidian`).
2. **Abrir pasta como cofre** → selecione `data/`.
3. Explore:
   - **Visão de grafo** (`Ctrl+G`): conceitos e pessoas no centro, com entregas e decisões ligadas a eles. Nós cinza são termos citados que ainda não têm página.
   - **Menções** (painel lateral) na página de um conceito: tudo que já foi feito ou decidido sobre ele.
   - **Propriedades** no topo de cada nota: status, métrica, prazo, editáveis à mão.

Edições feitas no Obsidian são lidas pelo servidor na próxima chamada, sem precisar reiniciar nada.

## Formato dos dados

```
data/
├── entregas/2026-07-22 Deploy de 40min para 8min.md
├── decisoes/2026-08-05 Adotar segundo provedor de autenticação como contingência.md
├── feedbacks/2026-08-20 Comunicar riscos mais cedo.md
├── compromissos/2026-09-05 Apresentar plano de testes do Q4.md
├── conceitos/API de Integrações.md
└── pessoas/Head de Engenharia.md
```

Conceitos e pessoas têm o nome exato do título, para que `[[Título]]` resolva no Obsidian. Os outros tipos levam a data na frente.

```markdown
---
id: 2026-07-22-deploy-de-40min-para-8min
tipo: entrega
titulo: Deploy de 40min para 8min
data: 2026-07-22
status: consolidado
metrica: Redução de 80% no tempo de deploy
metrica_categoria: tempo
metrica_antes: 40min
metrica_depois: 8min
metrica_confianca: medido
relacionados:
- '[[Pipeline de deploy]]'
- '[[Portal do Cliente]]'
tags:
- ci-cd
criado_em: '2026-09-11T17:02:10'
atualizado_em: '2026-09-11T17:02:10'
---

**Situação:** o [[Pipeline de deploy|pipeline]] levava 40min por deploy...
```

| Campo | Tipos | Significado |
|---|---|---|
| `id` | todos | Identificador estável (não muda ao renomear) |
| `data` | todos | Quando o fato aconteceu |
| `status` | entrega, compromisso | `aguardando_metrica`/`consolidado`; `aberto`/`concluido`/`cancelado` |
| `metrica*` | entrega | Descrição executiva, categoria, antes, depois, `medido`/`estimado` |
| `pessoa` | feedback, compromisso | Quem deu o feedback / para quem é o compromisso |
| `prazo` | compromisso | Data limite |
| `categoria` | conceito, pessoa, feedback | Tipo de conceito (`produto`, `sistema`, `kpi`, `carreira`...), cargo/área, `elogio`/`desenvolvimento` |
| `aliases` | conceito, pessoa | Sinônimos e siglas |
| `relacionados` | todos | Links para conceitos e pessoas |

Notas sem `tipo` no frontmatter são ignoradas pelo servidor, então você pode criar notas livres no mesmo cofre.

## Estrutura

```
mcp-career-tracker/
├── server.py                                    # Servidor MCP: tools e prompts
├── requirements.txt
├── data/                                        # Seus registros .md (ignorados pelo git)
├── doc/casos-de-uso.md                          # Guia de uso com exemplos
└── examples/
    └── skills/conselheiro-executivo/SKILL.md    # Skill de exemplo, para ~/.claude/skills/
```
