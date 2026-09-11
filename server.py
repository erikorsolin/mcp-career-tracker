from mcp.server.fastmcp import FastMCP
import json
import os
from datetime import datetime, timedelta

# ==========================================
# INICIALIZAÇÃO E CONFIGURAÇÃO
# ==========================================

# Inicializa o servidor MCP
mcp = FastMCP("CareerTracker")

# Caminhos dos arquivos de persistência locais.
# Resolvidos a partir da pasta do próprio server.py (e não do diretório de trabalho),
# pois o Claude Code pode iniciar o servidor a partir de qualquer pasta.
# Variáveis de ambiente (todas opcionais):
#   CAREER_TRACKER_DATA_DIR      diretório dos dados (ex: uma pasta criptografada)
#   CAREER_TRACKER_LOG_FILE      nome do arquivo do diário STAR
#   CAREER_TRACKER_DOMAIN_FILE   nome do arquivo do glossário de domínio
# O servidor é agnóstico ao setor: o nome do glossário é só um rótulo do arquivo,
# e o padrão "dominio_financeiro.json" existe apenas por compatibilidade com a
# especialização de exemplo deste repositório.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("CAREER_TRACKER_DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)

ARQUIVO_LOG = os.path.join(
    DATA_DIR, os.environ.get("CAREER_TRACKER_LOG_FILE", "career_log.json")
)
ARQUIVO_DOMINIO = os.path.join(
    DATA_DIR, os.environ.get("CAREER_TRACKER_DOMAIN_FILE", "dominio_financeiro.json")
)


# ==========================================
# FUNÇÕES AUXILIARES - LOGS DE CARREIRA
# ==========================================

def carregar_logs():
    if os.path.exists(ARQUIVO_LOG):
        with open(ARQUIVO_LOG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_logs(logs):
    # ensure_ascii=False garante a correta gravação de acentos
    with open(ARQUIVO_LOG, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)


# ==========================================
# FUNÇÕES AUXILIARES - DOMÍNIO DE NEGÓCIOS
# ==========================================

def carregar_dominio():
    if os.path.exists(ARQUIVO_DOMINIO):
        with open(ARQUIVO_DOMINIO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_dominio(dominio):
    with open(ARQUIVO_DOMINIO, 'w', encoding='utf-8') as f:
        json.dump(dominio, f, indent=4, ensure_ascii=False)


# ==========================================
# FERRAMENTAS DO MCP (TOOLS)
# ==========================================

@mcp.tool()
def registrar_impacto_diario(situacao: str, tarefa: str, acao: str, resultado: str, metrica_negocio: str) -> str:
    """
    Registra uma conquista diária usando a metodologia STAR (Situação, Tarefa, Ação, Resultado).
    Sempre relacione o impacto a uma métrica de negócio (ex: mitigação de risco, tempo de CI/CD, segurança).
    """
    logs = carregar_logs()
    novo_registro = {
        "data": datetime.now().isoformat(),
        "situacao": situacao,
        "tarefa": tarefa,
        "acao": acao,
        "resultado": resultado,
        "metrica_negocio": metrica_negocio
    }
    logs.append(novo_registro)
    salvar_logs(logs)
    
    return f"Sucesso: Impacto executivo registrado! Foco: {metrica_negocio}"


@mcp.tool()
def gerar_brag_document(dias: int = 30) -> str:
    """
    Gera um relatório executivo (Brag Document) em Markdown dos últimos X dias.
    Ideal para preparar reuniões de 1:1 com a gerência de engenharia.
    """
    logs = carregar_logs()
    limite_data = datetime.now() - timedelta(days=dias)
    
    logs_recentes = [
        log for log in logs 
        if datetime.fromisoformat(log['data']) >= limite_data
    ]
    
    if not logs_recentes:
        return f"Nenhum registro encontrado nos últimos {dias} dias."
    
    relatorio = f"# Brag Document - Últimos {dias} dias\n\n"
    for log in logs_recentes:
        data_formatada = datetime.fromisoformat(log['data']).strftime("%d/%m/%Y")
        relatorio += f"## Data: {data_formatada} | Impacto: {log['metrica_negocio']}\n"
        relatorio += f"- **Contexto (Situação/Tarefa):** {log['situacao']} - {log['tarefa']}\n"
        relatorio += f"- **Ação Executada:** {log['acao']}\n"
        relatorio += f"- **Resultado Final:** {log['resultado']}\n\n"
        
    return relatorio


@mcp.tool()
def mapear_conceito_dominio(termo: str, definicao: str, importancia_estrategica: str) -> str:
    """
    Registra um novo conceito, jargão ou regra de negócio da empresa.
    Use isso sempre que o usuário explicar como a empresa ganha dinheiro, 
    como a arquitetura funciona (ex: BaaS) ou termos do setor financeiro.
    """
    dominio = carregar_dominio()
    
    # Salva em minúsculas para facilitar a busca, mas mantém formatação original no payload
    dominio[termo.lower()] = {
        "termo_original": termo,
        "definicao": definicao,
        "importancia_estrategica": importancia_estrategica,
        "data_mapeamento": datetime.now().isoformat()
    }
    
    salvar_dominio(dominio)
    return f"Sucesso: O conceito '{termo}' foi adicionado à base de conhecimento corporativa."


@mcp.tool()
def consultar_base_de_negocios() -> str:
    """
    Retorna todo o glossário e regras de negócio mapeadas da empresa.
    O agente DEVE usar esta ferramenta antes de registrar um impacto diário ou gerar um Brag Document, 
    para garantir que está usando o jargão corporativo correto (ex: BaaS, White-label).
    """
    dominio = carregar_dominio()
    
    if not dominio:
        return "A base de conhecimento de negócios ainda está vazia."
    
    resultado = "Base de Conhecimento do Negócio:\n\n"
    for chave, dados in dominio.items():
        resultado += f"- **{dados['termo_original']}**: {dados['definicao']}\n"
        resultado += f"  *Por que importa para a diretoria:* {dados['importancia_estrategica']}\n\n"
        
    return resultado


# ==========================================
# EXECUÇÃO DO SERVIDOR
# ==========================================

if __name__ == "__main__":
    # Roda o servidor utilizando o transporte stdio padrão do MCP
    mcp.run()