import streamlit as st
import pandas as pd
from openai import OpenAI
import time
import requests
from requests.auth import HTTPBasicAuth
import json
import re
import concurrent.futures
import urllib.parse
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field, ValidationError, field_validator

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Arco Martech | Motor GEO", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Arco Martech | Motor GEO v3.0 (Integração WP)")
st.caption("Crie artigos técnicos em HTML estruturado para dominar as respostas de LLMs e Google.")

# ==========================================
# MENU LATERAL (GUIA DO USUÁRIO)
# ==========================================
with st.sidebar:
    st.header("📖 Guia do Motor GEO")
    st.markdown("Bem-vindo à v3.0. Este sistema utiliza uma arquitetura **multi-agentes** para criar conteúdo com autoridade máxima.")
    
    with st.expander("✍️ 1. Gerador de Artigos", expanded=False):
        st.markdown("""
        **O Fluxo da Inteligência Artificial:**
        1. **Busca (Serper + Jina):** Lê o conteúdo real do Top 3 do Google.
        2. **Auditoria (GPT-4o-mini):** Analisa o que as IAs já respondem hoje.
        3. **Estratégia (GPT-4o):** Identifica lacunas e cria o briefing de superação.
        4. **Redação (Claude 3.7 Sonnet):** Escreve o código HTML blindado.
        5. **Mídia (Unsplash API):** Injeta fotos corporativas reais.
        
        ⏱️ *Tempo médio: 45 a 60 segundos.*

        **💡 Como enriquecer sua Palavra-Chave:**
        Termos simples funcionam perfeitamente, mas adicionar contexto gera resultados cirúrgicos:
        - 📝 **Direto:** `inadimplência escolar`
        - 🎯 **Estratégico:** `como reduzir a inadimplência escolar (focar em soluções amigáveis para renegociação com os pais de escolas de médio porte)`
        
        - 📝 **Direto:** `ensino bilíngue`
        - 🎯 **Estratégico:** `impactos cognitivos do bilinguismo (usar referências de neurociência e focar na retenção de matrículas)`
        """)
        
    with st.expander("📚 2. Brandbook (Base de Dados)", expanded=False):
        st.markdown("""
        O **Claude 3.7** consulta esta matriz antes de escrever. Altere os dados aqui para injetar **inteligência proprietária** e dados reais da sua marca no texto:
        - **Posicionamento:** Atualize sempre que houver uma nova campanha, diferencial de mercado ou lançamento de produto.
        - **Regras Positivas:** É aqui que você embasa a autoridade. Ex: *"Sempre mencione que usamos a Metodologia X, cite que nossa solução atende 500 escolas e lembre que ganhamos o Prêmio Y em 2025."*
        - **Regras Negativas:** Proíba vícios ou menções de risco. Ex: *"Nunca use a palavra 'aluno' (use 'estudante'), nunca critique o sistema público de ensino."*
        """)
        
    with st.expander("🔍 3. Monitor de GEO e E-E-A-T", expanded=False):
        st.markdown("""
        Um simulador do algoritmo do Google, movido pelo **GPT-4o**.
        
        **O que é E-E-A-T?**
        É a sigla do Google para **Experiência, Especialidade, Autoridade e Confiabilidade**. IAs e motores de busca priorizam textos que provam E-E-A-T (trazendo dados reais, fontes nominais, metodologias validadas e tom especialista), punindo conteúdos genéricos.
        
        **Como usar a ferramenta:**
        Além de auditar os textos recém-gerados, você pode colar o HTML de artigos antigos do seu blog aqui para descobrir exatamente o que falta para eles ranquearem melhor sob a ótica do E-E-A-T.
        """)
        
    st.divider()
    st.caption("⚙️ **Stack:** Python | Streamlit | Pydantic\n🧠 **LLMs:** GPT-4o | Claude 3.7 Sonnet\n🔌 **APIs:** Serper.dev | Jina AI | Unsplash")

# ==========================================
# ESTRUTURAS PYDANTIC
# ==========================================
class MetadadosArtigo(BaseModel):
    title: str = Field(..., description="Título H1 otimizado (max 60 chars)")
    meta_description: str = Field(..., description="Meta description persuasiva (max 150 chars)")
    dicas_imagens: list[str] = Field(..., description="Lista com 2 prompts curtos EM INGLÊS para buscar imagens (ex: ['futuristic classroom', 'student studying'])")
    schema_faq: dict = Field(..., description="Objeto JSON-LD FAQPage completo e idêntico ao texto")

    @field_validator('title', mode='before')
    @classmethod
    def ajustar_tamanho_titulo(cls, v: str) -> str:
        return v[:57] + "..." if len(v) > 60 else v

    @field_validator('meta_description', mode='before')
    @classmethod
    def ajustar_tamanho_meta(cls, v: str) -> str:
        return v[:147] + "..." if len(v) > 150 else v

# ==========================================
# 2. BRANDBOOK EMBUTIDO (COM REGRAS POSITIVAS)
# ==========================================
if 'brandbook_df' not in st.session_state:
    dados_iniciais = [
        {
            "Marca": "@internationalschool",
            "Posicionamento": "O programa bilíngue mais premiado do Brasil. Pioneira em bilinguismo no país. Prover soluções educacionais consistentes e inovadoras. Transformar vidas por meio da educação bilíngue. Empoderar a comunidade escolar para desenvolver o aluno como ser integral.",
            "Territorios": "Bilinguismo, educação, integral, viagens",
            "TomDeVoz": "Especialista, inovador, inspirador, prático.",
            "PublicoAlvo": "Gestores, diretores e coordenadores de escolas (B2B) pais e famílias (Foco B2C)",
            "RegrasNegativas": "Não usar termos genéricos sem contexto, não soar arrogante ou sabe tudo, não inferir que quem aprende inglês é superior ou melhor, não citar palavras em inglês sem tradução entre parênteses depois. Não focar o discurso somente nos pais (lembrar sempre da figura da escola). NUNCA usar a construção 'neste artigo iremos' ou similares.",
            "RegrasPositivas": "Focar em estrutura informativa. Sempre trazer dados para embasar afirmações vindos de fontes seguras e confiáveis, sempre citar e linkar a fonte dos dados, preferir fontes de pesquisas, governos e instituições de renome. Sempre começar o primeiro parágrafo com um gancho que instigue a leitura, de preferência acompanhado de dado. Podemos usar pesquisas nacionais ou internacionais. Sempre usar construção gramatical focada em clareza: iniciar parágrafos com frases de afirmação, não com conectivos. Sempre conectar com a importância de aprender inglês indo além da gramática: focar na importância de aprender com contexto."
        },
        {"Marca": "@saseducacao", "Posicionamento": "Marca visionária, líder em aprovação. Entrega de valor em tecnologia e serviço.", "Territorios": "Vestibulares, Tecnologia, Inovação, Pesquisas", "TomDeVoz": "Acadêmico, inovador, especialista e inspirador.", "PublicoAlvo": "Estudantes, vestibulandos e pais. (Foco B2C)", "RegrasNegativas": "Não usar tom professoral antiquado, não prometer aprovação sem esforço.", "RegrasPositivas": ""},
        {"Marca": "@plataformacoc", "Posicionamento": "Marca aprovadora que evolui a escola pedagogicamente.", "Territorios": "Vestibulares, Esportes, Gestão escolar", "TomDeVoz": "Consultivo, parceiro, dinâmico.", "PublicoAlvo": "Mantenedores e coordenadores pedagógicos. (B2B)", "RegrasNegativas": "Não focar discurso apenas no aluno, não usar jargões sem explicação.", "RegrasPositivas": ""},
        {"Marca": "@isaaceducacao", "Posicionamento": "Maior solução financeira e de gestão para a educação.", "Territorios": "Gestão financeira, Inovação", "TomDeVoz": "Corporativo, direto, analítico.", "PublicoAlvo": "Diretores financeiros e donos de escolas. (B2B)", "RegrasNegativas": "Não parecer banco engessado, não usar linguagem infantilizada.", "RegrasPositivas": ""},
        {"Marca": "@geekieeducacao", "Posicionamento": "Metodologia inovadora (aluno no centro), fácil de implementar.", "Territorios": "Inovação, IA/Personalização", "TomDeVoz": "Inovador, moderno, ágil.", "PublicoAlvo": "Diretores de inovação e escolas modernas. (B2B)", "RegrasNegativas": "Não parecer sistema engessado, não usar linguagem punitiva.", "RegrasPositivas": ""},
        {"Marca": "@sistemapositivodeensino", "Posicionamento": "Formação integral, humana e próxima. A maior rede do Brasil.", "Territorios": "Formação integral, Inclusão, Tradição", "TomDeVoz": "Acolhedor, tradicional, humano.", "PublicoAlvo": "Famílias e diretores de escolas tradicionais.", "RegrasNegativas": "Não parecer frio, não usar jargões técnicos sem contexto acolhedor.", "RegrasPositivas": ""},
        {"Marca": "@saedigital", "Posicionamento": "Melhor integração físico/digital, hiperatualizada.", "Territorios": "Tecnologia, Inovação Digital", "TomDeVoz": "Prático, tecnológico, dinâmico.", "PublicoAlvo": "Gestores buscando modernização com custo-benefício.", "RegrasNegativas": "Não parecer inacessível, não diminuir a importância do material físico.", "RegrasPositivas": ""},
        {"Marca": "@solucaoconquista", "Posicionamento": "Solução completa focada na parceria Escola-Família.", "Territorios": "Família, Educação Infantil, Valores", "TomDeVoz": "Familiar, parceiro, simples e didático.", "PublicoAlvo": "Pais e gestores de escolas de educação infantil.", "RegrasNegativas": "Não usar tom corporativo frio, não focar em pressão de vestibular.", "RegrasPositivas": ""}
    ]
    st.session_state['brandbook_df'] = pd.DataFrame(dados_iniciais)

# ==========================================
# 3. CONEXÃO SEGURA E CREDENCIAIS
# ==========================================
try:
    TOKEN = st.secrets["OPENROUTER_KEY"]
except Exception:
    TOKEN = None

try:
    SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
except Exception:
    SERPAPI_KEY = None

WP_URL = st.secrets.get("WP_URL", "")
WP_USER = st.secrets.get("WP_USER", "")
WP_PWD = st.secrets.get("WP_APP_PASSWORD", "")
WP_READY = bool(WP_URL and WP_USER and WP_PWD)

# ==========================================
# 3.2 FUNÇÕES DE CONTEXTO E BUSCA
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def buscar_contexto_google(palavra_chave):
    if not SERPAPI_KEY:
        return "Sem chave Serper configurada. Pule o contexto do Google."
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": palavra_chave, "gl": "br", "hl": "pt-br"})
    headers = {'X-API-KEY': SERPAPI_KEY, 'Content-Type': 'application/json'}
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        dados = response.json()
        contexto_extraido = []
        if "answerBox" in dados:
            snippet = dados["answerBox"].get("snippet") or dados["answerBox"].get("answer", "Sem texto")
            contexto_extraido.append(f"📍 GOOGLE FEATURED SNIPPET ATUAL:\n{snippet}\n")
        if "knowledgeGraph" in dados:
            desc = dados["knowledgeGraph"].get("description", "")
            contexto_extraido.append(f"🧠 GOOGLE KNOWLEDGE GRAPH:\n{desc}\n")
        if "organic" in dados:
            contexto_extraido.append("📊 TOP 3 RESULTADOS ORGÂNICOS (CONTEÚDO LIDO VIA JINA):")

            def buscar_jina(res_item, index):
                titulo = res_item.get('title', 'Sem Título')
                snippet = res_item.get('snippet', 'Sem Snippet')
                link = res_item.get('link', '')
                conteudo_real = ""
                if link:
                    try:
                        jina_headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'X-Return-Format': 'markdown',
                            'Accept': 'text/plain'
                        }
                        jina_res = requests.get(f"https://r.jina.ai/{link}", headers=jina_headers, timeout=12)
                        if jina_res.status_code == 200:
                            conteudo_real = jina_res.text[:1500]
                    except Exception:
                        conteudo_real = "Falha ao ler o conteúdo integral."
                return f"{index+1}. Título: {titulo}\n Snippet: {snippet}\n Link: {link}\n Conteúdo:\n{conteudo_real}\n"

            with concurrent.futures.ThreadPoolExecutor() as executor:
                resultados_jina = list(executor.map(lambda x: buscar_jina(x[1], x[0]), enumerate(dados["organic"][:3])))
            contexto_extraido.extend(resultados_jina)
        resultado_final = "\n".join(contexto_extraido)
        return resultado_final if resultado_final else "Sem resultados orgânicos relevantes."
    except Exception as e:
        return f"Erro ao coletar dados do Google (Serper): {e}"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def chamar_llm(system_prompt, user_prompt, model, temperature=0.3, response_format=None):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=TOKEN,
        default_headers={"HTTP-Referer": "https://arcomartech.com", "X-Title": "Gerador GEO WP"}
    )
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
    }
    if response_format:
        kwargs["response_format"] = response_format
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_baseline_llm(palavra_chave):
    system_prompt = "Você é um pesquisador de IA sênior. Forneça a resposta que uma IA daria hoje para o termo pesquisado, citando o consenso atual."
    user_prompt = f"O que você sabe sobre: '{palavra_chave}'? Retorne um resumo profundo de como esse tema é respondido atualmente pelas IAs."
    try:
        return chamar_llm(system_prompt, user_prompt, model="openai/gpt-4o-mini", temperature=0.1)
    except Exception as e:
        return f"Erro ao buscar Baseline de IA: {e}"

# ==========================================
# 4. MOTOR PRINCIPAL
# ==========================================
def executar_geracao_completa(palavra_chave, marca_alvo):
    df = st.session_state['brandbook_df']
    marca_info = df[df['Marca'] == marca_alvo].iloc[0].to_dict()
    from datetime import datetime
    ano_atual = datetime.now().year

    st.write("🕵️‍♂️ Fase 0: Buscando Google (Serper + Jina) e IAs (Perplexity) em paralelo...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futuro_google = executor.submit(buscar_contexto_google, palavra_chave)
        futuro_ia = executor.submit(buscar_baseline_llm, palavra_chave)
        try:
            contexto_google = futuro_google.result(timeout=45)
        except concurrent.futures.TimeoutError:
            contexto_google = "Aviso: A busca orgânica demorou muito. Conteúdo ignorado para manter a velocidade."
        try:
            baseline_ia = futuro_ia.result(timeout=45)
        except concurrent.futures.TimeoutError:
            baseline_ia = "Aviso: O motor de Baseline demorou muito a responder. Ignorado."

    st.write("🧠 Fase 1: Planejamento Editorial (GPT-4o)...")

    system_1 = """
Você é um Estrategista de Conteúdo GEO (LLM + Search) e Editor-Chefe orientado por E‑E‑A‑T.
Objetivo: produzir um briefing que entregue GANHO DE INFORMAÇÃO e fuja de estruturas genéricas.

REGRAS-MESTRAS (obrigatórias):
1) Nada de “definições básicas” ou “o que é”. O leitor já domina fundamentos. Busque ângulos originais e comparativos.
2) Zero jargão vazio. Frases curtas, voz ativa, tom assertivo.
3) Anti-alucinação total: só liste dados/estudos se houver URL pública verificável (preferência: domínios .gov .edu .org e organismos internacionais). Se não houver, declare explicitamente FOCO CONCEITUAL/METODOLÓGICO.
4) Neutralidade competitiva: ignore marcas privadas concorrentes presentes no contexto bruto.
5) Saída sempre em pt-BR.

ENTREGÁVEIS DO BRIEFING:
A) ÂNGULO NARRATIVO ÚNICO: escolha 1 (ex.: Quebra de Mito; Guia Tático; Análise de Tendência; Framework Operacional). Justifique em 2-3 linhas.
B) ESTRUTURA ANTI-FÓRMULA (H2): proponha 4 H2 provocativos, específicos e complementares (sem “O que é”, “Benefícios”, “Conclusão”).
C) MAPA DE EVIDÊNCIAS: liste no máximo 6 bullets com pares (afirmação → URL). Inclua apenas fontes neutras e confiáveis. Se não existirem, escreva: FOCO TOTALMENTE CONCEITUAL E METODOLÓGICO, SEM ESTATÍSTICAS.
D) DENSIDADE SEMÂNTICA: 12 termos técnicos obrigatórios (curtos, específicos, ex.: “neuroplasticidade”, “taxa de retenção”, “currículo em espiral”). Sem definições, apenas a lista.
E) GATILHO DE MARCA (não publicitário): descreva como a marca aparecerá no terço final como “Estudo de Aplicação Metodológica” (tom jornalístico, técnico, sem adjetivos de venda).
"""

    user_1 = f"""
Palavra-chave: '{palavra_chave}'

Contexto extraído do Google (Serper + Jina):
{contexto_google}

Baseline de IAs (consenso atual):
{baseline_ia}

Marca Alvo:
- Posicionamento: {marca_info['Posicionamento']}
- Territórios Estratégicos: {marca_info['Territorios']}

Instruções:
- Construa o briefing completo seguindo as REGRAS-MESTRAS e ENTREGÁVEIS.
- Se o contexto carecer de dados confiáveis com URL, declare FOCO CONCEITUAL (sem inventar números).
"""

    analise = chamar_llm(system_1, user_1, model="openai/gpt-4o", temperature=0.3)

    st.write("✍️ Fase 2: Redigindo em HTML Avançado (Claude 3.7 Sonnet)...")

    system_2 = """
Você é Especialista em SEO Semântico (GEO) e Redator de Autoridade E‑E‑A‑T.
Produza um ARTIGO FINAL em HTML puro, pt-BR, com ganho de informação real.

MANIFESTO ANTI-ROBÔ — ESTILO:
1) Ritmo, profundidade e elegância. Voz ativa. Evite enchimento.
2) PROIBIDO usar: “No cenário atual”, “Cada vez mais”, “É inegável que”, “É importante ressaltar”, “Neste artigo veremos/iremos”, “Em resumo”, “Por fim”.
3) Não explique o óbvio; entregue leitura avançada com aplicações práticas e comparações.

REGRAS HTML (OBRIGATÓRIAS):
4) Use exclusivamente HTML puro: <h1>, <h2>, <p>, <ul>, <ol>, <li>, <blockquote>, <strong>, <em>, <code>, <pre>, <a>.
   - Não use Markdown nem ```.
   - Não insira <img> (as imagens serão injetadas pelo sistema).
5) Após o parágrafo inicial, **insira exatamente** a linha de marcador:
   <br>Resumo Rápido<br>
   Em seguida, um <ul> com 3 <li> objetivos (insights práticos do artigo).
6) TÍTULOS (H2): use integralmente os H2 sugeridos no briefing (sem “O que é”, “Benefícios”, “Conclusão”).
7) **FAQ avançado**: no terço final, insira **exatamente** a linha:
   <br>Perguntas Frequentes<br>
   Em seguida, crie 3 perguntas e respostas de nível avançado em HTML:
   - Cada pergunta em <p><strong>...</strong></p>
   - Cada resposta em <p>...</p>
8) Links (Evidências): SOMENTE se o briefing trouxer o par (afirmação → URL). Envolva o nome da instituição com <a href="URL_EXATA">Nome da Instituição</a>.
   - Proibido inventar números, anos, ou fontes. Se o briefing disser FOCO CONCEITUAL, **não** insira links nem estatísticas.
9) Cegueira a concorrentes: ignore marcas privadas de terceiros encontradas no contexto.
10) Marca Alvo (terço final): inserir uma seção <h2>Estudo de Aplicação Metodológica</h2> descrevendo a metodologia da marca de forma técnica e jornalística, sem adjetivos promocionais.

QUALIDADE E COBERTURA:
11) Tamanho orientativo: 1.000–1.600 palavras; maximize ganho de informação e exemplos aplicáveis.
12) Integre os termos da DENSIDADE SEMÂNTICA naturalmente no corpo (não liste).
13) REGRA DE OURO (SAÍDA PURA): Entregue EXCLUSIVAMENTE o código HTML. NÃO adicione nenhum comentário, introdução, conclusão, "AI:" ou autoavaliação do seu próprio trabalho no final do texto. O primeiro caractere da sua resposta DEVE ser <h1> e o último DEVE ser o fechamento da última tag HTML.
"""

    user_2 = f"""
Palavra-chave: '{palavra_chave}'

CONTEXTO TEMPORAL: Ano de {ano_atual}. Não projete o futuro sem evidência.
O QUE A CONCORRÊNCIA DIZ HOJE (para fact-checking e contraste):
{contexto_google}
{baseline_ia}

SEU BRIEFING (siga à risca o ângulo e os H2 propostos):
{analise}

MARCA ALVO (Cliente):
- Nome: {marca_alvo} (remova o '@' no texto)
- Posicionamento: {marca_info['Posicionamento']}
- Territórios: {marca_info['Territorios']}
- Tom de Voz: {marca_info['TomDeVoz']}
- Diretrizes OBRIGATÓRIAS: {marca_info.get('RegrasPositivas', '')}
- O que NÃO fazer: {marca_info['RegrasNegativas']}

Escreva o ARTIGO FINAL em HTML conforme as regras, preservando exatamente os marcadores:
<br>Resumo Rápido<br>
<br>Perguntas Frequentes<br>
"""

    artigo_html = chamar_llm(system_2, user_2, model="anthropic/claude-3.7-sonnet", temperature=0.3)
    artigo_html = re.sub(r'^```html\n|```$', '', artigo_html, flags=re.MULTILINE).strip()

    st.write("🛠️ Fase 3: Extraindo JSON e Metadados via Pydantic...")
    schema_gerado = MetadadosArtigo.model_json_schema() if hasattr(MetadadosArtigo, "model_json_schema") else MetadadosArtigo.schema_json()

    # NOTA: Aqui está a correção vital do {{}}
    system_3 = f"""
Você é especialista em SEO técnico e Schema.org.
Retorne EXCLUSIVAMENTE **um JSON** puro, válido e COMPATÍVEL com este schema Pydantic:
{json.dumps(schema_gerado, ensure_ascii=False)}

REGRAS CRÍTICAS:
1) NUNCA inclua markdown, comentários, ```json ou campos extras.
2) 'title': 45–60 caracteres (otimizado para H1/SEO, sem marca).
3) 'meta_description': 130–150 caracteres (promessa clara + gancho, sem clickbait).
4) 'dicas_imagens': exatamente 2 strings em inglês, descritivas e específicas (ex.: "bilingual classroom observation, natural light, candid, corporate", "school finance dashboard, clean ui, overhead"). Apenas substantivos/estilos; sem marcas.
5) 'schema_faq': JSON-LD **FAQPage** com @context "https://schema.org", @type "FAQPage" e mainEntity como lista de objetos Question/acceptedAnswer.
   - As perguntas e respostas DEVEM ser extraídas **textualmente** da seção “Perguntas Frequentes” presente no HTML fornecido (mesma grafia e sentido).
   - Se não houver FAQ no HTML, retorne 'schema_faq': {{}}. 

ANTI-CLOAKING E VALIDAÇÃO:
- Proibido inventar perguntas/respostas que não existam no HTML.
- Proibido inventar dados/anos/links no JSON.
- Saída deve conter apenas as chaves: title, meta_description, dicas_imagens, schema_faq.
"""

    user_3 = f"HTML COMPLETO:\n{artigo_html}"

    dicas_json = chamar_llm(system_3, user_3, model="anthropic/claude-3.7-sonnet", temperature=0.1, response_format={"type": "json_object"})

    try:
        json_limpo = dicas_json.strip().removeprefix('```json').removesuffix('```').strip()
        meta_dicas = json.loads(json_limpo)
        termos_busca = meta_dicas.get('dicas_imagens', [])
        UNSPLASH_KEY = st.secrets.get("UNSPLASH_KEY", "")
        if isinstance(termos_busca, list):
            for i, termo in enumerate(termos_busca[:2]):
                img_html_pronta = ""
                if UNSPLASH_KEY:
                    url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(termo)}&client_id={UNSPLASH_KEY}&per_page=1&orientation=landscape"
                    try:
                        res = requests.get(url, timeout=5)
                        if res.status_code == 200:
                            dados_img = res.json()
                            if "results" in dados_img and len(dados_img["results"]) > 0:
                                img_url = dados_img["results"][0]["urls"]["regular"]
                                alt_text = dados_img["results"][0]["alt_description"] or termo
                                img_html_pronta = f'<img src="{img_url}" alt="{alt_text}" loading="lazy" decoding="async" />'
                    except Exception:
                        pass
                if not img_html_pronta:
                    clean_termo = str(termo).replace("'", "").replace('"', '').strip()
                    p_codificado = urllib.parse.quote(clean_termo)
                    base_poll = "https://image.pollinations.ai/prompt/"
                    img_html_pronta = f'<img src="{base_poll}{p_codificado}" alt="{clean_termo}" loading="lazy" decoding="async" />'
                if img_html_pronta:
                    alvo_replace = '<br>Resumo Rápido<br>' if i == 0 else '<br>Perguntas Frequentes<br>'
                    artigo_html = artigo_html.replace(alvo_replace, f'{img_html_pronta}\n{alvo_replace}', 1)
    except Exception as e:
        print(f"Erro silencioso ao injetar imagem: {e}")

    return artigo_html, dicas_json, contexto_google, baseline_ia


def publicar_wp(titulo, conteudo_html, meta_dict):
    seo_title = meta_dict.get("title", titulo)
    meta_desc = meta_dict.get("meta_description", "")
    schema_faq = meta_dict.get("schema_faq", {})
    if schema_faq:
        script_schema = f'\n\n<script type="application/ld+json">{json.dumps(schema_faq, ensure_ascii=False)}</script>'
        conteudo_html += script_schema
    payload = {
        "title": titulo,
        "content": conteudo_html,
        "status": "draft",
        "meta": {
            "_yoast_wpseo_title": seo_title,
            "_yoast_wpseo_metadesc": meta_desc
        }
    }
    response = requests.post(WP_URL, json=payload, auth=HTTPBasicAuth(WP_USER, WP_PWD))
    return response

# ==========================================
# 5. INTERFACE PRINCIPAL
# ==========================================
tab1, tab2, tab3 = st.tabs(["✍️ Gerador de Artigos", "📚 Brandbook", "🔍 Monitor de GEO"])

with tab2:
    st.markdown("### Edite as regras, marcas e diretrizes:")
    st.session_state['brandbook_df'] = st.data_editor(st.session_state['brandbook_df'], num_rows="dynamic", use_container_width=True)
    st.info("💡 Dica: Adicione regras específicas na coluna 'RegrasPositivas'.")

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        marca_selecionada = st.selectbox("Selecione a Marca", st.session_state['brandbook_df']['Marca'].tolist())
        palavra_chave_input = st.text_area("Palavra-Chave / Briefing", placeholder="Ex: metodologia bilíngue nas escolas")
        gerar_btn = st.button("🚀 Gerar Artigo em HTML", use_container_width=True, type="primary")
        st.markdown("---")
        if not WP_READY:
            st.warning("🔌 Integração WordPress inativa. Faltam as credenciais no menu Secrets.")
        else:
            st.success("🔌 Conectado ao WordPress (Pronto para Yoast).")

    if gerar_btn:
        if not TOKEN:
            st.error("⚠️ Erro: A chave OPENROUTER_KEY não foi encontrada nos Secrets.")
        elif not palavra_chave_input:
            st.warning("⚠️ Por favor, digite uma palavra-chave.")
        else:
            with st.status("🤖 Processando Motor GEO v3...", expanded=True) as status:
                try:
                    artigo_html, dicas_json, google_data, ia_data = executar_geracao_completa(palavra_chave_input, marca_selecionada)
                    st.session_state['art_gerado'] = artigo_html
                    st.session_state['metas_geradas'] = dicas_json
                    st.session_state['google_ctx'] = google_data
                    st.session_state['ia_ctx'] = ia_data
                    st.session_state['marca_atual'] = marca_selecionada
                    st.session_state['keyword_atual'] = palavra_chave_input
                    status.update(label="✅ Artigo gerado com sucesso!", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ Erro durante a geração", state="error")
                    st.error(f"Erro Crítico: {e}")

    if 'art_gerado' in st.session_state:
        with col2:
            st.success("Tudo pronto! Seu código HTML está preparado para o WordPress.")
            try:
                string_json_limpa = st.session_state['metas_geradas'].strip().removeprefix('```json').removesuffix('```').strip()
                meta_validada = MetadadosArtigo.model_validate_json(string_json_limpa)
                meta = meta_validada.model_dump()
                st.subheader(meta.get("title", "Artigo Gerado"))
            except ValidationError as ve:
                meta = {"title": "Artigo Gerado via Motor GEO (Schema Fallback)", "meta_description": "", "dicas_imagens": [], "schema_faq": {}}
                st.error(f"Aviso: O JSON gerado pela IA feriu a estrutura do Pydantic. Detalhe: {ve}")
            except Exception as e:
                meta = {"title": "Artigo Gerado via Motor GEO (JSON Fallback)", "meta_description": "", "dicas_imagens": [], "schema_faq": {}}
                st.error(f"Aviso: O JSON não pôde ser lido de forma alguma. Detalhe: {e}")

            with st.expander("🕵️‍♂️ Auditoria: O que ranqueia hoje (Google & IA)?", expanded=False):
                st.markdown("**Google (Serper + Jina Reader):**")
                st.info(st.session_state['google_ctx'])
                st.markdown("**IA (Perplexity):**")
                st.info(st.session_state['ia_ctx'])

            with st.expander("👁️ Pré-visualização do HTML", expanded=False):
                st.markdown(st.session_state['art_gerado'], unsafe_allow_html=True)
                st.markdown("### 📋 Código HTML:")
                st.code(st.session_state['art_gerado'], language="html")

            with st.expander("🛠️ Metadados SEO & Schema", expanded=True):
                st.json(meta)
                if WP_READY:
                    if st.button("📤 Enviar Rascunho para WordPress (Yoast)"):
                        with st.spinner("Enviando via API..."):
                            res = publicar_wp(meta.get("title", st.session_state['keyword_atual']), st.session_state['art_gerado'], meta)
                            if res.status_code == 201:
                                st.success(f"✅ Rascunho criado! Link: {res.json().get('link')}")
                            else:
                                st.error(f"❌ Falha ao enviar: {res.text}")

# ==========================================
# 6. MONITOR DE GEO (GAMIFICAÇÃO E AUDITORIA ROBUSTA)
# ==========================================
# ==========================================
# 6. MONITOR DE GEO (GAMIFICAÇÃO E AUDITORIA ROBUSTA)
# ==========================================
with tab3:
    st.subheader("🔍 Monitor de Autoridade GEO")
    st.caption("Esta aba utiliza o **GPT-4o** para simular um algoritmo de busca, auditar seu texto e gerar insights de Prompt Engineering para os Devs.")
    conteudo_para_auditoria = st.session_state.get('art_gerado', '')
    keyword_para_auditoria = st.session_state.get('keyword_atual', '')
    marca_para_auditoria = st.session_state.get('marca_atual', 'a marca').replace('@', '')

    txt_auditoria = st.text_area("HTML do Artigo para Auditoria", height=300, value=conteudo_para_auditoria)
    kw_auditoria = st.text_input("Palavra-Chave Alvo", value=keyword_para_auditoria)

    if st.button("🔎 Analisar com GPT-4o e Gerar Insights"):
        if not txt_auditoria:
            st.warning("⚠️ Por favor, gere um artigo na aba 1 primeiro ou cole o HTML aqui.")
        else:
            with st.spinner("Auditando conteúdo, calculando GEO Score e criando Guardrails..."):
                # NOVO PROMPT: AGORA COM ENGENHARIA DE PROMPT REVERSA
                sys_audit = """
Você é um Auditor Sênior de SEO (E-E-A-T) e também um Especialista em Engenharia de Prompt (AI Dev).
Sua missão é avaliar o HTML fornecido e, além de criticar o texto atual, sugerir melhorias de GUARDRAILS para o sistema gerador.

REGRAS DE AUDITORIA (GUARDRAILS PARA O TEXTO):
1) JUSTIÇA CONTEXTUAL: Só exija links para afirmações estatísticas concretas. Textos puramente metodológicos não são penalizados por falta de links.
2) DETECÇÃO DE ALUCINAÇÃO E VÍCIOS: Penalize fortemente clichês textuais de IA (ex: "No cenário atual", "Em resumo", "Vale ressaltar").
3) INTEGRAÇÃO DA MARCA: A marca deve ser citada de forma técnica. Penalize panfletagem promocional.
4) HIGIENE HTML: Verifique a presença literal dos marcadores `<br>Resumo Rápido<br>` e `<br>Perguntas Frequentes<br>`.

REGRAS DE FEEDBACK PARA DESENVOLVEDORES (META-PROMPTING):
- Atue como um Engenheiro de Prompt. Ao notar uma falha recorrente no texto atual, crie 1 ou 2 sugestões de NOVAS REGRAS DE PROMPT.
- Estas regras DEVEM SER AGNÓSTICAS: não mencione a palavra-chave atual nem a marca atual. A regra deve servir para o "System Prompt" geral do agente (ex: "Adicione uma instrução proibindo o LLM de usar transições com gerúndio no início dos parágrafos").

RETORNO ESTRITAMENTE EM JSON PURO:
{
  "score": 85,
  "veredito": "Resumo de 2 linhas sobre o texto.",
  "critica": [
    "O parágrafo X usa o clichê 'no cenário atual'."
  ],
  "melhoria": [
    "Substituir clichês por afirmações diretas na voz ativa."
  ],
  "sugestoes_dev": [
    "ADICIONAR AO PROMPT DO REDATOR: 'É terminantemente proibido o uso da expressão [inserir clichê encontrado].'",
    "NOVO GUARDRAIL: 'Sempre que apresentar uma lista <ul>, certifique-se de não usar ponto final nos <li> caso sejam frases curtas.'"
  ]
}
"""

                usr_audit = f"""
Palavra-chave: {kw_auditoria}
Texto HTML: {txt_auditoria}
Marca Alvo: {marca_para_auditoria}

Analise friamente e retorne APENAS o JSON válido com as sugestões para os DEVs.
"""
                try:
                    relatorio_bruto = chamar_llm(
                        sys_audit,
                        usr_audit,
                        model="openai/gpt-4o",
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    relatorio_limpo = relatorio_bruto.strip().removeprefix('```json').removesuffix('```').strip()
                    dados_audit = json.loads(relatorio_limpo)
                    score = int(dados_audit.get("score", 0))

                    st.markdown("---")
                    st.markdown("### 📊 Relatório de Performance GEO")
                    kpi1, kpi2 = st.columns([1, 3])
                    with kpi1:
                        cor_delta = "normal" if score >= 80 else "inverse"
                        st.metric("🎯 GEO Score Estimado", f"{score}/100", delta=f"{score - 100} do ideal", delta_color=cor_delta)
                    with kpi2:
                        st.markdown("**Progresso E-E-A-T:**")
                        st.progress(score / 100)

                    if score >= 90:
                        st.success(f"**Veredito de Autoridade:** {dados_audit.get('veredito')}")
                    elif score >= 75:
                        st.info(f"**Veredito de Autoridade:** {dados_audit.get('veredito')}")
                    else:
                        st.warning(f"**Veredito de Autoridade:** {dados_audit.get('veredito')}")

                    st.markdown("#### Análise do Conteúdo Gerado")
                    col_critica, col_melhoria = st.columns(2)
                    
                    with col_critica:
                        with st.expander("🚨 Críticas Técnicas ao Texto", expanded=True):
                            criticas = dados_audit.get('critica', [])
                            if isinstance(criticas, list) and criticas:
                                for c in criticas:
                                    st.markdown(f"- {c}")
                            else:
                                st.markdown("Nenhuma crítica identificada.")
                                
                    with col_melhoria:
                        with st.expander("🛠️ Correções para este Artigo", expanded=True):
                            melhorias = dados_audit.get('melhoria', [])
                            if isinstance(melhorias, list) and melhorias:
                                for m in melhorias:
                                    st.markdown(f"- {m}")
                            else:
                                st.markdown("Sem sugestões de melhoria.")

                    # NOVA SEÇÃO: FEEDBACK PARA OS DEVS
                    st.markdown("---")
                    st.markdown("### ⚙️ Engenharia de Prompt (Melhoria Contínua)")
                    with st.expander("💡 Sugestões de Novos Guardrails para o Sistema", expanded=True):
                        sugestoes_dev = dados_audit.get('sugestoes_dev', [])
                        if isinstance(sugestoes_dev, list) and sugestoes_dev:
                            for s in sugestoes_dev:
                                st.info(f"🤖 **Insight para o Prompt:** {s}")
                            st.caption("Dica: Copie os insights acima que fizerem sentido e cole no `system_2` (prompt do Claude) no código principal.")
                        else:
                            st.success("O prompt atual parece robusto. Nenhuma sugestão estrutural gerada neste ciclo.")

                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar a auditoria visual. Detalhe técnico: {e}")
                    with st.expander("Ver resposta bruta da IA"):
                        st.write(relatorio_bruto if 'relatorio_bruto' in locals() else "Nenhuma resposta obtida.")
