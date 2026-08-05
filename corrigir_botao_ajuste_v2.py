
import os

RAIZ = os.getcwd()

if not os.path.exists(os.path.join(RAIZ, "app.py")):
    print("ERRO: execute na pasta raiz do projeto (onde esta app.py)")
    exit(1)

app_path = os.path.join(RAIZ, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    conteudo = f.read()

# 1. Remove key="input_metros_parede" do st.number_input
antigo_input = '            metros_parede = st.number_input(\n                "Paredes Lineares (m)",\n                value=float(dados["metros_parede"]), step=0.5, min_value=0.0,\n                key="input_metros_parede"\n            )'
novo_input = '            metros_parede = st.number_input(\n                "Paredes Lineares (m)",\n                value=float(dados["metros_parede"]), step=0.5, min_value=0.0\n            )'

conteudo = conteudo.replace(antigo_input, novo_input)

# 2. Remove a linha que tenta atualizar o session_state do widget
antigo_btn = '                if st.button(f"⚡ Ajustar para {sugestao_parede} m", key="btn_ajuste_parede"):\n                    st.session_state["dados_extraidos"]["metros_parede"] = sugestao_parede\n                    st.session_state["input_metros_parede"] = float(sugestao_parede)\n                    st.rerun()'
novo_btn = '                if st.button(f"⚡ Ajustar para {sugestao_parede} m", key="btn_ajuste_parede"):\n                    st.session_state["dados_extraidos"]["metros_parede"] = sugestao_parede\n                    st.rerun()'

conteudo = conteudo.replace(antigo_btn, novo_btn)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("✅ app.py corrigido:")
print("   • Removido key='input_metros_parede' do number_input")
print("   • Botao de ajuste agora so atualiza dados_extraidos + rerun")
print()
print("Rode o app novamente:")
print("  streamlit run app.py")
print()
