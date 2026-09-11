---
id: 2026-07-22-esteira-de-regressao-de-4h-para-12min
tipo: entrega
titulo: Esteira de regressão de 4h para 12min
data: 2026-07-22
status: consolidado
metrica: Redução de 95% no ciclo de validação
metrica_categoria: tempo
metrica_antes: 4h
metrica_depois: 12min
metrica_confianca: medido
relacionados:
- '[[Esteira de regressão]]'
- '[[Motor de crédito white-label]]'
- '[[Squad Crédito]]'
tags:
- ci-cd
criado_em: '2026-09-11T16:59:12'
atualizado_em: '2026-09-11T16:59:12'
---

**Situação:** a [[Esteira de regressão|esteira]] levava 4h por release e atrasava correções para os parceiros do [[BaaS]].

**Tarefa:** reduzir o lead time sem perder cobertura do [[Motor de crédito white-label|motor de crédito]].

**Ação:** execução paralela por parceiro, sharding da suíte e cache de fixtures.

**Resultado:** validação em 12min por release, com a mesma cobertura.
