# Casos de uso

Guia prático do CareerTracker MCP. Cada seção mostra quando usar, um exemplo de conversa e o que fica gravado.

Os exemplos usam a skill `conselheiro-executivo` ([instalação](../README.md#instalando-a-skill)) e uma empresa de software fictícia, com um Portal do Cliente, uma API de Integrações e um provedor externo de autenticação.

A skill roda na conversa principal do Claude Code. Por isso os diálogos abaixo são reais: o Claude pergunta a métrica que falta, mostra o rascunho e espera sua confirmação antes de gravar. Ela entra sozinha quando você fala de entregas, decisões, feedbacks ou pede um 1:1, ou pode ser chamada com `/conselheiro-executivo <o que aconteceu>`.

Com outra skill, o fluxo é o mesmo: por baixo, são sempre as quatro ferramentas (`registrar`, `atualizar`, `buscar`, `pendencias`) e os quatro prompts.

## Índice

**Registrar**
1. [Entrega com métrica](#1-entrega-com-métrica)
2. [Entrega sem métrica (ainda)](#2-entrega-sem-métrica-ainda)
3. [Trabalho antigo](#3-trabalho-antigo)
4. [Glossário do negócio](#4-glossário-do-negócio)
5. [Pessoas e stakeholders](#5-pessoas-e-stakeholders)
6. [Decisões](#6-decisões)
7. [Feedbacks recebidos](#7-feedbacks-recebidos)
8. [Compromissos](#8-compromissos)

**Consultar**

9. [Perguntar ao oráculo](#9-perguntar-ao-oráculo)
10. [Pendências e lacunas](#10-pendências-e-lacunas)

**Gerar documentos**

11. [Preparar um 1:1](#11-preparar-um-11)
12. [Relatório de período](#12-relatório-de-período)
13. [Briefing antes de uma reunião](#13-briefing-antes-de-uma-reunião)
14. [Dossiê de promoção](#14-dossiê-de-promoção)

**Manter e visualizar**

15. [Corrigir, completar e renomear](#15-corrigir-completar-e-renomear)
16. [Visualizar no Obsidian](#16-visualizar-no-obsidian)

---

## 1. Entrega com métrica

**Quando:** você terminou algo e já sabe o impacto.

```
Você:   Reduzi o tempo de deploy de 40min para 8min paralelizando os testes e cacheando o build.

Claude: [buscar(tipo="conceito", limite=200)]
        Situação: o [[Pipeline de deploy]] levava 40min e atrasava correções para os clientes do [[Portal do Cliente]].
        Tarefa: reduzir o tempo de deploy sem perder cobertura da [[API de Integrações]].
        Ação: testes paralelizados por módulo, sharding da suíte e cache de build.
        Resultado: deploy em 8min, com a mesma cobertura.
        Métrica: Redução de 80% no tempo de deploy (tempo · 40min → 8min · medido)
        Confirma?

Você:   Confirmo.

Claude: [registrar(tipo="entrega", ...)]
        Registrado. Tempo de entrega é o número que a liderança leva para a diretoria todo mês: essa entrega entra direto nessa conversa.
```

**O que fica gravado:** `entregas/2026-07-22 Deploy de 40min para 8min.md`, com `status: consolidado` e os campos `metrica_*` no frontmatter.

**Dica:** use `confianca: estimado` sempre que o número for aproximado. No relatório isso aparece marcado, e ninguém é pego inflando resultado.

---

## 2. Entrega sem métrica (ainda)

**Quando:** o trabalho está pronto, mas o impacto só vai aparecer depois (monitoramento, prevenção, melhoria de processo).

```
Você:   Coloquei no ar o monitoramento sintético do provedor de autenticação.

Claude: Ainda não dá para dizer o impacto: monitoramento só prova valor quando pega uma falha.
        Já houve algum alerta? Quanto tempo levava para perceber uma queda do login antes?

Você:   Antes era por reclamação de cliente, umas 2h. Ainda não teve alerta.

Claude: [registrar(tipo="entrega", ..., sem metrica)]
        Registrado como aguardando métrica. No primeiro incidente, me conta o tempo de detecção.
```

**O que fica gravado:** `status: aguardando_metrica`. A entrega aparece em `pendencias()` até ganhar uma métrica.

**Semanas depois:**

```
Você:   O provedor caiu ontem e o monitoramento alertou em 3 minutos.

Claude: [pendencias()] → encontrou "Monitoramento sintético do provedor de autenticação"
        [atualizar("2026-09-02-monitoramento-sintetico-do-provedor-de-autenticacao",
                   metrica={descricao: "Detecção de falha no login de ~2h para 3min", categoria: "tempo",
                            antes: "~2h", depois: "3min", confianca: "medido"},
                   acrescentar="Primeiro incidente detectado em 3min, antes de qualquer cliente reclamar.")]
        Atualizado. Status: consolidado.
```

---

## 3. Trabalho antigo

**Quando:** você começou a usar o MCP com a casa já andando e quer montar o histórico.

```
Você:   Quero registrar coisas de antes. Em junho implementei testes de contrato na API de Integrações,
        e no primeiro mês eles pegaram duas quebras de contrato antes do deploy.

Claude: [registrar(tipo="entrega", data="2026-06-10", ...)]
```

O parâmetro `data` aceita qualquer dia passado (AAAA-MM-DD). O arquivo recebe essa data no nome e os relatórios de período o encontram normalmente.

**Dica:** faça isso em lotes. Abra o histórico de PRs, tickets ou a última avaliação de desempenho e peça ao Claude para registrar um item por vez.

---

## 4. Glossário do negócio

**Quando:** alguém explicou como a empresa ganha dinheiro, um produto, um sistema, um parceiro, uma regulação, um KPI ou um jargão interno.

```
Você:   O provedor de autenticação é o serviço externo que faz o login dos clientes. Se ele cai, ninguém entra no portal.

Claude: [buscar(texto="provedor de autenticação", tipo="conceito")] → não existe
        [registrar(tipo="conceito", titulo="Provedor de autenticação", categoria="parceiro", ...)]
        Mapeei "Provedor de autenticação" (parceiro).
```

**Categorias úteis:** `produto`, `sistema`, `processo`, `squad`, `parceiro`, `regulacao`, `kpi`, `jargao`, `carreira`. São texto livre; o importante é ser consistente.

**Aliases:** siglas e jeitos diferentes de falar o mesmo termo.

```
registrar(tipo="conceito", titulo="Pipeline de deploy", aliases=["esteira", "pipeline"], ...)
```

A partir daí, `[[esteira]]` em qualquer registro é gravado como `[[Pipeline de deploy|esteira]]` e aponta para a página certa no grafo.

**Sem duplicatas:** registrar um termo que já existe (pelo título ou por alias) é recusado:

```
Não registrado: 'portal' já existe como 'Portal do Cliente'. Use atualizar('Portal do Cliente', ...) para complementar.
```

**A definição mudou?** Use `acrescentar` para manter o histórico:

```
atualizar("Portal do Cliente", acrescentar="Após a reorganização de outubro, o Portal do Cliente passou a incluir o app mobile.")
```

---

## 5. Pessoas e stakeholders

**Quando:** alguém aparece com frequência nas suas conversas e decisões.

```
Você:   Mudanças no portal passam por Head de Produto, que só prioriza vendo o impacto no churn.

Claude: [registrar(tipo="pessoa", titulo="Head de Produto", categoria="Produto",
                   conteudo="Responsável pelo roadmap do [[Portal do Cliente]]. Quer ver impacto em
                             [[Churn mensal]] antes de priorizar mudanças.")]
```

O que vale registrar: o que a pessoa valoriza, como prefere receber informação e do que tem medo. É o que alimenta o [briefing](#13-briefing-antes-de-uma-reunião).

> Os dados ficam só na sua máquina, mas continue registrando apenas informação profissional.

---

## 6. Decisões

**Quando:** a empresa, a área ou o time decidiu algo relevante, principalmente se você influenciou.

```
Você:   Decidiram contratar um segundo provedor de autenticação por causa das quedas de julho.
        Aumentar a duração das sessões foi descartado pela segurança. Eu levei os dados de indisponibilidade.

Claude: [registrar(tipo="decisao", titulo="Adotar segundo provedor de autenticação como contingência",
                   relacionados=["Provedor de autenticação", "Head de Produto", "Portal do Cliente"], ...)]
```

**Estrutura recomendada do conteúdo:** contexto, decisão, alternativas descartadas (e por quê), quem decidiu, seu papel.

Um ano depois, "por que não aumentamos a duração das sessões?" vira `buscar(texto="sessões", tipo="decisao")`.

---

## 7. Feedbacks recebidos

**Quando:** recebeu elogio ou ponto de desenvolvimento, em 1:1, avaliação ou de passagem.

```
Você:   No 1:1, a liderança disse que a análise do provedor de autenticação foi ótima mas chegou tarde.
        Pediu para eu trazer riscos na primeira semana.

Claude: [registrar(tipo="feedback", titulo="Comunicar riscos mais cedo", pessoa="Head de Engenharia",
                   categoria="desenvolvimento", conteudo="\"A análise do provedor foi excelente, mas chegou...\"")]
```

**Por que registrar:** no próximo ciclo, o `dossie_promocao` e o `preparar_1on1` cruzam esses pontos com as entregas seguintes e mostram se o ponto foi endereçado.

---

## 8. Compromissos

**Quando:** você prometeu algo com prazo, principalmente para a liderança.

```
Você:   Fiquei de apresentar o plano de testes do segundo provedor até o fim do mês.

Claude: [registrar(tipo="compromisso", titulo="Apresentar plano de testes do Q4",
                   pessoa="Head de Engenharia", prazo="2026-09-30")]
```

Status padrão `aberto`. Ao cumprir:

```
Você:   Apresentei o plano hoje.
Claude: [atualizar("Apresentar plano de testes do Q4", status="concluido")]
```

Compromissos vencidos aparecem em destaque em `pendencias()`. Compromissos cumpridos também contam como evidência de confiabilidade no 1:1.

---

## 9. Perguntar ao oráculo

A ferramenta `buscar` combina filtros. Na prática, você pergunta e o Claude monta a busca.

| Pergunta | Busca |
|---|---|
| "O que já fiz na API de Integrações?" | `buscar(relacionado="API de Integrações", tipo="entrega")` |
| "O que é o Portal do Cliente e por que importa?" | `buscar(texto="Portal do Cliente", tipo="conceito", detalhado=True)` |
| "Por que decidimos pelo segundo provedor?" | `buscar(texto="provedor", tipo="decisao", detalhado=True)` |
| "O que entreguei no último trimestre?" | `buscar(tipo="entrega", de="2026-07-01", ate="2026-09-30")` |
| "Que feedbacks de desenvolvimento recebi?" | `buscar(tipo="feedback", texto="desenvolvimento")` |
| "Tudo que envolve Head de Produto" | `buscar(relacionado="Head de Produto", detalhado=True)` |

Detalhes:
- `texto` ignora acentos e maiúsculas, e exige todas as palavras (`"provedor autenticacao"` só traz registros com as duas).
- `relacionado` aceita título ou alias e traz os registros que citam a página, pelos `[[links]]` do texto ou pelos campos `relacionados`/`pessoa`.
- Sem `detalhado`, vem uma linha por registro (barato para o contexto da IA). Com `detalhado=True`, vem o conteúdo inteiro.

---

## 10. Pendências e lacunas

```
Você:   O que está pendente?

Claude: [pendencias()]
```

```
## Entregas aguardando métrica
- Monitoramento sintético do provedor de autenticação (id: `2026-09-02-monitoramento-sintetico-do-provedor-de-autenticacao`, há 9 dias)

## Compromissos em aberto
- Apresentar plano de testes do Q4 com [[Head de Engenharia]] · vence em 19 dias (id: `2026-09-05-apresentar-plano-de-testes-do-q4`)

## Lacunas no glossário (citados sem página)
- Squad Plataforma (citado 2x)
```

A terceira seção mostra **o que você ainda não entende da empresa**: nomes que aparecem nos seus registros mas nunca foram explicados. No grafo do Obsidian, são os nós cinza.

**Hábito sugerido:** peça as pendências toda sexta-feira.

---

## 11. Preparar um 1:1

**Pelo prompt:**

```
/mcp__career-tracker__preparar_1on1 tecnica 30
```

**Ou em linguagem natural:** "prepara meu 1:1 de amanhã com a liderança técnica".

O prompt manda a IA:
1. buscar entregas, decisões e feedbacks do período;
2. rodar `pendencias()`;
3. ler a página da liderança, se existir.

**Resultado esperado:**

```
## Três temas de impacto
1. Tempo de entrega: deploy de 40min para 8min (medido)...
2. Confiabilidade da API: 2 quebras de contrato interceptadas antes de afetar clientes...
3. Resiliência do login: monitoramento sintético no ar (impacto a medir)...

## Abertura
"Neste trimestre ataquei os dois maiores riscos do Portal do Cliente: tempo de entrega e dependência do provedor de autenticação."

## Compromissos
- Plano de testes do Q4: em aberto, vence 30/09.

## Ponto de desenvolvimento
- Comunicar riscos mais cedo (feedback de 20/08). O que mudou desde então...

## Pedidos
- ...
```

Com `audiencia="executiva"`, o mesmo conteúdo sai sem detalhes técnicos, com foco em receita, risco, custo e cliente.

---

## 12. Relatório de período

**Quando:** status semanal, review trimestral, autoavaliação do ciclo de desempenho.

```
/mcp__career-tracker__relatorio_periodo 2026-07-01 2026-09-30 executiva
```

A IA busca tudo do período com o vocabulário da empresa e monta:
- resumo executivo;
- resultados agrupados por tema (produto, sistema ou objetivo em comum);
- decisões relevantes e o seu papel nelas;
- entregas com impacto a medir;
- próximos passos.

Métricas da mesma categoria são somadas só quando faz sentido, e as estimadas vêm marcadas.

---

## 13. Briefing antes de uma reunião

**Quando:** antes de falar com alguém de outra área, um diretor ou um stakeholder que você vê pouco.

```
/mcp__career-tracker__briefing_stakeholder Head de Produto
```

Resultado: quem é a pessoa e o que valoriza, o histórico de decisões e feedbacks com essa pessoa, suas entregas que tocam essa área (com métricas), os compromissos em aberto e três pontos para levar à reunião.

Se a pessoa ainda não tem página, o briefing sugere criar uma.

---

## 14. Dossiê de promoção

**Primeiro, mapeie a trilha de carreira** como conceitos de categoria `carreira`:

```
Você:   O próximo nível é Staff Engineer. As expectativas são: estratégia técnica de uma área inteira,
        influenciar arquitetura com dados, desenvolver o time e comunicar risco técnico para a diretoria.

Claude: [registrar(tipo="conceito", titulo="Staff Engineer", categoria="carreira", conteudo="## Expectativas\n- ...")]
```

**Depois:**

```
/mcp__career-tracker__dossie_promocao Staff Engineer
```

Resultado:

| Expectativa | Evidências | Força |
|---|---|---|
| Influencia arquitetura com dados | Decisão "segundo provedor de autenticação" (08/2026), dados de indisponibilidade | Forte |
| Comunica risco técnico em linguagem de negócio | Testes de contrato: "2 quebras de contrato interceptadas antes de afetar clientes" | Média |
| Desenvolve outras pessoas | — | **Lacuna** |

E ainda: sugestões concretas para cobrir as lacunas, os pontos de desenvolvimento (e se foram endereçados) e uma narrativa de promoção em um parágrafo.

**Dica:** rode o dossiê a cada trimestre, não só na semana da avaliação. As lacunas viram o seu plano de desenvolvimento.

---

## 15. Corrigir, completar e renomear

`atualizar` localiza o registro pelo `id` ou pelo título exato e muda só o que for passado.

| Situação | Chamada |
|---|---|
| Chegou a métrica de uma entrega pendente | `atualizar(id, metrica={...})` → status vira `consolidado` |
| Corrigir o texto inteiro | `atualizar(id, conteudo="...")` |
| Complementar sem perder o histórico | `atualizar(id, acrescentar="...")` → nova seção `## Atualização AAAA-MM-DD` |
| Fato registrado com a data errada | `atualizar(id, data="2026-06-10")` → o arquivo é renomeado |
| Compromisso cumprido ou cancelado | `atualizar(id, status="concluido")` |
| Conceito mudou de nome | `atualizar("API de Integrações", titulo="API Pública")` |

Ao renomear um conceito ou pessoa, o servidor corrige os `[[links]]` em todos os outros registros:

```
Atualizado: [conceito] API Pública (id: api-de-integracoes). Links atualizados em 4 registro(s).
```

O `id` não muda ao renomear, então referências antigas continuam funcionando.

Se dois registros tiverem o mesmo título, o servidor pede o `id`:

```
Erro: Mais de um registro com o título 'Paralelização da suíte'. Use o id: 2026-08-01-paralelizacao-da-suite, 2026-08-01-paralelizacao-da-suite-2
```

**Editar à mão:** tudo pode ser editado direto no Obsidian ou em qualquer editor. O servidor relê os arquivos a cada chamada. Notas criadas à mão também entram na base, desde que tenham `tipo` no frontmatter.

---

## 16. Visualizar no Obsidian

1. No Obsidian: **Abrir pasta como cofre** → `data/`.
2. **Grafo** (`Ctrl+G`):
   - conceitos e pessoas são os nós mais conectados, as "peças" da organização;
   - entregas, decisões e feedbacks se ligam a eles;
   - nós cinza são termos citados sem página (as lacunas do [item 10](#10-pendências-e-lacunas)).
   - Dica: em *Grupos*, pinte por pasta (`path:conceitos`, `path:entregas`, `path:pessoas`) para distinguir os tipos.
3. **Menções (backlinks):** abra `conceitos/Provedor de autenticação.md` e veja no painel lateral a decisão, a entrega, o feedback e o compromisso que citam o provedor. É a história daquele assunto na empresa.
4. **Propriedades:** o topo de cada nota mostra `status`, `metrica`, `prazo` etc., editáveis ali mesmo.

> Não ative Obsidian Sync nem coloque `data/` em pasta sincronizada sem checar a política da empresa.
