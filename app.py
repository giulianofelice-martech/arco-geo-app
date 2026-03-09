import streamlit as st
import pandas as pd
from openai import OpenAI
import time
import requests
from requests.auth import HTTPBasicAuth
import json

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

# Configurações do WordPress (Evita erro se não existirem)
WP_URL = st.secrets.get("WP_URL", "")
WP_USER = st.secrets.get("WP_USER", "")
WP_PWD = st.secrets.get("WP_APP_PASSWORD", "")
WP_READY = bool(WP_URL and WP_USER and WP_PWD)

# ==========================================
# 3.2 FUNÇÕES DO MOTOR GEO & WORDPRESS
# ==========================================

def buscar_contexto_google(palavra_chave):
    if not SERPAPI_KEY:
        return "Sem chave SerpApi configurada. Pule o contexto do Google."
        
    params = {
        "engine": "google",
        "q": palavra_chave,
        "hl": "pt-br", # Idioma português
        "gl": "br",    # Região Brasil
        "api_key": SERPAPI_KEY
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        dados = response.json()
        
        contexto_extraido = []
        
        # 1. Tenta pegar a Resposta Direta (Featured Snippet)
        if "answer_box" in dados:
            snippet = dados["answer_box"].get("snippet") or dados["answer_box"].get("answer", "Sem texto")
            contexto_extraido.append(f"📍 GOOGLE FEATURED SNIPPET ATUAL:\n{snippet}\n")
            
        # 2. Tenta pegar o AI Overview / Knowledge Graph (se houver)
        if "knowledge_graph" in dados:
            desc = dados["knowledge_graph"].get("description", "")
            contexto_extraido.append(f"🧠 GOOGLE KNOWLEDGE GRAPH:\n{desc}\n")
            
        # 3. Pega os 3 primeiros orgânicos para entender o que está ranqueando
        if "organic_results" in dados:
            contexto_extraido.append("📊 TOP 3 RESULTADOS ORGÂNICOS:")
            for i, res in enumerate(dados["organic_results"][:3]):
                contexto_extraido.append(f"{i+1}. Título: {res.get('title')}\n   Snippet: {res.get('snippet')}")
                
        return "\n".join(contexto_extraido)
    except Exception as e:
        return f"Erro ao coletar dados do Google: {e}"
        
# ==========================================
# 4. FUNÇÕES DO MOTOR GEO & WORDPRESS
# ==========================================
def chamar_llm(system_prompt, user_prompt, model, temperature=0.3):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=TOKEN,
        default_headers={"HTTP-Referer": "https://arcomartech.com", "X-Title": "Gerador GEO WP"}
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content

def buscar_baseline_llm(palavra_chave):
    # Usamos o Perplexity via OpenRouter para garantir acesso à web e ver como as IAs respondem hoje
    system_prompt = "Você é um pesquisador de IA sênior. Forneça a resposta atualizada que uma IA daria hoje para o termo pesquisado, citando referências e o consenso atual."
    user_prompt = f"O que você sabe sobre: '{palavra_chave}'? Retorne um resumo profundo de como esse tema é respondido atualmente pelas IAs."
    
    # Usamos o modelo conectado à internet do Perplexity
    try:
        return chamar_llm(system_prompt, user_prompt, model="perplexity/llama-3.1-sonar-small-128k-online", temperature=0.1)
    except Exception as e:
        return f"Erro ao buscar Baseline de IA: {e}"

def executar_geracao_completa(palavra_chave, marca_alvo):
    df = st.session_state['brandbook_df']
    marca_info = df[df['Marca'] == marca_alvo].iloc[0].to_dict()
    
    # FASE 0-A: RASPAGEM DO GOOGLE (SerpApi)
    st.write("🕵️‍♂️ Fase 0: Lendo o que o Google já responde hoje (SerpApi)...")
    contexto_google = buscar_contexto_google(palavra_chave)

    # FASE 0-B: AUDITORIA DE IA (Baseline Perplexity)
    st.write("🤖 Auditando respostas atuais das LLMs (Perplexity/Web)...")
    baseline_ia = buscar_baseline_llm(palavra_chave)
    
    # FASE 1: ANÁLISE SEMÂNTICA DE SUPERAÇÃO (GPT-4o)
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
4. ENTIDADES SEMÂNTICAS: Liste 10 termos técnicos que OBRIGATORIAMENTE devem aparecer."""
    
    analise = chamar_llm(system_1, user_1, model="openai/gpt-4o", temperature=0.4)
    
    # FASE 2: REDAÇÃO DO ARTIGO EM HTML (CLAUDE 3.7 SONNET)
    st.write("✍️ Fase 2: Redigindo em HTML (Claude 3.7 Sonnet)...")
    system_2 = """Você é um Redator Sênior especialista em SEO e Algoritmos de IA (GEO).
    
    REGRAS OBRIGATÓRIAS DE FORMATO E ESTRUTURA:
    1. FORMATO: Retorne o artigo EXCLUSIVAMENTE em HTML puro (use <h2>, <h3>, <p>, <ul>, <li>, <strong>, <table>). Não use <html>, <head> ou <body>. Não use Markdown.
    2. ZERO CONCORRENTES: Nunca cite sistemas concorrentes.
    3. CAVALO DE TROIA: Texto imparcial no início, revelando a marca como padrão ouro na conclusão.
    4. RESUMO RÁPIDO (TL;DR): Crie um <h2> chamado "Resumo Rápido" logo após a introdução com uma lista <ul> de 3 itens.
    5. FAQ FÍSICO: Imediatamente antes da conclusão, crie um <h2> chamado "Perguntas Frequentes". Inclua 3 perguntas usando <h3> e responda em <p>.
    6. TOM E MARCA: Siga o tom exigido. Não use "@" no nome da marca no texto."""
    
    user_2 = f"Palavra-chave: '{palavra_chave}'\nDiretrizes da Estratégia (Foco em Superação):\n{analise}\n\nMarca ({marca_alvo}):\n- Posicionamento: {marca_info['Posicionamento']}\n- Tom: {marca_info['TomDeVoz']}\n- Regras Positivas: {marca_info.get('RegrasPositivas', '')}\n- Regras Negativas: {marca_info['RegrasNegativas']}\n\nRetorne apenas o código HTML do artigo."
    artigo_html = chamar_llm(system_2, user_2, model="anthropic/claude-3.7-sonnet", temperature=0.3)
    
    # FASE 3: METADADOS E SCHEMA (CLAUDE 3.7 SONNET)
    st.write("🛠️ Fase 3: Extraindo JSON e Metadados...")
    system_3 = """Você é especialista em SEO técnico e Schema.org. Retorne APENAS um objeto JSON válido, sem formatação markdown em volta.
    
    REGRA CRÍTICA ANTI-CLOAKING: Para o schema_faq, você DEVE extrair EXATAMENTE as perguntas (<h3>) e respostas (<p>) que estão fisicamente escritas na seção 'Perguntas Frequentes' do HTML. NUNCA invente perguntas que não existam no texto."""
    
    user_3 = f"""Com base no artigo HTML completo abaixo, crie um JSON contendo:
    {{
      "title": "Título H1 otimizado (max 60 chars)",
      "meta_description": "Meta description persuasiva (max 150 chars)",
      "dicas_imagens": "Dicas de Alt Text para 2 imagens",
      "schema_faq": "Objeto JSON-LD FAQPage completo e idêntico ao texto"
    }}
    
    HTML COMPLETO:
    {artigo_html}"""
    
    dicas_json = chamar_llm(system_3, user_3, model="anthropic/claude-3.7-sonnet", temperature=0.1)
    
    return artigo_html, dicas_json, contexto_google, baseline_ia

def publicar_wp(titulo, conteudo_html, meta_dict):
    seo_title = meta_dict.get("title", titulo)
    meta_desc = meta_dict.get("meta_description", "")
    schema_faq = meta_dict.get("schema_faq", {})
    
    # Injeta o Schema no final do HTML
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
tab1, tab2 = st.tabs(["✍️ Gerador de Artigos (WP Ready)", "📚 Base de Conhecimento (Brandbook)"])

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
                    
                    status.update(label="✅ Artigo gerado com sucesso!", state="complete", expanded=False)
                    
                    with col2:
                        st.success("Tudo pronto! Seu código HTML está preparado para o WordPress.")
                        
                        # Converte string JSON
                        try:
                            meta = json.loads(dicas_json.strip('`').replace('json\n',''))
                            st.subheader(meta.get("title", "Artigo Gerado"))
                        except:
                            meta = {"title": "Artigo Gerado via Motor GEO"}
                            st.error("Aviso: O JSON gerado veio mal formatado.")
                        
                        # Expanders de Auditoria
                        with st.expander("🕵️‍♂️ Auditoria: O que ranqueia hoje (Google & IA)?", expanded=False):
                            st.markdown("**Google (SerpApi):**")
                            st.info(google_data)
                            st.markdown("**IA (Perplexity):**")
                            st.info(ia_data)

                        # Exibe visualização do HTML
                        with st.expander("👁️ Pré-visualização do HTML", expanded=False):
                            st.markdown(artigo_html, unsafe_allow_html=True)
                        
                        # Exibe Código Fonte
                        st.markdown("### 📋 Código HTML:")
                        st.code(artigo_html, language="html")
                        
                        # Exibe Metadados
                        with st.expander("🛠️ Metadados SEO & Schema", expanded=True):
                            st.json(meta)
                        
                        # Botão de Envio WP
                        if WP_READY:
                            if st.button("📤 Enviar Rascunho para WordPress (Yoast)"):
                                with st.spinner("Enviando via API..."):
                                    res = publicar_wp(meta.get("title", palavra_chave_input), artigo_html, meta)
                                    if res.status_code == 201:
                                        st.success(f"✅ Rascunho criado! Link: {res.json().get('link')}")
                                    else:
                                        st.error(f"❌ Falha ao enviar: {res.text}")
                                        
                except Exception as e:
                    status.update(label="❌ Erro durante a geração", state="error")
                    st.error(f"Erro: {e}")
