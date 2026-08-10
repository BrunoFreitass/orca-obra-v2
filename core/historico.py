import sqlite3
from datetime import UTC, datetime

from core import paths
from core.coeficientes import VERSAO_TABELA

DB_PATH = paths.DB_PATH


def _conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    """Cria a tabela de orcamentos, se ainda nao existir. Seguro de
    chamar toda vez que o app sobe (CREATE TABLE IF NOT EXISTS)."""
    conn = _conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_criacao TEXT NOT NULL,
            nome_projeto TEXT NOT NULL,
            estado_uf TEXT NOT NULL,
            padrao TEXT NOT NULL,
            tipo_cobertura TEXT NOT NULL,
            area_piso REAL NOT NULL,
            area_piso_seco REAL NOT NULL DEFAULT 0,
            area_piso_molhado REAL NOT NULL DEFAULT 0,
            area_piso_externo REAL NOT NULL DEFAULT 0,
            metros_parede REAL NOT NULL DEFAULT 0,
            portas_internas INTEGER NOT NULL DEFAULT 0,
            portas_externas INTEGER NOT NULL DEFAULT 0,
            janelas INTEGER NOT NULL DEFAULT 0,
            custo_direto REAL NOT NULL,
            bdi_percentual REAL NOT NULL,
            preco_venda REAL NOT NULL,
            versao_coeficientes TEXT NOT NULL DEFAULT '',
            caminho_excel TEXT NOT NULL,
            caminho_pdf TEXT
        )
    """)

    # Migrações suaves: adiciona colunas que possam faltar em bancos antigos
    _migrar_coluna(conn, "caminho_pdf", "TEXT")
    _migrar_coluna(conn, "area_piso_seco", "REAL NOT NULL DEFAULT 0")
    _migrar_coluna(conn, "area_piso_molhado", "REAL NOT NULL DEFAULT 0")
    _migrar_coluna(conn, "area_piso_externo", "REAL NOT NULL DEFAULT 0")
    _migrar_coluna(conn, "metros_parede", "REAL NOT NULL DEFAULT 0")
    _migrar_coluna(conn, "portas_internas", "INTEGER NOT NULL DEFAULT 0")
    _migrar_coluna(conn, "portas_externas", "INTEGER NOT NULL DEFAULT 0")
    _migrar_coluna(conn, "janelas", "INTEGER NOT NULL DEFAULT 0")
    _migrar_coluna(conn, "versao_coeficientes", "TEXT NOT NULL DEFAULT ''")

    conn.commit()
    conn.close()


def _migrar_coluna(conn, nome_coluna, tipo_definicao):
    """Adiciona uma coluna se ela ainda nao existir. Ignora erro de duplicado."""
    try:
        conn.execute(f"ALTER TABLE orcamentos ADD COLUMN {nome_coluna} {tipo_definicao}")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise


def salvar_orcamento(nome_projeto, estado_uf, padrao, tipo_cobertura,
                      area_piso, custo_direto, bdi_percentual, preco_venda,
                      caminho_excel, caminho_pdf=None,
                      area_piso_seco=0, area_piso_molhado=0, area_piso_externo=0,
                      metros_parede=0, portas_internas=0, portas_externas=0,
                      janelas=0):
    """Grava um orcamento gerado no historico. Retorna o id do registro."""
    conn = _conectar()
    cursor = conn.execute("""
        INSERT INTO orcamentos (
            data_criacao, nome_projeto, estado_uf, padrao, tipo_cobertura,
            area_piso, area_piso_seco, area_piso_molhado, area_piso_externo,
            metros_parede, portas_internas, portas_externas, janelas,
            custo_direto, bdi_percentual, preco_venda,
            versao_coeficientes, caminho_excel, caminho_pdf
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(tz=UTC).strftime("%d/%m/%Y %H:%M"),
        nome_projeto, estado_uf, padrao, tipo_cobertura,
        area_piso, area_piso_seco, area_piso_molhado, area_piso_externo,
        metros_parede, portas_internas, portas_externas, janelas,
        custo_direto, bdi_percentual, preco_venda,
        VERSAO_TABELA,
        caminho_excel, caminho_pdf,
    ))
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return novo_id


def listar_orcamentos():
    """Retorna todos os orcamentos salvos, mais recente primeiro."""
    conn = _conectar()
    linhas = conn.execute(
        "SELECT * FROM orcamentos ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]


def excluir_orcamento(orcamento_id):
    """Remove um registro do historico pelo id (nao apaga os arquivos
    Excel/PDF em disco, so o registro no banco)."""
    conn = _conectar()
    conn.execute("DELETE FROM orcamentos WHERE id = ?", (orcamento_id,))
    conn.commit()
    conn.close()
