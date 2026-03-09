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
    st.markdown("Bem-vindo à v3.0. Este sistema utiliza uma arquitetura **multi-agentes** para criar conteúdo com autoridade máxima (E-E-A-T).")
    
    with st.expander("✍️ 1. Gerador de Artigos", expanded=False):
        st.markdown("""
        **O Fluxo da Inteligência Artificial:**
        1. **Busca (Serper + Jina Reader):** Lê o conteúdo real do Top 3 do Google.
        2. **Auditoria (GPT-4o-mini):** Analisa o que as IAs já respondem hoje.
        3. **Estratégia (GPT-4o):** Identifica lacunas e cria o briefing de superação.
        4. **Redação (Claude 3.7 Sonnet):** Escreve o código HTML blindado.
        5. **Mídia (Unsplash API):** Injeta fotos corporativas em alta resolução.
        
        ⏱️ *Tempo médio: 45 a 60 segundos.*

        **💡 Como escrever a Palavra-Chave:**
        Adicione direcionamento (prompt) junto à palavra para resultados cirúrgicos:
        - ❌ **Fraco:** `inadimplência escolar`
        - ✅ **Forte:** `como reduzir a inadimplência escolar (focar em soluções amigáveis para renegociação com os pais)`
        
        - ❌ **Fraco:** `ensino bilíngue`
        - ✅ **Forte:** `impactos cognitivos do bilinguismo (usar referências de neurociência e dados de retenção)`
        """)
        
    with st.expander("📚 2. Brandbook", expanded=False):
        st.markdown("""
        O **Claude 3.7** consulta esta matriz antes de escrever qualquer vírgula.
        - **Regras Negativas:** Proíba vícios (ex: *"Nunca use a palavra 'aluno', use 'estudante'"* ou *"Nunca critique o sistema público"*).
        - **Regras Positivas:** Force formatos (ex: *"Sempre inicie o texto com uma estatística chocante"*).
        """)
        
    with st.expander("🔍 3. Monitor de GEO", expanded=False):
        st.markdown("""
        Um simulador do algoritmo E-E-A-T do Google movido pelo **GPT-4o**.
        - **O que ele avalia:** Densidade de Entidades, Escaneabilidade e Veracidade de Dados (sem alucinações).
        - **Dica de Ouro:** Além de testar os textos novos, cole o HTML de artigos antigos do seu blog aqui para descobrir exatamente o que falta para eles ranquearem melhor.
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
        "PublicoAlvo": "Gestores, diretores e coordenadores de escolas (B2B)  pais e famílias (Foco B2C)", 
        "RegrasNegativas": "Não usar termos genéricos sem contexto, não soar arrogante ou sabe tudo, não inferir que quem aprende inglês é superior ou melhor, não citar palavras em inglês sem tradução entre parênteses depois. Não focar o discurso somente nos pais (lembrar sempre da figura da escola). NUNCA usar a construção 'neste artigo iremos' ou similares.", 
        "RegrasPositivas": "Focar em estrutura informativa. Sempre trazer dados para embasar afirmações vindos de fontes seguras e confiáveis, sempre citar e linkar a fonte dos dados, preferir fontes de pesquisas, governos e instituições de renome. Sempre começar o primeiro parágrafo com um gancho que instigue a leitura, de preferência acompanhado de dado. Podemos usar pesquisas nacionais ou internacionais. Sempre usar construção gramatical focada em clareza: iniciar parágrafos com frases de afirmação, não com conectivos. Sempre conectar com a importância de aprender inglês indo além da gramática: focar na importância de aprender com contexto."
    },
    {
        "Marca": "@saseducacao", 
        "Posicionamento": "Marca visionária, líder em aprovação. Entrega de valor em tecnologia e serviço.", 
        "Territorios": "Vestibulares, Tecnologia, Inovação, Pesquisas", 
        "TomDeVoz": "Acadêmico, inovador, especialista e inspirador.", 
        "PublicoAlvo": "Estudantes, vestibulandos e pais. (Foco B2C)", 
        "RegrasNegativas": "Não usar tom professoral antiquado, não prometer aprovação sem esforço.", 
        "RegrasPositivas": ""
    },
    {
        "Marca": "@plataformacoc", 
        "Posicionamento": "Marca aprovadora que evolui a escola pedagogicamente.", 
        "Territorios": "Vestibulares, Esportes, Gestão escolar", 
        "TomDeVoz": "Consultivo, parceiro, dinâmico.", 
        "PublicoAlvo": "Mantenedores e coordenadores pedagógicos. (B2B)", 
        "RegrasNegativas": "Não focar discurso apenas no aluno, não usar jargões sem explicação.", 
        "RegrasPositivas": ""
    },
    {
        "Marca": "@isaaceducacao", 
        "Posicionamento": "Maior solução financeira e de gestão para a educação.", 
        "Territorios": "Gestão financeira, Inovação", 
        "TomDeVoz": "Corporativo, direto, analítico.", 
        "PublicoAlvo": "Diretores financeiros e donos de escolas. (B2B)", 
        "RegrasNegativas": "Não parecer banco engessado, não usar linguagem infantilizada.", 
        "RegrasPositivas": ""
    },
    {
        "Marca": "@geekieeducacao", 
        "Posicionamento": "Metodologia inovadora (aluno no centro), fácil de implementar.", 
        "Territorios": "Inovação, IA/Personalização", 
        "TomDeVoz": "Inovador, moderno, ágil.", 
        "PublicoAlvo": "Diretores de inovação e escolas modernas. (B2B)", 
        "RegrasNegativas": "Não parecer sistema engessado, não usar linguagem punitiva.", 
        "RegrasPositivas": ""
    },
    {
        "Marca": "@sistemapositivodeensino", 
        "Posicionamento": "Formação integral, humana e próxima. A maior rede do Brasil.", 
        "Territorios": "Formação integral, Inclusão, Tradição", 
        "TomDeVoz": "Acolhedor, tradicional, humano.", 
        "PublicoAlvo": "Famílias e diretores de escolas tradicionais.", 
        "RegrasNegativas": "Não parecer frio, não usar jargões técnicos sem contexto acolhedor.", 
        "RegrasPositivas": ""
    },
    {
        "Marca": "@saedigital", 
        "Posicionamento": "Melhor integração físico/digital, hiperatualizada.", 
        "Territorios": "Tecnologia, Inovação Digital", 
        "TomDeVoz": "Prático, tecnológico, dinâmico.", 
        "PublicoAlvo": "Gestores buscando modernização com custo-benefício.", 
        "RegrasNegativas": "Não parecer inacessível, não diminuir a importância do material físico.", 
        "RegrasPositivas": ""
    },
    {
        "Marca": "@solucaoconquista", 
        "Posicionamento": "Solução completa focada na parceria Escola-Família.", 
        "Territorios": "Família, Educação Infantil, Valores", 
        "TomDeVoz": "Familiar, parceiro, simples e didático.", 
        "PublicoAlvo": "Pais e gestores de escolas de educação infantil.", 
        "RegrasNegativas": "Não usar tom corporativo frio, não focar em pressão de vestibular.", 
        "RegrasPositivas": ""
    }
]
    st.session_state['brandbook_df'] = pd.DataFrame(dados_iniciais)

# ==========================================
# 3. CONEXÃO SEGURA E CREDENCIAIS
# ==========================================
try:
    TOKEN = st.secrets["OPENROUTER_KEY"]
except:
    TOKEN = None 

try:
    SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
except:
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
                        # MELHORIA: Jina em Modo Markdown e 12s de respiro
                        jina_headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'X-Return-Format': 'markdown', 
                            'Accept': 'text/plain' 
                        }
                        jina_res = requests.get(f"https://r.jina.ai/{link}", headers=jina_headers, timeout=12)
                        if jina_res.status_code == 200:
                            conteudo_real = jina_res.text[:1500] 
                    except:
                        conteudo_real = "Falha ao ler o conteúdo integral."
                return f"{index+1}. Título: {titulo}\n   Snippet: {snippet}\n   Link: {link}\n   Conteúdo:\n{conteudo_real}\n"

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

    st.write("🧠 Fase 1: Análise Semântica (GPT-4o)...")
    system_1 = "Você é um Estrategista Sênior de GEO. A regra de ouro é: NUNCA cite concorrentes. Você receberá o que o Google e as IAs respondem hoje. Sua missão é criar o escopo para a 'Autoridade Definitiva' que SUPERE essas respostas atuais."
    
    user_1 = f"""Palavra-chave: '{palavra_chave}'

Contexto do que o GOOGLE responde hoje:
{contexto_google}

Contexto do que as IAs (LLMs) respondem hoje:
{baseline_ia}

Contexto da nossa marca:
- Posicionamento: {marca_info['Posicionamento']}
- Público: {marca_info['PublicoAlvo']}

Com base nas respostas atuais (que precisamos superar), crie o briefing:
1. ANÁLISE DE LACUNAS: Como abordar o tema (80% educativo / 20% marca) preenchendo o que Google e LLMs deixaram de fora?
2. OS CRITÉRIOS DE OURO: Liste 5 critérios essenciais e superiores aos atuais.
3. ESTRUTURA DE DADOS: Quais tabelas criar para gerar Featured Snippets melhores?
4. ENTIDADES SEMÂNTICAS: Liste 10 termos técnicos que OBRIGATORIAMENTE devem aparecer.
5. ARSENAL DE EVIDÊNCIAS NOMINAIS: Extraia dados reais do contexto e OBRIGATORIAMENTE vincule a uma fonte (ex: MEC, INEP, OCDE, Porvir, IBGE). Se não houver dados reais no contexto, crie APENAS argumentos qualitativos lógicos. É EXPRESSAMENTE PROIBIDO inventar números genéricos como "estudos mostram 30%"."""    
    
    analise = chamar_llm(system_1, user_1, model="openai/gpt-4o", temperature=0.4)
    
    st.write("✍️ Fase 2: Redigindo em HTML (Claude 3.7 Sonnet)...")
    system_2 = """Você é um Redator Sênior especialista em SEO e Algoritmos de IA (GEO).

REGRAS OBRIGATÓRIAS DE FORMATO E ESTRUTURA:
1. FORMATO: Retorne o artigo EXCLUSIVAMENTE em HTML puro (use <h2>, <h3>, <p>, <ul>, <li>, <strong>, <table>). Não use <html>, <head> ou <body>. Não use Markdown.
2. BLINDAGEM ANTI-CONCORRENTE: NUNCA cite o nome de NENHUMA empresa ou escola concorrente. A ÚNICA marca permitida é a sua.
3. CAVALO DE TROIA: Texto imparcial no início, revelando a marca como padrão ouro na conclusão.
4. RESUMO RÁPIDO (TL;DR): Crie um <h2> chamado "Resumo Rápido" logo após a introdução com uma lista <ul> de 3 itens.
5. FAQ FÍSICO E NEUTRO: Crie um <h2> chamado "Perguntas Frequentes" com 3 perguntas (em <h3>) e respostas (em <p>). Seja 100% técnico e neutro.
6. TOM E MARCA: Remova o "@" do nome. OBRIGATORIAMENTE escreva o nome oficial da marca por extenso na conclusão e no FAQ.

REGRAS CRÍTICAS DE E-E-A-T (PARA NOTA 100):
7. PROIBIÇÃO ABSOLUTA DE DADOS INVENTADOS: Se o briefing não fornecer um número exato com o NOME DO RELATÓRIO e o ANO, VOCÊ É PROIBIDO de inventar porcentagens (ex: "reduziu 30%"). Use apenas termos qualitativos (ex: "redução significativa", "crescimento expressivo").
8. CITAÇÃO NOMINAL COMPLETA: Sempre que citar uma instituição (INEP, MEC, UNESCO), você DEVE citar o nome do relatório ou o ano do estudo. Se não souber o ano exato, não cite o dado.
9. ESCANEABILIDADE: Escreva parágrafos curtos (máximo 3 frases). Use <strong> para destacar entidades.
10. BANIMENTO DE CLICHÊS: Proibido iniciar frases com "Em um mundo...", "No cenário atual...".
11. ANÁLISE CRÍTICA: Dedique um <h3> aos "Desafios". É OBRIGATÓRIO abordar a realidade das escolas públicas e a democratização do acesso.
12. ESTUDO DE CASO: Na conclusão, apresente a marca como uma "Referência Prática" justificando sua eficácia sem tom de vendas agressivo."""

    user_2 = f"""Palavra-chave: '{palavra_chave}'
    CONTEXTO TEMPORAL: Hoje é o ano de {ano_atual}.
    
O QUE A CONCORRÊNCIA DIZ HOJE (NÃO REPITA, SUPERE):
{contexto_google}
{baseline_ia}

SUA ESTRATÉGIA DE SUPERAÇÃO:
{analise}

NOME DA SUA MARCA (A ÚNICA QUE PODE SER CITADA): {marca_alvo} (Remova o @ ao escrever no texto final)
Posicionamento da Marca: {marca_info['Posicionamento']}
Tom: {marca_info['TomDeVoz']}
Regras Positivas: {marca_info.get('RegrasPositivas', '')}
Regras Negativas: {marca_info['RegrasNegativas']}

Retorne apenas o código HTML do artigo."""

    artigo_html = chamar_llm(system_2, user_2, model="anthropic/claude-3.7-sonnet", temperature=0.3)
    artigo_html = re.sub(r'^```html\n|```$', '', artigo_html, flags=re.MULTILINE).strip()
    
    st.write("🛠️ Fase 3: Extraindo JSON e Metadados via Pydantic...")
    schema_gerado = MetadadosArtigo.model_json_schema() if hasattr(MetadadosArtigo, "model_json_schema") else MetadadosArtigo.schema_json()
    
    system_3 = f"""Você é especialista em SEO técnico e Schema.org. 
Você DEVE retornar APENAS UM JSON puro, válido e compatível com este schema:
{json.dumps(schema_gerado, ensure_ascii=False)}

REGRA CRÍTICA ANTI-CLOAKING: Para o schema_faq, você DEVE extrair EXATAMENTE as perguntas (<h3>) e respostas (<p>) que estão fisicamente escritas na seção 'Perguntas Frequentes' do HTML. NUNCA invente perguntas que não existam no texto.
NÃO envolva a resposta em markdown (como ```json)."""
    
    user_3 = f"HTML COMPLETO:\n{artigo_html}"
    dicas_json = chamar_llm(system_3, user_3, model="anthropic/claude-3.7-sonnet", temperature=0.1, response_format={"type": "json_object"})

    # NOVO MOTOR DE IMAGENS UNSPLASH
    try:
        # Lê o JSON que acabou de ser gerado
        json_limpo = dicas_json.strip().removeprefix('```json').removesuffix('```').strip()
        meta_dicas = json.loads(json_limpo)
        termos_busca = meta_dicas.get('dicas_imagens', [])
        
        UNSPLASH_KEY = st.secrets.get("UNSPLASH_KEY", "")
        
        if UNSPLASH_KEY and isinstance(termos_busca, list):
            for i, termo in enumerate(termos_busca[:2]): 
                url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(termo)}&client_id={UNSPLASH_KEY}&per_page=1&orientation=landscape"
                res = requests.get(url, timeout=5)
                
                if res.status_code == 200:
                    dados_img = res.json()
                    if "results" in dados_img and len(dados_img["results"]) > 0:
                        img_url = dados_img["results"][0]["urls"]["regular"]
                        alt_text = dados_img["results"][0]["alt_description"] or termo
                        
                        # Cria a tag HTML da foto
                        tag_img = f'<figure style="margin: 25px 0;"><img src="{img_url}" alt="{alt_text}" style="width:100%; border-radius:8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></figure>'
                        
                        # Encontra onde colar no HTML gerado
                        alvo_replace = '<h2>Resumo Rápido</h2>' if i == 0 else '<h2>Perguntas Frequentes</h2>'
                        artigo_html = artigo_html.replace(alvo_replace, f'{tag_img}\n{alvo_replace}', 1)
    except Exception as e:
        print(f"Erro silencioso ao injetar imagem: {e}")
    
    return artigo_html, dicas_json, contexto_google, baseline_ia

def publicar_wp(titulo, conteudo_html, meta_dict):
    seo_title = meta_dict.get("title", titulo)
    meta_desc = meta_dict.get("meta_description", "")
    schema_faq = meta_dict.get("schema_faq", {})
    
    if schema_faq:
        script_schema = f'\n\n<script type="application/ld+json">\n{json.dumps(schema_faq, ensure_ascii=False, indent=2)}\n</script>'
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
                    st.session_state['imagens_injetadas'] = False 
                    
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
                
                # MELHORIA: Integração Unsplash
                UNSPLASH_KEY = st.secrets.get("UNSPLASH_KEY", "")

                if not st.session_state.get('imagens_injetadas') and UNSPLASH_KEY:
                    html_atual = st.session_state['art_gerado']
                    termos_busca = meta.get('dicas_imagens', [])
                    
                    for i, termo in enumerate(termos_busca[:2]): 
                        url = f"[https://api.unsplash.com/search/photos?query=](https://api.unsplash.com/search/photos?query=){urllib.parse.quote(termo)}&client_id={UNSPLASH_KEY}&per_page=1&orientation=landscape"
                        try:
                            res = requests.get(url, timeout=5).json()
                            if "results" in res and len(res["results"]) > 0:
                                img_url = res["results"][0]["urls"]["regular"]
                                alt_text = res["results"][0]["alt_description"] or termo
                                
                                tag_img = f'<figure style="margin: 25px 0;"><img src="{img_url}" alt="{alt_text}" style="width:100%; border-radius:8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></figure>'
                                
                                alvo_replace = '<h2>Resumo Rápido</h2>' if i == 0 else '<h2>Perguntas Frequentes</h2>'
                                html_atual = html_atual.replace(alvo_replace, f'{tag_img}\n{alvo_replace}', 1)
                        except Exception as e:
                            st.toast(f"Falha ao buscar imagem no Unsplash para '{termo}': {e}")

                    st.session_state['art_gerado'] = html_atual
                    st.session_state['imagens_injetadas'] = True

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
# 6. MONITOR DE GEO (GAMIFICAÇÃO)
# ==========================================
with tab3:
    st.subheader("🔍 Monitor de Autoridade GEO")
    st.caption("Esta aba utiliza o **GPT-4o** para simular um algoritmo de busca e auditar seu texto.")
    
    conteudo_para_auditoria = st.session_state.get('art_gerado', '')
    keyword_para_auditoria = st.session_state.get('keyword_atual', '')
    marca_para_auditoria = st.session_state.get('marca_atual', 'a marca').replace('@', '')

    txt_auditoria = st.text_area("HTML do Artigo para Auditoria", height=300, value=conteudo_para_auditoria)
    kw_auditoria = st.text_input("Palavra-Chave Alvo", value=keyword_para_auditoria)
    
    if st.button("🔎 Analisar com GPT-4o"):
        if not txt_auditoria:
            st.warning("⚠️ Por favor, gere um artigo na aba 1 primeiro ou cole o HTML aqui.")
        else:
            with st.spinner("Auditando conteúdo e calculando GEO Score..."):
                sys_audit = """Você é um algoritmo rigoroso de busca e auditoria E-E-A-T.
                
                REGRAS DE AUDITORIA:
                1. A REGRA DE NEGÓCIO DESTA EMPRESA PROÍBE CITAR CONCORRENTES. É estritamente proibido penalizar o texto por falta de comparação com outras marcas ou sistemas.
                2. Verifique se o texto evita alucinações (ex: "estudos mostram 30%" sem citar fonte).
                3. Avalie se a marca é apresentada de forma elegante e técnica (como um estudo de caso/solução estruturada) e não como um panfleto publicitário barato.
                
                VOCÊ DEVE RETORNAR EXCLUSIVAMENTE UM OBJETO JSON COM A SEGUINTE ESTRUTURA E CHAVES EXATAS:
                {
                  "score": "Um número inteiro de 0 a 100",
                  "veredito": "Um parágrafo de resumo se a marca ganhou autoridade ou parece panfletagem",
                  "critica": "Pontos fracos técnicos (em bullet points)",
                  "melhoria": "O que adicionar para bater a nota 100 (em bullet points)"
                }"""
                
                usr_audit = f"""Palavra-chave: {kw_auditoria}
                Texto HTML: {txt_auditoria}
                Marca Alvo: {marca_para_auditoria}
                
                Audite e retorne APENAS o JSON."""
                
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

                    st.markdown("#### Análise Profunda")
                    col_critica, col_melhoria = st.columns(2)
                    
                    with col_critica:
                        with st.expander("🚨 Críticas Técnicas", expanded=True):
                            st.markdown(dados_audit.get('critica'))
                            
                    with col_melhoria:
                        with st.expander("🛠️ Plano de Melhoria", expanded=True):
                            st.markdown(dados_audit.get('melhoria'))
                            
                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar a auditoria visual. Detalhe técnico: {e}")
                    with st.expander("Ver resposta bruta da IA"):
                        st.write(relatorio_bruto if 'relatorio_bruto' in locals() else "Nenhuma resposta obtida.")
