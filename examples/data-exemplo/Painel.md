# Painel

Tabelas que se atualizam sozinhas a partir dos registros. Requer o plugin da comunidade **Dataview**
(Configurações → Plugins da comunidade → Procurar → Dataview → Instalar e ativar).

## Compromissos em aberto

```dataview
TABLE prazo, pessoa AS "com"
FROM "compromissos"
WHERE status = "aberto"
SORT prazo ASC
```

## Entregas aguardando métrica

```dataview
TABLE data
FROM "entregas"
WHERE status = "aguardando_metrica"
SORT data ASC
```

## Entregas dos últimos 90 dias

```dataview
TABLE data, metrica, metrica_categoria AS "categoria", metrica_confianca AS "confiança"
FROM "entregas"
WHERE data >= date(today) - dur(90 days)
SORT data DESC
```

## Decisões recentes

```dataview
TABLE data, relacionados
FROM "decisoes"
SORT data DESC
LIMIT 10
```

## Feedbacks recebidos

```dataview
TABLE data, pessoa AS "de", categoria
FROM "feedbacks"
SORT data DESC
```

## Glossário

```dataview
TABLE categoria, aliases
FROM "conceitos"
SORT categoria ASC, file.name ASC
```

## Pessoas

```dataview
TABLE categoria AS "cargo / área"
FROM "pessoas"
SORT file.name ASC
```
