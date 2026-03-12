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

    /* TAG ESTILO ARCO (Azulzinha) - ADICIONADA AQUI */
    .arco-tag {
        display: inline-flex;
        align-items: center;
        background-color: #E8F2FA;
        color: #418EDE !important;
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 4px 12px;
        border-radius: 50px;
        text-transform: uppercase;
        margin-bottom: 4px;
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

# ==========================================
# CABEÇALHO ALINHADO COM A TAG
# ==========================================
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 24px;">
    <img src="https://cdn.prod.website-files.com/6810e8cd1c64e82623876ba8/681134835142ef28e05b06ba_logo-arco-dark.svg" style="width: 180px; margin-right: -10px;" alt="Logo Arco">
    <div style="display: flex; flex-direction: column; justify-content: center;">
        <div class="arco-tag" style="width: fit-content; margin-bottom: 4px;">MOTOR DE INTELIGÊNCIA</div>
        <h1 style="margin: 0; padding: 0; font-size: 2.4rem;">Motor GEO v7.0 <span style="color: #F05D23; font-size: 0.6em;">AI Search Native</span></h1>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PIPELINE COM TOOLTIPS (ATUALIZADO V7.0)
# ==========================================
pipeline_html = """
<div class="pipeline-container">
    <strong style="color: #111827; font-family: 'Montserrat', sans-serif;">Pipeline GEO v7.0:</strong> 
    <span title="Busca dados reais no Google (Serper + Jina) e IAs." class="pipeline-step">1. Search</span> ➔ 
    <span title="Engenharia reversa das dúvidas de usuários e LLMs." class="pipeline-step">2. Intent Map</span> ➔ 
    <span title="Mapeia buracos semânticos e nós de autoridade." class="pipeline-step">3. Entity Graph</span> ➔ 
    <span title="Redação HTML E-E-A-T com proteção anti-alucinação." class="pipeline-step">4. Writer</span> ➔ 
    <span title="Criação de dados ocultos Schema/JSON-LD." class="pipeline-step">5. Schema</span> ➔ 
    <span title="Cálculos Python: Chunk Citability, Answer-First e Evidence Density." class="pipeline-step">6. Math Heuristics</span> ➔ 
    <span title="Simulação LLM: Retrieval, Risco de Hijacking e Coverage." class="pipeline-step">7. RAG Simulation</span>
</div>
"""
st.markdown(pipeline_html, unsafe_allow_html=True)

# ==========================================
# MENU LATERAL (GUIA DO USUÁRIO)
# ==========================================
with st.sidebar:
    st.header("📖 Guia do Motor GEO")
    st.markdown("Bem-vindo à v7.0. Este sistema utiliza uma arquitetura **multi-agentes aliada a heurísticas matemáticas** para criar conteúdo nativamente otimizado para Motores Gerativos (Perplexity, SearchGPT, SGE).")
    
    with st.expander("✍️ 1. Como funciona o Motor?", expanded=False):
        st.markdown("""
        **O Pipeline de 7 Passos:**
        1. **Search:** Escaneia o Top 3 do Google e o baseline de IAs.
        2. **Reverse Query:** Descobre as perguntas ocultas dos usuários.
        3. **Entity Strategy:** Mapeia os jargões que provam autoridade.
        4. **Writer:** Redige usando Copywriting corporativo e blocos GEO.
        5. **Media & Schema:** Injeta imagens e código JSON-LD.
        6. **Math Heuristics:** Algoritmos Python calculam densidade de evidências, tamanho de parágrafos e facilidade de citação.
        7. **RAG Simulation:** Simula se uma IA real usaria seu texto como fonte.
        """)
        
    with st.expander("📚 2. Brandbook (Base de Dados)", expanded=False):
        st.markdown("""
        O cérebro da sua marca. Altere os dados aqui para injetar **inteligência proprietária** e cases reais. O motor tem regras absolutas para sempre usar os dados institucionais daqui sem alucinar estatísticas concorrentes.
        """)
        
    with st.expander("🔍 3. Monitor de GEO e E-E-A-T", expanded=False):
        st.markdown("""
        Um simulador do algoritmo do Google, movido pelo **GPT-4o**. Ele funciona como um inspetor implacável: se você inventar um dado de mercado sem link, ele zera sua nota E-E-A-T.
        """)

    with st.expander("📖 Dicionário de Métricas (v7.0)", expanded=False):
        st.markdown("""
        **Métricas Matemáticas (Python):**
        * **Chunk Citability:** Mede a formatação (listas, parágrafos curtos). Quanto mais estruturado, mais fácil a IA ler e te citar.
        * **Answer-First:** Checa se a resposta direta está nos primeiros 800 caracteres.
        * **Evidence Density:** Conta links e números exatos para validar E-E-A-T.
        * **Information Gain:** Subtrai as palavras do seu texto pelas do Top 3 do Google para ver o quanto de vocabulário "inédito" você trouxe.
        
        **Métricas Semânticas (IA):**
        * **Entity Coverage:** Quais jargões obrigatórios você usou e quais esqueceu.
        * **RAG Chunk Ranking:** Quais trechos do seu texto a IA recortaria para gerar um resumo.
        * **AI Hijacking Risk:** Avalia se seu texto dá "voltas demais" e pode perder o clique para um concorrente mais direto.
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
            "Marca": "SAS Educação",
            "URL": "https://www.saseducacao.com.br/",
            "Posicionamento": "Marca visionária, líder em aprovação. Entrega de valor em tecnologia e serviço. | Protagonistas na evolução da forma de ensinar e aprender. Abordagem com diagnósticos e embasamentos profundos, superamos as expectativas de parceiros. Somos alta performance e transformamos complexidade em oportunidades. | Promessa: Educação de excelência com foco em resultados acadêmicos, suporte pedagógico próximo e uso de dados para aprendizado.",
            "Territorios": "Vestibulares, Tecnologia, Inovação, Pesquisas",
            "TomDeVoz": "Acadêmico, inovador, especialista e inspirador. Visionário, colaborativo",
            "PublicoAlvo": "Mantenedores e gestores de escolas médias e grandes, com alto rigor acadêmico e foco em resultados no ENEM. Estudantes, vestibulandos e pais",
            "RegrasNegativas": "Não usar tom professoral antiquado, não prometer aprovação sem esforço.",
            "RegrasPositivas": "Destaque os diferenciais: - Líder nacional em aprovação no SiSU 2025, - Maior sistema de ensino do Brasil, - +1.300 escolas parceiras, - 97% de fidelização. Propósito da marca: Moldar, com coragem e embasamento, a educação do futuro ao lado das escolas."
        },
        {
            "Marca": "Geekie",
            "URL": "https://www.geekie.com.br/",
            "Posicionamento": "Metodologia inovadora (aluno no centro), fácil de implementar. | Material didático inteligente que apoia práticas ativas e que possibilita a personalização da aprendizagem por meio de dados. | Promessa: Aprendizado personalizado, engajante e baseado em dados.",
            "Territorios": "Inovação, IA/Personalização, Tecnologia, Dados",
            "TomDeVoz": "Inovador, moderno, ágil. Transformador, visionário, experimental, adaptável e inspirador",
            "PublicoAlvo": "Mantenedores e Gestores. Diretores de inovação e escolas modernas.",
            "RegrasNegativas": "Não parecer sistema engessado, não usar linguagem punitiva.",
            "RegrasPositivas": "Destaque os diferenciais: - A primeira plataforma de educação baseada em dados, - Mais de 12 milhões de estudantes impactados, - Melhor solução de IA premiada no Top Educação. Propósito da marca: Transformar a educação para que cada estudante seja tratado como único."
        },
        {
            "Marca": "COC",
            "URL": "https://coc.com.br/",
            "Posicionamento": "Marca aprovadora que evolui a escola pedagogicamente. | Promover transformação de alto impacto, através de resultados de crescimento para a gestão da escola e ao longo de toda a trajetória do aluno | Promessa: Resultados de crescimento para a gestão da escola e ao longo de toda a trajetória do aluno.",
            "Territorios": "Vestibulares, Esportes, Gestão escolar, Crescimento",
            "TomDeVoz": "Consultivo, parceiro, dinâmico. Viva, ponta firme, sagaz, aberta, contemporânea",
            "PublicoAlvo": "Mantenedores e Gestores. Coordenadores pedagógicos.",
            "RegrasNegativas": "Não focar discurso apenas no aluno, não usar jargões sem explicação.",
            "RegrasPositivas": "Destaque os diferenciais: - Mais de 60 anos, - Melhor consultoria do Brasil 2x premiada no Top Educação. Propósito: Impulsionar escolas rumo a uma educação contemporânea de excelência."
        },
        {
            "Marca": "Sistema Positivo",
            "URL": "https://www.sistemapositivo.com.br/",
            "Posicionamento": "Formação integral, humana e próxima. A maior rede do Brasil. | Com uma abordagem inspiradora e humana, somos referência em solutions que guiam nossas escolas parceiras a evoluírem na missão de ensinar, transformando positivamente a vida dos brasileiros.",
            "Territorios": "Formação integral, Inclusão, Tradição",
            "TomDeVoz": "Acolhedor, tradicional, humano. Experiente, criativa, inovadora e segura",
            "PublicoAlvo": "Famílias. Mantenedores e Gestores de escolas tradicionais.",
            "RegrasNegativas": "Não parecer frio, não usar jargões técnicos sem contexto acolhedor.",
            "RegrasPositivas": "Destaque os diferenciais: - Mais de 45 anos de atuação. Propósito: Inspirar e fortalecer escolas para que evoluam a educação brasileira com humanidade."
        },
        {
            "Marca": "SAE Digital",
            "URL": "https://sae.digital/",
            "Posicionamento": "Melhor integração físico/digital, hiperatualizada. | Nos consolidamos como o sistema de ensino atualizado, que melhor integra o físico com o digital para potencializar o resultado dos alunos e dos nossos parceiros.",
            "Territorios": "Tecnologia, Inovação Digital",
            "TomDeVoz": "Prático, tecnológico, dinâmico. Jovem, amigável, antenado, parceiro",
            "PublicoAlvo": "Mantenedores e Gestores buscando modernização com custo-benefício.",
            "RegrasNegativas": "Não parecer inacessível, não diminuir a importância do material físico.",
            "RegrasPositivas": "Propósito: Desbravar o caminho para uma educação excelente e acessível, que permita a cada aluno e educador escolher e concretizar seus sonhos."
        },
        {
            "Marca": "Conquista Solução Educacional",
            "URL": "https://www.educacaoconquista.com.br/",
            "Posicionamento": "Solução completa focada na parceria Escola-Família. | Desenvolvimento integral e acessível, a partir de 4 pilares: educação financeira, empreendedorismo, educação socioemocional e família.",
            "Territorios": "Família, Educação Infantil, Valores, Comunidade, Empreendedorismo, Socioemocional",
            "TomDeVoz": "Familiar, parceiro, simples e didático. Integradora, descomplicada",
            "PublicoAlvo": "Pais. Mantenedores e Gestores de escolas de educação infantil.",
            "RegrasNegativas": "Não usar tom corporativo frio, não focar em pressão de vestibular.",
            "RegrasPositivas": "Propósito: Colaborar com escolas para formar alunos protagonistas que constroem seu próprio caminho."
        },
        {
            "Marca": "Escola da Inteligência",
            "URL": "https://escoladainteligencia.com.br/",
            "Posicionamento": "Um ecossistema de educação que transforma alunos, professores, escolas e famílias pelo desenvolvimento da inteligência socioemocional.",
            "Territorios": "Comunidade, Socioemocional, habilidades e competências",
            "TomDeVoz": "Madura, especialista, profunda, humana, acessível, sentimental, suave, estável.",
            "PublicoAlvo": "Mantenedores e Gestores de escolas médias, tradicionais que desejam qualidade e são movidos por um senso de propósito (Ticket alto).",
            "RegrasNegativas": "Evitar linguagem robótica, sem focar excessivamente na competição e em pressões externas.",
            "RegrasPositivas": "Destaque: Primeira solução socioemocional do mercado Brasileiro, presente desde 2010. Tricampeões invictos do Top Educação. Citar ferramentas 'Pulso', 'Mapa Socioemocional' e 'Indicadores Multifocais'. 1.2 milhões de pessoas impactadas."
        },
        {
            "Marca": "PES English",
            "URL": "https://www.pesenglish.com.br/",
            "Posicionamento": "O maior programa de inglês integrado às escolas, facilitador do ensino de qualidade, com resultados que mudam vidas. | Promessa: Educação acessível, integrada e descomplicada.",
            "Territorios": "Bilíngue, crescimento, tecnologia",
            "TomDeVoz": "Especialista, humano, dinâmico, acessível, suave",
            "PublicoAlvo": "Mantenedores e Gestores de escolas que visam escala na educação linguística com custo-benefício para famílias.",
            "RegrasNegativas": "Não prometer fluência irreal em curto prazo, não utilizar termos em inglês soltos sem conexão com o currículo.",
            "RegrasPositivas": "Destaque: 91% de aprovação nos exames de Cambridge, parcerias com Cambridge e Pearson, sistema 'Level Up'. Programa curricular flexível. Mais de 800 escolas, custando 10x menos que curso de idiomas avulso."
        },
        {
            "Marca": "Nave a Vela",
            "URL": "https://www.naveavela.com.br/",
            "Posicionamento": "Referência em educação tecnológica para formar estudantes protagonistas na resolução de problemas reais com tecnologia e criatividade por meio de experiências práticas.",
            "Territorios": "Inovação, tecnologia, criatividade",
            "TomDeVoz": "Especialista, espontâneo, racional, dinâmico",
            "PublicoAlvo": "Mantenedores e Gestore de escolas modernas que valorizam cultura Maker e letramento tecnológico.",
            "RegrasNegativas": "Não desmerecer o ensino tradicional. O foco deve ser a integração complementar.",
            "RegrasPositivas": "Destaque: Abordagem STEAM, 4Cs (criatividade, pensamento crítico, colaboração e comunicação), foco em Inteligência Artificial ética. 4x ganhadores no Top Educação em Educação Tecnológica."
        },
        {
            "Marca": "Programa Pleno",
            "URL": "https://programapleno.com.br/",
            "Posicionamento": "O Pleno transforma o convívio escolar através da educação socioemocional interdisciplinar e com rigor científico, trabalhando saúde mental, física e relações interpessoais.",
            "Territorios": "Projetos, socioemocional, habilidades e competências, bem estar",
            "TomDeVoz": "Coletivo, jovem, dinâmico, espontâneo, sofisticado, humano, especialista",
            "PublicoAlvo": "Mantenedores e Gestores buscando metodologias baseadas em projetos com comprovação científica.",
            "RegrasNegativas": "Não atrelar as soluções como um serviço clínico. É um desenvolvimento escolar de convivência.",
            "RegrasPositivas": "Destaque: Baseado no modelo internacional CASEL, abordagem SAFER, aprendizado baseado em projetos, Guia de trabalho nos espaços públicos e alinhamento à BNCC."
        },
        {
            "Marca": "Gênio das Finanças",
            "URL": "https://geniodasfinancas.com.br/",
            "Posicionamento": "Através da educação financeira comportamental, unimos escolas, alunos e famílias para cultivar autonomia, consciência e equilíbrio nas decisões financeiras, fortalecendo projetos de vida mais saudáveis.",
            "Territorios": "Educação financeira comportamental, habilidades e competências",
            "TomDeVoz": "Dinâmico, specialist, acessível, humano, estável",
            "PublicoAlvo": "Mantenedores e Gestores de escolas focadas em habilidades para a vida do aluno do ensino básico.",
            "RegrasNegativas": "Não usar termos como ficar rico ou fórmulas mágicas. O foco é 'comportamental e equilíbrio', nunca promessas milagrosas.",
            "RegrasPositivas": "Destaque: Educação financeira com propósito, ensinando finanças sem julgamentos e com foco no bem-estar emocional."
        },
        {
            "Marca": "Maralto",
            "URL": "https://maralto.com.br/",
            "Posicionamento": "A Maralto assume a sua responsabilidade no processo de construção de um país leitor e apresenta o Programa de Formação Leitora Maralto com o desejo de promover diálogos em torno do livro, da leitura e dos leitores.",
            "Territorios": "Literatura, associação pedagógica",
            "TomDeVoz": "Coletiva, especialista, sofisticada, humana, profunda, formal",
            "PublicoAlvo": "Educadores que apreciam bibliotecas robustas e incentivo literário profundo.",
            "RegrasNegativas": "Não resumir a literatura a apenas materiais didáticos conteudistas. A chave é 'leitura por prazer e diálogo'.",
            "RegrasPositivas": "Destaque: Investimento autoral em conteúdo literário e visual. Propósito: Formar um país de leitores."
        },
        {
            "Marca": "International School",
            "URL": "https://internationalschool.global/",
            "Posicionamento": "O programa bilíngue mais premiado do Brasil. Pioneira em bilinguismo no país. Prover soluções educacionais consistentes e inovadoras. Transformar vidas por meio da educação bilíngue. Empoderar a comunidade escolar para desenvolver o aluno como ser integral. | Promessa: Resultados concretos no aprendizado.",
            "Territorios": "Bilinguismo, educação, integral, viagens, inovação, pioneirismo",
            "TomDeVoz": "Especialista, inovador, inspirador, prático, pioneiro, parceiro",
            "PublicoAlvo": "Gestores, diretores e coordenadores de escolas. Pais e famílias. Escolas privadas de ticket alto e famílias de classes A, B e C.",
            "RegrasNegativas": "Não usar termos genéricos sem contexto, não soar arrogante ou sabe-tudo. Não inferir que quem aprende inglês é superior ou melhor. Não citar palavras em inglês sem tradução entre parênteses depois. Não focar o discurso somente nos pais (lembrar sempre da figura da escola). NUNCA usar a construção 'neste artigo iremos' ou similares.",
            "RegrasPositivas": "Focar em estrutura informativa. Sempre trazer dados para embasar afirmações vindos de fontes seguras e confiáveis, sempre citar e linkar a fonte dos dados, preferir fontes de pesquisas, governos e instituições de renome. Sempre começar o primeiro parágrafo com um gancho que instigue a leitura, de preferência acompanhado de dado. Podemos usar pesquisas nacionais ou internacionais. Sempre usar construção gramatical focada em clareza: iniciar parágrafos com frases de afirmação, não com conectivos. Sempre conectar com a importância de aprender inglês indo além da gramática: focar na importância de aprender com contexto. Destaque os diferenciais (CSV): Utilização da metodologia CLIL de forma integral. Aborde vivências internacionais reais (KSCIA, Cambridge, Minecraft, Ubisoft, Leo) e a integração do inglês à rotina escolar."
        },
        {
            "Marca": "Isaac",
            "URL": "https://isaac.com.br/",
            "Posicionamento": "A maior plataforma financeira e de gestão para a educação. | Promessa: Mensalidades em dia, sem dor de cabeça.",
            "Territorios": "Gestão financeira, Inovação, dados, tecnologia",
            "TomDeVoz": "Corporativo, direto, analítico. Simples (acessível) e parceiro, especialista em gestão financeira.",
            "PublicoAlvo": "Mantenedores, gestores e diretores financeiros de escolas, faculdades e confessionais.",
            "RegrasNegativas": "Não parecer banco engessado, não usar linguagem infantilizada ou agressiva contra a família devedora.",
            "RegrasPositivas": "Destaque: Diminuição real da inadimplência, 2x premiada no Top educação, excelência técnica, comprometimento e resultados tangíveis."
        },
        {
            "Marca": "ClassApp",
            "URL": "https://www.classapp.com.br/",
            "Posicionamento": "A agenda escolar online melhor avaliada do Brasil | Promessa: Mais que funcionalidades, soluções definitivas para os desafios reais da escola.",
            "Territorios": "Comunicação escolar, gestão, inovação",
            "TomDeVoz": "Autoridade acessível (sabe e explica como faz), empática e humana.",
            "PublicoAlvo": "Mantenedores, gestores, diretores, coordenadores, TI e marketing de escolas.",
            "RegrasNegativas": "Não falar mal do uso do papel de forma grosseira, sempre usar como avanço de modernização.",
            "RegrasPositivas": "Destaque: Adesão de 95% e leitura de 85%, segurança, única vencedora do Top Educação na categoria e mais de 260 mil avaliações com nota 4.8."
        },
        {
            "Marca": "Activesoft",
            "URL": "https://activesoft.com.br/",
            "Posicionamento": "Gestão escolar mais simples e eficiente com a Activesoft: tudo o que sua escola precisa para otimizar processos, ganhar eficiência e alcançar melhores resultados.",
            "Territorios": "Gestão escolar, dados, gestão acadêmica, gestão financeira, administrativa",
            "TomDeVoz": "Simples, acessível, clara e amigável.",
            "PublicoAlvo": "Mantenedores, gestores, diretores e TI de escolas.",
            "RegrasNegativas": "Não usar terminologia muito rebuscada para TI.",
            "RegrasPositivas": "Destaque: Plataforma 100% online (ao contrário de desktops), 25 anos de mercado, atendimento em chat em até 2 minutos (90% de satisfação). Mais de 3 milhões de usuários."
        },
        {
            "Marca": "Arco Educação",
            "URL": "https://www.arcoeducacao.com.br/",
            "Posicionamento": "A plataforma integrada de soluções educacionais da Arco Educação. Ponto de encontro de soluções que simplificam a rotina. +12.000 escolas parceiras e +4 milhões de alunos. | Promessa: Tudo que a educação precisa, em um só lugar.",
            "Territorios": "Conexão e tecnologia, foco no elo entre gestão e família (herança isaac/ClassApp).",
            "TomDeVoz": "Confiável, estratégica: torna o complicado mais simples, conecta o que estava separado.",
            "PublicoAlvo": "Mantenedores, gestores e diretores. Professores. Famílias. Alunos.",
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

# NOVA FUNÇÃO: Busca credenciais WP dinâmicas da marca selecionada
def obter_credenciais_wp(marca):
    """Busca as credenciais do WP específicas da marca nos secrets (seção [wordpress])."""
    try:
        if "wordpress" in st.secrets and marca in st.secrets["wordpress"]:
            creds = st.secrets["wordpress"][marca]
            return creds.get("WP_URL", ""), creds.get("WP_USER", ""), creds.get("WP_APP_PASSWORD", "")
    except Exception:
        pass
    return "", "", ""
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
    Retorne APENAS um JSON:
    {
      "citabilidade_score": "nota de 0 a 100",
      "motivo": "explicação"
    }
    """
    user = f"ARTIGO:\n{artigo_html}\n\nKEYWORD: {palavra_chave}"
    return chamar_llm(system, user, "openai/gpt-4o-mini", 0.1, response_format={"type":"json_object"})

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

# ==========================================================
# NOVAS MÉTRICAS MATEMÁTICAS RAG / GEO (V7.0)
# ==========================================================
def extrair_numero(valor):
    try:
        if isinstance(valor, dict):
            valor = json.dumps(valor)
        match = re.search(r'\d+', str(valor))
        if match:
            return int(match.group())
    except:
        pass
    return 0

def calcular_geo_score_matematico(citation_score, originalidade, citabilidade, entity_coverage_str):
    # Converte tudo para número
    citation = extrair_numero(citation_score) * 20  # Multiplica por 20 para virar escala 0-100
    original = extrair_numero(originalidade)
    cita_llm = extrair_numero(citabilidade)
    
    # Extrai o score de entidades do dict que a IA gerou antes
    try:
        entity_dict = json.loads(entity_coverage_str)
        entity = int(entity_dict.get("entity_coverage_score", 0))
    except:
        entity = extrair_numero(entity_coverage_str)

    # Cálculo Ponderado Matemático (Soma 100%)
    geo = (0.35 * citation) + (0.25 * cita_llm) + (0.25 * entity) + (0.15 * original)

    return {
        "citation_score_normalizado": f"{citation}/100",
        "citabilidade_llm": cita_llm,
        "originalidade": original,
        "entity_coverage": entity,
        "geo_score_final": round(geo, 2),
        "veredito": "Score calculado matematicamente via heurística RAG com pesos fixos (não subjetivo)."
    }

def avaliar_chunk_citability(artigo_html):
    paragrafos = artigo_html.split("</p>")
    definicoes = 0
    listas = artigo_html.count("<li>")
    paragrafos_curtos = 0

    for p in paragrafos:
        texto_limpo = re.sub(r'<[^>]+>', '', p).strip()
        palavras = len(texto_limpo.split())
        if ":" in texto_limpo and palavras < 40 and palavras > 5:
            definicoes += 1
        if 10 < palavras < 35:
            paragrafos_curtos += 1

    # NOVA LÓGICA DE FREIO: Máximo de 15 pontos para listas (aprox. 5 itens no total)
    pontos_lista = min(listas * 3, 15)

    score = (definicoes * 10) + pontos_lista + (paragrafos_curtos * 2)
    score = min(score, 100)
    return {
        "chunk_citability_score": score,
        "definicoes_estrategicas_detectadas": definicoes,
        "itens_de_lista": listas,
        "paragrafos_de_leitura_rapida": paragrafos_curtos
    }

def avaliar_answer_first(artigo_html):
    inicio = artigo_html[:800].lower()
    padroes = ["resposta direta:", "definição:", "é ", "refere-se", "significa"]
    for p in padroes:
        if p in inicio:
            return {"answer_first_score": 100, "padrao_detectado": p, "status": "Excelente (Resposta no Topo)"}
    return {"answer_first_score": 40, "padrao_detectado": "nenhum", "status": "Alerta: A IA pode ter dificuldade de achar a resposta rápida."}

def simular_rag_chunks(artigo_html, keyword):
    chunks = artigo_html.split("\n\n")
    resultados = []
    for c in chunks:
        texto_limpo = re.sub(r'<[^>]+>', '', c).strip()
        if not texto_limpo: continue
        score = 0
        palavras = texto_limpo.lower()
        if keyword.lower() in palavras:
            score += 30
        score += palavras.count(keyword.lower()) * 5
        if ":" in texto_limpo: score += 10
        if len(texto_limpo.split()) < 45: score += 10
        resultados.append({"chunk": texto_limpo[:150] + "...", "score": score})
    
    top_chunks = sorted(resultados, key=lambda x: x["score"], reverse=True)[:3]
    return {"top_chunks_para_llm": top_chunks, "retrieval_strength": round(sum([c["score"] for c in top_chunks])/3, 2) if top_chunks else 0}

def calcular_evidence_density(artigo_html):
    texto_limpo = re.sub(r'<[^>]+>', '', artigo_html).strip()
    numeros = len(re.findall(r'\b\d+\b', texto_limpo))
    porcentagens = len(re.findall(r'\d+%', texto_limpo))
    links = artigo_html.count("href=")
    score = min((numeros * 2) + (porcentagens * 5) + (links * 10), 100)
    return {"evidence_density_score": score, "numeros_absolutos": numeros, "porcentagens": porcentagens, "links_de_referencia": links}

def calcular_information_gain(artigo_html, google_ctx):
    palavras_artigo = set(re.findall(r'\w+', re.sub(r'<[^>]+>', '', artigo_html).lower()))
    palavras_serp = set(re.findall(r'\w+', google_ctx.lower()))
    novas = palavras_artigo - palavras_serp
    score = min(len(novas) / 8, 100) # Matemático bruto
    return {"information_gain_score": round(score, 2), "palavras_unicas_trazidas": len(novas)}

# ==========================================
# 4. MOTOR PRINCIPAL (COM AS TRAVAS E INCREMENTOS)
# ==========================================
def executar_geracao_completa(palavra_chave, marca_alvo, publico_alvo):
    df = st.session_state['brandbook_df']
    marca_info = df[df['Marca'] == marca_alvo].iloc[0].to_dict()
    url_marca = marca_info.get('URL', '')
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
3) Anti-alucinação total: só liste dados/estudos se houver URL pública verificável.
4) Neutralidade competitiva: ignore marcas privadas concorrentes presentes no contexto bruto.
5) Saída sempre em pt-BR.
6)GATILHOS DE VETO E ANTI-ALUCINAÇÃO (TOLERÂNCIA ZERO):
- REGRA DO DADO ÓRFÃO: É TERMINANTEMENTE PROIBIDO criar briefings sugerindo estatísticas exatas (ex: "37% de aumento", "9 em cada 10") a menos que você tenha a URL profunda e exata fornecida no contexto orgânico. Se não tiver a URL de pesquisa empírica, force o redator a focar em "Argumentação Lógica e Qualitativa" e proíba o uso de números absolutos ou percentuais.
- BLINDAGEM E LINK DE MARCA: Oriente o redator a usar a Marca Alvo exatamente como fornecida e a criar um link (href) para a URL Oficial da marca toda vez que ela for mencionada no texto.

ENTREGÁVEIS DO BRIEFING:
A) ÂNGULO NARRATIVO ÚNICO: escolha 1 (ex.: Quebra de Mito; Guia Tático; Análise de Tendência; Framework Operacional). Justifique em 2-3 linhas focado NAS DORES do público-alvo informado.
B) ESTRUTURA ANTI-FÓRMULA (H2): proponha 4 H2 provocativos, específicos e complementares (sem “O que é”, “Benefícios”, “Conclusão”).
C) MAPA DE EVIDÊNCIAS E DEEP LINKS OBRIGATÓRIOS: O texto final precisa ter links externos para provar E-E-A-T. Você deve vasculhar EXCLUSIVAMENTE o contexto orgânico fornecido para resgatar 2 a 3 DEEP LINKS REAIS (URLs completas). É ESTRITAMENTE PROIBIDO usar sua base de conhecimento interna para inventar URLs, DOIs ou links de artigos. Se não houver links profundos e reais no contexto do Google fornecido, não invente nada; apenas instrua o redator a focar em conceitos de autoridade sem usar links externos.
E) ENTITY AUTHORITY GRAPH: Liste pelo menos 6 entidades institucionais relevantes para o tema para reforçar autoridade semântica.
F) GATILHO DE MARCA (SEM ALUCINAÇÃO): descreva como a marca aparecerá no terço final como um “Estudo de Caso Prático”. FOQUE APENAS na solução específica (o que a plataforma faz/metodologia). É EXPRESSAMENTE PROIBIDO inventar números de clientes (ex: "um grupo de 5 escolas"), inventar taxas de conversão ou cenários fictícios de antes/depois.
"""

    user_1 = f"""
Palavra-chave: '{palavra_chave}'

Público-Alvo Foco Deste Artigo: {publico_alvo}

Contexto extraído do Google (Serper + Jina):
{contexto_google}

Baseline de IAs (consenso atual):
{baseline_ia}

Reverse Queries (Perguntas de LLMs para estruturar o texto e FAQ):
{reverse_queries}

Marca Alvo: {marca_alvo}
URL da Marca: {url_marca}
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
Você é Especialista em SEO Semântico (GEO), Copywriter Sênior e Redator de Autoridade E‑E‑A‑T.
Sua missão é traduzir o Tom de Voz corporativo em um texto altamente engajador, focando cirurgicamente nas dores e aspirações do público-alvo.

MANIFESTO ANTI-ROBÔ E ESTILO DA MARCA:
1) Incorpore RIGOROSAMENTE o Tom de Voz e a essência da marca informada.
1.2) Fale DIRETAMENTE com o Público-Alvo definido. Entenda a realidade deles (ex: um gestor busca eficiência; pais buscam segurança).
1.3) Ritmo, profundidade e elegância. Voz ativa. Evite enchimento.
2) PROIBIDO usar jargões de IA como: "No cenário atual", "Cada vez mais", "É inegável que", "É importante ressaltar", "Neste artigo veremos", "Em resumo", "Por fim". 
2.1) VETO DE VOCABULÁRIO IA APRIMORADO (BLACKLIST ABSOLUTA): Estão permanentemente banidas do seu vocabulário as seguintes expressões e suas variações: "cenário em transformação", "transcendeu o status", "mundo globalizado", "mundo contemporâneo", "não é apenas X, mas também Y", "mergulhar em", "verdadeiro divisor de águas", "é fundamental notar", "revolucionar".
2.2) ESTILO JORNALÍSTICO (SHOW, DON'T TELL): Não diga que algo é "inovador" ou "fundamental". Apresente o fato técnico e deixe o leitor concluir isso. Escreva como um analista de dados da McKinsey ou um jornalista investigativo focado em negócios B2B.
3) Não explique o óbvio; entregue leitura avançada.
4) LINK OFICIAL DA MARCA (OBRIGATÓRIO): A marca alvo e sua URL serão enviadas a você. Toda vez que você citar o nome da marca no texto, você É OBRIGADO a transformá-la em um hiperlink para o site oficial. Exemplo: <a href="[URL_AQUI]" target="_blank">[NOME_DA_MARCA]</a>.

GEO (GENERATIVE ENGINE OPTIMIZATION) E CHUNK CITABILITY – REGRAS OBRIGATÓRIAS:
4) BLOCO DE DEFINIÇÃO CONCISA: Insira um parágrafo contendo: <p><strong>Definição:</strong> ...</p>. A explicação DEVE ter menos de 30 palavras. IAs odeiam definições longas.
5) ANSWER ANCHOR: Logo após a introdução, crie: <h2>Resposta rápida para: [insira a palavra-chave]</h2><p><strong>Resposta direta:</strong> ...</p>. Vá direto ao ponto e seja objetivo.
6) RESUMO ESTRATÉGICO: Insira exatamente a linha `<br>Resumo Estratégico<br>` e crie um <ul> com 3 a 5 bullet points centrais e altamente informativos.
7) FRAMEWORK E LEITURA ESCANEÁVEL (CHUNK CITABILITY COM ASSIMETRIA EXTREMA): Transforme seções em frameworks estruturados. O limite MÁXIMO de um parágrafo é de 4 linhas (aprox. 35 palavras). É OBRIGATÓRIO QUEBRAR A SIMETRIA: Intercale parágrafos "maiores" (25 a 35 palavras) com parágrafos de impacto ultracurtos formados por UMA ÚNICA FRASE (8 a 15 palavras). É TERMINANTEMENTE PROIBIDO que os parágrafos tenham o mesmo tamanho visual. LIMITAÇÃO DE LISTAS: Use no máximo 2 a 3 listas (<ul>) em todo o artigo.
8) MICRO BLOCO DE AUTORIDADE: Inclua: <p><strong>Segundo especialistas:</strong> ...</p> ancorado com dados factuais ou conceitos sólidos.

REGRAS HTML E E-E-A-T (CRÍTICAS E ABSOLUTAS):
9) Use exclusivamente HTML puro: <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <a>. Sem Markdown ou <img>.
10) INTELIGÊNCIA COMPETITIVA (VETO TOTAL A RIVAIS): É ESTRITAMENTE PROIBIDO citar o nome de qualquer empresa, produto ou sistema de ensino que seja rival comercial da Marca Alvo. Se um concorrente estiver no contexto orgânico, ignore-o. O único nome de marca que pode aparecer é o da Marca Alvo. Parceiros estratégicos/tecnológicos listados no briefing estão liberados.
11) PROTOCOLO DE RASTREABILIDADE (DEEP LINKS OBRIGATÓRIOS): É OBRIGATÓRIO incluir pelo menos 2 a 3 links externos (<a href="..." target="_blank">) ancorando afirmações ou dados. 
11.1) VETO AO LAZY LINKING: É ESTRITAMENTE PROIBIDO linkar para homepages genéricas (ex: "onu.org", "ibge.gov.br"). Todo link DEVE ser um DEEP LINK (URL completa e específica que leva direto à página do estudo/artigo citado, contendo slugs visíveis).
11.2) FONTE DOS LINKS (PROIBIDO ALUCINAR URL): Use EXCLUSIVAMENTE os deep links que foram explicitamente fornecidos no briefing. É ESTRITAMENTE PROIBIDO inventar, adivinhar ou construir URLs da sua própria memória (ex: criar links falsos da SciELO, DOIs falsos, ou caminhos fictícios de universidades). Se o briefing não te fornecer uma URL válida e real, você está liberado da obrigação de colocar links externos. Nesse caso, apenas foque na argumentação conceitual, MAS NÃO CITE o nome do estudo/instituição para não quebrar a regra 11.3.
11.3) REGRA DE OURO DOS DADOS CITADOS (ANTI-PENALIZAÇÃO): É ESTRITAMENTE PROIBIDO citar o nome de associações, institutos, pesquisas ou dados numéricos de mercado (ex: Associação Brasileira de Ensino Bilíngue, IBGE, OMS) sem ancorar a citação em um link (<a href="...">). Se você não tiver o link externo real para inserir, NÃO CITE o nome da instituição ou o dado; reescreva a frase de forma puramente conceitual. Exceção: Dados institucionais da própria Marca Alvo não precisam de link.
13) ESTUDO DE CASO REAL SEM ALUCINAÇÃO: Inserir uma seção <h2>Estudo de Caso na Prática</h2> descrevendo a tecnologia/metodologia REAL da marca. É ESTRITAMENTE PROIBIDO inventar uma historinha sobre um cliente fictício, números de "antes e depois" ou métricas falsas.
13.1) FRAMEWORK DO ESTUDO DE CASO (P.A.R.): O seu "Estudo de Caso" não pode parecer um panfleto publicitário. Ele deve ser escrito na estrutura Problema (qual dor técnica havia) > Ação da Marca (qual tecnologia exata foi usada) > Resultado (o ganho institucional listado no brandbook). Use o nome comercial da marca.
14) O primeiro caractere DEVE ser <h1> e o último DEVE ser o fechamento da última tag HTML.
15) ENTITY SATURATION: Integre naturalmente as entidades mapeadas para provar domínio do nicho.
16) VARIAÇÃO HUMANA DE RITMO (OBRIGATÓRIO E EXTREMO):
Humanos não escrevem com ritmo perfeitamente regular. Introduza variação natural drástica:
- Misture frases normais com frases de altíssimo impacto e curtas.
- É OBRIGATÓRIO que a estrutura visual do texto oscile entre blocos maiores e blocos bem curtos.
17) OBSERVAÇÃO OPERACIONAL (ANTI-TEXTO GENÉRICO):
-Sempre que explicar um conceito , inclua uma observação concreta da situação ou implementação.
-Evite abstrações vagas. Prefira descrições operacionais.
18) CONTRAPONTO ANALÍTICO (OBRIGATÓRIO EM PELO MENOS 1 H2):
Inclua pelo menos um momento do texto onde uma crença comum do setor é questionada ou refinada.
19) MICRO-ANÁLISE CAUSAL:
Sempre que apresentar um benefício ou prática, explique rapidamente o mecanismo por trás.
20) LISTAS COM CONTEXTO E LIMITE: O texto não pode parecer uma apresentação de slides. Se usar uma lista (respeitando o limite máximo de 3 no texto todo), é obrigatório introduzi-la com contexto e concluí-la com forte interpretação analítica.
21) VOZ EDITORIAL DE ANALISTA:
Escreva como um analista que observa padrões do setor educacional.
22) MICRO-SÍNTESE:
Após alguns blocos analíticos, inclua uma frase curta que consolide a ideia.
23) PROIBIDO PARÁGRAFOS SIMÉTRICOS: Verifique o texto antes de entregar. Se você notar que os parágrafos estão visualmente do mesmo tamanho, fragmente-os imediatamente. Obrigatoriamente inclua frases isoladas para criar respiros visuais profundos.
"""

    user_2 = f"""
Palavra-chave: '{palavra_chave}'

CONTEXTO TEMPORAL: Ano de {ano_atual}. Não projete o futuro sem evidência.
O QUE A CONCORRÊNCIA DIZ HOJE (Use APENAS para fatos e conceitos, NUNCA cite os nomes das empresas concorrentes que estão aqui):
{contexto_google}

SEU BRIEFING (siga à risca o ângulo e integre o Entity Authority Graph):
{analise}

DIRECIONAMENTO DE COPYWRITING E MARCA:
- Público-Alvo Deste Texto (Foque toda a narrativa neles): {publico_alvo}
- Tom de Voz Exigido: {marca_info['TomDeVoz']}
- Marca Alvo: {marca_alvo}
- URL da Marca: {url_marca} (OBRIGATÓRIO: Linkar a marca para esta URL sempre que citada).
- Posicionamento: {marca_info['Posicionamento']}
- Territórios: {marca_info['Territorios']}
- Diretrizes OBRIGATÓRIAS: {marca_info.get('RegrasPositivas', '')}
- O que NÃO fazer: {marca_info['RegrasNegativas']}

<checklist_de_seguranca_obrigatorio>
1. A sua "Resposta rápida" está bem no início do texto e é super objetiva?
2. A sua "Definição" tem menos de 30 palavras? (Se tiver mais, reduza agora).
3. ASSIMETRIA VISUAL: Você quebrou os parágrafos corretamente? Há frases isoladas servindo como parágrafos curtos misturadas com parágrafos de 3 linhas? Se o texto estiver um "bloco de tijolo" igual, altere agora.
4. Você usou todas as entidades obrigatórias mapeadas no briefing?
5. VETO A RIVAIS: Verifique seu texto. Você citou o nome de ALGUMA OUTRA EMPRESA/SISTEMA que não seja a {marca_alvo}? (Ex: Edify, SAS, Bernoulli, etc). SE SIM, APAGUE E FOQUE NO CONCEITO.
6. O seu "Estudo de Caso" foca na tecnologia/metodologia real da {marca_alvo}? Verifique se você inventou historinha de cliente fictício ou números falsos. Se sim, APAGUE ISSO.
7. CHECK DE DEEP LINKS: Você incluiu pelo menos 2 links externos? Olhe para as URLs dentro do <a href>. Elas são DEEP LINKS reais (com caminho completo/slug, ex: /artigos/nome-do-estudo), ou você fez lazy linking para uma página inicial (ex: .com.br/)? Se usou página inicial, substitua IMEDIATAMENTE por um deep link específico de um relatório ou apague o link.
8. Você garantiu que TODAS as menções à {marca_alvo} contêm o link <a href="{url_marca}">?
9. Você checou a existência de dados numéricos no briefing? Se não houver, garanta que sua abordagem é conceitual e livre de alucinações matemáticas.
10. AUDITORIA DE FONTES (TOLERÂNCIA ZERO): Você citou alguma Associação, Instituto, Estudo, Pesquisa, Ministério (ex: MEC) ou Órgão Governamental no texto? Se sim, a tag de link (<a href="...">) está EXATAMENTE junto ao nome deles? Se estiver sem link, APAGUE a frase inteira imediatamente. Não tente consertar, apenas apague a afirmação.
</checklist_de_seguranca_obrigatorio>

Escreva o ARTIGO FINAL em HTML conforme as regras GEO, preservando exatamente os marcadores:
<br>Resumo Estratégico<br>
<br>Perguntas Frequentes<br>

ATENÇÃO: Pare de escrever IMEDIATAMENTE após a última tag HTML. NUNCA gere auto-avaliações, comentários ou textos que comecem com "AI:".
"""

    artigo_html = chamar_llm(system_2, user_2, model="anthropic/claude-3.7-sonnet", temperature=0.45)
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
4) 'dicas_imagens': exatamente 2 strings em inglês, MUITO CURTAS E SIMPLES (máximo 1 a 2 palavras, ex.: "classroom", "students", "school"). É ESTRITAMENTE PROIBIDO gerar frases longas. Termos longos quebram a busca da API.
5) 'schema_faq': JSON-LD **FAQPage** com @context "[https://schema.org](https://schema.org)", @type "FAQPage" e mainEntity como lista de objetos Question/acceptedAnswer.
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
                    # URL LIMPA E DIRETA
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
                    # FALLBACK LIMPO E DIRETA
                    clean_termo = str(termo).replace("'", "").replace('"', '').strip()
                    p_codificado = urllib.parse.quote(clean_termo)
                    base_poll = "https://image.pollinations.ai/prompt/"
                    img_html_pronta = f'<img src="{base_poll}{p_codificado}?width=1024&height=512&nologo=true&model=flux" alt="{clean_termo}" style="width:100%; border-radius:8px;" loading="lazy" decoding="async" />'
                    
                if img_html_pronta:
                    alvo_replace = '<br>Resumo Estratégico<br>' if i == 0 else '<br>Perguntas Frequentes<br>'
                    artigo_html = artigo_html.replace(alvo_replace, f'{img_html_pronta}\n{alvo_replace}', 1)
    except Exception as e:
        st.error(f"Erro ao injetar imagem: {e}") # Mudei para st.error para você ver se falhar

    # CHAMADAS INCREMENTAIS PÓS-REDAÇÃO (GEO PIPELINE COMPLETO)
    st.write("📊 Fase 4: Calculando Originalidade, Citabilidade GEO e Cluster...")
    score_originalidade = avaliar_originalidade(artigo_html, contexto_google)
    citabilidade = prever_citabilidade_llm(artigo_html, palavra_chave)
    cluster = gerar_cluster(palavra_chave)
    citation_score = calcular_citation_score(artigo_html)

    st.write("🧪 Fase 5: Calculando Matrizes RAG e Entity Coverage...")
    entity_coverage = calcular_entity_coverage(artigo_html, entity_gap)
    
    geo_score = calcular_geo_score_matematico(citation_score, score_originalidade, citabilidade, entity_coverage)
    chunk_citability = avaliar_chunk_citability(artigo_html)
    answer_first = avaliar_answer_first(artigo_html)
    rag_chunks = simular_rag_chunks(artigo_html, palavra_chave)
    evidence_density = calcular_evidence_density(artigo_html)
    information_gain = calcular_information_gain(artigo_html, contexto_google)

    st.write("🔬 Fase 6: Simulação de RAG e Citation Hijacking (Motores LLM)...")
    retrieval_simulation = simular_llm_retrieval(palavra_chave, artigo_html)
    hijacking_risk = detectar_citation_hijacking(artigo_html)
    ai_simulation = simular_resposta_ai(palavra_chave, artigo_html)

    return (
        artigo_html, dicas_json, contexto_google, baseline_ia, entity_gap, 
        score_originalidade, citabilidade, cluster, reverse_queries, 
        citation_score, entity_coverage, geo_score, retrieval_simulation, 
        hijacking_risk, ai_simulation, chunk_citability, answer_first, 
        rag_chunks, evidence_density, information_gain
    )

def publicar_wp(titulo, conteudo_html, meta_dict, wp_url, wp_user, wp_pwd):
    import base64
    from urllib.parse import urlparse
    
    seo_title = meta_dict.get("title", titulo)
    meta_desc = meta_dict.get("meta_description", "")
    
    # 🚨 REMOVIDA a injeção da tag <script> no conteúdo. 
    # Firewalls (como AWS WAF do CloudFront) bloqueiam QUALQUER requisição POST 
    # via API que contenha a palavra "<script>" por acharem que é ataque hacker (XSS).
    
    payload = {
        "title": titulo,
        # Substitua a variável conteudo_html por uma string simples de teste:
        "content": "Este é um teste de API sem nenhuma tag HTML para verificar o firewall.",
        "status": "draft",
        "meta": {
            "_yoast_wpseo_title": seo_title,
            "_yoast_wpseo_metadesc": meta_desc
        }
    }
    
    # 1. Limpa espaços da senha (o WP gera com espaços, mas o base64 prefere sem)
    wp_pwd_clean = wp_pwd.replace(" ", "").strip()
    credenciais = f"{wp_user}:{wp_pwd_clean}"
    token_auth = base64.b64encode(credenciais.encode('utf-8')).decode('utf-8')
    
    # 2. Extrai o domínio base para o CORS
    parsed_url = urlparse(wp_url)
    dominio_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # 3. Cabeçalhos de Navegador Legítimo
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Authorization': f'Basic {token_auth}',
        'Origin': dominio_base,
        'Referer': f"{dominio_base}/",
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    try:
        response = requests.post(wp_url, json=payload, headers=headers, timeout=30)
        return response
    except Exception as e:
        class ErrorResponse:
            status_code = 500
            text = f"Erro interno de conexão: {str(e)}"
            def json(self): return {}
        return ErrorResponse()

# ==========================================
# 5. INTERFACE PRINCIPAL
# ==========================================
tab1, tab2, tab3 = st.tabs(["✍️ Gerador de Artigos", "📚 Brandbook", "🔍 Monitor de GEO"])

with tab2:
    st.markdown("### Edite as regras, marcas e diretrizes:")
    st.session_state['brandbook_df'] = st.data_editor(st.session_state['brandbook_df'], num_rows="dynamic", use_container_width=True)
    st.info("💡 Dica: Adicione regras específicas na coluna 'RegrasPositivas'.")

with tab1:
    # 1. CRIANDO A "CAIXA" NO TOPO ANTES DAS COLUNAS
    caixa_topo = st.container()
    st.markdown("<br>", unsafe_allow_html=True) # Dá um pequeno respiro visual
    
    col1, col2 = st.columns([1, 2])
    with col1:
        marca_selecionada = st.selectbox("Selecione a Marca", st.session_state['brandbook_df']['Marca'].tolist())
        # --- EXTRAÇÃO DINÂMICA DE PÚBLICO-ALVO ---
        try:
            publicos_da_marca = st.session_state['brandbook_df'][st.session_state['brandbook_df']['Marca'] == marca_selecionada]['PublicoAlvo'].iloc[0]
            
            # AGORA SIM: Cortando EXCLUSIVAMENTE pelo ponto final
            opcoes_publico = [p.strip() for p in publicos_da_marca.split('.') if p.strip()]
            
            # Prevenção: Se a marca não tiver público cadastrado, joga o "Geral"
            if not opcoes_publico:
                opcoes_publico = ["Público Geral (Baseado na Keyword)"]
            else:
                # Adiciona o "Público Geral" logo abaixo dos públicos da marca
                opcoes_publico.append("Público Geral (Baseado na Keyword)")
                
        except Exception:
            # Fallback de segurança se der erro
            opcoes_publico = ["Público Geral (Baseado na Keyword)"]
            
        # A opção de digitar sempre vai para o final da fila
        opcoes_publico.append("✍️ Digitar outro público (Personalizado)...")
        
        # Selectbox para o usuário
        escolha_publico = st.selectbox("🎯 Para quem estamos escrevendo?", opcoes_publico, help="Escolha uma persona do Brandbook ou selecione 'Digitar outro' para inserir uma nova.")
        
        # Se o usuário quiser digitar, abre o campo de texto
        if escolha_publico == "✍️ Digitar outro público (Personalizado)...":
            publico_selecionado = st.text_input("Qual é o público-alvo?", placeholder="Ex: pais de alunos, estudantes do ensino médio, professores...")
        else:
            publico_selecionado = escolha_publico
        # ----------------------------------------------
        palavra_chave_input = st.text_area("Palavra-Chave / Briefing", placeholder="Ex: metodologia bilíngue nas escolas")
        gerar_btn = st.button("🚀 Gerar Artigo em HTML", use_container_width=True, type="primary")
        st.markdown("---")
        
        wp_url_marca, wp_user_marca, wp_pwd_marca = obter_credenciais_wp(marca_selecionada)
        WP_READY = bool(wp_url_marca and wp_user_marca and wp_pwd_marca)

        if not WP_READY:
            st.warning(f"🔌 Integração WordPress inativa para a marca {marca_selecionada}. Faltam as credenciais no arquivo Secrets.")
        else:
            st.success(f"🔌 Conectado ao WordPress da marca: {marca_selecionada} (Pronto para Yoast).")

    # 2. DIRECIONANDO O CARREGAMENTO PARA A CAIXA DO TOPO
    if gerar_btn:
        if not TOKEN:
            st.error("⚠️ Erro: A chave OPENROUTER_KEY não foi encontrada nos Secrets.")
        elif not palavra_chave_input:
            st.warning("⚠️ Por favor, digite uma palavra-chave.")
        else:
            with caixa_topo:
                with st.status("🤖 Processando Motor GEO v7.0...", expanded=True) as status:
                    try:
                        (
                            artigo_html, dicas_json, google_data, ia_data, entity_gap, 
                            score_originalidade, citabilidade, cluster, reverse_queries, 
                            citation_score, entity_coverage, geo_score, retrieval_simulation, 
                            hijacking_risk, ai_simulation, chunk_citability, answer_first, 
                            rag_chunks, evidence_density, information_gain
                        ) = executar_geracao_completa(palavra_chave_input, marca_selecionada, publico_selecionado)
                        
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
                        st.session_state['chunk_citability'] = chunk_citability
                        st.session_state['answer_first'] = answer_first
                        st.session_state['rag_chunks'] = rag_chunks
                        st.session_state['evidence_density'] = evidence_density
                        st.session_state['information_gain'] = information_gain
                        
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

            # NOVAS ABAS DE EXPANSÃO MATEMÁTICAS E ESTRUTURAIS
            with st.expander("🚀 GEO Score Global", expanded=True):
                st.caption("ℹ️ **O que é isso:** Uma nota matemática de 0 a 100 que pondera a estrutura do texto, a densidade de palavras-chave (entidades), a originalidade e a clareza. É o termômetro final de qualidade.")
                st.json(st.session_state.get('geo_score', '{}'))
                
            with st.expander("📑 Chunk Citability & Answer-First (Estrutura)", expanded=False):
                st.caption("ℹ️ **O que é isso:** Mede se o seu texto tem o formato que as IAs amam ler (parágrafos curtos e listas) e se você entregou a 'Resposta Direta' logo no início do texto (Answer-First).")
                st.markdown("**Chunk Citability (Formatação legível para IA):**")
                st.json(st.session_state.get('chunk_citability', '{}'))
                st.markdown("**Answer-First Score (Resposta Antecipada):**")
                st.json(st.session_state.get('answer_first', '{}'))

            with st.expander("📊 Evidence Density & Info Gain (E-E-A-T)", expanded=False):
                st.caption("ℹ️ **O que é isso:** Avalia o Ganho de Informação (quantas palavras/ideias úteis novas você trouxe em relação ao Google) e a densidade de evidências reais (números, estatísticas e links).")
                st.markdown("**Densidade de Evidências (Números e Links):**")
                st.json(st.session_state.get('evidence_density', '{}'))
                st.markdown("**Information Gain (Palavras Novas vs Google TOP 3):**")
                st.json(st.session_state.get('information_gain', '{}'))

            with st.expander("🧠 RAG Chunk Ranking (Simulador Matemático)", expanded=False):
                st.caption("ℹ️ **O que é isso:** Simula matematicamente quais parágrafos (chunks) do seu texto uma IA como o ChatGPT 'pescaria' no banco de dados dela para usar como fonte na hora de responder um usuário.")
                st.json(st.session_state.get('rag_chunks', '{}'))
                
            with st.expander("🧠 Entity Coverage (Topical Authority)", expanded=False):
                st.caption("ℹ️ **O que é isso:** Mostra a porcentagem de jargões, conceitos e termos técnicos essenciais (Entidades) que você incluiu no texto comparado ao que os concorrentes estão usando.")
                st.json(st.session_state.get('entity_coverage', '{}'))
                
            with st.expander("🔎 LLM Retrieval Simulation", expanded=False):
                st.caption("ℹ️ **O que é isso:** Uma simulação semântica onde a própria IA julga se o seu conteúdo é claro, denso e neutro o suficiente para ser citado como uma 'Fonte Oficial'.")
                st.json(st.session_state.get('retrieval_simulation', '{}'))
                
            with st.expander("⚠️ AI Citation Hijacking Risk", expanded=False):
                st.caption("ℹ️ **O que é isso:** Avalia se o seu texto 'dá voltas demais' para explicar algo, correndo o risco de uma IA preferir citar um concorrente seu que tenha sido mais direto e didático.")
                st.json(st.session_state.get('hijacking_risk', '{}'))
                
            with st.expander("🤖 AI Search Result Simulator", expanded=False):
                st.caption("ℹ️ **O que é isso:** Mostra exatamente como seria a resposta final gerada na tela do ChatGPT ou Perplexity se eles usassem o seu artigo como única fonte de verdade.")
                st.json(st.session_state.get('ai_simulation', '{}'))

            with st.expander("🔄 Reverse Query Engine (Search Intent)", expanded=False):
                st.caption("ℹ️ **O que é isso:** Engenharia reversa de buscas. Mostra o que os usuários perguntam (forma leiga) e quais as dúvidas profundas que a IA tenta resolver nos bastidores para montar respostas.")
                st.json(st.session_state.get('reverse_queries', '{}'))
                
            with st.expander("🧩 Entity Gap Analysis (Oportunidades Semânticas)", expanded=False):
                st.caption("ℹ️ **O que é isso:** Lista de palavras e conceitos que o motor detectou nos concorrentes orgânicos e exigiu que o nosso redator incluísse para superar o mercado.")
                st.markdown(st.session_state.get('entity_gap', '⚠️ Dados não encontrados.'))
            
            with st.expander("🧠 Previsão de Citabilidade por IAs (LLMs)", expanded=False):
                st.caption("ℹ️ **O que é isso:** O motivo narrativo pelo qual a IA escolheu (ou não) o seu texto como uma fonte forte e confiável.")
                st.markdown(st.session_state.get('citabilidade', '⚠️ Dados não encontrados.'))
                
            with st.expander("🥇 Originalidade do Artigo (vs Concorrentes)", expanded=False):
                st.caption("ℹ️ **O que é isso:** Parecer textual detalhando quais ângulos únicos e abordagens frescas o seu texto trouxe que não existem no Top 3 do Google atualmente.")
                st.markdown(st.session_state.get('score_originalidade', '⚠️ Dados não encontrados.'))
                
            with st.expander("🗺️ Sugestão de Content Cluster (Topical Authority)", expanded=False):
                st.caption("ℹ️ **O que é isso:** Sugestão de 8 pautas satélites para você escrever no futuro, lincar para este artigo e criar uma 'teia de autoridade' no seu blog.")
                st.markdown(st.session_state.get('cluster', '⚠️ Dados não encontrados.'))

            with st.expander("🕵️‍♂️ Auditoria Bruta: O que ranqueia hoje (Google & IA)?", expanded=False):
                st.caption("ℹ️ **O que é isso:** O texto cru (sem filtro) que o nosso motor leu dos seus concorrentes no Google e nos consensos de Inteligência Artificial para basear a escrita.")
                st.markdown("**Google (Serper + Jina Reader):**")
                st.info(st.session_state.get('google_ctx', 'Sem dados.'))
                st.markdown("**IA (Perplexity Baseline):**")
                st.info(st.session_state.get('ia_ctx', 'Sem dados.'))

            with st.expander("👁️ Pré-visualização do Artigo (Visual)", expanded=False):
                st.markdown(st.session_state['art_gerado'], unsafe_allow_html=True)
                
            st.markdown("---")
            st.subheader("📋 Copie seu HTML Pronto")
            st.info("Passe o mouse no canto superior direito do bloco abaixo e clique no ícone de copiar 📋.")
            
            # Text area trocado por st.code para habilitar o ícone de cópia nativo!
            st.code(st.session_state['art_gerado'], language="html")
            st.markdown("---")

            # NOVO LUGAR DO BOTÃO DO WORDPRESS (Fora do expander evita o bug de clique do Streamlit)
            wp_url_atual, wp_user_atual, wp_pwd_atual = obter_credenciais_wp(st.session_state['marca_atual'])
            if wp_url_atual and wp_user_atual and wp_pwd_atual:
                st.subheader("🌐 Publicação Direta")
                if st.button(f"📤 Enviar Rascunho para WordPress ({st.session_state['marca_atual']})", type="primary", use_container_width=True):
                    with st.spinner("Enviando via API para o WordPress... Isso pode levar alguns segundos."):
                        res = publicar_wp(meta.get("title", st.session_state['keyword_atual']), st.session_state['art_gerado'], meta, wp_url_atual, wp_user_atual, wp_pwd_atual)
                        if res.status_code == 201:
                            st.success(f"✅ Rascunho criado com sucesso! Link: {res.json().get('link')}")
                        else:
                            st.error(f"❌ Falha ao enviar (Erro HTTP {res.status_code}): {res.text}")

            with st.expander("🛠️ Metadados SEO & Schema", expanded=True):
                st.json(meta)

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
            with st.spinner("Executando Raio-X Matemático e Auditoria Semântica (GPT-4o)..."):
                
                # ==========================================
                # 1. EXECUTA A MATEMÁTICA NO TEXTO INSERIDO
                # ==========================================
                try:
                    math_chunk = avaliar_chunk_citability(txt_auditoria)
                    math_evidence = calcular_evidence_density(txt_auditoria)
                    math_answer = avaliar_answer_first(txt_auditoria)
                except Exception as e:
                    math_chunk, math_evidence, math_answer = {}, {}, {}
                    print(f"Erro nas métricas matemáticas do monitor: {e}")

                # ==========================================
                # 2. AUDITORIA SEMÂNTICA (GPT-4o)
                # ==========================================
                sys_audit = """Você é um Auditor Sênior de SEO e E-E-A-T do Google, além de Especialista em Engenharia de Prompt. Seu padrão é altíssimo, mas baseado em lógica estrutural e não em achismos.
                
                REGRAS CRÍTICAS DE AUDITORIA (VETOS ABSOLUTOS E PENALIZAÇÕES):
                1. AVALIAÇÃO DE CONCORRENTES VS. PARCEIROS: O texto é proibido de mencionar rivais comerciais da marca alvo. Tecnologias de apoio ou certificadoras da marca SÃO PARCEIROS.
                2. RASTREABILIDADE DE DADOS E LINKS: Se o texto apresentar dados DE MERCADO ou citar PESQUISAS e INSTITUIÇÕES (ex: British Council, USP), é obrigatório ter um link referencial real (<a href>). Sem link, REDUZA A NOTA. EXCEÇÃO ABSOLUTA: Dados institucionais da própria Marca Alvo (ex: % de fidelização, número de escolas) SÃO PROPRIETÁRIOS e não levam link.
                3. VALIDAÇÃO CONCEITUAL: Se o texto for puramente conceitual, NÃO requer links.
                4. TOM DA MARCA ALVO: A marca deve ser mencionada com tom de estudo de caso.
                5. IMAGENS IGNORADAS: IGNORE COMPLETAMENTE AS TAGS HTML DE IMAGEM (<img...>) NA SUA AVALIAÇÃO.
                6. LIBERDADE TEXTUAL (SEM NITPICKING): É expressamente proibido penalizar o texto, criar críticas ou reduzir pontos por causa de jargões corporativos, clichês ou expressões como "mundo globalizado", "cenário atual", "em resumo" ou "transcendeu". Foque exclusivamente na estrutura E-E-A-T e nos dados, e deixe o estilo literário livre.
                7. LINKAGEM DA MARCA (FOCO NO HTML): Toda vez que a Marca Alvo for mencionada no texto, ela deve obrigatoriamente conter um link (href) para sua URL oficial. Penalize se a marca for citada sem o link para o site.
                
                DIRETRIZ DE PONTUAÇÃO E FEEDBACK (A REGRA DOS 100 PONTOS):
                - Se você NÃO encontrar nenhuma quebra das regras acima (ou seja, se os arrays 'critica' e 'melhoria' estiverem vazios), O SCORE DEVE SER ESTRITAMENTE 100.
                - É EXPRESSAMENTE PROIBIDO subtrair pontos (ex: dar 90, 85) baseando-se em avaliações estéticas subjetivas ou vocabulário. Se tirou ponto, a justificativa TÊM que estar no array 'critica' baseada nas regras de 1 a 7.
                
                VOCÊ DEVE RETORNAR EXCLUSIVAMENTE UM OBJETO JSON COM A SEGUINTE ESTRUTURA:
                {
                  "score": "Um número inteiro de 0 a 100",
                  "veredito": "Resumo de autoridade.",
                  "critica": ["Ponto fraco 1", "Ponto fraco 2"],
                  "melhoria": ["Como arrumar 1"],
                  "sugestoes_dev": ["Insight para o prompt do Redator"]
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
                    
                    # EXIBIÇÃO: Métricas Matemáticas vs Semânticas
                    col_math1, col_math2, col_math3 = st.columns(3)
                    with col_math1:
                        st.metric("📏 Chunk Citability (Estrutura)", f"{math_chunk.get('chunk_citability_score', 0)}/100", help="Mede a facilidade de IAs lerem o texto (listas e parágrafos curtos).")
                    with col_math2:
                        st.metric("⚡ Answer First", f"{math_answer.get('answer_first_score', 0)}/100", help="Verifica se a resposta direta está no topo do texto.")
                    with col_math3:
                        st.metric("🔗 Evidence Density", f"{math_evidence.get('evidence_density_score', 0)}/100", help="Volume de números e links no texto.")

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    kpi1, kpi2 = st.columns([1, 3])
                    with kpi1:
                        cor_delta = "normal" if score >= 80 else "inverse"
                        st.metric("🎯 LLM Audit Score", f"{score}/100", delta=f"{score - 100} do ideal", delta_color=cor_delta, help="Nota dada pelo GPT-4o baseada nas regras de E-E-A-T.")
                    
                    with kpi2:
                        st.markdown("**Progresso E-E-A-T (Qualitativo):**")
                        st.progress(score / 100)
                        
                        if score == 100:
                            st.success(f"🏆 **Veredito de Autoridade:** {dados_audit.get('veredito')}")
                        elif score >= 80:
                            st.info(f"✅ **Veredito de Autoridade:** {dados_audit.get('veredito')}")
                        else:
                            st.warning(f"⚠️ **Veredito de Autoridade:** {dados_audit.get('veredito')}")

                    st.markdown("#### Análise Qualitativa (GPT-4o)")
                    col_critica, col_melhoria = st.columns(2)
                    
                    with col_critica:
                        with st.expander("🚨 Críticas Técnicas ao Texto", expanded=True):
                            criticas = dados_audit.get('critica', [])
                            if isinstance(criticas, list) and criticas:
                                for c in criticas:
                                    st.markdown(f"- {c}")
                            else:
                                st.markdown("✅ **Nenhuma crítica identificada. O texto passou ileso!**")
                                
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
