"""
OrçaObra AI — Corrige IDs duplicados do Streamlit
=================================================
Adiciona 'key=' único em todos os widgets Streamlit (text_input,
number_input, selectbox, file_uploader, etc.) que não tiverem um.

Também verifica se há blocos de código DUPLICADOS no app.py
(efeito colateral do merge anterior).

Execute na pasta raiz do projeto.
"""
import os
import re

RAIZ = os.getcwd()

if not os.path.exists(os.path.join(RAIZ, "app.py")):
    print("❌ ERRO: execute na pasta raiz do projeto (onde está app.py)")
    exit(1)

app_path = os.path.join(RAIZ, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# =====================================================================
# 1. DETECTA CÓDIGO DUPLICADO (merge pode ter colado o mesmo bloco 2x)
# =====================================================================
print("=" * 60)
print("  VERIFICAÇÃO DE DUPLICAÇÃO")
print("=" * 60)

# Procura por padrões que NÃO deveriam aparecer 2 vezes
padroes_unicos = [
    r'st\.title\s*\(\s*"🏗️ OrçaObra AI"\s*\)',
    r'st\.subheader\s*\(\s*"Transforme plantas baixas em orçamentos em segundos"\s*\)',
    r'perfil = carregar_perfil\(\)',
]

duplicados = []
for padrao in padroes_unicos:
    ocorrencias = len(re.findall(padrao, conteudo))
    if ocorrencias > 1:
        duplicados.append(f"  • '{padrao[:40]}...' aparece {ocorrencias}x")

if duplicados:
    print("⚠️  ATENÇÃO: detectado possível conteúdo duplicado no app.py:")
    for d in duplicados:
        print(d)
    print()
    print("Sugestão: abra app.py no VS Code e procure por esses trechos.")
    print("Se houver blocos idênticos repetidos, delete a cópia extra.")
    print()
else:
    print("✅ Nenhum conteúdo obviamente duplicado detectado.")
    print()

# =====================================================================
# 2. ADICIONA key= EM WIDGETS SEM KEY
# =====================================================================
print("=" * 60)
print("  ADICIONANDO key= NOS WIDGETS")
print("=" * 60)

# Widgets que precisam de key único
WIDGETS = [
    "st.text_input",
    "st.number_input",
    "st.selectbox",
    "st.file_uploader",
    "st.button",
    "st.data_editor",
    "st.expander",
]

contador = 0
linhas = conteudo.splitlines()
novas_linhas = []

# Regex para detectar chamada de widget sem key=
# Ex: st.text_input("Label", value=...)
# Mas NÃO: st.text_input("Label", key="...", ...)
widget_regex = re.compile(
    r'^(\s*)((?:' + '|'.join(re.escape(w) for w in WIDGETS) + r')\s*\()'
)

# Conjunto de labels já vistos para evitar duplicar keys
labels_vistos = set()

i = 0
while i < len(linhas):
    linha = linhas[i]
    match = widget_regex.match(linha)

    if match and 'key=' not in linha:
        # Verifica se a chamada do widget continua nas próximas linhas
        chamada = linha
        j = i + 1
        while j < len(linhas) and not chamada.rstrip().endswith(")"):
            chamada += " " + linhas[j].strip()
            j += 1

        # Tenta extrair o label (primeiro argumento string)
        label_match = re.search(r'"([^"]+)"', chamada)
        if label_match:
            label = label_match.group(1)
            # Gera key baseada no label
            key_base = re.sub(r'[^\w]', '_', label.lower())
            key = key_base

            # Se já vimos esse label, adiciona sufixo numérico
            n = 1
            while key in labels_vistos:
                key = f"{key_base}_{n}"
                n += 1
            labels_vistos.add(key)

            # Adiciona key= antes do fechamento do parenteses
            # Encontra a posição do ')' final na linha original ou nas seguintes
            if chamada.rstrip().endswith(")"):
                # Insere key= antes do último )
                pos = linha.rfind(")")
                if pos != -1:
                    linha = linha[:pos] + f', key="{key}"' + linha[pos:]
                    contador += 1

    novas_linhas.append(linha)
    i += 1

# Reconstroi o conteúdo
conteudo = "\n".join(novas_linhas)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(conteudo)

print(f"✅ {contador} widget(s) receberam key= único")
print()
print("Próximo passo: rode o app novamente")
print("  streamlit run app.py")
print()
