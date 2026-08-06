"""
Monitor de uso da API Gemini — rastreia chamadas, sucessos, falhas
e alerta antes da cota acabar. Persiste em SQLite (sobrevive reruns
do Streamlit).
"""

import os
import sqlite3
from datetime import UTC, datetime, timedelta

from core import paths

DB_PATH = paths.DB_PATH  # mesma base do historico de orcamentos

# Limite diario configuravel via .env (padrao: 1500, limite generoso do Gemini free)
LIMITE_DIARIO = int(os.environ.get("GEMINI_DAILY_LIMIT", "1500"))
# Thresholds de alerta (percentual)
ALERTA_AMARELO = 0.70
ALERTA_VERMELHO = 0.90


def _conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_tabela_monitor():
    """Cria a tabela de monitoramento se nao existir. Seguro de chamar
toda vez que o app sobe."""
    conn = _conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_chamadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            modelo TEXT,
            status TEXT NOT NULL,
            chave_indice INTEGER,
            erro_status TEXT,
            duracao_ms INTEGER,
            bytes_enviados INTEGER
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_chamadas_data 
        ON api_chamadas(data_hora)
    """)
    conn.commit()
    conn.close()


def registrar_chamada(
    status: str,
    modelo: str | None = None,
    chave_indice: int | None = None,
    erro_status: str | None = None,
    duracao_ms: int = 0,
    bytes_enviados: int = 0,
):
    """Registra uma chamada a API (sucesso ou falha)."""
    conn = _conectar()
    conn.execute("""
        INSERT INTO api_chamadas 
        (data_hora, modelo, status, chave_indice, erro_status, duracao_ms, bytes_enviados)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(UTC).isoformat(),
        modelo,
        status,
        chave_indice,
        erro_status,
        duracao_ms,
        bytes_enviados,
    ))
    conn.commit()
    conn.close()


def resumo_periodo(dias: int = 1) -> dict:
    """Retorna estatisticas de uso nos ultimos N dias."""
    conn = _conectar()
    desde = (datetime.now(UTC) - timedelta(days=dias)).isoformat()
    row = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) as sucessos,
            SUM(CASE WHEN status = 'ERRO' THEN 1 ELSE 0 END) as falhas,
            SUM(CASE WHEN status = 'CACHE' THEN 1 ELSE 0 END) as caches
        FROM api_chamadas
        WHERE data_hora >= ?
    """, (desde,)).fetchone()
    conn.close()
    return {
        "total": row["total"] or 0,
        "sucessos": row["sucessos"] or 0,
        "falhas": row["falhas"] or 0,
        "caches": row["caches"] or 0,
    }


def status_cota() -> dict:
    """Retorna o status atual da cota para exibicao na UI."""
    hoje = resumo_periodo(dias=1)
    total = hoje["total"]
    limite = LIMITE_DIARIO
    uso = total / limite if limite > 0 else 0

    if uso >= ALERTA_VERMELHO:
        nivel = "critico"
        emoji = "🔴"
        mensagem = f"Cota critica: {total}/{limite} ({uso*100:.0f}%)"
    elif uso >= ALERTA_AMARELO:
        nivel = "alerta"
        emoji = "🟡"
        mensagem = f"Cota alta: {total}/{limite} ({uso*100:.0f}%)"
    else:
        nivel = "ok"
        emoji = "🟢"
        mensagem = f"API: {total}/{limite} hoje"

    return {
        "nivel": nivel,
        "emoji": emoji,
        "mensagem": mensagem,
        "total": total,
        "limite": limite,
        "uso_percentual": uso * 100,
        "sucessos": hoje["sucessos"],
        "falhas": hoje["falhas"],
        "caches": hoje["caches"],
    }
