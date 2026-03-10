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

st.title("🤖 Arco Martech | Motor GEO v4.0 (Enterprise)")
st.caption("Pipeline Avançado: Search -> Entity Gap -> Strategy -> Writer -> Schema -> Injector -> QA/Cluster")

# ==========================================
# MENU LATERAL (GUIA DO USUÁRIO)
# ==========================================
with st.sidebar:
    st.header("📖 Guia do Motor GEO")
    st.markdown("Bem-vindo à v4.0. Este sistema utiliza uma arquitetura **multi-agentes** para criar conteúdo com autoridade máxima.")
    
    with st.expander("✍️ 1. Gerador de Artigos", expanded=False):
        st.markdown("""
        **O Pipeline Completo:**
        1. **Search:** Lê Google (Serper + Jina) e Baseline LLM.
        2. **Entity Gap:** Descobre buracos semânticos nos concorrentes.
        3. **Strategy:** Monta briefing blindado contra alucinações.
        4. **Writer:** Redige em HTML (com manifesto anti-robô).
        5. **Media:** Injeta imagens (Unsplash ou Pollinations).
        6. **QA & Cluster:** Mede originalidade, citabilidade e sugere próximos artigos.
        """)
        
    with st.expander("📚 2. Brandbook (Base de Dados)", expanded=False):
        st.markdown("""
        O **Claude 3.7** consulta esta matriz antes de escrever. Altere os dados aqui para injetar **inteligência proprietária** e dados reais da sua marca no texto.
        """)
        
    with st.expander("🔍 3. Monitor de GEO e E-E-A-T", expanded=False):
        st.markdown("""
        Um simulador do algoritmo do Google, movido pelo **GPT-4o**. Avalia a densidade de entidades e a veracidade de dados.
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
# 2. BRANDBOOK EMBUTIDO 
# ==========================================
if 'brandbook_df' not in st.session_state:
    dados_iniciais = [
        {
            "Marca": "@saseducacao",
            "Posicionamento": "Marca visionária, líder em aprovação. Entrega de valor em tecnologia e serviço. | Protagonistas na evolução da forma de ensinar e aprender. Abordagem com diagnósticos e embasamentos profundos, superamos as expectativas de parceiros. Somos alta performance e transformamos complexidade em oportunidades. | Promessa: Educação de excelência com foco em resultados acadêmicos, suporte pedagógico próximo e uso de dados para aprendizado.",
            "Territorios": "Vestibulares, Tecnologia, Inovação, Pesquisas",
            "TomDeVoz": "Acadêmico, inovador, especialista e inspirador. Visionário, colaborativo",
            "PublicoAlvo": "Estudantes, vestibulandos e pais. (Foco B2C) Mantenedores de escolas médias e grandes, com alto rigor acadêmico e foco em resultados no ENEM.",
            "RegrasNegativas": "Não usar tom professoral antiquado, não prometer aprovação sem esforço.",
            "RegrasPositivas": "Destaque os diferenciais: - Líder nacional em aprovação no SiSU 2025, - Maior sistema de ensino do Brasil, - +1.300 escolas parceiras, - 97% de fidelização. Propósito da marca: Moldar, com coragem e embasamento, a educação do futuro ao lado das escolas."
        },
        {
            "Marca": "@geekieeducacao",
            "Posicionamento": "Metodologia inovadora (aluno no centro), fácil de implementar. | Material didático inteligente que apoia práticas ativas e que possibilita a personalização da aprendizagem por meio de dados. | Promessa: Aprendizado personalizado, engajante e baseado em dados.",
            "Territorios": "Inovação, IA/Personalização, Tecnologia, Dados",
            "TomDeVoz": "Inovador, moderno, ágil. Transformador, visionário, experimental, adaptável e inspirador",
            "PublicoAlvo": "Diretores de inovação e escolas modernas. (B2B)",
            "RegrasNegativas": "Não parecer sistema engessado, não usar linguagem punitiva.",
            "RegrasPositivas": "Destaque os diferenciais: - A primeira plataforma de educação baseada em dados, - Mais de 12 milhões de estudantes impactados, - Melhor solução de IA premiada no Top Educação. Propósito da marca: Transformar a educação para que cada estudante seja tratado como único."
        },
        {
            "Marca": "@plataformacoc",
            "Posicionamento": "Marca aprovadora que evolui a escola pedagogicamente. | Promover transformação de alto impacto, através de resultados de crescimento para a gestão da escola e ao longo de toda a trajetória do aluno | Promessa: Resultados de crescimento para a gestão da escola e ao longo de toda a trajetória do aluno.",
            "Territorios": "Vestibulares, Esportes, Gestão escolar, Crescimento",
            "TomDeVoz": "Consultivo, parceiro, dinâmico. Viva, ponta firme, sagaz, aberta, contemporânea",
            "PublicoAlvo": "Mantenedores e coordenadores pedagógicos. (B2B)",
            "RegrasNegativas": "Não focar discurso apenas no aluno, não usar jargões sem explicação.",
            "RegrasPositivas": "Destaque os diferenciais: - Mais de 60 anos, - Melhor consultoria do Brasil 2x premiada no Top Educação. Propósito: Impulsionar escolas rumo a uma educação contemporânea de excelência."
        },
        {
            "Marca": "@sistemapositivodeensino",
            "Posicionamento": "Formação integral, humana e próxima. A maior rede do Brasil. | Com uma abordagem inspiradora e humana, somos referência em solutions que guiam nossas escolas parceiras a evoluírem na missão de ensinar, transformando positivamente a vida dos brasileiros.",
            "Territorios": "Formação integral, Inclusão, Tradição",
            "TomDeVoz": "Acolhedor, tradicional, humano. Experiente, criativa, inovadora e segura",
            "PublicoAlvo": "Famílias e diretores de escolas tradicionais.",
            "RegrasNegativas": "Não parecer frio, não usar jargões técnicos sem contexto acolhedor.",
            "RegrasPositivas": "Destaque os diferenciais: - Mais de 45 anos de atuação. Propósito: Inspirar e fortalecer escolas para que evoluam a educação brasileira com humanidade."
        },
        {
            "Marca": "@saedigital",
            "Posicionamento": "Melhor integração físico/digital, hiperatualizada. | Nos consolidamos como o sistema de ensino atualizado, que melhor integra o físico com o digital para potencializar o resultado dos alunos e dos nossos parceiros.",
            "Territorios": "Tecnologia, Inovação Digital",
            "TomDeVoz": "Prático, tecnológico, dinâmico. Jovem, amigável, antenado, parceiro",
            "PublicoAlvo": "Gestores buscando modernização com custo-benefício.",
            "RegrasNegativas": "Não parecer inacessível, não diminuir a importância do material físico.",
            "RegrasPositivas": "Propósito: Desbravar o caminho para uma educação excelente e acessível, que permita a cada aluno e educador escolher e concretizar seus sonhos."
        },
        {
            "Marca": "@solucaoconquista",
            "Posicionamento": "Solução completa focada na parceria Escola-Família. | Desenvolvimento integral e acessível, a partir de 4 pilares: educação financeira, empreendedorismo, educação socioemocional e família.",
            "Territorios": "Família, Educação Infantil, Valores, Comunidade, Empreendedorismo, Socioemocional",
            "TomDeVoz": "Familiar, parceiro, simples e didático. Integradora, descomplicada",
            "PublicoAlvo": "Pais e gestores de escolas de educação infantil.",
            "RegrasNegativas": "Não usar tom corporativo frio, não focar em pressão de vestibular.",
            "RegrasPositivas": "Propósito: Colaborar com escolas para formar alunos protagonistas que constroem seu próprio caminho."
        },
        {
            "Marca": "@escoladainteligencia",
            "Posicionamento": "Um ecossistema de educação que transforma alunos, professores, escolas e famílias pelo desenvolvimento da inteligência socioemocional.",
            "Territorios": "Comunidade, Socioemocional, habilidades e competências",
            "TomDeVoz": "Madura, especialista, profunda, humana, acessível, sentimental, suave, estável.",
            "PublicoAlvo": "Mantenedores de escolas médias, tradicionais que desejam qualidade e são movidos por um senso de propósito (Ticket alto).",
            "RegrasNegativas": "Evitar linguagem robótica, sem focar excessivamente na competição e em pressões externas.",
            "RegrasPositivas": "Destaque: Primeira solução socioemocional do mercado Brasileiro, presente desde 2010. Tricampeões invictos do Top Educação. Citar ferramentas 'Pulso', 'Mapa Socioemocional' e 'Indicadores Multifocais'. 1.2 milhões de pessoas impactadas."
        },
        {
            "Marca": "@pesenglish",
            "Posicionamento": "O maior programa de inglês integrado às escolas, facilitador do ensino de qualidade, com resultados que mudam vidas. | Promessa: Educação acessível, integrada e descomplicada.",
            "Territorios": "Bilíngue, crescimento, tecnologia",
            "TomDeVoz": "Especialista, humano, dinâmico, acessível, suave",
            "PublicoAlvo": "Gestores de escolas que visam escala na educação linguística com custo-benefício para famílias.",
            "RegrasNegativas": "Não prometer fluência irreal em curto prazo, não utilizar termos em inglês soltos sem conexão com o currículo.",
            "RegrasPositivas": "Destaque: 91% de aprovação nos exames de Cambridge, parcerias com Cambridge e Pearson, sistema 'Level Up'. Programa curricular flexível. Mais de 800 escolas, custando 10x menos que curso de idiomas avulso."
        },
        {
            "Marca": "@naveavela",
            "Posicionamento": "Referência em educação tecnológica para formar estudantes protagonistas na resolução de problemas reais com tecnologia e criatividade por meio de experiências práticas.",
            "Territorios": "Inovação, tecnologia, criatividade",
            "TomDeVoz": "Especialista, espontâneo, racional, dinâmico",
            "PublicoAlvo": "Escolas modernas que valorizam cultura Maker e letramento tecnológico.",
            "RegrasNegativas": "Não desmerecer o ensino tradicional. O foco deve ser a integração complementar.",
            "RegrasPositivas": "Destaque: Abordagem STEAM, 4Cs (criatividade, pensamento crítico, colaboração e comunicação), foco em Inteligência Artificial ética. 4x ganhadores no Top Educação em Educação Tecnológica."
        },
        {
            "Marca": "@programapleno",
            "Posicionamento": "O Pleno transforma o convívio escolar através da educação socioemocional interdisciplinar e com rigor científico, trabalhando saúde mental, física e relações interpessoais.",
            "Territorios": "Projetos, socioemocional, habilidades e competências, bem estar",
            "TomDeVoz": "Coletivo, jovem, dinâmico, espontâneo, sofisticado, humano, especialista",
            "PublicoAlvo": "Gestores buscando metodologias baseadas em projetos com comprovação científica.",
            "RegrasNegativas": "Não atrelar as soluções como um serviço clínico. É um desenvolvimento escolar de convivência.",
            "RegrasPositivas": "Destaque: Baseado no modelo internacional CASEL, abordagem SAFER, aprendizado baseado em projetos, Guia de trabalho nos espaços públicos e alinhamento à BNCC."
        },
        {
            "Marca": "@geniodasfinancas",
            "Posicionamento": "Através da educação financeira comportamental, unimos escolas, alunos e famílias para cultivar autonomia, consciência e equilíbrio nas decisões financeiras, fortalecendo projetos de vida mais saudáveis.",
            "Territorios": "Educação financeira comportamental, habilidades e competências",
            "TomDeVoz": "Dinâmico, especialista, acessível, humano, estável",
            "PublicoAlvo": "Escolas focadas em habilidades para a vida do aluno do ensino básico.",
            "RegrasNegativas": "Não usar termos como ficar rico ou fórmulas mágicas. O foco é 'comportamental e equilíbrio', nunca promessas milagrosas.",
            "RegrasPositivas": "Destaque: Educação financeira com propósito, ensinando finanças sem julgamentos e com foco no bem-estar emocional."
        },
        {
            "Marca": "@maraltoedicoes",
            "Posicionamento": "A Maralto assume a sua responsabilidade no processo de construção de um país leitor e apresenta o Programa de Formação Leitora Maralto com o desejo de promover diálogos em torno do livro, da leitura e dos leitores.",
            "Territorios": "Literatura, associação pedagógica",
            "TomDeVoz": "Coletiva, especialista, sofisticada, humana, profunda, formal",
            "PublicoAlvo": "Educadores que apreciam bibliotecas robustas e incentivo literário profundo.",
            "RegrasNegativas": "Não resumir a literatura a apenas materiais didáticos conteudistas. A chave é 'leitura por prazer e diálogo'.",
            "RegrasPositivas": "Destaque: Investimento autoral em conteúdo literário e visual. Propósito: Formar um país de leitores."
        },
        {
            "Marca": "@internationalschoolsoficial",
            "Posicionamento": "O programa bilíngue mais premiado do Brasil. Pioneira em bilinguismo no país. Prover soluções educacionais consistentes e inovadoras. Transformar vidas por meio da educação bilíngue. Empoderar a comunidade escolar para desenvolver o aluno como ser integral. | Promessa: Resultados concretos no aprendizado.",
            "Territorios": "Bilinguismo, educação, integral, viagens, inovação, pioneirismo",
            "TomDeVoz": "Especialista, inovador, inspirador, prático, pioneiro, parceiro",
            "PublicoAlvo": "Gestores, diretores e coordenadores de escolas (B2B) pais e famílias (Foco B2C). Escolas privadas de ticket alto e famílias de classes A, B e C.",
            "RegrasNegativas": "Não usar termos genéricos sem contexto, não soar arrogante ou sabe-tudo. Não inferir que quem aprende inglês é superior ou melhor. Não citar palavras em inglês sem tradução entre parênteses depois. Não focar o discurso somente nos pais (lembrar sempre da figura da escola). NUNCA usar a construção 'neste artigo iremos' ou similares.",
            "RegrasPositivas": "Focar em estrutura informativa. Sempre trazer dados para embasar afirmações vindos de fontes seguras e confiáveis, sempre citar e linkar a fonte dos dados, preferir fontes de pesquisas, governos e instituições de renome. Sempre começar o primeiro parágrafo com um gancho que instigue a leitura, de preferência acompanhado de dado. Podemos usar pesquisas nacionais ou internacionais. Sempre usar construção gramatical focada em clareza: iniciar parágrafos com frases de afirmação, não com conectivos. Sempre conectar com a importância de aprender inglês indo além da gramática: focar na importância de aprender com contexto. Destaque os diferenciais (CSV): Utilização da metodologia CLIL de forma integral. Aborde vivências internacionais reais (KSCIA, Cambridge, Minecraft, Ubisoft, Leo) e a integração do inglês à rotina escolar."
        },
        {
            "Marca": "@isaaceducacao",
            "Posicionamento": "A maior plataforma financeira e de gestão para a educação. | Promessa: Mensalidades em dia, sem dor de cabeça.",
            "Territorios": "Gestão financeira, Inovação, dados, tecnologia",
            "TomDeVoz": "Corporativo, direto, analítico. Simples (acessível) e parceiro, especialista em gestão financeira.",
            "PublicoAlvo": "Mantenedores, gestores e diretores financeiros de escolas, faculdades e confessionais.",
            "RegrasNegativas": "Não parecer banco engessado, não usar linguagem infantilizada ou agressiva contra a família devedora.",
            "RegrasPositivas": "Destaque: Diminuição real da inadimplência, 2x premiada no Top educação, excelência técnica, comprometimento e resultados tangíveis."
        },
        {
            "Marca": "@classapp",
            "Posicionamento": "A agenda escolar online melhor avaliada do Brasil | Promessa: Mais que funcionalidades, soluções definitivas para os desafios reais da escola.",
            "Territorios": "Comunicação escolar, gestão, inovação",
            "TomDeVoz": "Autoridade acessível (sabe e explica como faz), empática e humana.",
            "PublicoAlvo": "Mantenedores, gestores, diretores, coordenadores, TI e marketing de escolas e confessionais.",
            "RegrasNegativas": "Não falar mal do uso do papel de forma grosseira, sempre usar como avanço de modernização.",
            "RegrasPositivas": "Destaque: Adesão de 95% e leitura de 85%, segurança, única vencedora do Top Educação na categoria e mais de 260 mil avaliações com nota 4.8."
        },
        {
            "Marca": "@activesoft",
            "Posicionamento": "Gestão escolar mais simples e eficiente com a Activesoft: tudo o que sua escola precisa para otimizar processos, ganhar eficiência e alcançar melhores resultados.",
            "Territorios": "Gestão escolar, dados, gestão acadêmica, gestão financeira, administrativa",
            "TomDeVoz": "Simples, acessível, clara e amigável.",
            "PublicoAlvo": "Mantenedores, gestores, diretores e TI de escolas e confessionais.",
            "RegrasNegativas": "Não usar terminologia muito rebuscada para TI.",
            "RegrasPositivas": "Destaque: Plataforma 100% online (ao contrário de desktops), 25 anos de mercado, atendimento em chat em até 2 minutos (90% de satisfação). Mais de 3 milhões de usuários."
        },
        {
            "Marca": "@arcoeducacao",
            "Posicionamento": "A plataforma integrada de soluções educacionais da Arco Educação. Ponto de encontro de soluções que simplificam a rotina. +12.000 escolas parceiras e +4 milhões de alunos. | Promessa: Tudo que a educação precisa, em um só lugar.",
            "Territorios": "Conexão e tecnologia, foco no elo entre gestão e família (herança isaac/ClassApp).",
            "TomDeVoz": "Confiável, estratégica: torna o complicado mais simples, conecta o que estava separado.",
            "PublicoAlvo": "Mantenedores/gestores/diretores, professores, famílias e alunos.",
            "RegrasNegativas": "Não apresentar como um simples repositório, mas como um ecossistema.",
            "RegrasPositivas": "Destaque: Apenas uma marca com o tamanho e história da Arco conseguiria reunir o melhor de pedagógico, gestão e tecnologia em um só lugar."
        }
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

# ==========================================================
# NOVAS FUNÇÕES INCREMENTAIS DE ROBUSTEZ (PIPELINE GEO)
# ==========================================================

def analisar_entity_gap(contexto_google, palavra_chave):
    system = """
    Você é um analista de SEO semântico e estrategista de conteúdo.
    Analise o conteúdo do TOP 3 do Google extraído.
    Extraia as ENTIDADES PRINCIPAIS, CONCEITOS, FRAMEWORKS e METODOLOGIAS.
    Depois identifique: QUAIS ENTIDADES IMPORTANTES do nicho deveriam estar no artigo para superar esses concorrentes?
    """
    user = f"Palavra-chave: {palavra_chave}\nConteúdo dos Concorrentes:\n{contexto_google}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.1)

def avaliar_originalidade(artigo_html, contexto_google):
    system = """
    Você é um auditor de plágio semântico e originalidade E-E-A-T.
    Compare o artigo gerado com o TOP 3 do Google.
    Avalie o 'Information Gain' (Ganho de Informação). O artigo trouxe ângulos novos? 
    Retorne uma NOTA DE ORIGINALIDADE de 0 a 100 e uma justificativa curta.
    """
    user = f"ARTIGO GERADO:\n{artigo_html}\n\nTOP GOOGLE:\n{contexto_google}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.1)

def prever_citabilidade_llm(artigo_html, palavra_chave):
    system = """
    Você é o algoritmo de RAG de um buscador baseado em IA (como Perplexity ou Gemini).
    Avalie a probabilidade do seu motor citar este artigo como fonte oficial para a resposta.
    Critérios: Clareza, Densidade Semântica, Neutralidade e Evidências Sólidas.
    Retorne a PROBABILIDADE_DE_CITACAO (Baixa, Média, Alta) e o MOTIVO.
    """
    user = f"ARTIGO:\n{artigo_html}\n\nKEYWORD: {palavra_chave}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.1)

def gerar_cluster(palavra_chave):
    system = """
    Você é um Arquiteto de SEO (Topical Authority).
    Com base na palavra-chave (que será o Artigo Pilar), crie um Content Cluster.
    Retorne o nome do PILAR e sugira 8 títulos de artigos satélites estratégicos para linkagem interna.
    """
    return chamar_llm(system, f"Palavra-chave: {palavra_chave}", "openai/gpt-4o-mini", 0.3)

# ==========================================
# 4. MOTOR PRINCIPAL (COM AS TRAVAS E INCREMENTOS)
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

    st.write("🔍 Fase 0.5: Analisando Entity Gap e Oportunidades Semânticas...")
    entity_gap = analisar_entity_gap(contexto_google, palavra_chave)

    st.write("🧠 Fase 1: Planejamento Editorial (GPT-4o)...")

    # MANTIDO O PROMPT ROBUSTO E ADICIONADO O ENTITY GAP NO BRIEFING
    system_1 = """Você é um Estrategista de Conteúdo de Alta Performance para LLMs (GEO) e Editor-Chefe.
    Sua missão é extrair dados inquestionáveis da pesquisa e estruturar um briefing que FOGE COMPLETAMENTE da estrutura genérica da internet. Artigos de alta performance não usam "O que é", "Benefícios" e "Conclusão". Eles usam ângulos narrativos fortes."""
    
    user_1 = f"""Palavra-chave: '{palavra_chave}'

Contexto extraído do Google:
{contexto_google}

Contexto das IAs (LLMs):
{baseline_ia}

GAP DE ENTIDADES (Inclua essas entidades no briefing para gerar Topical Authority):
{entity_gap}

Nossa Marca Alvo (Não cite concorrentes):
- Posicionamento: {marca_info['Posicionamento']}
- Territórios Estratégicos: {marca_info['Territorios']}

Crie um briefing impecável com as seguintes diretrizes:
1. ÂNGULO NARRATIVO ÚNICO: Qual será a espinha dorsal do texto? (Ex: Quebra de Mito, Análise de Tendência, Guia Estratégico). Escolha um que faça sentido com os Territórios da marca.
2. ESTRUTURA ANTI-FÓRMULA (H2s): Escreva 4 sugestões de Títulos H2 que sejam provocativos ou altamente informativos. É PROIBIDO sugerir títulos clichês como "O que é", "A Importância", "Benefícios" ou "Conclusão".
3. MAPEAMENTO DE EVIDÊNCIAS (MODERAÇÃO E RIGOR): Vasculhe o contexto. Extraia DADOS NUMÉRICOS OU ESTUDOS APENAS se tiverem uma URL neutra válida (governos, ONGs, universidades, grandes jornais). Descarte dados de marcas privadas concorrentes. Se o contexto for pobre e não tiver dados com URLs confiáveis, escreva explicitamente: "FOCO TOTALMENTE CONCEITUAL E METODOLÓGICO, SEM ESTATÍSTICAS."
4. DENSIDADE SEMÂNTICA: Liste 10 termos técnicos obrigatórios baseados no Entity Gap para elevar o nível do texto.
5. GATILHO PARA A MARCA: Como a marca e seu posicionamento vão entrar no final do texto como uma solução lógica, sem soar como panfletagem?"""

    analise = chamar_llm(system_1, user_1, model="openai/gpt-4o", temperature=0.3)

    st.write("✍️ Fase 2: Redigindo em HTML Avançado (Claude 3.7 Sonnet)...")
    
    # MANTIDA A TRAVA DE TITÂNIO E O MANIFESTO ANTI-ROBÔ
    system_2 = """Você é um Especialista em SEO Semântico (GEO) e um Redator de Autoridade. Sua missão é criar um artigo denso, de altíssima qualidade para ser lido tanto por humanos (B2B/B2C) quanto por IAs (Google Gemini/ChatGPT).

DIRETRIZES DE ESTILO E TOM (O MANIFESTO ANTI-ROBÔ):
1. O texto deve ter ritmo, profundidade e elegância. 
2. PALAVRAS E FRASES PROIBIDAS: "No cenário atual", "Cada vez mais", "É inegável que", "É importante ressaltar", "Neste artigo veremos", "Em resumo", "Por fim". Vá direto ao ponto, usando voz ativa e afirmações contundentes.
3. FUJA DA ESTRUTURA WIKIPEDIA: Não defina termos básicos a menos que seja para quebrar um paradigma. Seu leitor já sabe o básico. Entregue 'Information Gain' (Informação Nova e Profunda).

REGRAS ESTRUTURAIS OBRIGATÓRIAS DE HTML:
4. Use EXCLUSIVAMENTE HTML puro (<h2>, <h3>, <p>, <ul>, <li>, <strong>, <table>, <a>). Sem ```html ou tags <html><body>.
5. RESUMO RÁPIDO: Logo após o parágrafo de introdução (sem título de introdução), insira um <h2> chamado "Resumo Rápido" com 3 bullet points curtos (<ul><li>).
6. TÍTULOS (H2): Use os títulos provocativos e informativos do briefing. PROIBIDO usar "O que é", "Benefícios" ou "Conclusão".
7. FAQ ESTRATÉGICO: Crie um <h2> chamado "Perguntas Frequentes" com 3 perguntas de nível avançado (em <h3>) e respostas (em <p>).

REGRAS CRÍTICAS DE E-E-A-T (HONESTIDADE E REFERÊNCIAS):
8. A REGRA DE OURO DA REFERÊNCIA: É mil vezes preferível um texto magistralmente escrito sem nenhum dado ou link, do que um texto com dados inventados. VOCÊ É PROIBIDO DE INVENTAR ESTATÍSTICAS, ANOS OU PESQUISAS (ex: "Censo 2026", "aumentou 114%").
9. USO DE LINKS (href): Se o briefing lhe fornecer um dado com uma URL neutra válida, você DEVE envelopar a fonte com a tag HTML correta (ex: <a href="URL_EXATA" target="_blank" rel="noopener noreferrer">Nome da Instituição</a>). Se o briefing disser "Foco conceitual", NÃO insira links nem invente dados. Use apenas argumentos lógicos, pedagógicos e filosóficos. Toda afirmação estatística no corpo do texto exige obrigatoriamente um link real.
10. CEGUEIRA PARA CONCORRENTES: Ignore qualquer menção a marcas ou escolas privadas concorrentes que estejam no contexto. 
11. POSICIONAMENTO DA MARCA ALVO: A marca alvo deve aparecer no terço final do texto, em um <h3>. Apresente-a como um "Caso de Aplicação Metodológica" ou "Abordagem Prática". Descreva a metodologia dela de forma fria, técnica e jornalística. É terminantemente proibido usar adjetivos publicitários e panfletários (ex: "é a melhor escolha", "maravilhosa", "perfeita"). Demonstre autoridade provando que ela usa a metodologia ensinada no texto."""

    user_2 = f"""Palavra-chave: '{palavra_chave}'
    CONTEXTO TEMPORAL: Hoje é o ano de {ano_atual}. Não projete o futuro se não tiver provas.
    
O QUE A CONCORRÊNCIA DIZ HOJE (CONTEXTO BRUTO PARA FACT-CHECKING):
{contexto_google}
{baseline_ia}

SEU BRIEFING EDITORIAL (SIGA O ÂNGULO NARRATIVO E A ESTRUTURA DAQUI E CUBRA O ENTITY GAP):
{analise}

A MARCA ALVO (O CLIENTE):
Nome da Marca: {marca_alvo} (Remova o @)
Posicionamento e Essência: {marca_info['Posicionamento']}
Territórios da Marca (Incorpore isso na essência do texto): {marca_info['Territorios']}
Tom de Voz Exigido: {marca_info['TomDeVoz']}
Diretrizes OBRIGATÓRIAS: {marca_info.get('RegrasPositivas', '')}
O que NÃO fazer (Regras Negativas): {marca_info['RegrasNegativas']}

Escreva o artigo final em HTML seguindo o manifesto anti-robô e as regras de E-E-A-T."""

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

    # MOTOR DUPLO DE IMAGENS (UNSPLASH + FALLBACK POLLINATIONS)
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
                                img_html_pronta = f'<figure style="margin: 25px 0;"><img src="{img_url}" alt="{alt_text}" style="width:100%; border-radius:8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></figure>'
                    except:
                        pass 
                
                if not img_html_pronta:
                    clean_termo = str(termo).replace("'", "").replace('"', '').strip()
                    p_codificado = urllib.parse.quote(clean_termo)
                    base_poll = "https://image.pollinations.ai/prompt/"
                    img_html_pronta = f'<figure style="margin: 25px 0;"><img src="{base_poll}{p_codificado}?width=1024&height=512&nologo=true&model=flux" alt="{clean_termo}" style="width:100%; border-radius:8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></figure>'

                if img_html_pronta:
                    alvo_replace = '<h2>Resumo Rápido</h2>' if i == 0 else '<h2>Perguntas Frequentes</h2>'
                    artigo_html = artigo_html.replace(alvo_replace, f'{img_html_pronta}\n{alvo_replace}', 1)
                    
    except Exception as e:
        print(f"Erro silencioso ao injetar imagem: {e}")

    # CHAMADAS INCREMENTAIS PÓS-REDAÇÃO (ORIGINALIDADE, CITABILIDADE E CLUSTER)
    st.write("📊 Fase 4: Calculando Originalidade, Citabilidade e Cluster...")
    score_originalidade = avaliar_originalidade(artigo_html, contexto_google)
    citabilidade = prever_citabilidade_llm(artigo_html, palavra_chave)
    cluster = gerar_cluster(palavra_chave)

    return (artigo_html, dicas_json, contexto_google, baseline_ia, entity_gap, score_originalidade, citabilidade, cluster)


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
            with st.status("🤖 Processando Motor GEO v4...", expanded=True) as status:
                try:
                    (
                        artigo_html, 
                        dicas_json, 
                        google_data, 
                        ia_data, 
                        entity_gap, 
                        score_originalidade, 
                        citabilidade, 
                        cluster
                    ) = executar_geracao_completa(palavra_chave_input, marca_selecionada)
                    
                    st.session_state['art_gerado'] = artigo_html
                    st.session_state['metas_geradas'] = dicas_json
                    st.session_state['google_ctx'] = google_data
                    st.session_state['ia_ctx'] = ia_data
                    st.session_state['entity_gap'] = entity_gap
                    st.session_state['score_originalidade'] = score_originalidade
                    st.session_state['citabilidade'] = citabilidade
                    st.session_state['cluster'] = cluster
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

            # NOVAS ABAS DE EXPANSÃO (MÉTRICAS DO V4)
            with st.expander("🧩 Entity Gap Analysis (Oportunidades Semânticas)", expanded=False):
                st.markdown(st.session_state['entity_gap'])
            
            with st.expander("🧠 Previsão de Citabilidade por IAs (LLMs)", expanded=False):
                st.markdown(st.session_state['citabilidade'])
                
            with st.expander("🥇 Originalidade do Artigo (vs Concorrentes)", expanded=False):
                st.markdown(st.session_state['score_originalidade'])
                
            with st.expander("🗺️ Sugestão de Content Cluster (Topical Authority)", expanded=False):
                st.markdown(st.session_state['cluster'])

            with st.expander("🕵️‍♂️ Auditoria Bruta: O que ranqueia hoje (Google & IA)?", expanded=False):
                st.markdown("**Google (Serper + Jina Reader):**")
                st.info(st.session_state['google_ctx'])
                st.markdown("**IA (Perplexity Baseline):**")
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
# 6. MONITOR DE GEO (GAMIFICAÇÃO E AUDITORIA)
# ==========================================
with tab3:
    st.subheader("🔍 Monitor de Autoridade GEO")
    st.caption("Esta aba utiliza o **GPT-4o** para simular um algoritmo de busca, auditar seu texto e gerar insights estruturais.")
    conteudo_para_auditoria = st.session_state.get('art_gerado', '')
    keyword_para_auditoria = st.session_state.get('keyword_atual', '')
    marca_para_auditoria = st.session_state.get('marca_atual', 'a marca').replace('@', '')

    txt_auditoria = st.text_area("HTML do Artigo para Auditoria", height=300, value=conteudo_para_auditoria)
    kw_auditoria = st.text_input("Palavra-Chave Alvo", value=keyword_para_auditoria)

    if st.button("🔎 Analisar com GPT-4o e Gerar Insights"):
        if not txt_auditoria:
            st.warning("⚠️ Por favor, gere um artigo na aba 1 primeiro ou cole o HTML aqui.")
        else:
            with st.spinner("Realizando auditoria contextual profunda e calculando GEO Score..."):
                
                # MANTIDO O PROMPT RESTRITIVO E PERFEITO QUE VOCÊ APROVOU PARA O MONITOR
                sys_audit = """Você é um auditor sênior de SEO e E-E-A-T do Google. Seu padrão é altíssimo.
                
                REGRAS DE AUDITORIA:
                1. A REGRA DE NEGÓCIO PROÍBE CITAR CONCORRENTES. Não penalize o texto por falta de comparações com marcas do mesmo nicho.
                2. PENALIZAÇÃO DE ALUCINAÇÃO (FALHA CRÍTICA): Se o texto inventar estatísticas óbvias sem link ou alucinar datas futuras, a nota deve ser muito baixa.
                3. PENALIZAÇÃO DE BACKLINKS: Verifique as tags <a href>. Todos os dados numéricos e estudos DEVEM ter links para fontes. Se houver dado sem link, penalize fortemente.
                4. AVALIAÇÃO DA MARCA ALVO (ESTUDO DE CASO): A marca deve ser mencionada com um tom jornalístico, técnico e imparcial. Se a linguagem for panfletária, cheia de adjetivos bajuladores (ex: "a melhor escolha", "maravilhosa"), puna o E-E-A-T.
                5. IMAGENS IGNORADAS: IGNORE COMPLETAMENTE AS TAGS HTML DE IMAGEM (<img...>) NA SUA AVALIAÇÃO. NÃO tire pontos se a imagem não tiver fonte ou parecer genérica. Avalie apenas a autoridade do TEXTO.
                
                VOCÊ DEVE RETORNAR EXCLUSIVAMENTE UM OBJETO JSON COM A SEGUINTE ESTRUTURA E CHAVES EXATAS:
                {
                  "score": "Um número inteiro de 0 a 100",
                  "veredito": "Resumo de autoridade e apontamento crítico",
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

                    st.markdown("#### Análise do Conteúdo Gerado")
                    col_critica, col_melhoria = st.columns(2)
                    
                    with col_critica:
                        with st.expander("🚨 Críticas Técnicas ao Texto", expanded=True):
                            st.markdown(dados_audit.get('critica', 'Sem críticas.'))
                            
                    with col_melhoria:
                        with st.expander("🛠️ Correções para este Artigo", expanded=True):
                            st.markdown(dados_audit.get('melhoria', 'Sem melhorias.'))

                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar a auditoria visual. Detalhe técnico: {e}")
                    with st.expander("Ver resposta bruta da IA"):
                        st.write(relatorio_bruto if 'relatorio_bruto' in locals() else "Nenhuma resposta obtida.")
