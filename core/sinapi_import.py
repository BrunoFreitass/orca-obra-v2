"""
Importador do SINAPI oficial (CAIXA/IBGE) para o motor de cálculo do
OrçaObra.

POR QUE O DOWNLOAD CONTINUA MANUAL: o portal da Caixa
(caixa.gov.br/poder-publico/.../sinapi) bloqueia acesso automatizado
via robots.txt. Respeitar isso significa que baixar o ZIP mensal
continua sendo um passo manual — leva ~2 minutos, uma vez por mês.
Este script cuida do resto: abrir a planilha oficial já baixada,
localizar os códigos SINAPI mapeados em core/sinapi_codigos.py,
extrair o preço vigente para Roraima e gravar como override no
OrçaObra — com a fonte e a data de referência corretas, sem digitar
nada à mão.

Esse ganho já resolve o problema real que a equipe teve na prática
(preço de cimento desatualizado no calculator.py, corrigido só depois
de perceber a olho): a partir daqui, atualizar os preços vira "baixar
o ZIP do mês e rodar um comando", em vez de lembrar de conferir cada
valor manualmente.

COMO USAR
1. Baixe e extraia o ZIP do mês em:
   https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/Paginas/default.aspx
   -> Preços de Insumos e Composições -> RR -> mês mais recente ->
   versão "Não Desonerado"
2. Preencha os códigos reais em core/sinapi_codigos.py (uma vez só --
   ver instruções lá).
3. Rode, apontando para o(s) arquivo(s) .xlsx extraído(s) do ZIP:
       python -m core.sinapi_import relatorio_insumos_RR.xlsx relatorio_composicoes_RR.xlsx
4. O script imprime um resumo (o que mudou, o que não foi encontrado,
   o que ficou sem código mapeado) e pede confirmação antes de gravar.
   Use --sim para gravar sem perguntar (útil em automação futura).

O QUE ELE NÃO FAZ
Não decide se o preço extraído "faz sentido" -- isso é responsabilidade
de core/validacao.py, que já roda em cima de qualquer preço vigente
(veio do SINAPI, de override manual, ou do padrão de
core/coeficientes.py) no momento do cálculo do orçamento.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import openpyxl

from core import tabela_precos as tp
from core.sinapi_codigos import MAPEAMENTO_SINAPI, UF_COLUNA_ALVOS


def _normalizar(texto) -> str:
    return str(texto).strip().lower() if texto is not None else ""


def _achar_cabecalho(ws):
    """Procura, nas primeiras 20 linhas da planilha, a linha que
    contém uma coluna de código. Retorna (indice_linha, valores_normalizados)
    ou (None, None) se não achar -- planilhas do SINAPI têm um bloco de
    título/legenda antes do cabeçalho real, então não dá pra assumir
    linha 1."""
    for row in ws.iter_rows(min_row=1, max_row=20):
        valores = [_normalizar(c.value) for c in row]
        if any("código" in v or "codigo" in v for v in valores):
            return row[0].row, valores
    return None, None


def _achar_colunas(cabecalho_valores):
    """Localiza os índices (0-based) das colunas de código, descrição,
    unidade e preço (para a UF configurada) dentro da linha de
    cabeçalho já normalizada."""
    idx = {}
    for i, v in enumerate(cabecalho_valores):
        if ("código" in v or "codigo" in v) and "codigo" not in idx:
            idx["codigo"] = i
        elif "descri" in v and "descricao" not in idx:
            idx["descricao"] = i
        elif v.strip() in ("unid", "unidade", "und") and "unidade" not in idx:
            idx["unidade"] = i
        elif v.strip() in UF_COLUNA_ALVOS and "preco" not in idx:
            idx["preco"] = i
    return idx


def _extrair_mes_referencia(caminho: Path) -> str | None:
    """Tenta adivinhar o mês de referência (AAAA-MM) a partir do nome
    do arquivo baixado da Caixa. Se não conseguir, o chamador deve
    pedir --mes explicitamente."""
    m = re.search(r"(20\d{2})[-_]?(\d{2})", caminho.stem)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None


def ler_planilha_sinapi(caminho: Path) -> dict[str, dict]:
    """Lê um arquivo .xlsx oficial do SINAPI e retorna
    {codigo_sinapi: {"preco": float, "descricao": str, "unidade": str}}
    para todos os códigos encontrados (não só os mapeados -- filtragem
    pelo mapeamento acontece depois, em importar())."""
    wb = openpyxl.load_workbook(caminho, data_only=True)
    encontrados = {}

    for ws in wb.worksheets:
        linha_cab, valores_cab = _achar_cabecalho(ws)
        if linha_cab is None:
            continue
        colunas = _achar_colunas(valores_cab)
        if "codigo" not in colunas or "preco" not in colunas:
            continue

        for row in ws.iter_rows(min_row=linha_cab + 1):
            codigo_cel = row[colunas["codigo"]].value if colunas["codigo"] < len(row) else None
            if codigo_cel is None:
                continue
            codigo = str(codigo_cel).strip()
            if not codigo or not codigo.replace(".", "", 1).isdigit():
                continue

            preco_cel = row[colunas["preco"]].value if colunas["preco"] < len(row) else None
            if preco_cel is None:
                continue
            try:
                preco = float(preco_cel)
            except (TypeError, ValueError):
                continue

            descricao = row[colunas["descricao"]].value if "descricao" in colunas else ""
            unidade = row[colunas["unidade"]].value if "unidade" in colunas else ""

            encontrados[codigo] = {
                "preco": preco,
                "descricao": str(descricao or "").strip(),
                "unidade": str(unidade or "").strip(),
            }

    return encontrados


def importar(arquivos: list[Path], mes_referencia: str | None = None) -> tuple[dict, list[str]]:
    """Lê um ou mais arquivos oficiais do SINAPI, cruza com
    core/sinapi_codigos.py e retorna (precos_para_gravar, avisos).

    precos_para_gravar: {chave_interna: {"valor": float, "descricao": str}}
    avisos: mensagens sobre chaves sem código, códigos não encontrados
    nos arquivos, ou mudanças de unidade suspeitas.
    """
    todos_codigos: dict[str, dict] = {}
    mes_detectado = mes_referencia
    for caminho in arquivos:
        todos_codigos.update(ler_planilha_sinapi(caminho))
        if mes_detectado is None:
            mes_detectado = _extrair_mes_referencia(caminho)

    precos_para_gravar = {}
    avisos = []

    for chave, mapeamento in MAPEAMENTO_SINAPI.items():
        if mapeamento.codigo is None:
            avisos.append(f"'{chave}' ainda sem código mapeado em sinapi_codigos.py -- pulado.")
            continue

        dado = todos_codigos.get(str(mapeamento.codigo))
        if dado is None:
            avisos.append(f"'{chave}' (código {mapeamento.codigo}) não foi encontrado nos "
                           f"arquivos informados -- confira se baixou o relatório certo "
                           f"({mapeamento.tipo}).")
            continue

        if mapeamento.unidade_esperada and dado["unidade"]:
            if mapeamento.unidade_esperada.lower() not in dado["unidade"].lower() and \
               dado["unidade"].lower() not in mapeamento.unidade_esperada.lower():
                avisos.append(f"'{chave}' (código {mapeamento.codigo}): unidade no SINAPI é "
                               f"'{dado['unidade']}', esperava algo como "
                               f"'{mapeamento.unidade_esperada}' -- confira antes de confiar no valor.")

        valor_convertido = dado["preco"] * mapeamento.fator_conversao
        if mapeamento.fator_conversao != 1.0:
            avisos.append(f"'{chave}' (código {mapeamento.codigo}): preço bruto do SINAPI "
                           f"R$ {dado['preco']:.2f} convertido para R$ {valor_convertido:.2f} "
                           f"(fator ×{mapeamento.fator_conversao}) -- confira se a conversão faz sentido.")

        precos_para_gravar[chave] = {
            "valor": valor_convertido,
            "descricao": dado["descricao"],
        }

    if mes_detectado is None:
        avisos.append("Não consegui identificar o mês de referência pelo nome do arquivo -- "
                       "use --mes AAAA-MM para informar manualmente. Os preços não serão "
                       "gravados sem essa informação.")

    return precos_para_gravar, avisos, mes_detectado


def _resumo(precos: dict, avisos: list[str], mes_ref: str | None):
    print(f"\n{'='*70}\nResumo da importação SINAPI\n{'='*70}")
    if mes_ref:
        print(f"Mês de referência detectado: {mes_ref}\n")

    if precos:
        print(f"{len(precos)} item(ns) prontos para atualizar:\n")
        for chave, dado in precos.items():
            atual = tp.obter_preco(chave, tp.coef.Preco(0, "", "")).valor
            marcador = " (sem mudança)" if abs(atual - dado["valor"]) < 0.005 else ""
            print(f"  - {chave}: R$ {atual:.2f} -> R$ {dado['valor']:.2f}{marcador}"
                  f"  [{dado['descricao'][:60]}]")
    else:
        print("Nenhum item pronto para atualizar.")

    if avisos:
        print(f"\n{len(avisos)} aviso(s):")
        for a in avisos:
            print(f"  ! {a}")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("arquivos", nargs="+", type=Path, help="Arquivo(s) .xlsx oficiais do SINAPI (Insumos e/ou Composições)")
    parser.add_argument("--mes", dest="mes", default=None, help="Mês de referência AAAA-MM, se não puder ser detectado pelo nome do arquivo")
    parser.add_argument("--sim", action="store_true", help="Grava sem pedir confirmação (para uso em automação)")
    args = parser.parse_args()

    for arq in args.arquivos:
        if not arq.exists():
            print(f"Arquivo não encontrado: {arq}", file=sys.stderr)
            sys.exit(1)

    precos, avisos, mes_ref = importar(args.arquivos, mes_referencia=args.mes)
    _resumo(precos, avisos, mes_ref)

    if not precos or mes_ref is None:
        print("Nada a gravar.")
        return

    if not args.sim:
        resp = input(f"Gravar {len(precos)} preço(s) como override, com fonte 'SINAPI oficial "
                      f"({mes_ref})'? [s/N] ").strip().lower()
        if resp != "s":
            print("Cancelado -- nada foi gravado.")
            return

    valores = {chave: dado["valor"] for chave, dado in precos.items()}
    tp.salvar_overrides(valores, fonte=f"SINAPI oficial (CAIXA/IBGE) - ref. {mes_ref}", data_ref=mes_ref)
    print(f"{len(valores)} preço(s) gravado(s) em {tp.CAMINHO_OVERRIDES}.")


if __name__ == "__main__":
    main()
