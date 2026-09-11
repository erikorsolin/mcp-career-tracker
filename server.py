from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta
from typing import Literal
import os
import re
import tempfile
import unicodedata

import yaml

# ==========================================
# INICIALIZAÇÃO E CONFIGURAÇÃO
# ==========================================

mcp = FastMCP("CareerTracker")

# Cada registro é um arquivo Markdown com frontmatter YAML dentro de DATA_DIR.
# A pasta pode ser aberta diretamente como cofre (vault) do Obsidian: os
# [[links]] entre registros viram o grafo da organização.
# Resolvido a partir da pasta do próprio server.py (e não do diretório de trabalho),
# pois o Claude Code pode iniciar o servidor a partir de qualquer pasta.
# Variável de ambiente opcional:
#   CAREER_TRACKER_DATA_DIR   diretório dos dados (ex: uma pasta criptografada)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("CAREER_TRACKER_DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# tipo -> pasta
PASTAS = {
    "entrega": "entregas",
    "decisao": "decisoes",
    "feedback": "feedbacks",
    "compromisso": "compromissos",
    "conceito": "conceitos",
    "pessoa": "pessoas",
}
Tipo = Literal["entrega", "decisao", "feedback", "compromisso", "conceito", "pessoa"]

# Conceitos e pessoas são as "páginas" do grafo: o arquivo tem o nome exato do
# título, para que [[Título]] resolva no Obsidian.
TIPOS_ENTIDADE = {"conceito", "pessoa"}

# Ordem das chaves no frontmatter, para os arquivos ficarem legíveis
ORDEM_CAMPOS = [
    "id", "tipo", "titulo", "data", "status", "prazo", "pessoa", "categoria",
    "metrica", "metrica_categoria", "metrica_antes", "metrica_depois",
    "metrica_confianca", "aliases", "relacionados", "tags", "criado_em", "atualizado_em",
]

LINK_RE = re.compile(r"\[\[([^\]|#]+)(#[^\]|]*)?(\|[^\]]*)?\]\]")


class Metrica(BaseModel):
    descricao: str = Field(description="Métrica em linguagem executiva. Ex: 'Redução de 95% no ciclo de validação'")
    categoria: str | None = Field(None, description="financeiro, tempo, risco, qualidade, compliance, cliente...")
    antes: str | None = Field(None, description="Valor antes. Ex: '4h'")
    depois: str | None = Field(None, description="Valor depois. Ex: '12min'")
    confianca: Literal["medido", "estimado"] | None = Field(None, description="'medido' se veio de dado real, 'estimado' se é aproximação")


# ==========================================
# FUNÇÕES AUXILIARES - ARQUIVOS
# ==========================================

def normalizar(texto) -> str:
    """Minúsculas e sem acentos, para buscas e comparações."""
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).lower().strip()


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalizar(texto)).strip("-")[:60] or "registro"


def nome_arquivo_seguro(texto: str) -> str:
    # Caracteres proibidos em nomes de arquivo ou que quebram [[links]] no Obsidian
    texto = re.sub(r'[\\/:*?"<>|#^\[\]]', "", texto)
    return re.sub(r"\s+", " ", texto).strip()[:100] or "registro"


def validar_data(valor: str | None, campo: str = "data") -> str | None:
    if valor is None:
        return None
    try:
        return date.fromisoformat(str(valor)[:10]).isoformat()
    except ValueError:
        raise ValueError(f"'{campo}' inválida: '{valor}'. Use o formato AAAA-MM-DD.")


def ler_arquivo(caminho: str) -> dict | None:
    """Lê um .md e devolve {meta, corpo, caminho}. Ignora notas sem 'tipo' conhecido."""
    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read().replace("\r\n", "\n")
    if not texto.startswith("---\n"):
        return None
    fim = texto.find("\n---", 4)
    if fim == -1:
        return None
    try:
        meta = yaml.safe_load(texto[4:fim]) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict) or meta.get("tipo") not in PASTAS:
        return None
    # Datas digitadas à mão no Obsidian chegam como date; padroniza como texto
    for chave, valor in meta.items():
        if isinstance(valor, (date, datetime)):
            meta[chave] = valor.isoformat()
    meta.setdefault("id", os.path.splitext(os.path.basename(caminho))[0])
    meta.setdefault("titulo", os.path.splitext(os.path.basename(caminho))[0])
    corpo = texto[fim + 4:].lstrip("\n")
    return {"meta": meta, "corpo": corpo, "caminho": caminho}


def escrever_arquivo(caminho: str, meta: dict, corpo: str):
    meta_ordenado = {k: meta[k] for k in ORDEM_CAMPOS if meta.get(k) not in (None, [], "")}
    meta_ordenado.update({k: v for k, v in meta.items() if k not in ORDEM_CAMPOS and v not in (None, [], "")})
    # Datas sem aspas, para o Obsidian e o Dataview reconhecerem como data
    for campo in ("data", "prazo"):
        try:
            meta_ordenado[campo] = date.fromisoformat(str(meta_ordenado[campo])[:10])
        except (KeyError, ValueError):
            pass
    frontmatter = yaml.safe_dump(meta_ordenado, allow_unicode=True, sort_keys=False, width=1000)
    conteudo = f"---\n{frontmatter}---\n\n{corpo.strip()}\n"
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    # Escrita atômica: nunca deixa um arquivo pela metade se o processo cair
    fd, temporario = tempfile.mkstemp(dir=os.path.dirname(caminho), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(conteudo)
    os.replace(temporario, caminho)


def carregar_registros() -> list[dict]:
    registros = []
    for raiz, pastas, arquivos in os.walk(DATA_DIR):
        pastas[:] = [p for p in pastas if not p.startswith(".")]  # ignora .obsidian, .trash
        for nome in arquivos:
            if nome.endswith(".md"):
                registro = ler_arquivo(os.path.join(raiz, nome))
                if registro:
                    registros.append(registro)
    return registros


def indice_entidades(registros: list[dict]) -> dict[str, str]:
    """Mapa nome/alias normalizado -> título canônico de conceitos e pessoas."""
    indice = {}
    for r in registros:
        if r["meta"]["tipo"] in TIPOS_ENTIDADE:
            titulo = r["meta"]["titulo"]
            for nome in [titulo, *(r["meta"].get("aliases") or [])]:
                indice[normalizar(nome)] = titulo
    return indice


def como_link(nome: str, indice: dict[str, str]) -> str:
    nome = nome.strip().removeprefix("[[").removesuffix("]]")
    return f"[[{indice.get(normalizar(nome), nome)}]]"


def normalizar_links_corpo(corpo: str, indice: dict[str, str]) -> str:
    """[[portal]] -> [[Portal do Cliente|portal]], para que aliases e variações de caixa resolvam no Obsidian."""
    def trocar(m):
        alvo, ancora, rotulo = m.group(1).strip(), m.group(2) or "", m.group(3)
        canonico = indice.get(normalizar(alvo))
        if not canonico or canonico == alvo:
            return m.group(0)
        return f"[[{canonico}{ancora}{rotulo or '|' + alvo}]]"
    return LINK_RE.sub(trocar, corpo)


def links_do_registro(registro: dict) -> set[str]:
    meta = registro["meta"]
    nomes = {m.group(1).strip() for m in LINK_RE.finditer(registro["corpo"])}
    for valor in [*(meta.get("relacionados") or []), meta.get("pessoa")]:
        if valor:
            nomes.update(m.group(1).strip() for m in LINK_RE.finditer(str(valor)))
    return nomes


def localizar(registros: list[dict], id_ou_titulo: str) -> dict:
    alvo = normalizar(id_ou_titulo)
    por_id = [r for r in registros if normalizar(r["meta"]["id"]) == alvo]
    if por_id:
        return por_id[0]
    por_titulo = [r for r in registros if normalizar(r["meta"]["titulo"]) == alvo]
    if len(por_titulo) == 1:
        return por_titulo[0]
    if len(por_titulo) > 1:
        ids = ", ".join(r["meta"]["id"] for r in por_titulo)
        raise ValueError(f"Mais de um registro com o título '{id_ou_titulo}'. Use o id: {ids}")
    raise ValueError(f"Registro '{id_ou_titulo}' não encontrado. Use buscar() para achar o id.")


def caminho_para(tipo: str, titulo: str, data_registro: str, ignorar: str | None = None) -> str:
    base = nome_arquivo_seguro(titulo)
    if tipo not in TIPOS_ENTIDADE:
        base = f"{data_registro} {base}"
    pasta = os.path.join(DATA_DIR, PASTAS[tipo])
    caminho, n = os.path.join(pasta, f"{base}.md"), 2
    while os.path.exists(caminho) and caminho != ignorar:
        caminho, n = os.path.join(pasta, f"{base} ({n}).md"), n + 1
    return caminho


def aplicar_campos(meta: dict, indice: dict[str, str], *, relacionados, tags, metrica, status,
                   prazo, pessoa, categoria, aliases):
    """Campos opcionais comuns a registrar() e atualizar(). None = não mexer."""
    if relacionados is not None:
        meta["relacionados"] = [como_link(n, indice) for n in relacionados]
    if tags is not None:
        meta["tags"] = [t.strip().lstrip("#").replace(" ", "-") for t in tags]
    if metrica is not None:
        meta.update({
            "metrica": metrica.descricao,
            "metrica_categoria": metrica.categoria,
            "metrica_antes": metrica.antes,
            "metrica_depois": metrica.depois,
            "metrica_confianca": metrica.confianca,
        })
    if prazo is not None:
        meta["prazo"] = validar_data(prazo, "prazo")
    if pessoa is not None:
        meta["pessoa"] = como_link(pessoa, indice)
    if categoria is not None:
        meta["categoria"] = categoria
    if aliases is not None:
        meta["aliases"] = aliases
    if status is not None:
        meta["status"] = status


def formatar_resumo(r: dict) -> str:
    meta = r["meta"]
    partes = [f"- [{meta['tipo']}] {meta.get('data', '')} · **{meta['titulo']}** (id: `{meta['id']}`)"]
    for campo in ("status", "categoria", "prazo", "pessoa", "metrica"):
        if meta.get(campo):
            partes.append(f"{campo}: {meta[campo]}")
    if meta.get("aliases"):
        partes.append(f"aliases: {', '.join(meta['aliases'])}")
    if meta["tipo"] in TIPOS_ENTIDADE:
        primeira_linha = next((l.strip() for l in r["corpo"].splitlines() if l.strip()), "")
        if primeira_linha:
            partes.append(primeira_linha[:140])
    return " · ".join(partes)


def formatar_detalhado(r: dict) -> str:
    meta = r["meta"]
    campos = {k: v for k, v in meta.items() if k not in ("id", "tipo", "titulo", "criado_em", "atualizado_em")}
    linhas = [f"### [{meta['tipo']}] {meta['titulo']}", f"id: `{meta['id']}`"]
    linhas += [f"{k}: {', '.join(map(str, v)) if isinstance(v, list) else v}" for k, v in campos.items()]
    linhas += [f"arquivo: {os.path.relpath(r['caminho'], DATA_DIR)}", "", r["corpo"].strip(), ""]
    return "\n".join(linhas)


# ==========================================
# FERRAMENTAS DO MCP (TOOLS)
# ==========================================

@mcp.tool()
def registrar(
    tipo: Tipo,
    titulo: str,
    conteudo: str,
    data: str | None = None,
    relacionados: list[str] | None = None,
    tags: list[str] | None = None,
    metrica: Metrica | None = None,
    status: str | None = None,
    prazo: str | None = None,
    pessoa: str | None = None,
    categoria: str | None = None,
    aliases: list[str] | None = None,
) -> str:
    """
    Registra um fato sobre a organização como um arquivo Markdown.

    Tipos:
    - entrega: trabalho concluído. Sem `metrica`, fica com status 'aguardando_metrica'
      e aparece em pendencias() até ser completado com atualizar().
    - decisao: decisão da empresa ou do time (contexto, decisão, alternativas, quem decidiu, por quê).
    - feedback: feedback recebido. `pessoa` = quem deu; `categoria` = elogio ou desenvolvimento.
    - compromisso: algo prometido. `pessoa` = para quem; `prazo` = AAAA-MM-DD; status padrão 'aberto'.
    - conceito: termo, produto, sistema, squad, processo, regulador, KPI ou nível de carreira
      (`categoria`). `aliases` = sinônimos e siglas.
    - pessoa: stakeholder. `categoria` = cargo/área. `conteudo` = o que valoriza, como se comunica.

    `data` (AAAA-MM-DD) permite registrar fatos passados; o padrão é hoje.
    `relacionados` recebe nomes de conceitos e pessoas e vira [[links]] no grafo do Obsidian.
    No `conteudo`, também use [[Nome]] ao citar conceitos e pessoas.
    Conceitos e pessoas não são sobrescritos: se já existirem, use atualizar().
    """
    titulo = titulo.strip()
    data_registro = validar_data(data) or date.today().isoformat()
    registros = carregar_registros()
    indice = indice_entidades(registros)

    if tipo in TIPOS_ENTIDADE:
        for nome in [titulo, *(aliases or [])]:
            existente = indice.get(normalizar(nome))
            if existente:
                return (f"Não registrado: '{nome}' já existe como '{existente}'. "
                        f"Use atualizar('{existente}', ...) para complementar.")

    if status is None:
        if tipo == "entrega":
            status = "consolidado" if metrica else "aguardando_metrica"
        elif tipo == "compromisso":
            status = "aberto"

    base_id = slug(titulo) if tipo in TIPOS_ENTIDADE else f"{data_registro}-{slug(titulo)}"
    ids = {r["meta"]["id"] for r in registros}
    novo_id, n = base_id, 2
    while novo_id in ids:
        novo_id, n = f"{base_id}-{n}", n + 1

    agora = datetime.now().isoformat(timespec="seconds")
    meta = {"id": novo_id, "tipo": tipo, "titulo": titulo, "data": data_registro,
            "criado_em": agora, "atualizado_em": agora}
    # A própria entidade entra no índice para que o conteúdo possa citá-la
    if tipo in TIPOS_ENTIDADE:
        indice.update({normalizar(n): titulo for n in [titulo, *(aliases or [])]})
    aplicar_campos(meta, indice, relacionados=relacionados, tags=tags, metrica=metrica, status=status,
                   prazo=prazo, pessoa=pessoa, categoria=categoria, aliases=aliases)

    caminho = caminho_para(tipo, titulo, data_registro)
    escrever_arquivo(caminho, meta, normalizar_links_corpo(conteudo, indice))

    aviso = " Sem métrica: ficará em pendencias() até ser completada." if status == "aguardando_metrica" else ""
    return f"Registrado: [{tipo}] {titulo} (id: {novo_id}) em {os.path.relpath(caminho, DATA_DIR)}.{aviso}"


@mcp.tool()
def atualizar(
    id: str,
    titulo: str | None = None,
    conteudo: str | None = None,
    acrescentar: str | None = None,
    data: str | None = None,
    relacionados: list[str] | None = None,
    tags: list[str] | None = None,
    metrica: Metrica | None = None,
    status: str | None = None,
    prazo: str | None = None,
    pessoa: str | None = None,
    categoria: str | None = None,
    aliases: list[str] | None = None,
) -> str:
    """
    Atualiza um registro existente, localizado pelo id ou pelo título exato.
    Só os campos informados mudam.

    - `conteudo` substitui o texto inteiro; `acrescentar` adiciona uma seção datada ao final,
      preservando o histórico (prefira para mudanças de definição ou evolução de um fato).
    - Informar `metrica` numa entrega 'aguardando_metrica' muda o status para 'consolidado'.
    - Compromisso cumprido: status='concluido' (ou 'cancelado').
    - Renomear um conceito ou pessoa atualiza os [[links]] em todos os outros registros.
    """
    registros = carregar_registros()
    try:
        registro = localizar(registros, id)
        data_nova = validar_data(data)
    except ValueError as e:
        return f"Erro: {e}"

    meta, corpo = registro["meta"], registro["corpo"]
    tipo, titulo_antigo = meta["tipo"], meta["titulo"]
    indice = indice_entidades(registros)
    titulo = titulo.strip() if titulo else None

    if tipo in TIPOS_ENTIDADE:
        for nome in [titulo, *(aliases or [])]:
            existente = indice.get(normalizar(nome)) if nome else None
            if existente and existente != titulo_antigo:
                return f"Erro: '{nome}' já pertence a '{existente}'."

    if status is None and metrica is not None and meta.get("status") == "aguardando_metrica":
        status = "consolidado"

    if titulo:
        meta["titulo"] = titulo
    if data_nova:
        meta["data"] = data_nova
    if tipo in TIPOS_ENTIDADE:
        indice.update({normalizar(n): meta["titulo"] for n in [meta["titulo"], *(aliases or meta.get("aliases") or [])]})
    aplicar_campos(meta, indice, relacionados=relacionados, tags=tags, metrica=metrica, status=status,
                   prazo=prazo, pessoa=pessoa, categoria=categoria, aliases=aliases)
    meta["atualizado_em"] = datetime.now().isoformat(timespec="seconds")

    if conteudo is not None:
        corpo = conteudo
    if acrescentar:
        corpo = f"{corpo.rstrip()}\n\n## Atualização {date.today().isoformat()}\n\n{acrescentar.strip()}"
    corpo = normalizar_links_corpo(corpo, indice)

    caminho = caminho_para(tipo, meta["titulo"], meta["data"], ignorar=registro["caminho"])
    escrever_arquivo(caminho, meta, corpo)
    if caminho != registro["caminho"]:
        os.remove(registro["caminho"])

    renomeados = 0
    if tipo in TIPOS_ENTIDADE and meta["titulo"] != titulo_antigo:
        renomeados = renomear_links(registros, registro["caminho"], titulo_antigo, meta["titulo"])

    extra = f" Links atualizados em {renomeados} registro(s)." if renomeados else ""
    return f"Atualizado: [{tipo}] {meta['titulo']} (id: {meta['id']}).{extra}"


def renomear_links(registros: list[dict], caminho_ignorado: str, antigo: str, novo: str) -> int:
    alvo = normalizar(antigo)
    total = 0
    for r in registros:
        if r["caminho"] == caminho_ignorado:
            continue

        def trocar(m):
            if normalizar(m.group(1)) != alvo:
                return m.group(0)
            return f"[[{novo}{m.group(2) or ''}{m.group(3) or ''}]]"

        corpo = LINK_RE.sub(trocar, r["corpo"])
        meta = dict(r["meta"])
        for campo in ("relacionados", "pessoa"):
            valor = meta.get(campo)
            if isinstance(valor, list):
                meta[campo] = [LINK_RE.sub(trocar, str(v)) for v in valor]
            elif valor:
                meta[campo] = LINK_RE.sub(trocar, str(valor))
        if corpo != r["corpo"] or meta != r["meta"]:
            escrever_arquivo(r["caminho"], meta, corpo)
            total += 1
    return total


@mcp.tool()
def buscar(
    texto: str | None = None,
    tipo: Tipo | None = None,
    de: str | None = None,
    ate: str | None = None,
    status: str | None = None,
    relacionado: str | None = None,
    detalhado: bool = False,
    limite: int = 30,
) -> str:
    """
    Consulta a base da organização. Todos os filtros são opcionais e se combinam.

    - texto: palavras procuradas no título, aliases, tags, categoria, pessoa, métrica e conteúdo
      (sem diferenciar acentos).
    - tipo: entrega, decisao, feedback, compromisso, conceito ou pessoa.
    - de / ate: período (AAAA-MM-DD) pela data do registro.
    - status: ex. 'aguardando_metrica', 'aberto'.
    - relacionado: nome de um conceito ou pessoa; retorna os registros que o citam.
    - detalhado: False traz uma linha por registro; True traz o conteúdo completo
      (use para relatórios e para responder perguntas sobre o conteúdo).

    Resultado ordenado do mais recente para o mais antigo.
    """
    try:
        de, ate = validar_data(de, "de"), validar_data(ate, "ate")
    except ValueError as e:
        return f"Erro: {e}"

    registros = carregar_registros()
    indice = indice_entidades(registros)
    palavras = normalizar(texto).split() if texto else []

    if relacionado:
        canonico = indice.get(normalizar(relacionado), relacionado)
        nomes_alvo = {normalizar(n) for n, t in indice.items() if t == canonico} | {normalizar(canonico)}

    encontrados = []
    for r in registros:
        meta = r["meta"]
        if tipo and meta["tipo"] != tipo:
            continue
        if status and normalizar(meta.get("status", "")) != normalizar(status):
            continue
        if de and str(meta.get("data", "")) < de:
            continue
        if ate and str(meta.get("data", "")) > ate:
            continue
        if relacionado:
            if meta["titulo"] == canonico or not {normalizar(n) for n in links_do_registro(r)} & nomes_alvo:
                continue
        if palavras:
            alvo = normalizar(" ".join([meta["titulo"], *map(str, meta.get("aliases") or []),
                                        *map(str, meta.get("tags") or []), str(meta.get("metrica", "")),
                                        str(meta.get("categoria", "")), str(meta.get("pessoa", "")),
                                        r["corpo"]]))
            if not all(p in alvo for p in palavras):
                continue
        encontrados.append(r)

    if not encontrados:
        return "Nenhum registro encontrado com esses filtros."

    encontrados.sort(key=lambda r: (str(r["meta"].get("data", "")), str(r["meta"].get("criado_em", ""))), reverse=True)
    exibidos = encontrados[:limite]
    formatar = formatar_detalhado if detalhado else formatar_resumo
    saida = "\n".join(formatar(r) for r in exibidos)
    if len(encontrados) > limite:
        saida += f"\n\n(Mostrando {limite} de {len(encontrados)}. Refine os filtros ou aumente o limite.)"
    return saida


@mcp.tool()
def pendencias() -> str:
    """
    Lista o que precisa de atenção: entregas aguardando métrica, compromissos em aberto
    (vencidos e próximos do prazo) e lacunas no glossário (nomes citados em [[links]]
    que ainda não têm página de conceito ou pessoa).
    """
    registros = carregar_registros()
    indice = indice_entidades(registros)
    hoje = date.today()
    blocos = []

    sem_metrica = sorted((r for r in registros if r["meta"]["tipo"] == "entrega"
                          and r["meta"].get("status") == "aguardando_metrica"),
                         key=lambda r: str(r["meta"].get("data", "")))
    if sem_metrica:
        linhas = []
        for r in sem_metrica:
            dias = (hoje - date.fromisoformat(str(r["meta"]["data"])[:10])).days
            linhas.append(f"- {r['meta']['titulo']} (id: `{r['meta']['id']}`, há {dias} dias)")
        blocos.append("## Entregas aguardando métrica\n" + "\n".join(linhas))

    abertos = [r for r in registros if r["meta"]["tipo"] == "compromisso" and r["meta"].get("status") == "aberto"]
    if abertos:
        linhas = []
        for r in sorted(abertos, key=lambda r: str(r["meta"].get("prazo") or "9999")):
            meta = r["meta"]
            com = f" com {meta['pessoa']}" if meta.get("pessoa") else ""
            if not meta.get("prazo"):
                situacao = "sem prazo"
            else:
                dias = (date.fromisoformat(str(meta["prazo"])[:10]) - hoje).days
                situacao = (f"VENCIDO há {-dias} dias" if dias < 0 else
                            "vence hoje" if dias == 0 else f"vence em {dias} dias")
            linhas.append(f"- {meta['titulo']}{com} · {situacao} (id: `{meta['id']}`)")
        blocos.append("## Compromissos em aberto\n" + "\n".join(linhas))

    lacunas: dict[str, int] = {}
    for r in registros:
        for nome in links_do_registro(r):
            if normalizar(nome) not in indice:
                lacunas[nome] = lacunas.get(nome, 0) + 1
    if lacunas:
        linhas = [f"- {nome} (citado {n}x)" for nome, n in sorted(lacunas.items(), key=lambda x: -x[1])]
        blocos.append("## Lacunas no glossário (citados sem página)\n" + "\n".join(linhas))

    return "\n\n".join(blocos) if blocos else "Nenhuma pendência."


# ==========================================
# PROMPTS DO MCP (modelos de relatório)
# No Claude Code aparecem como /mcp__career-tracker__<nome>
# ==========================================

@mcp.prompt()
def preparar_1on1(audiencia: str = "tecnica", dias: int = 30) -> str:
    """Prepara a pauta de um 1:1. audiencia: 'tecnica' (gerência de engenharia) ou 'executiva' (diretoria)."""
    inicio = (date.today() - timedelta(days=dias)).isoformat()
    foco = (
        "Destaque os desafios técnicos resolvidos, arquitetura, redução de débito técnico e ferramentas usadas, "
        "sempre ligados à métrica de negócio."
        if normalizar(audiencia).startswith("tec") else
        "Oculte detalhes de código e ferramentas. Foque em receita, risco, custo, time-to-market e cliente."
    )
    return f"""Prepare meu 1:1 ({audiencia}) cobrindo de {inicio} até hoje.

1. Chame buscar(tipo="entrega", de="{inicio}", detalhado=True).
2. Chame buscar(tipo="decisao", de="{inicio}") e buscar(tipo="feedback", de="{inicio}", detalhado=True).
3. Chame pendencias() para trazer compromissos e entregas sem métrica.
4. Se houver uma pessoa do tipo 'pessoa' para a liderança do 1:1, leia o que ela valoriza com buscar(tipo="pessoa", texto=..., detalhado=True).

Entregue:
- **Três temas de impacto** do período, cada um com as entregas e métricas que o sustentam. {foco}
- **Frase de abertura** para o 1:1.
- **Compromissos**: o que foi cumprido e o que está em aberto.
- **Ponto de desenvolvimento** a discutir (use os feedbacks, se houver).
- **Pedidos**: o que preciso da liderança (bloqueios, visibilidade, escopo).

Não invente números. Entregas sem métrica aparecem como "impacto a medir"."""


@mcp.prompt()
def relatorio_periodo(de: str, ate: str, audiencia: str = "executiva") -> str:
    """Relatório de um período (semana, trimestre, ciclo de avaliação). Datas AAAA-MM-DD."""
    return f"""Monte um relatório das minhas contribuições entre {de} e {ate} para audiência {audiencia}.

1. Chame buscar(de="{de}", ate="{ate}", detalhado=True, limite=200).
2. Chame buscar(tipo="conceito", limite=200) para usar o vocabulário da empresa.

Estrutura:
- **Resumo executivo** (3 a 5 linhas).
- **Resultados por tema**, agrupando entregas pelo produto, sistema ou objetivo em comum
  (use os [[links]] e `relacionados`). Some métricas da mesma categoria quando for honesto somar;
  marque o que é estimado.
- **Decisões relevantes** do período e o meu papel nelas.
- **Em andamento / impacto a medir** (entregas aguardando métrica).
- **Próximos passos**.

Linguagem {audiencia}. Sem inflar resultados."""


@mcp.prompt()
def dossie_promocao(nivel_alvo: str) -> str:
    """Dossiê de evidências para promoção ao nível informado, comparado à trilha de carreira da empresa."""
    return f"""Monte meu dossiê de promoção para o nível "{nivel_alvo}".

1. Chame buscar(tipo="conceito", texto="{nivel_alvo}", detalhado=True) para ler as expectativas do nível
   (conceitos de categoria 'carreira'). Se não existir, diga que a trilha precisa ser mapeada e pergunte
   as expectativas antes de continuar.
2. Chame buscar(tipo="entrega", detalhado=True, limite=300) e buscar(tipo="feedback", detalhado=True, limite=100).
3. Chame buscar(tipo="decisao", detalhado=True, limite=100) para achar decisões que influenciei.

Entregue:
- **Tabela competência x evidências**: para cada expectativa do nível, as entregas, decisões e feedbacks
  que a comprovam (com data e métrica).
- **Lacunas**: expectativas com pouca ou nenhuma evidência, e uma sugestão concreta de como gerar evidência.
- **Pontos de desenvolvimento** apontados em feedbacks e se já foram endereçados.
- **Narrativa de promoção** em um parágrafo.

Seja crítico: evidência fraca deve ser apontada como fraca."""


@mcp.prompt()
def briefing_stakeholder(pessoa: str) -> str:
    """Briefing antes de uma reunião com uma pessoa: o que ela valoriza, histórico e pendências."""
    return f"""Prepare um briefing para minha reunião com {pessoa}.

1. Chame buscar(tipo="pessoa", texto="{pessoa}", detalhado=True).
2. Chame buscar(relacionado="{pessoa}", detalhado=True, limite=50).
3. Chame pendencias() e filtre os compromissos com {pessoa}.

Entregue:
- **Quem é e o que valoriza** (se não houver página, sugira criar uma com registrar(tipo="pessoa")).
- **Histórico**: últimas interações, decisões e feedbacks envolvendo {pessoa}.
- **O que entreguei que toca a área dessa pessoa**, com métricas.
- **Compromissos em aberto** com {pessoa}.
- **Três pontos para levar à reunião**."""


# ==========================================
# EXECUÇÃO DO SERVIDOR
# ==========================================

if __name__ == "__main__":
    # Roda o servidor utilizando o transporte stdio padrão do MCP
    mcp.run()
