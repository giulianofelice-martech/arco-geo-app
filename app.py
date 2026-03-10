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
    /* Importando as fontes do site da Arco */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Montserrat:wght@400;600;700;800&display=swap');

    /* Forçando a tipografia global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Estilizando os Títulos para Montserrat (Idêntico ao site) */
    h1, h2, h3 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        color: #111827 !important;
        letter-spacing: -0.02em;
    }

    /* Botões Primários (Estilo Botão Header Arco) */
    .stButton > button {
        background-color: #111827 !important; /* Fundo escuro elegante */
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        height: 3.2em;
        font-family: 'Inter', sans-serif;
        font-weight: 600 !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .stButton > button:hover {
        background-color: #374151 !important; /* Cinza mais claro no hover */
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        color: #FFFFFF !important;
    }

    /* Estilo das Abas (Tabs) */
    [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 2px solid #E5E7EB;
    }
    [data-baseweb="tab"] {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        color: #6B7280;
        padding-top: 16px;
        padding-bottom: 16px;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        color: #F05D23 !important; /* Laranja Arco ativo */
        border-bottom-color: #F05D23 !important;
    }

    /* Melhorando os Expanders (Para parecerem Cards) */
    .streamlit-expanderHeader {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600 !important;
        color: #111827;
        background-color: #FFFFFF;
        border-radius: 8px;
    }
    
    div[data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 16px;
    }

    /* Customizando o Tooltip (Pipeline Ultimate) */
    .pipeline-container {
        font-family: 'Inter', sans-serif;
        font-size: 0.9em; 
        color: #6B7280; 
        margin-bottom: 2rem;
        background-color: #FFFFFF;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
    }
    .pipeline-step {
        cursor: help; 
        color: #374151;
        font-weight: 500;
        border-bottom: 1px dashed #D1D5DB;
        transition: color 0.2s;
    }
    .pipeline-step:hover {
        color: #F05D23;
        border-bottom-color: #F05D23;
    }
    </style>
""", unsafe_allow_html=True)

# Trazendo a logo da Arco do próprio CDN deles
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("https://cdn.prod.website-files.com/6810e8cd1c64e82623876ba8/681134835142ef28e05b06ba_logo-arco-dark.svg", width=120)

st.markdown("<h1 style='margin-top: -20px;'>Motor GEO v6.0 <span style='color: #F05D23; font-size: 0.6em;'>AI Search Native</span></h1>", unsafe_allow_html=True)

# SUBSTITUIÇÃO DO ST.CAPTION PELO HTML COM TOOLTIPS
pipeline_html = """
<div class="pipeline-container">
    <strong style="color: #111827; font-family: 'Montserrat', sans-serif;">Pipeline Ultimate:</strong> 
    <span title="Busca dados reais no Google e IAs concorrentes. (Tech: Serper.dev, Jina AI, GPT-4o-mini)" class="pipeline-step">Search</span> ➔ 
    <span title="Descobre as perguntas exatas que as IAs fazem nos bastidores. (Tech: GPT-4o-mini)" class="pipeline-step">Reverse Query</span> ➔ 
    <span title="Mapeia palavras e conceitos de autoridade para o nicho. (Tech: GPT-4o)" class="pipeline-step">Entity Graph</span> ➔ 
    <span title="Redação estratégica focada em retenção e E-E-A-T. (Tech: Claude 3.7 Sonnet)" class="pipeline-step">Writer</span> ➔ 
    <span title="Criação do código oculto (JSON-LD) que o Google adora. (Tech: Claude 3.7 Sonnet)" class="pipeline-step">Schema</span> ➔ 
    <span title="Mede se o texto cobriu todos os tópicos exigidos pelo buscador." class="pipeline-step">Coverage</span> ➔ 
    <span title="Simula se IAs como Perplexity e SearchGPT usariam seu texto como fonte oficial." class="pipeline-step">RAG Simulation</span> ➔ 
    <span title="Blinda o texto para garantir que a IA cite a sua marca, e não a concorrência." class="pipeline-step">Hijacking Defense</span>
</div>
"""
st.markdown(pipeline_html, unsafe_allow_html=True)

# ==========================================
# MENU LATERAL (GUIA DO USUÁRIO)
# ==========================================
with st.sidebar:
    st.header("📖 Guia do Motor GEO")
    st.markdown("Bem-vindo à v6.0. Este sistema utiliza uma arquitetura **multi-agentes** para criar conteúdo com autoridade máxima e otimização nativa para Motores Gerativos (Perplexity, SearchGPT).")
    
    with st.expander("✍️ 1. Gerador de Artigos", expanded=False):
        st.markdown("""
        **O Pipeline Completo:**
        1. **Search:** Lê Google (Serper + Jina) e Baseline LLM.
        2. **Reverse Query:** Gera perguntas que as IAs fazem internamente.
        3. **Entity Gap & Strategy:** Descobre buracos semânticos e monta o Entity Authority Graph.
        4. **Writer:** Redige com Answer Anchors e Entity Saturation.
        5. **Media:** Injeta imagens em HQ.
        6. **Scoring Avançado:** Calcula Entity Coverage e o Score Global GEO.
        7. **RAG Simulation:** Simula se a IA te escolheria como fonte e detecta Hijacking.
        """)
        
    with st.expander("📚 2. Brandbook (Base de Dados)", expanded=False):
        st.markdown("""
        O **Claude 3.7** consulta esta matriz antes de escrever. Altere os dados aqui para injetar **inteligência proprietária** e dados reais da sua marca no texto.
        """)
        
    with st.expander("🔍 3. Monitor de GEO e E-E-A-T", expanded=False):
        st.markdown("""
        Um simulador do algoritmo do Google, movido pelo **GPT-4o**. Avalia a densidade de entidades e a veracidade de dados.
        """)

    with st.expander("📖 Dicionário: O que nossa IA faz?", expanded=False):
        st.markdown("""
        * **GEO (Generative Engine Optimization):** Otimização para buscadores com IA (como ChatGPT e Perplexity).
        * **E-E-A-T:** Sigla do Google para Experiência, Especialidade, Autoridade e Confiabilidade.
        * **Entity Graph:** Mapeamento inteligente de palavras e conceitos para provar que você domina o assunto.
        * **RAG Simulation:** Simulamos se uma IA usaria seu texto como fonte oficial.
        * **Hijacking Defense:** Defesa contra "roubo de citação", garantindo que a IA cite sua marca e não um concorrente.
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
# NOVAS FUNÇÕES INCREMENTAIS DE ROBUSTEZ E GEO (v5 e v6)
# ==========================================================

def gerar_reverse_queries(palavra_chave):
    system = """
    Você é um analista de comportamento de LLMs e SearchGPT.
    Dada uma keyword principal, gere perguntas que mecanismos de IA provavelmente fazem internamente para construir respostas (Search Intent).
    Retorne APENAS um JSON estrito:
    {
     "user_questions": ["pergunta1", "pergunta2"],
     "llm_reasoning_questions": ["pergunta1", "pergunta2"],
     "semantic_depth_questions": ["pergunta1", "pergunta2"]
    }
    """
    try:
        return chamar_llm(system, f"Keyword principal: {palavra_chave}", "openai/gpt-4o-mini", 0.1, response_format={"type": "json_object"})
    except Exception as e:
        return "{}"

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

def calcular_citation_score(artigo_html):
    score = 0
    if "<strong>Definição:" in artigo_html or "<strong>Definição" in artigo_html: score += 1
    if "<strong>Resposta direta:" in artigo_html or "<strong>Resposta direta" in artigo_html: score += 1
    if "Resumo Estratégico" in artigo_html or "Resumo estratégico" in artigo_html: score += 1
    if "Segundo especialistas" in artigo_html or "Especialistas" in artigo_html: score += 1
    if "Perguntas Frequentes" in artigo_html: score += 1
    return f"{score}/5"

def calcular_entity_coverage(artigo_html, entity_gap_text):
    system = """
    Você é um analisador de SEO semântico.
    Compare:
    1) ENTIDADES importantes sugeridas (Entity Gap)
    2) ENTIDADES presentes no artigo
    Retorne um JSON:
    {
      "entity_coverage_score": "0-100",
      "entities_present": [],
      "entities_missing": []
    }
    """
    user = f"ENTIDADES RECOMENDADAS:\n{entity_gap_text}\n\nARTIGO:\n{artigo_html}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.1, response_format={"type":"json_object"})

def calcular_geo_score(citation_score, originalidade, citabilidade):
    system = """
    Combine os indicadores em um GEO SCORE de 0 a 100.
    Considere: Citation Score, Originalidade, e Probabilidade de Citabilidade por LLM.
    Retorne JSON:
    {
      "geo_score": "0-100",
      "veredito": "curta explicação"
    }
    """
    user = f"Citation Score: {citation_score}\nOriginalidade: {originalidade}\nCitabilidade LLM: {citabilidade}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.1, response_format={"type":"json_object"})

def simular_llm_retrieval(keyword, artigo_html):
    system = """
    Você simula o processo de recuperação de fontes usado por motores de busca baseados em LLM.
    Dada uma pergunta do usuário e um artigo, avalie se o conteúdo seria selecionado como fonte.
    Considere: clareza, estrutura citável, entidades confiáveis, completude, neutralidade.
    Retorne JSON:
    {
      "retrieval_score": "0-100",
      "chance_de_ser_usado_como_fonte": "baixa | média | alta",
      "motivo": "explicação curta"
    }
    """
    user = f"PERGUNTA DO USUÁRIO:\n{keyword}\n\nARTIGO:\n{artigo_html}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.1, response_format={"type":"json_object"})

def detectar_citation_hijacking(artigo_html):
    system = """
    Analise o artigo e identifique vulnerabilidade a AI Citation Hijacking.
    Citation Hijacking acontece quando outro conteúdo concorrente pode responder melhor ou mais direto à mesma pergunta.
    Avalie: ausência de resposta direta, falta de definição clara, falta de estrutura citável, excesso de narrativa.
    Retorne JSON:
    {
      "risco_hijacking": "baixo | médio | alto",
      "pontos_fracos": [],
      "melhorias_recomendadas": []
    }
    """
    user = f"ARTIGO:\n{artigo_html}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.1, response_format={"type":"json_object"})

def simular_resposta_ai(keyword, artigo_html):
    system = """
    Simule como um motor de busca baseado em IA (SGE/Perplexity) responderia a uma pergunta do usuário usando o artigo fornecido APENAS como fonte.
    Produza a resposta final que o usuário veria.
    Depois avalie: clareza, completude, necessidade de outras fontes.
    Retorne JSON:
    {
      "resposta_simulada": "...",
      "qualidade_resposta": "0-100",
      "precisaria_de_outras_fontes": true | false
    }
    """
    user = f"PERGUNTA:\n{keyword}\n\nFONTE:\n{artigo_html}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.2, response_format={"type":"json_object"})

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
        futuro_reverse = executor.submit(gerar_reverse_queries, palavra_chave)
        
        try:
            contexto_google = futuro_google.result(timeout=45)
        except concurrent.futures.TimeoutError:
            contexto_google = "Aviso: A busca orgânica demorou muito. Conteúdo ignorado para manter a velocidade."
        try:
            baseline_ia = futuro_ia.result(timeout=45)
        except concurrent.futures.TimeoutError:
            baseline_ia = "Aviso: O motor de Baseline demorou muito a responder. Ignorado."
        try:
            reverse_queries = futuro_reverse.result(timeout=20)
        except:
            reverse_queries = "{}"

    st.write("🔍 Fase 0.5: Analisando Entity Gap e Oportunidades Semânticas...")
    entity_gap = analisar_entity_gap(contexto_google, palavra_chave)

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
C) MAPA DE EVIDÊNCIAS (MODERAÇÃO E DEEP LINKS): Liste no MÁXIMO 2 ou 3 bullets com pares (afirmação → URL). REGRA DE OURO: A URL DEVE ser um link profundo e exato para a página do estudo/artigo (ex: site.com/pesquisa-xyz-2026). É ESTRITAMENTE PROIBIDO usar URLs genéricas de homepages (ex: https://www.nih.gov/ ou https://www.unesco.org/). Se o contexto só tiver homepages genéricas ou falta de fontes claras, descarte-as e escreva: FOCO TOTALMENTE CONCEITUAL E METODOLÓGICO, SEM ESTATÍSTICAS.D) DENSIDADE SEMÂNTICA (NLP/TF-IDF): Analise o contexto orgânico e liste até 8 "entidades" (jargões, metodologias ou conceitos técnicos) de alto valor presentes no Top 3. 
E) ENTITY AUTHORITY GRAPH: Liste pelo menos 6 entidades institucionais relevantes para o tema (Ex: universidades, organizações internacionais, órgãos governamentais, centros de pesquisa, fundações educacionais). Essas entidades devem ser integradas naturalmente ao texto para reforçar autoridade semântica.
F) GATILHO DE MARCA (não publicitário): descreva como a marca aparecerá no terço final como um “Estudo de Caso Prático” (focando na sua solução específica, seja ela pedagógica, financeira, tecnológica ou de gestão, de forma descritiva e sem adjetivos de venda).
"""

    user_1 = f"""
Palavra-chave: '{palavra_chave}'

Contexto extraído do Google (Serper + Jina):
{contexto_google}

Baseline de IAs (consenso atual):
{baseline_ia}

Reverse Queries (Perguntas de LLMs para estruturar o texto e FAQ):
{reverse_queries}

Marca Alvo:
- Posicionamento: {marca_info['Posicionamento']}
- Territórios Estratégicos: {marca_info['Territorios']}

Instruções:
- Construa o briefing completo seguindo as REGRAS-MESTRAS e ENTREGÁVEIS.
- Use as Reverse Queries para entender a intenção de busca profunda da IA.
- Se o contexto carecer de dados confiáveis com URL, declare FOCO CONCEITUAL (sem inventar números).
"""

    analise = chamar_llm(system_1, user_1, model="openai/gpt-4o", temperature=0.3)

    st.write("✍️ Fase 2: Redigindo em HTML Avançado (Claude 3.7 Sonnet)...")

    system_2 = """
Você é Especialista em SEO Semântico (GEO) e Redator de Autoridade E‑E‑A‑T.
Produza um ARTIGO FINAL em HTML puro, pt-BR, com ganho de informação real.

MANIFESTO ANTI-ROBÔ E ESTILO:
1) Ritmo, profundidade e elegância. Voz ativa. Evite enchimento.
2) PROIBIDO usar: "No cenário atual", "Cada vez mais", "É inegável que", "É importante ressaltar", "Neste artigo veremos/iremos", "Em resumo", "Por fim", "Pesquisas recentes revelam", "Vale ressaltar".
3) Não explique o óbvio; entregue leitura avançada com aplicações práticas e comparações.

GEO (GENERATIVE ENGINE OPTIMIZATION) – REGRAS OBRIGATÓRIAS (MAXIMIZAR CITABILIDADE DA IA):
O artigo deve maximizar a citabilidade por motores de IA. Inclua obrigatoriamente:
4) BLOCO DE DEFINIÇÃO: Insira um parágrafo contendo: <p><strong>Definição:</strong> ...</p>
5) ANSWER ANCHOR E RESPOSTA DIRETA: Logo após a introdução, crie um bloco: <h2>Resposta rápida para: [insira a palavra-chave]</h2><p><strong>Resposta direta:</strong> ...</p>
6) RESUMO ESTRATÉGICO: Insira **exatamente** a linha de marcador `<br>Resumo Estratégico<br>` e crie um <ul> com 3 insights centrais do artigo.
7) FRAMEWORK ESTRUTURADO: Transforme uma das seções em um Framework prático. Ex: <h2>Os principais pilares de...</h2><ul><li>...</li></ul>
8) MICRO BLOCO DE CITAÇÃO E AUTORIDADE: Sempre inclua pelo menos um bloco usando frases de autoridade (Ex: <p><strong>Segundo especialistas:</strong> ...</p> ou "Estudos do setor demonstram que...").

REGRAS HTML E E-E-A-T (CRÍTICAS):
9) Use exclusivamente HTML puro: <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <a>. Não use Markdown nem ```. Não insira <img>.
10) LINKS (EVIDÊNCIAS DE ALTA QUALIDADE): SOMENTE se o briefing trouxer o par (afirmação → URL). Envolva a fonte com <a href="URL_EXATA" target="_blank" rel="noopener noreferrer">Nome do Estudo/Instituição</a>. MODERAÇÃO: Use no MÁXIMO 2 a 3 links no texto inteiro. É terminantemente PROIBIDO linkar para homepages genéricas (ex: site.com.br/ ou .org/). Se a URL recebida for uma homepage genérica, NÃO FAÇA O LINK. Use apenas Deep Links (links profundos para artigos específicos). Proibido inventar números.
11) **FAQ INTELIGENTE**: No terço final, insira **exatamente** a linha `<br>Perguntas Frequentes<br>`. Use as perguntas geradas pelo Reverse Query Engine fornecidas no briefing para criar a seção FAQ (escolha as 3 mais relevantes).
12) Estudo de Caso da Marca Alvo: Inserir uma seção <h2>Estudo de Caso na Prática</h2> descrevendo a solução, tecnologia ou metodologia da marca de forma técnica e jornalística.
13) O primeiro caractere da sua resposta DEVE ser <h1> e o último DEVE ser o fechamento da última tag HTML.
14) ENTITY SATURATION: Integre naturalmente as entidades do Entity Authority Graph ao longo do texto para aumentar a cobertura semântica.
15) VETO ABSOLUTO A CONCORRENTES (RISCO DE FALHA CRÍTICA): É EXPRESSAMENTE PROIBIDO citar, listar ou fazer referência a qualquer empresa, produto ou solução concorrente do mesmo nicho da marca alvo (seja nicho pedagógico, financeiro, literário ou software). Se o contexto do Google mencionar concorrentes diretos ou indiretos, APAGUE-OS da sua memória. A ÚNICA marca comercial permitida em todo o texto é a Marca Alvo.
"""

    user_2 = f"""
Palavra-chave: '{palavra_chave}'

CONTEXTO TEMPORAL: Ano de {ano_atual}. Não projete o futuro sem evidência.
O QUE A CONCORRência DIZ HOJE (para fact-checking e contraste):
{contexto_google}

SEU BRIEFING (siga à risca o ângulo e integre o Entity Authority Graph):
{analise}

MARCA ALVO (Cliente):
- Nome: {marca_alvo} (remova o '@' no texto)
- Posicionamento: {marca_info['Posicionamento']}
- Territórios: {marca_info['Territorios']}
- Tom de Voz: {marca_info['TomDeVoz']}
- Diretrizes OBRIGATÓRIAS: {marca_info.get('RegrasPositivas', '')}
- O que NÃO fazer: {marca_info['RegrasNegativas']}

Escreva o ARTIGO FINAL em HTML conforme as regras GEO, preservando exatamente os marcadores:
<br>Resumo Estratégico<br>
<br>Perguntas Frequentes<br>

ATENÇÃO: Pare de escrever IMEDIATAMENTE após a última tag HTML. NUNCA gere auto-avaliações, comentários ou textos que comecem com "AI:".
"""

    artigo_html = chamar_llm(system_2, user_2, model="anthropic/claude-3.7-sonnet", temperature=0.3)
    artigo_html = re.sub(r'^```html\n|```$', '', artigo_html, flags=re.MULTILINE).strip()
    
    # GUILHOTINA PYTHON: Corta qualquer "auto-avaliação" da IA que venha depois do fechamento do HTML
    if '<' in artigo_html and '>' in artigo_html:
        artigo_html = artigo_html[artigo_html.find('<') : artigo_html.rfind('>') + 1]

    st.write("🛠️ Fase 3: Extraindo JSON e Metadados via Pydantic...")
    schema_gerado = MetadadosArtigo.model_json_schema() if hasattr(MetadadosArtigo, "model_json_schema") else MetadadosArtigo.schema_json()

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
                                img_html_pronta = f'<img src="{img_url}" alt="{alt_text}" style="width:100%; border-radius:8px;" loading="lazy" decoding="async" />'
                    except Exception:
                        pass
                
                if not img_html_pronta:
                    clean_termo = str(termo).replace("'", "").replace('"', '').strip()
                    p_codificado = urllib.parse.quote(clean_termo)
                    base_poll = "https://image.pollinations.ai/prompt/"
                    img_html_pronta = f'<img src="{base_poll}{p_codificado}?width=1024&height=512&nologo=true&model=flux" alt="{clean_termo}" style="width:100%; border-radius:8px;" loading="lazy" decoding="async" />'
                
                if img_html_pronta:
                    alvo_replace = '<br>Resumo Estratégico<br>' if i == 0 else '<br>Perguntas Frequentes<br>'
                    artigo_html = artigo_html.replace(alvo_replace, f'{img_html_pronta}\n{alvo_replace}', 1)
    except Exception as e:
        print(f"Erro silencioso ao injetar imagem: {e}")

    # CHAMADAS INCREMENTAIS PÓS-REDAÇÃO (GEO PIPELINE COMPLETO)
    st.write("📊 Fase 4: Calculando Originalidade, Citabilidade GEO e Cluster...")
    score_originalidade = avaliar_originalidade(artigo_html, contexto_google)
    citabilidade = prever_citabilidade_llm(artigo_html, palavra_chave)
    cluster = gerar_cluster(palavra_chave)
    citation_score = calcular_citation_score(artigo_html)

    st.write("🧪 Fase 5: Calculando Entity Coverage & GEO Score Global...")
    entity_coverage = calcular_entity_coverage(artigo_html, entity_gap)
    geo_score = calcular_geo_score(citation_score, score_originalidade, citabilidade)

    st.write("🔬 Fase 6: Simulação de RAG e Citation Hijacking (Motores LLM)...")
    retrieval_simulation = simular_llm_retrieval(palavra_chave, artigo_html)
    hijacking_risk = detectar_citation_hijacking(artigo_html)
    ai_simulation = simular_resposta_ai(palavra_chave, artigo_html)

    return (
        artigo_html, dicas_json, contexto_google, baseline_ia, entity_gap, 
        score_originalidade, citabilidade, cluster, reverse_queries, 
        citation_score, entity_coverage, geo_score, retrieval_simulation, 
        hijacking_risk, ai_simulation
    )

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
            with st.status("🤖 Processando Motor GEO v6...", expanded=True) as status:
                try:
                    (
                        artigo_html, 
                        dicas_json, 
                        google_data, 
                        ia_data, 
                        entity_gap, 
                        score_originalidade, 
                        citabilidade, 
                        cluster,
                        reverse_queries,
                        citation_score,
                        entity_coverage,
                        geo_score,
                        retrieval_simulation,
                        hijacking_risk,
                        ai_simulation
                    ) = executar_geracao_completa(palavra_chave_input, marca_selecionada)
                    
                    st.session_state['art_gerado'] = artigo_html
                    st.session_state['metas_geradas'] = dicas_json
                    st.session_state['google_ctx'] = google_data
                    st.session_state['ia_ctx'] = ia_data
                    st.session_state['entity_gap'] = entity_gap
                    st.session_state['score_originalidade'] = score_originalidade
                    st.session_state['citabilidade'] = citabilidade
                    st.session_state['cluster'] = cluster
                    st.session_state['reverse_queries'] = reverse_queries
                    st.session_state['citation_score'] = citation_score
                    st.session_state['entity_coverage'] = entity_coverage
                    st.session_state['geo_score'] = geo_score
                    st.session_state['retrieval_simulation'] = retrieval_simulation
                    st.session_state['hijacking_risk'] = hijacking_risk
                    st.session_state['ai_simulation'] = ai_simulation
                    
                    st.session_state['marca_atual'] = marca_selecionada
                    st.session_state['keyword_atual'] = palavra_chave_input
                    status.update(label="✅ Artigo gerado com sucesso!", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ Erro durante a geração", state="error")
                    st.error(f"Erro Crítico: {e}")

    if 'art_gerado' in st.session_state:
        with col2:
            st.success("Tudo pronto! Seu código HTML está preparado para o WordPress.")
            
            kpi_c1, kpi_c2 = st.columns(2)
            with kpi_c1:
                st.metric("🎯 LLM Citation Score", st.session_state.get('citation_score', 'N/A'), help="Mede a presença de blocos GEO (Definição, Resposta Direta, FAQ, Autoridade e Resumo)")
                
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

            # NOVAS ABAS DE EXPANSÃO (MÉTRICAS DO V6 COM GET SEGURO)
            with st.expander("🚀 GEO Score Global", expanded=True):
                st.json(st.session_state.get('geo_score', '{}'))
                
            with st.expander("🧠 Entity Coverage (Topical Authority)", expanded=False):
                st.json(st.session_state.get('entity_coverage', '{}'))
                
            with st.expander("🔎 LLM Retrieval Simulation", expanded=False):
                st.json(st.session_state.get('retrieval_simulation', '{}'))
                
            with st.expander("⚠️ AI Citation Hijacking Risk", expanded=False):
                st.json(st.session_state.get('hijacking_risk', '{}'))
                
            with st.expander("🤖 AI Search Result Simulator", expanded=False):
                st.json(st.session_state.get('ai_simulation', '{}'))

            with st.expander("🔄 Reverse Query Engine (Search Intent)", expanded=False):
                st.json(st.session_state.get('reverse_queries', '{}'))
                
            with st.expander("🧩 Entity Gap Analysis (Oportunidades Semânticas)", expanded=False):
                st.markdown(st.session_state.get('entity_gap', '⚠️ Dados não encontrados.'))
            
            with st.expander("🧠 Previsão de Citabilidade por IAs (LLMs)", expanded=False):
                st.markdown(st.session_state.get('citabilidade', '⚠️ Dados não encontrados.'))
                
            with st.expander("🥇 Originalidade do Artigo (vs Concorrentes)", expanded=False):
                st.markdown(st.session_state.get('score_originalidade', '⚠️ Dados não encontrados.'))
                
            with st.expander("🗺️ Sugestão de Content Cluster (Topical Authority)", expanded=False):
                st.markdown(st.session_state.get('cluster', '⚠️ Dados não encontrados.'))

            with st.expander("🕵️‍♂️ Auditoria Bruta: O que ranqueia hoje (Google & IA)?", expanded=False):
                st.markdown("**Google (Serper + Jina Reader):**")
                st.info(st.session_state.get('google_ctx', 'Sem dados.'))
                st.markdown("**IA (Perplexity Baseline):**")
                st.info(st.session_state.get('ia_ctx', 'Sem dados.'))

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
                
                sys_audit = """Você é um Auditor Sênior de SEO e E-E-A-T do Google, além de Especialista em Engenharia de Prompt. Seu padrão é altíssimo, mas justo e contextual.
                
                REGRAS CRÍTICAS DE AUDITORIA (VETOS ABSOLUTOS E PENALIZAÇÕES):
                1. VETO A CONCORRENTES (FALHA CRÍTICA): O texto é ESTRITAMENTE PROIBIDO de citar marcas, produtos ou empresas concorrentes do mesmo segmento da marca alvo. Se o texto contiver o nome de QUALQUER outra marca privada concorrente que não seja a marca alvo, REDUZA A NOTA PARA 50 imediatamente e critique isso duramente. (Nota: não penalize o texto pela "falta" de comparações externas).
                2. ALUCINAÇÃO (FALHA CRÍTICA): Se o texto inventar estatísticas óbvias sem link (ex: "cresceu 114%") ou alucinar datas futuras irreais, DESTRUA a nota.
                3. CONDICIONAL DE BACKLINKS VS. TEXTO CONCEITUAL: 
                   - Se o texto citar DADOS NUMÉRICOS EXATOS ou ESTUDOS NOMINAIS, eles DEVEM obrigatoriamente ter um link (<a href>). Penalize fortemente se faltar.
                   - PORÉM, se o texto NÃO tiver números exatos e for puramente CONCEITUAL/FILOSÓFICO, É ESTRITAMENTE PROIBIDO penalizá-lo por "falta de links" ou "falta de dados". Avalie apenas a coerência, a lógica e a densidade teórica.
                4. AVALIAÇÃO DA MARCA ALVO (ESTUDO DE CASO): A marca DEVE ser mencionada com um tom jornalístico e técnico (focando em sua solução, tecnologia, produto ou metodologia). Se for assim, a integração está PERFEITA; não exija "provas externas". Só puna se a linguagem for panfletária e cheia de adjetivos bajuladores.
                5. IMAGENS IGNORADAS: IGNORE COMPLETAMENTE AS TAGS HTML DE IMAGEM (<img...>) NA SUA AVALIAÇÃO. NUNCA tire pontos se a imagem não tiver fonte ou parecer genérica.
                6. EXTENSÃO E CLICHÊS: Textos densos e extensos são o objetivo. SÓ penalize se houver jargões robóticos de IA ("Em resumo", "É inegável que", "No cenário atual").
                
                DIRETRIZ DE PONTUAÇÃO E FEEDBACK (META-PROMPTING):
                - PERMISSÃO DE NOTA MÁXIMA: Se o texto seguiu as regras, NÃO CITOU CONCORRENTES, não alucinou e fez uma integração técnica da marca, VOCÊ DEVE DAR NOTA 100.
                - Se a nota for 100, retorne ARRAYS VAZIOS `[]` nas chaves "critica", "melhoria" e "sugestoes_dev". Não invente defeitos genéricos só para dar nota 90.
                
                VOCÊ DEVE RETORNAR EXCLUSIVAMENTE UM OBJETO JSON COM A SEGUINTE ESTRUTURA E CHAVES EXATAS:
                {
                  "score": "Um número inteiro de 0 a 100",
                  "veredito": "Resumo de autoridade e apontamento crítico. Direto ao ponto.",
                  "critica": ["Ponto fraco 1", "Ponto fraco 2"],
                  "melhoria": ["Como arrumar 1", "Como arrumar 2"],
                  "sugestoes_dev": ["Insight para o prompt do Redator (se houver falha de padrão)"]
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
                            criticas = dados_audit.get('critica', [])
                            if isinstance(criticas, list) and criticas:
                                for c in criticas:
                                    st.markdown(f"- {c}")
                            else:
                                st.markdown("✅ **Nenhuma crítica identificada. Texto cirúrgico!**")
                                
                    with col_melhoria:
                        with st.expander("🛠️ Correções para este Artigo", expanded=True):
                            melhorias = dados_audit.get('melhoria', [])
                            if isinstance(melhorias, list) and melhorias:
                                for m in melhorias:
                                    st.markdown(f"- {m}")
                            else:
                                st.markdown("✅ **Sem sugestões de melhoria pendentes.**")

                    st.markdown("---")
                    st.markdown("### ⚙️ Engenharia de Prompt (Melhoria Contínua)")
                    with st.expander("💡 Sugestões de Novos Guardrails Estruturais", expanded=True):
                        sugestoes_dev = dados_audit.get('sugestoes_dev', [])
                        if isinstance(sugestoes_dev, list) and len(sugestoes_dev) > 0:
                            for s in sugestoes_dev:
                                st.info(f"🤖 **Insight para o Prompt:** {s}")
                            st.caption("Dica: Copie os insights acima que fizerem sentido e cole no prompt do Claude no código principal.")
                        else:
                            st.success("✨ **O prompt atual está performando de forma excelente para este nicho. Nenhuma sugestão gerada.**")

                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar a auditoria visual. Detalhe técnico: {e}")
                    with st.expander("Ver resposta bruta da IA"):
                        st.write(relatorio_bruto if 'relatorio_bruto' in locals() else "Nenhuma resposta obtida.")
