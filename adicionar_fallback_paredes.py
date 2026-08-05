"""
OrçaObra AI — Fallback automatico para metros de parede
========================================================
Adiciona uma correcao automatica no vision.py:
se a IA retornar metros_parede < area_piso_total * 0.55,
ajusta para area_piso_total * 0.75 e marca confianca como baixa.

Execute na pasta raiz do projeto.
"""
import os

RAIZ = os.getcwd()

if not os.path.exists(os.path.join(RAIZ, "app.py")):
    print("ERRO: execute na pasta raiz do projeto")
    exit(1)

vision_path = os.path.join(RAIZ, "core", "vision.py")
with open(vision_path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# Encontra o bloco onde os dados sao retornados (depois do json.loads)
# e antes do return dados
marcador = """    for campo in CAMPOS_AGREGADOS:
        dados.setdefault(campo, 0)"""

if marcador not in conteudo:
    print("ERRO: nao encontrei o ponto de insercao no vision.py")
    exit(1)

fallback = """    # ------------------------------------------------------------------
    # FALLBACK: corrige metros de parede se a IA subestimou
    # ------------------------------------------------------------------
    area_total = (
        dados.get("area_piso_seco", 0)
        + dados.get("area_piso_molhado", 0)
        + dados.get("area_piso_externo", 0)
    )
    mp = dados.get("metros_parede", 0)
    if area_total > 0 and mp < area_total * 0.55:
        sugestao = round(area_total * 0.75, 2)
        dados["metros_parede"] = sugestao
        if "confianca" not in dados:
            dados["confianca"] = {}
        dados["confianca"]["metros_parede"] = {
            "nivel": "baixa",
            "motivo": f"IA subestimou ({mp:.0f}m); corrigido automaticamente para {sugestao:.0f}m"
        }
    # ------------------------------------------------------------------

"""

novo_conteudo = conteudo.replace(marcador, fallback + marcador)

with open(vision_path, "w", encoding="utf-8") as f:
    f.write(novo_conteudo)

print("=" * 50)
print("  FALLBACK ADICIONADO!")
print("=" * 50)
print()
print("Regra:")
print("  Se metros_parede < area_total * 0.55:")
print("    -> ajusta automaticamente para area_total * 0.75")
print("    -> confianca vira 'baixa' com motivo explicativo")
print()
print("Proximos passos:")
print("  1. pytest tests/ -v")
print("  2. git add core/vision.py")
print("  3. git commit -m 'feat: fallback auto para paredes subestimadas'")
print("  4. git push && reboot no Streamlit Cloud")
print()
