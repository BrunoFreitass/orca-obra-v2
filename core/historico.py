from datetime import datetime
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

import config
from core.coeficientes import VERSAO_TABELA

# data_criacao é texto exibido como hora local de RR. Registros antigos
# (gravados em UTC) não são migrados.
FUSO_OBRA = ZoneInfo("America/Boa_Vista")

_COLUNAS_LISTAGEM = """
    id, data_criacao, nome_projeto, cliente, estado_uf, padrao, tipo_cobertura,
    area_piso, area_piso_seco, area_piso_molhado, area_piso_externo,
    metros_parede, portas_internas, portas_externas, janelas,
    custo_direto, bdi_percentual, preco_venda, versao_coeficientes
"""


def _conectar():
    if not config.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não configurada -- defina no .env (ver .env.example)."
        )
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row)


def inicializar_db():
    """Cria a tabela de orcamentos, se ainda nao existir. Seguro de
    chamar toda vez que o app sobe (CREATE TABLE IF NOT EXISTS)."""
    with _conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orcamentos (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                data_criacao TEXT NOT NULL,
                nome_projeto TEXT NOT NULL,
                cliente TEXT NOT NULL DEFAULT '',
                estado_uf TEXT NOT NULL,
                padrao TEXT NOT NULL,
                tipo_cobertura TEXT NOT NULL,
                area_piso DOUBLE PRECISION NOT NULL,
                area_piso_seco DOUBLE PRECISION NOT NULL DEFAULT 0,
                area_piso_molhado DOUBLE PRECISION NOT NULL DEFAULT 0,
                area_piso_externo DOUBLE PRECISION NOT NULL DEFAULT 0,
                metros_parede DOUBLE PRECISION NOT NULL DEFAULT 0,
                portas_internas INTEGER NOT NULL DEFAULT 0,
                portas_externas INTEGER NOT NULL DEFAULT 0,
                janelas INTEGER NOT NULL DEFAULT 0,
                custo_direto DOUBLE PRECISION NOT NULL,
                bdi_percentual DOUBLE PRECISION NOT NULL,
                preco_venda DOUBLE PRECISION NOT NULL,
                versao_coeficientes TEXT NOT NULL DEFAULT '',
                orcamento_json JSONB NOT NULL
            )
        """)
        # Migração idempotente para bancos existentes
        conn.execute("""
            ALTER TABLE orcamentos ADD COLUMN IF NOT EXISTS cliente TEXT NOT NULL DEFAULT ''
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor JSONB NOT NULL
            )
        """)


def salvar_orcamento(nome_projeto, estado_uf, padrao, tipo_cobertura,
                      area_piso, custo_direto, bdi_percentual, preco_venda,
                      orcamento_json, cliente="",
                      area_piso_seco=0, area_piso_molhado=0, area_piso_externo=0,
                      metros_parede=0, portas_internas=0, portas_externas=0,
                      janelas=0):
    """Grava um orcamento gerado no historico, incluindo a lista completa
    de itens (materiais + mao de obra) em orcamento_json, pra poder
    regenerar Excel/PDF depois sem precisar guardar arquivo em disco.
    Retorna o id do registro."""
    with _conectar() as conn:
        cursor = conn.execute("""
            INSERT INTO orcamentos (
                data_criacao, nome_projeto, cliente, estado_uf, padrao, tipo_cobertura,
                area_piso, area_piso_seco, area_piso_molhado, area_piso_externo,
                metros_parede, portas_internas, portas_externas, janelas,
                custo_direto, bdi_percentual, preco_venda,
                versao_coeficientes, orcamento_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            datetime.now(tz=FUSO_OBRA).strftime("%d/%m/%Y %H:%M"),
            nome_projeto, cliente or "", estado_uf, padrao, tipo_cobertura,
            area_piso, area_piso_seco, area_piso_molhado, area_piso_externo,
            metros_parede, portas_internas, portas_externas, janelas,
            custo_direto, bdi_percentual, preco_venda,
            VERSAO_TABELA, Jsonb(orcamento_json),
        ))
        return cursor.fetchone()["id"]


def listar_orcamentos():
    """Retorna todos os orcamentos salvos, mais recente primeiro (sem
    orcamento_json -- usado pela tabela do historico, que nao precisa
    do payload completo de itens)."""
    with _conectar() as conn:
        linhas = conn.execute(
            f"SELECT {_COLUNAS_LISTAGEM} FROM orcamentos ORDER BY id DESC"
        ).fetchall()
        return linhas


def buscar_orcamento(orcamento_id):
    """Retorna um orcamento pelo id, incluindo orcamento_json (itens
    completos) -- usado para regenerar Excel/PDF sob demanda. None se
    nao existir."""
    with _conectar() as conn:
        return conn.execute(
            "SELECT * FROM orcamentos WHERE id = %s", (orcamento_id,)
        ).fetchone()


def excluir_orcamento(orcamento_id):
    """Remove um registro do historico pelo id."""
    with _conectar() as conn:
        conn.execute("DELETE FROM orcamentos WHERE id = %s", (orcamento_id,))


def obter_configuracao(chave: str) -> dict | None:
    """Busca uma configuracao JSON no banco Postgres. Retorna None se
    DATABASE_URL nao estiver configurada, se a tabela nao existir ou se a chave
    nao for encontrada."""
    if not config.DATABASE_URL:
        return None
    try:
        with _conectar() as conn:
            linha = conn.execute(
                "SELECT valor FROM configuracoes WHERE chave = %s", (chave,)
            ).fetchone()
            return linha["valor"] if linha and linha.get("valor") is not None else None
    except Exception:
        return None


def salvar_configuracao(chave: str, valor: dict) -> bool:
    """Salva ou atualiza uma configuracao JSON no banco Postgres. Retorna
    True em caso de sucesso, False caso o banco nao esteja disponivel."""
    if not config.DATABASE_URL:
        return False
    try:
        with _conectar() as conn:
            conn.execute("""
                INSERT INTO configuracoes (chave, valor)
                VALUES (%s, %s)
                ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor
            """, (chave, Jsonb(valor)))
            return True
    except Exception:
        return False


def deletar_configuracao(chave: str) -> bool:
    """Remove uma configuracao do banco Postgres."""
    if not config.DATABASE_URL:
        return False
    try:
        with _conectar() as conn:
            conn.execute("DELETE FROM configuracoes WHERE chave = %s", (chave,))
            return True
    except Exception:
        return False

