"""
OrçaObra AI — Aplica melhorias de persistência e prompt
========================================================
1. Adiciona core/paths.py para detectar ambiente local vs Streamlit Cloud
2. Atualiza core/vision.py com prompt melhorado para paredes
3. Atualiza app.py, core/historico.py, core/perfil_empresa.py,
   core/cache.py e core/tabela_precos.py para usar os caminhos
   persistentes de core/paths.py

Execute na pasta raiz do projeto.
"""
import os
import shutil

RAIZ = os.getcwd()

if not os.path.exists(os.path.join(RAIZ, "app.py")):
    print("❌ ERRO: execute na pasta raiz do projeto (onde está app.py)")
    exit(1)

print("=" * 60)
print("  ORÇAOBRA AI — MELHORIAS: PERSISTÊNCIA + PROMPT")
print("=" * 60)
print()

# ------------------------------------------------------------------
# 1. Cria core/paths.py
# ------------------------------------------------------------------
paths_content = r'''"""
Utilitário de caminhos de arquivo que funciona tanto no
ambiente de desenvolvimento local quanto no Streamlit Cloud.

No Streamlit Cloud, o filesystem do container é efêmero -- reinícios
apagam tudo fora do diretório persistente. Este módulo detecta o
ambiente e retorna caminhos adequados.
"""
import os


def _diretorio_base():
    """Retorna o diretório base para dados persistentes.

    No Streamlit Cloud, existe um diretório persistente em
    /mount/data/ (ou similar, dependendo da versão). Em ambiente
    local, usa a pasta raiz do projeto.
    """
    # Streamlit Cloud (versões mais recentes usam /mount/data)
    for candidato in ("/mount/data", "/app/data"):
        if os.path.exists(candidato) and os.access(candidato, os.W_OK):
            return candidato

    # Ambiente local: pasta raiz do projeto (onde está app.py)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


RAIZ = _diretorio_base()

PASTA_ORCAMENTOS = os.path.join(RAIZ, "orcamentos_salvos")
PASTA_PERFIL = os.path.join(RAIZ, "perfil_empresa")
DB_PATH = os.path.join(RAIZ, "historico.db")
CACHE_DIR = os.path.join(RAIZ, ".cache_ia")
PERFIL_PATH = os.path.join(RAIZ, "perfil_empresa.json")
OVERRIDES_PATH = os.path.join(RAIZ, "precos_customizados.json")


def garantir_diretorios():
    """Cria os diretórios de dados se não existirem."""
    for pasta in (PASTA_ORCAMENTOS, PASTA_PERFIL, CACHE_DIR):
        os.makedirs(pasta, exist_ok=True)
'''

paths_path = os.path.join(RAIZ, "core", "paths.py")
with open(paths_path, "w", encoding="utf-8") as f:
    f.write(paths_content)
print("✅ core/paths.py criado")

# ------------------------------------------------------------------
# 2. Atualiza core/vision.py — prompt melhorado para paredes
# ------------------------------------------------------------------
vision_path = os.path.join(RAIZ, "core", "vision.py")
with open(vision_path, "r", encoding="utf-8") as f:
    vision_content = f.read()

# Substitui o bloco do passo 4 (paredes) pelo mais detalhado
old_step4 = """    4. Percorra o perimetro de cada comodo e conte os segmentos de
       parede, somando os comprimentos lineares (nao conte a mesma
       parede duas vezes quando ela e compartilhada entre dois comodos)."""

new_step4 = """    4. **PAREDES (instrução crítica -- leia com atenção):**
       Percorra o perimetro de cada comodo e some os comprimentos
       lineares de TODOS os segmentos de parede. **IMPORTANTE:**
       - Uma parede COMPARTILHADA entre dois comodos (ex: parede entre
         sala e cozinha) deve ser contada APENAS UMA VEZ no total.
       - Paredes EXTERNAS (fachada) contam sempre.
       - Paredes INTERNAS (divisórias) contam uma vez cada, mesmo que
         sejam usadas por dois cômodos adjacentes.
       - NÃO subestime: o total de metros de parede tipicamente é
         0,55 a 1,10 vezes a área total de piso. Se sua soma der menos
         que 0,55x a área total, revise -- provavelmente esqueceu de
         contar paredes internas ou externas.
       - Para cada parede, use o comprimento linear (nao a area)."""

if old_step4 in vision_content:
    vision_content = vision_content.replace(old_step4, new_step4)
    with open(vision_path, "w", encoding="utf-8") as f:
        f.write(vision_content)
    print("✅ core/vision.py — prompt de paredes melhorado")
else:
    print("⚠️  core/vision.py — bloco do passo 4 não encontrado exatamente")
    print("   (pode já estar atualizado ou o formato mudou)")

# ------------------------------------------------------------------
# 3. Atualiza app.py para usar core/paths
# ------------------------------------------------------------------
app_path = os.path.join(RAIZ, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

# Adiciona import de paths no topo (depois dos outros imports)
if "from core import paths" not in app_content:
    # Encontra a linha do import de tabela_precos e adiciona depois
    app_content = app_content.replace(
        "from core import tabela_precos",
        "from core import tabela_precos\nfrom core import paths"
    )
    # Substitui as definições de pasta
    app_content = app_content.replace(
        'PASTA_ORCAMENTOS = "orcamentos_salvos"\nos.makedirs(PASTA_ORCAMENTOS, exist_ok=True)\n\nPASTA_PERFIL = "perfil_empresa"\nos.makedirs(PASTA_PERFIL, exist_ok=True)',
        'paths.garantir_diretorios()\nPASTA_ORCAMENTOS = paths.PASTA_ORCAMENTOS\nPASTA_PERFIL = paths.PASTA_PERFIL'
    )
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.py — usando caminhos persistentes")
else:
    print("ℹ️  app.py — já usa core/paths")

# ------------------------------------------------------------------
# 4. Atualiza core/historico.py
# ------------------------------------------------------------------
hist_path = os.path.join(RAIZ, "core", "historico.py")
with open(hist_path, "r", encoding="utf-8") as f:
    hist_content = f.read()

if "from core import paths" not in hist_content:
    hist_content = hist_content.replace(
        "import sqlite3\nimport os\nfrom datetime import datetime",
        "import sqlite3\nimport os\nfrom datetime import datetime\n\nfrom core import paths"
    )
    hist_content = hist_content.replace(
        'DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "historico.db")',
        'DB_PATH = paths.DB_PATH'
    )
    with open(hist_path, "w", encoding="utf-8") as f:
        f.write(hist_content)
    print("✅ core/historico.py — usando caminho persistente")
else:
    print("ℹ️  core/historico.py — já atualizado")

# ------------------------------------------------------------------
# 5. Atualiza core/perfil_empresa.py
# ------------------------------------------------------------------
perfil_path = os.path.join(RAIZ, "core", "perfil_empresa.py")
with open(perfil_path, "r", encoding="utf-8") as f:
    perfil_content = f.read()

if "from core import paths" not in perfil_content:
    perfil_content = perfil_content.replace(
        "import json\nimport os",
        "import json\nimport os\n\nfrom core import paths"
    )
    perfil_content = perfil_content.replace(
        'PERFIL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "perfil_empresa.json")',
        'PERFIL_PATH = paths.PERFIL_PATH'
    )
    with open(perfil_path, "w", encoding="utf-8") as f:
        f.write(perfil_content)
    print("✅ core/perfil_empresa.py — usando caminho persistente")
else:
    print("ℹ️  core/perfil_empresa.py — já atualizado")

# ------------------------------------------------------------------
# 6. Atualiza core/cache.py
# ------------------------------------------------------------------
cache_path = os.path.join(RAIZ, "core", "cache.py")
with open(cache_path, "r", encoding="utf-8") as f:
    cache_content = f.read()

if "from core import paths" not in cache_content:
    cache_content = cache_content.replace(
        "import hashlib\nimport json\nimport os",
        "import hashlib\nimport json\nimport os\n\nfrom core import paths"
    )
    cache_content = cache_content.replace(
        'CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache_ia")\nos.makedirs(CACHE_DIR, exist_ok=True)',
        'CACHE_DIR = paths.CACHE_DIR\npaths.garantir_diretorios()'
    )
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(cache_content)
    print("✅ core/cache.py — usando caminho persistente")
else:
    print("ℹ️  core/cache.py — já atualizado")

# ------------------------------------------------------------------
# 7. Atualiza core/tabela_precos.py
# ------------------------------------------------------------------
tp_path = os.path.join(RAIZ, "core", "tabela_precos.py")
with open(tp_path, "r", encoding="utf-8") as f:
    tp_content = f.read()

if "from core import paths" not in tp_content:
    tp_content = tp_content.replace(
        "import json\nimport os\nfrom datetime import date",
        "import json\nimport os\nfrom datetime import date\n\nfrom core import paths"
    )
    tp_content = tp_content.replace(
        'CAMINHO_OVERRIDES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "precos_customizados.json")',
        'CAMINHO_OVERRIDES = paths.OVERRIDES_PATH'
    )
    with open(tp_path, "w", encoding="utf-8") as f:
        f.write(tp_content)
    print("✅ core/tabela_precos.py — usando caminho persistente")
else:
    print("ℹ️  core/tabela_precos.py — já atualizado")

print()
print("=" * 60)
print("  ✅ MELHORIAS APLICADAS!")
print("=" * 60)
print()
print("Resumo:")
print("  • core/paths.py — caminhos persistentes (local + cloud)")
print("  • core/vision.py — prompt melhorado para paredes")
print("  • app.py, historico.py, perfil_empresa.py, cache.py,")
print("    tabela_precos.py — usando caminhos persistentes")
print()
print("Próximos passos:")
print("  1. Rode os testes: pytest tests/ -v")
print("  2. Commit e push: git add . && git commit -m ... && git push")
print("  3. No Streamlit Cloud, clique em 'Reboot' para aplicar")
print()