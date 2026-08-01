"""Camada de servico do OrcaObra AI.

Reune regras de negocio que antes viviam misturadas com codigo de
interface (Streamlit) dentro de app.py -- geracao de nome de arquivo,
soma de custo direto e calculo do preco de venda com BDI. Nenhuma
funcao aqui importa streamlit; app.py chama estas funcoes e so cuida
de mostrar o resultado na tela.
"""

from datetime import datetime


def nome_arquivo_seguro(nome_projeto: str, limite: int = 40) -> str:
    """Gera um nome de arquivo unico e seguro a partir do nome do
    projeto/cliente: remove caracteres invalidos e prefixa com um
    timestamp, para nunca sobrescrever um orcamento anterior."""
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    limpo = "".join(c if c.isalnum() or c in " -_" else "_" for c in nome_projeto)
    limpo = limpo.strip().replace(" ", "_")[:limite]
    return f"{carimbo}_{limpo}"


def calcular_custo_e_preco(itens: list, bdi_percentual: float) -> tuple[float, float]:
    """Soma o custo direto (material + mao de obra) de uma lista de
    itens de orcamento e aplica o BDI para chegar ao preco de venda.
    Retorna (custo_direto, preco_venda), ambos arredondados a 2 casas."""
    custo_direto = round(sum(item["Total"] for item in itens), 2)
    preco_venda = round(custo_direto * (1 + bdi_percentual / 100), 2)
    return custo_direto, preco_venda


def montar_orcamento_completo(materiais_editados: list, mao_de_obra_editada: list) -> list:
    """Junta os materiais e a mao de obra (ambos ja editados pelo usuario
    na tela) num unico orcamento -- lista de dicts no formato que
    reporter.py e proposta_pdf.py esperam."""
    return materiais_editados + mao_de_obra_editada
