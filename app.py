import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
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
    <p>Consulta legislação portuguesa — fonte: diariodarepublica.pt</p>
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

# ── Busca directa no Diário da República ──────────────────────────────────────

DRE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DRE_BASE = "https://diariodarepublica.pt"

# Páginas fixas de legislação consolidada por código
DRE_CODIGOS = {
    "trabalho": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-trabalho",
    "civil": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-civil",
    "penal": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-penal",
    "comercial": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-comercial",
    "processo civil": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-processo-civil",
    "processo penal": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-processo-penal",
    "iva": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-iva",
    "irs": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-irs",
    "irc": f"{DRE_BASE}/dr/legislacao-por-codigo/codigo-irc",
    "arrendamento": f"{DRE_BASE}/dr/legislacao-por-codigo/nrau",
}


def _extrair_texto(html: str, url: str, max_chars: int = 4000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    texto = soup.get_text(separator="\n", strip=True)
    linhas = [l.strip() for l in texto.splitlines() if len(l.strip()) > 25]
    conteudo = "\n".join(linhas)
    return f"[Fonte: {url}]\n{conteudo[:max_chars]}"


def _get(url: str, timeout: int = 12) -> requests.Response | None:
    try:
        r = requests.get(url, headers=DRE_HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None


def buscar_dre(pergunta: str) -> str:
    """
    1. Tenta a pesquisa no DRE (endpoint /dr/pesquisa).
    2. Se não encontrar links, usa as páginas de códigos relevantes.
    Devolve o texto extraído (máx. ~8000 chars total).
    """
    blocos: list[str] = []

    # ── 1. Pesquisa no DRE ──────────────────────────────────────────────────
    url_pesquisa = f"{DRE_BASE}/dr/pesquisa?q={quote_plus(pergunta)}"
    r = _get(url_pesquisa)

    links_encontrados: list[str] = []
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href]"):
            href: str = a["href"]
            if any(p in href for p in ["/detalhe/", "/legislacao/", "/dr/", "/sumario/"]):
                full = href if href.startswith("http") else DRE_BASE + href
                if full not in links_encontrados and DRE_BASE in full:
                    links_encontrados.append(full)

    for url in links_encontrados[:3]:
        r2 = _get(url)
        if r2:
            blocos.append(_extrair_texto(r2.text, url))
        if len(blocos) >= 2:
            break

    # ── 2. Fallback: páginas de código relevantes ────────────────────────────
    if not blocos:
        pq = pergunta.lower()
        for chave, url_codigo in DRE_CODIGOS.items():
            if chave in pq or any(w in pq for w in chave.split()):
                r3 = _get(url_codigo)
                if r3:
                    blocos.append(_extrair_texto(r3.text, url_codigo))
                break

        # Se ainda nada, tenta a página principal de legislação por código
        if not blocos:
            url_leg = f"{DRE_BASE}/dr/legislacao-por-codigo"
            r4 = _get(url_leg)
            if r4:
                blocos.append(_extrair_texto(r4.text, url_leg, max_chars=2000))

    return "\n\n---\n\n".join(blocos)


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """És um especialista jurídico em legislação portuguesa atualizada.

=== BASE DE CONHECIMENTO JURÍDICO VERIFICADO ===
Usa estes valores como referência base — a pesquisa ao DRE confirma ou actualiza:

DIREITO DO TRABALHO (Código do Trabalho — Lei n.º 7/2009, de 12 de fevereiro):
- SMN 2025: €870/mês (Decreto-Lei n.º 108-A/2024, de 31 de dezembro de 2024)
- SMN 2024: €820/mês
- Art. 400.º CT — Aviso prévio por iniciativa do TRABALHADOR:
  * Contrato a termo ≤ 6 meses: 15 dias
  * Contrato a termo > 6 meses: 30 dias
  * Contrato por tempo indeterminado com antiguidade < 2 anos: 30 dias
  * Contrato por tempo indeterminado com antiguidade ≥ 2 anos: 60 dias
- Art. 337.º CT — Prescrição de créditos laborais: 1 ano após cessação do contrato
- Art. 394.º CT — Justa causa de resolução pelo trabalhador
- Art. 391.º CT — Indemnização por despedimento ilícito

ARRENDAMENTO URBANO (NRAU — Lei n.º 6/2006, de 27 de fevereiro):
- Art. 1098.º CC — Denúncia pelo ARRENDATÁRIO (prazo certo):
  * < 3 meses: 1/3 do prazo
  * 3-6 meses: 60 dias
  * ≥ 6 meses: 120 dias antes do termo ou renovação
- Art. 1101.º CC — Denúncia pelo SENHORIO
- Art. 1096.º CC — Renovação automática

OUTROS:
- IVA: 23% normal | 13% intermédia | 6% reduzida (Portugal continental)
- Prazo geral de prescrição civil: 20 anos (Art. 309.º CC)
- Prazo especial: 5 anos para obrigações periódicas (Art. 310.º CC)

=== REGRAS OBRIGATÓRIAS ===
1. Responde EXCLUSIVAMENTE com base no conteúdo fornecido do diariodarepublica.pt
2. Se o conteúdo do DRE confirmar ou actualizar a base de conhecimento, usa o DRE
3. Cita o artigo EXATO e o diploma legal completo
4. Nunca inventes artigos — se não souberes, diz explicitamente
5. Distingue sempre entre a regra geral e as exceções
6. Responde em português de Portugal

=== FORMATO OBRIGATÓRIO ===
**Resposta direta:** [resposta clara em 1-2 frases]

**Base legal:** [Artigo X.º do Diploma Y — versão em vigor]

**Detalhes e exceções:**
- [detalhe relevante 1]
- [exceção ou caso especial, se existir]

**📌 Fonte:** diariodarepublica.pt

**⚠️ Aviso:** Esta informação é orientativa. Para decisões importantes, consulte um advogado."""

# ── Chat ──────────────────────────────────────────────────────────────────────

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
        with st.spinner("A consultar diariodarepublica.pt..."):

            # 1. Buscar conteúdo directamente no DRE
            conteudo_dre = buscar_dre(pergunta)

            if conteudo_dre:
                contexto = f"""=== CONTEÚDO OBTIDO DE DIARIODAREPUBLICA.PT ===
{conteudo_dre}

Com base no conteúdo acima do Diário da República Electrónico, responde à seguinte questão:
{pergunta}"""
            else:
                # DRE não respondeu — usa apenas a base de conhecimento
                contexto = f"""Não foi possível obter conteúdo do diariodarepublica.pt neste momento.
Responde com base na tua base de conhecimento jurídico verificado e indica que o utilizador deve confirmar em diariodarepublica.pt.

Questão: {pergunta}"""

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contexto,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                    )
                )
                resposta = response.text
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})

            except Exception as e:
                st.error(f"Erro ao gerar resposta: {str(e)}")

if st.session_state.messages:
    if st.sidebar.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()
