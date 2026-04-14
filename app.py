import os
import streamlit as st
from google import genai
from google.genai import types

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

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """És um especialista jurídico em legislação portuguesa atualizada.

=== BASE DE CONHECIMENTO JURÍDICO VERIFICADO ===
Usa estes valores como referência base — verifica sempre via pesquisa se houve alterações posteriores:

DIREITO DO TRABALHO (Código do Trabalho — Lei n.º 7/2009, de 12 de fevereiro):
- SMN 2025: €870/mês (Decreto-Lei n.º 108-A/2024, de 31 de dezembro de 2024)
- SMN 2024: €820/mês
- Art. 400.º CT — Aviso prévio por iniciativa do TRABALHADOR (cessação por iniciativa do trabalhador):
  * Contrato a termo com duração ≤ 6 meses: 15 dias
  * Contrato a termo com duração > 6 meses: 30 dias
  * Contrato por tempo indeterminado com antiguidade < 2 anos: 30 dias
  * Contrato por tempo indeterminado com antiguidade ≥ 2 anos: 60 dias
- Art. 337.º CT — Prescrição de créditos laborais: 1 ano após a data de cessação do contrato de trabalho
  (os créditos não prescrevem durante a vigência do contrato — Art. 337.º n.º 2 CT)
- Art. 394.º CT — Justa causa de resolução pelo trabalhador
- Indemnização por despedimento ilícito: Art. 391.º CT

ARRENDAMENTO URBANO (NRAU — Lei n.º 6/2006, de 27 de fevereiro, com alterações):
- Art. 1098.º CC — Denúncia pelo ARRENDATÁRIO de contrato a prazo certo:
  * Prazo contratual < 3 meses: antecedência de 1/3 do prazo
  * Prazo contratual entre 3 e 6 meses: 60 dias de antecedência
  * Prazo contratual ≥ 6 meses (ou ≥ 1 ano): 120 dias de antecedência antes do termo ou renovação
- Art. 1101.º CC — Denúncia pelo SENHORIO (não pelo arrendatário!)
- Art. 1096.º CC — Renovação automática do contrato
- Art. 1083.º CC — Resolução por incumprimento

OUTROS:
- IVA taxa normal: 23% (Portugal continental)
- IVA taxa intermédia: 13% | IVA taxa reduzida: 6%
- Prazo geral de prescrição civil: 20 anos (Art. 309.º CC)
- Prazo especial de prescrição: 5 anos para obrigações periódicas (Art. 310.º CC)

=== REGRAS OBRIGATÓRIAS ===
1. PESQUISA SEMPRE antes de responder — usa "site:diariodarepublica.pt [tema]" para verificar a versão atual
2. Os valores numéricos (prazos, montantes, percentagens) DEVEM ser confirmados pela pesquisa web
3. Se a pesquisa contradizer a base de conhecimento acima, usa o resultado da pesquisa e indica a alteração
4. Cita o artigo EXATO e o diploma legal completo
5. Se não encontrares confirmação via pesquisa, usa a base de conhecimento e indica "verificar em diariodarepublica.pt"
6. Nunca inventes artigos — se não souberes, diz explicitamente
7. Distingue sempre entre a regra geral e as exceções
8. Responde em português de Portugal

=== FORMATO OBRIGATÓRIO ===
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
            # Tentativa 1: gemini-2.5-flash com Google Search grounding (novo SDK)
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=pergunta,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    )
                )
                resposta = response.text
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

            except Exception as e1:
                # Fallback: gemini-2.5-flash sem grounding
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=pergunta,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                        )
                    )
                    resposta = response.text
                    st.markdown(resposta)
                    st.session_state.messages.append({"role": "assistant", "content": resposta})
                except Exception as e2:
                    st.error(f"Erro: {str(e2)}")

if st.session_state.messages:
    if st.sidebar.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()
