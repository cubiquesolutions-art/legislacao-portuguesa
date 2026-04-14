import os
import streamlit as st
import google.generativeai as genai

st.set_page_config(
    page_title="Cubique Apoio de Leis",
    page_icon="⚖️",
    layout="centered"
)

st.markdown("""
<style>
    /* Fundo e fonte geral */
    .stApp { background-color: #0f1117; }

    /* Header */
    .header-container {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .header-container h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 0.3rem;
    }
    .header-container p {
        color: #8b8fa8;
        font-size: 0.95rem;
        margin: 0;
    }
    .cubique-badge {
        display: inline-block;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 0.8rem;
    }

    /* Mensagens */
    .stChatMessage { border-radius: 12px; }

    /* Input */
    .stChatInput textarea {
        border-radius: 12px !important;
        border-color: #2d2f3e !important;
        background-color: #1a1d2e !important;
        color: #ffffff !important;
    }

    /* Botão sidebar */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        background-color: #1a1d2e;
        color: #8b8fa8;
        border: 1px solid #2d2f3e;
    }
    .stButton button:hover {
        background-color: #2d2f3e;
        color: #ffffff;
    }

    /* Esconder o menu do Streamlit */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
    <div class="cubique-badge">Cubique</div>
    <h1>⚖️ Apoio de Leis</h1>
    <p>Consulta legislação portuguesa com referência ao artigo e código exatos.</p>
</div>
""", unsafe_allow_html=True)

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

genai.configure(api_key=api_key)

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

pergunta = st.chat_input("Coloca aqui a tua questão jurídica...")

if pergunta:
    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("A pesquisar na legislação portuguesa..."):
            try:
                model = genai.GenerativeModel(
                    "gemini-2.5-flash-lite",
                    system_instruction=SYSTEM_PROMPT
                )
                response = model.generate_content(pergunta)
                resposta = response.text
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

            except Exception as e:
                err = str(e)
                st.error(f"Erro: {err}")

if st.session_state.messages:
    if st.sidebar.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()
