import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "historico.db")


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
            custo_direto REAL NOT NULL,
            bdi_percentual REAL NOT NULL,
            preco_venda REAL NOT NULL,
            caminho_excel TEXT NOT NULL
        )
    """)
    # Migracao: bancos criados antes do PDF de proposta nao tem essa
    # coluna. ALTER TABLE ADD COLUMN falha se ela ja existir -- ignoramos
    # esse erro especifico, que e o caso normal em bancos ja migrados.
    try:
        conn.execute("ALTER TABLE orcamentos ADD COLUMN caminho_pdf TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise
    conn.commit()
    conn.close()


def salvar_orcamento(nome_projeto, estado_uf, padrao, tipo_cobertura,
                      area_piso, custo_direto, bdi_percentual, preco_venda,
                      caminho_excel, caminho_pdf=None):
    """Grava um orcamento gerado no historico. Retorna o id do registro."""
    conn = _conectar()
    cursor = conn.execute("""
        INSERT INTO orcamentos (
            data_criacao, nome_projeto, estado_uf, padrao, tipo_cobertura,
            area_piso, custo_direto, bdi_percentual, preco_venda,
            caminho_excel, caminho_pdf
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        nome_projeto, estado_uf, padrao, tipo_cobertura,
        area_piso, custo_direto, bdi_percentual, preco_venda,
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
