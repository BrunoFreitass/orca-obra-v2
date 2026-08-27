"""Camada de servico do OrcaObra AI.

Reune regras de negocio que antes viviam misturadas com codigo de
interface (Streamlit) dentro de app.py -- geracao de nome de arquivo,
soma de custo direto e calculo do preco de venda com BDI. Nenhuma
funcao aqui importa streamlit; app.py chama estas funcoes e so cuida
de mostrar o resultado na tela.
"""

import os
from datetime import UTC, datetime

from core import paths
from core.historico import salvar_orcamento
from core.logger import get_logger
from core.perfil_empresa import carregar_perfil
from core.proposta_pdf import gerar_pdf_proposta
from core.reporter import gerar_excel

logger = get_logger(__name__)


def nome_arquivo_seguro(nome_projeto: str, limite: int = 40) -> str:
    """Gera um nome de arquivo unico e seguro a partir do nome do
    projeto/cliente: remove caracteres invalidos e prefixa com um
    timestamp, para nunca sobrescrever um orcamento anterior."""
    carimbo = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
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
    local_obra: str,
) -> dict:
    """Calcula custo/preço, gera Excel + PDF em disco e persiste no
    histórico -- mesma sequência que core/ui_orcamento.py:_gerar_documentos
    executa hoje pela tela do Streamlit, extraída aqui pra ser chamada
    também por um front-end sem Streamlit (ex: uma API).

    Retorna {custo_direto, preco_venda, caminho_excel, caminho_pdf,
    historico_id} -- não faz nenhuma renderização, quem chamar decide
    como mostrar o resultado."""
    custo_direto, preco_venda = calcular_custo_e_preco(orcamento_final, bdi_percentual)

    base_nome = nome_arquivo_seguro(nome_projeto)
    excel_path = os.path.join(paths.PASTA_ORCAMENTOS, f"{base_nome}.xlsx")
    pdf_path = os.path.join(paths.PASTA_ORCAMENTOS, f"{base_nome}.pdf")

    caminho_excel = gerar_excel(orcamento_final, excel_path, bdi_percentual)

    perfil = carregar_perfil()

    contato_linhas = []
    if perfil.get("profissional_responsavel"):
        contato_linhas.append(f"Profissional Responsável: {perfil['profissional_responsavel']}")
    if perfil.get("telefone"):
        contato_linhas.append(f"Contato: {perfil['telefone']}")
    if perfil.get("email"):
        contato_linhas.append(f"E-mail: {perfil['email']}")

    registro_str = ""
    if perfil.get("registro"):
        registro_str = f"Registro (CREA/CAU/CNPJ): {perfil['registro']}"

    caminho_pdf = gerar_pdf_proposta(
        orcamento_final, pdf_path,
        nome_projeto=nome_projeto,
        estado_uf=local_obra, padrao=padrao,
        tipo_cobertura=estrutura, area_piso=area_piso_total,
        bdi_percentual=bdi_percentual,
        nome_empresa=perfil["nome_empresa"] or "OrçaObra AI",
        contato=contato_linhas,
        registro=registro_str,
        caminho_logo=perfil["caminho_logo"],
    )

    historico_id = salvar_orcamento(
        nome_projeto=nome_projeto,
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
        caminho_excel=caminho_excel,
        caminho_pdf=caminho_pdf,
    )

    return {
        "custo_direto": custo_direto,
        "preco_venda": preco_venda,
        "caminho_excel": caminho_excel,
        "caminho_pdf": caminho_pdf,
        "historico_id": historico_id,
    }