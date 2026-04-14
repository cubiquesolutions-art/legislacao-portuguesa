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

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div style="max-width:340px;margin:4rem auto 0 auto;padding:2rem;background:#1a1d2e;border-radius:16px;border:1px solid #2d2f3e;">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div class="cubique-badge">Cubique</div>
            <h2 style="color:#ffffff;font-size:1.3rem;margin:0.5rem 0 0 0;">Acesso restrito</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        utilizador = st.text_input("Utilizador")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True)
        if submitted:
            if utilizador == st.secrets.get("LOGIN_USER", "") and password == st.secrets.get("LOGIN_PASS", ""):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Utilizador ou password incorretos.")
    st.stop()

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

SYSTEM_PROMPT = """És um especialista jurídico em legislação portuguesa atualizada.

FONTE OBRIGATÓRIA:
- Pesquisa SEMPRE em site:diariodarepublica.pt antes de responder
- A fonte primária é https://diariodarepublica.pt/dr/legislacao-por-codigo
- Só usa outras fontes se não encontrares a informação no Diário da República

REGRAS OBRIGATÓRIAS:
1. Usa a pesquisa web com "site:diariodarepublica.pt [tema]" para verificar a versão atual da lei
2. Cita o artigo EXATO e o diploma legal completo (ex: "Art. 232.º do Código do Trabalho, aprovado pela Lei n.º 7/2009, de 12 de fevereiro, com as alterações introduzidas pela Lei n.º X/XXXX")
3. Se a lei foi alterada recentemente, menciona a alteração e a data
4. Se não tiveres certeza absoluta do artigo, diz explicitamente "Atenção: verifique este artigo em diariodarepublica.pt"
5. Distingue sempre entre a regra geral e as exceções
6. Responde em português de Portugal
7. Nunca inventes artigos — se não souberes, admite e recomenda consulta a advogado

FORMATO OBRIGATÓRIO DA RESPOSTA:
**Resposta direta:** [resposta clara em 1-2 frases]

**Base legal:** [Artigo X.º do Diploma Y — versão em vigor]

**Detalhes e exceções:**
- [detalhe relevante 1]
- [exceção ou caso especial, se existir]

**⚠️ Aviso:** Esta informação é orientativa. Para decisões importantes, consulte um advogado ou verifique em diariodarepublica.pt."""

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
                search_tool = genai.protos.Tool(
                    google_search_retrieval=genai.protos.GoogleSearchRetrieval(
                        dynamic_retrieval_config=genai.protos.DynamicRetrievalConfig(
                            dynamic_threshold=0.3
                        )
                    )
                )
                model = genai.GenerativeModel(
                    "gemini-2.5-flash-lite",
                    system_instruction=SYSTEM_PROMPT
                )
                response = model.generate_content(pergunta, tools=[search_tool])
                resposta = response.text
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

            except Exception as e:
                # fallback sem search grounding
                try:
                    model = genai.GenerativeModel(
                        "gemini-2.5-flash-lite",
                        system_instruction=SYSTEM_PROMPT
                    )
                    response = model.generate_content(pergunta)
                    resposta = response.text
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
                except Exception as e2:
                    st.error(f"Erro: {str(e2)}")

if st.session_state.messages:
    if st.sidebar.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()
