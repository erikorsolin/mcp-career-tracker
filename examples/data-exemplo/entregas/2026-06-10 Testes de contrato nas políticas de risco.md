---
id: 2026-06-10-testes-de-contrato-nas-politicas-de-risco
tipo: entrega
titulo: Testes de contrato nas políticas de risco
data: 2026-06-10
status: consolidado
metrica: 2 falhas de política de crédito interceptadas antes de produção
metrica_categoria: risco
metrica_confianca: medido
relacionados:
- '[[Motor de crédito white-label]]'
- '[[Esteira de regressão]]'
- '[[Head de Risco]]'
tags:
- testes-de-contrato
- ia
criado_em: '2026-09-11T16:59:12'
atualizado_em: '2026-09-11T16:59:12'
---

**Situação:** o [[Motor de crédito white-label]] era validado manualmente a cada mudança de política de parceiro.

**Tarefa:** garantir que nenhuma política quebrada chegasse a produção.

**Ação:** suíte de testes de contrato gerada com apoio de IA a partir das políticas de cada parceiro, rodando na [[Esteira de regressão]].

**Resultado:** duas políticas com limite incorreto interceptadas antes do deploy no primeiro mês.
