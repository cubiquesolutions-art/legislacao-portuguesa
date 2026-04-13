import os
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Consulta de Legislação Portuguesa",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ Consulta de Legislação Portuguesa")
st.caption("Faz uma pergunta e obtém a resposta com referência ao artigo e código exatos.")

try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
except Exception:
    api_key = None
api_key = api_key or os.environ.get("GEMINI_API_KEY") or st.sidebar.text_input(
    "🔑 Chave API Google (Gemini)",
    type="password",
    placeholder="AIza...",
)

if not api_key:
    st.sidebar.warning("Insere a tua chave API para começar.")
    st.info("👈 Insere a tua chave API do Google na barra lateral para começar.")
    st.stop()

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """És um especialista em legislação portuguesa.
Quando o utilizador faz uma pergunta sobre direitos, deveres ou regras legais em Portugal:
1. Pesquisa a legislação relevante (Código do Trabalho, Civil, Penal, etc.)
2. Responde de forma clara e direta à pergunta
3. Cita SEMPRE o artigo exato e o código/lei onde está a informação (ex: "Art. 249.º do Código do Trabalho")
4. Se houver exceções importantes, menciona-as
5. Responde em português de Portugal

Formato da resposta:
- Resposta direta à pergunta
- Base legal: [Artigo X.º do Código Y / Lei n.º X/XXXX]
- Detalhes adicionais relevantes (se aplicável)"""

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Ex: As faltas a consultas médicas são pagas?")

if pergunta:
    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("A pesquisar na legislação portuguesa..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=pergunta,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                    )
                )
                resposta = response.text
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    st.error("Limite de pedidos atingido. Aguarda um minuto e tenta novamente.")
                elif "API_KEY" in err or "401" in err:
                    st.error("Chave API inválida. Verifica a tua chave.")
                else:
                    st.error(f"Erro: {err}")

if st.session_state.messages:
    if st.sidebar.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()
