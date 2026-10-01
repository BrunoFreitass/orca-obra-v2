"""Camada de servico do OrcaObra AI.

Reune regras de negocio do orcamento -- soma de custo direto, calculo
do preco de venda com BDI e persistencia no historico. Nenhuma funcao
aqui importa UI; quem chama (a API) so cuida de mostrar o resultado na
tela.
"""

from core.historico import salvar_orcamento
from core.logger import get_logger

logger = get_logger(__name__)


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
    orcamento = materiais_editados + mao_de_obra_editada
    total = round(sum(item.get("Total", 0) for item in orcamento), 2)
    logger.info(
        "Orçamento montado: %d itens (%d material, %d mão de obra), custo direto R$%.2f",
        len(orcamento), len(materiais_editados), len(mao_de_obra_editada), total,
    )
    return orcamento


def gerar_orcamento_completo(
    orcamento_final: list, bdi_percentual: float, nome_projeto: str, padrao: str,
    estrutura: str, area_piso_total: float, metros_parede: float,
    portas_internas: int, portas_externas: int, janelas: int,
    area_piso_seco: float, area_piso_molhado: float, area_piso_externo: float,
    local_obra: str, cliente: str = "",
) -> dict:
    """Calcula custo/preço e persiste no histórico (com orcamento_json completo).
    Downloads de Excel e PDF são gerados sob demanda via API (api/routers/historico.py)
    a partir do orcamento_json, dispensando arquivos estáticos duplicados em disco.

    Retorna {custo_direto, preco_venda, historico_id}."""
    custo_direto, preco_venda = calcular_custo_e_preco(orcamento_final, bdi_percentual)

    historico_id = salvar_orcamento(
        nome_projeto=nome_projeto,
        cliente=cliente,
        estado_uf=local_obra,
        padrao=padrao,
        tipo_cobertura=estrutura,
        area_piso=area_piso_total,
        area_piso_seco=area_piso_seco,
        area_piso_molhado=area_piso_molhado,
        area_piso_externo=area_piso_externo,
        metros_parede=metros_parede,
        portas_internas=portas_internas,
        portas_externas=portas_externas,
        janelas=janelas,
        custo_direto=round(custo_direto, 2),
        bdi_percentual=bdi_percentual,
        preco_venda=preco_venda,
        orcamento_json=orcamento_final,
    )

    return {
        "custo_direto": custo_direto,
        "preco_venda": preco_venda,
        "historico_id": historico_id,
    }