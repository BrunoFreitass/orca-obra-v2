"""Guarda: a suite nunca pode falar com um Postgres real (o .env aponta
pro banco de producao). Ver tests/conftest.py."""
import os

import pytest

import config
from core import historico, monitor_api


def test_database_url_vazio_durante_a_suite():
    assert os.environ.get("DATABASE_URL") == ""
    assert config.DATABASE_URL == ""


@pytest.mark.parametrize("modulo", [historico, monitor_api])
def test_conexao_com_banco_e_recusada(modulo):
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        modulo._conectar()
