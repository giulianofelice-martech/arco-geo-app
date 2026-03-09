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
        {"Marca": "@internationalschool", "Posicionamento": "O programa bilíngue mais premiado do Brasil. Pioneira em bilinguismo no país. Prover soluções educacionais consistentes e inovadoras. Transformar vidas por meio da educação bilíngue. Empoderar a comunidade escolar para desenvolver o aluno como ser integral.", "Territorios": "Bilinguismo, educação, integral, viagens", "TomDeVoz": "Especialista, inovador, inspirador, prático.", "PublicoAlvo": "Gestores, diretores e coordenadores de escolas (B2B)  pais e famílias (Foco B2C)", "RegrasNegativas": "Não usar termos genéricos sem contexto, não soar arrogante ou sabe tudo, não inferir que quem aprende inglês é superior ou melhor, não citar palavras em inglês sem tradução entre parênteses depois. Não focar o discurso somente nos pais (lembrar sempre da figura da escola).", "RegrasPositivas": "Sempre trazer dados para embasar afirmações vindos de fontes seguras e confiáveis, sempre citar e linkar a fonte dos dados, preferir fontes de pesquisas, governos e instituições de renome. Podemos usar pesquisas nacionais ou internacionais. Sempre usar construção gramatical focada em clareza : iniciar parágrafos com frases de afirmação, não com conectivos. Sempre conectar com a importância de aprender inglês indo além da gramática: focar na importãncia de aprender com contexto."},
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
except:
    TOKEN = None 

# Configurações do WordPress (Evita erro se não existirem)
WP_URL = st.secrets.get("WP_URL", "")
WP_USER = st.secrets.get("WP_USER", "")
WP_PWD = st.secrets.get("WP_APP_PASSWORD", "")
WP_READY = bool(WP_URL and WP_USER and WP_PWD)

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

def executar_geracao_completa(palavra_chave, marca_alvo):
    df = st.session_state['brandbook_df']
    marca_info = df[df['Marca'] == marca_alvo].iloc[0].to_dict()
    
    # FASE 1: ANÁLISE SEMÂNTICA (GPT-4o)
    system_1 = "Você é um Estrategista Sênior de GEO. A regra de ouro é: NUNCA cite concorrentes. Para vencermos referências comparativas, crie a 'Autoridade Definitiva' listando critérios técnicos rigorosos."
    user_1 = f"Palavra-chave: '{palavra_chave}'\n\nContexto da marca:\n- Posicionamento: {marca_info['Posicionamento']}\n- Público: {marca_info['PublicoAlvo']}\n\n1. O ÂNGULO DE AUTORIDADE: Como abordar o tema 80% educativo e 20% marca?\n2. OS CRITÉRIOS DE OURO: Liste 5 critérios essenciais.\n3. ESTRUTURA DE DADOS: Quais tabelas criar?\n4. ENTIDADES SEMÂNTICAS: Liste 10 termos técnicos que OBRIGATORIAMENTE devem aparecer."
    analise = chamar_llm(system_1, user_1, model="openai/gpt-4o", temperature=0.4)
    
    # FASE 2: REDAÇÃO DO ARTIGO EM HTML (CLAUDE 3.7 SONNET)
    system_2 = """Você é um Redator Sênior especialista em SEO e Algoritmos de IA (GEO).
    
    REGRAS OBRIGATÓRIAS DE FORMATO E ESTRUTURA:
    1. FORMATO: Retorne o artigo EXCLUSIVAMENTE em HTML puro (use <h2>, <h3>, <p>, <ul>, <li>, <strong>, <table>). Não use <html>, <head> ou <body>. Não use Markdown.
    2. ZERO CONCORRENTES: Nunca cite sistemas concorrentes.
    3. CAVALO DE TROIA: Texto imparcial no início, revelando a marca como padrão ouro na conclusão.
    4. RESUMO RÁPIDO (TL;DR): Crie um <h2> chamado "Resumo Rápido" logo após a introdução com uma lista <ul> de 3 itens.
    5. FAQ FÍSICO: Imediatamente antes da conclusão, crie um <h2> chamado "Perguntas Frequentes". Inclua 3 perguntas usando <h3> e responda em <p>.
    6. TOM E MARCA: Siga o tom exigido. Não use "@" no nome da marca no texto."""
    
    user_2 = f"Palavra-chave: '{palavra_chave}'\nDiretrizes da Estratégia:\n{analise}\n\nMarca ({marca_alvo}):\n- Posicionamento: {marca_info['Posicionamento']}\n- Tom: {marca_info['TomDeVoz']}\n- Regras Positivas (O que FAZER): {marca_info.get('RegrasPositivas', '')}\n- Regras Negativas (O que NÃO FAZER): {marca_info['RegrasNegativas']}\n\nRetorne apenas o código HTML do artigo."
    artigo_html = chamar_llm(system_2, user_2, model="anthropic/claude-3.7-sonnet", temperature=0.3)
    
    # FASE 3: METADADOS E SCHEMA (CLAUDE 3.7 SONNET)
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
    
    return artigo_html, dicas_json

def publicar_wp(titulo, conteudo_html):
    payload = {
        "title": titulo,
        "content": conteudo_html,
        "status": "draft" # Publica como rascunho
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
    st.info("💡 Dica: Adicione regras específicas na nova coluna 'RegrasPositivas'.")

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        marca_selecionada = st.selectbox("Selecione a Marca", st.session_state['brandbook_df']['Marca'].tolist())
        palavra_chave_input = st.text_area("Palavra-Chave / Briefing", placeholder="Ex: metodologia bilíngue nas escolas")
        gerar_btn = st.button("🚀 Gerar Artigo em HTML", use_container_width=True, type="primary")
        
        st.markdown("---")
        if not WP_READY:
            st.warning("🔌 Integração WordPress inativa. Faltam as credenciais no menu Secrets (WP_URL, WP_USER, WP_APP_PASSWORD). O texto será gerado normalmente para você copiar.")
        else:
            st.success("🔌 Conectado ao WordPress. Você poderá enviar como Rascunho.")

    if gerar_btn:
        if not TOKEN: 
            st.error("⚠️ Erro: A chave OPENROUTER_KEY não foi encontrada nos Secrets.")
        elif not palavra_chave_input:
            st.warning("⚠️ Por favor, digite uma palavra-chave.")
        else:
            with st.status("🤖 Processando Motor GEO v3...", expanded=True) as status:
                st.write("🔍 Fase 1: Análise Semântica (GPT-4o)...")
                try:
                    artigo_html, dicas_json = executar_geracao_completa(palavra_chave_input, marca_selecionada)
                    
                    st.write("✍️ Fase 2: Redigindo em HTML (Claude 3.7 Sonnet)...")
                    st.write("🛠️ Fase 3: Extraindo JSON e Metadados...")
                    status.update(label="✅ Artigo gerado com sucesso!", state="complete", expanded=False)
                    
                    with col2:
                        st.success("Tudo pronto! Seu código HTML está preparado para o WordPress.")
                        
                        # Converte string JSON da Fase 3 para dicionário
                        try:
                            meta = json.loads(dicas_json.strip('`').replace('json\n',''))
                            st.subheader(meta.get("title", "Artigo Gerado"))
                        except:
                            meta = {"title": "Artigo Gerado via Motor GEO"}
                        
                        # Exibe visualização do HTML
                        with st.expander("👁️ Pré-visualização do HTML", expanded=False):
                            st.markdown(artigo_html, unsafe_allow_html=True)
                        
                        # Exibe Código Fonte Copiável
                        st.markdown("### 📋 Código HTML (Copie e cole no WordPress):")
                        st.code(artigo_html, language="html")
                        
                        # Exibe Metadados
                        with st.expander("🛠️ Metadados SEO & Schema", expanded=True):
                            st.json(meta)
                        
                        # Botão de Envio para WordPress
                        if WP_READY:
                            if st.button("📤 Enviar Rascunho para WordPress"):
                                with st.spinner("Enviando via API..."):
                                    res = publicar_wp(meta.get("title", palavra_chave_input), artigo_html)
                                    if res.status_code == 201:
                                        st.success(f"✅ Rascunho criado no WP! Link: {res.json().get('link')}")
                                    else:
                                        st.error(f"❌ Falha ao enviar: {res.text}")
                                        
                except Exception as e:
                    status.update(label="❌ Erro durante a geração", state="error")
                    st.error(f"Erro: {e}")
