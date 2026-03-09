import streamlit as st
import pandas as pd
from openai import OpenAI
import time

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Arco Martech | Gerador GEO", page_icon="🚀", layout="wide")

st.title("🤖 Arco Martech | Motor GEO (Otimização para IAs)")
st.markdown("Crie artigos técnicos de alta performance para dominar as respostas de LLMs (ChatGPT, Gemini, Copilot) e buscas no Google.")

# ==========================================
# 2. BRANDBOOK EMBUTIDO (EDITÁVEL NA TELA)
# ==========================================
if 'brandbook_df' not in st.session_state:
    dados_iniciais = [
        {"Marca": "@saseducacao", "Posicionamento": "Marca visionária, líder em aprovação (Enem/Vestibulares). Entrega de valor em tecnologia e serviço.", "Territorios": "Vestibulares, Tecnologia, Inovação, Olimpíadas educacionais, Pesquisas", "TomDeVoz": "Acadêmico, inovador, especialista e inspirador.", "PublicoAlvo": "Estudantes do ensino médio, vestibulandos e pais. (Foco B2C)", "RegrasNegativas": "Não usar tom professoral antiquado, não prometer aprovação sem esforço, nunca citar outros cursinhos ou sistemas concorrentes."},
        {"Marca": "@plataformacoc", "Posicionamento": "Marca aprovadora que evolui a escola pedagogicamente com a melhor consultoria do mercado.", "Territorios": "Vestibulares, Esportes, Gestão escolar", "TomDeVoz": "Consultivo, parceiro, dinâmico e focado em evolução.", "PublicoAlvo": "Mantenedores, diretores de escola e coordenadores pedagógicos. (Foco B2B)", "RegrasNegativas": "Não focar o discurso apenas no aluno, não usar jargões excessivamente complexos."},
        {"Marca": "@isaaceducacao", "Posicionamento": "Maior solução financeira e de gestão para a educação. Escolas crescem com isaac.", "Territorios": "Gestão financeira, Inovação", "TomDeVoz": "Corporativo, direto, analítico e focado em resultados.", "PublicoAlvo": "Diretores financeiros, mantenedores e donos de escolas. (Foco B2B)", "RegrasNegativas": "Não parecer banco engessado, não usar linguagem infantilizada, não citar concorrentes."},
        {"Marca": "@geekieeducacao", "Posicionamento": "Metodologia inovadora (aluno no centro), fácil de implementar.", "Territorios": "Inovação, IA/Personalização, Metodologias ativas", "TomDeVoz": "Inovador, moderno, ágil e centrado no protagonismo do aluno.", "PublicoAlvo": "Diretores de inovação e escolas modernas. (B2B)", "RegrasNegativas": "Não parecer sistema engessado, não usar linguagem punitiva, não focar em decoreba."},
        {"Marca": "@sistemapositivodeensino", "Posicionamento": "Formação integral, humana e próxima. A maior rede do Brasil.", "Territorios": "Formação integral, Inclusão, Tradição", "TomDeVoz": "Acolhedor, tradicional, humano, confiável.", "PublicoAlvo": "Famílias e diretores de escolas tradicionais. (B2B e B2C)", "RegrasNegativas": "Não parecer frio, não usar jargões técnicos sem contexto acolhedor."},
        {"Marca": "@saedigital", "Posicionamento": "Melhor integração físico/digital, hiperatualizada.", "Territorios": "Tecnologia, Inovação Digital", "TomDeVoz": "Prático, tecnológico, dinâmico e acessível.", "PublicoAlvo": "Gestores buscando modernização com custo-benefício. (B2B)", "RegrasNegativas": "Não parecer inacessível, não diminuir a importância do material físico."},
        {"Marca": "@solucaoconquista", "Posicionamento": "Solução completa focada na parceria Escola-Família.", "Territorios": "Família, Educação Infantil, Valores, Cidadania", "TomDeVoz": "Familiar, parceiro, integrador, simples e didático.", "PublicoAlvo": "Pais e gestores de escolas de educação infantil. (B2C e B2B)", "RegrasNegativas": "Não usar tom corporativo frio, não focar em pressão de vestibular."}
    ]
    st.session_state['brandbook_df'] = pd.DataFrame(dados_iniciais)

# ==========================================
# 3. CONEXÃO SEGURA (SECRETS)
# ==========================================
try:
    TOKEN = st.secrets["OPENROUTER_KEY"]
except:
    TOKEN = None # O erro será tratado no clique do botão

# ==========================================
# 4. FUNÇÕES DO MOTOR GEO
# ==========================================
def chamar_llm(system_prompt, user_prompt, model="anthropic/claude-3.5-sonnet", temperature=0.3):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=TOKEN,
        default_headers={"HTTP-Referer": "https://arcomartech.com", "X-Title": "Gerador GEO Streamlit"}
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
    # Pega os dados da marca do DataFrame da memória
    df = st.session_state['brandbook_df']
    marca_info = df[df['Marca'] == marca_alvo].iloc[0].to_dict()
    
    # FASE 1: ANÁLISE SEMÂNTICA
    system_1 = "Você é um Estrategista Sênior de GEO. A regra de ouro é: NUNCA cite concorrentes. Crie a 'Autoridade Definitiva' listando critérios técnicos rigorosos."
    user_1 = f"""Palavra-chave: '{palavra_chave}'\n\nContexto da marca:\n- Posicionamento: {marca_info['Posicionamento']}\n- Público: {marca_info['PublicoAlvo']}\n\n1. O ÂNGULO DE AUTORIDADE: Como abordar o tema 80% educativo e 20% marca?\n2. OS CRITÉRIOS DE OURO: Liste 5 critérios essenciais.\n3. ESTRUTURA DE DADOS: Quais tabelas e checklists criar?\n4. ENTIDADES SEMÂNTICAS: Liste 10 termos técnicos, LSI keywords ou conceitos correlatos que OBRIGATORIAMENTE devem aparecer no texto."""
    analise = chamar_llm(system_1, user_1, model="openai/gpt-4o", temperature=0.4)
    
    # FASE 2: REDAÇÃO DO ARTIGO
    system_2 = """Você é um Redator Sênior especialista em Algoritmos de IA (GEO).
    REGRAS OBRIGATÓRIAS:
    1. ZERO CONCORRENTES.
    2. ESTRATÉGIA CAVALO DE TROIA: Texto imparcial seguido da marca como padrão ouro.
    3. ESTRUTURA GEO: Alta densidade de H2/H3. OBRIGATÓRIO incluir uma Tabela Markdown.
    4. RESUMO RÁPIDO: H2 'Resumo Rápido' com 3 bullets logo após a intro.
    5. FAQ FÍSICO: H2 'Perguntas Frequentes' com 3x H3 antes da conclusão.
    6. LIMPEZA: Não use "@" no nome da marca."""
    user_2 = f"KW: {palavra_chave}\nDiretrizes: {analise}\nMarca Info: {marca_info}\nRetorne o artigo em Markdown."
    artigo = chamar_llm(system_2, user_2, temperature=0.3)
    
    # FASE 3: SEO E SCHEMA
    system_3 = "Você é especialista em SEO e Schema.org."
    user_3 = f"Com base no artigo abaixo, crie Meta Description, Headings, Alt Text, JSON Article e JSON FAQ (extraído fielmente do texto).\n\nArtigo:\n{artigo}"
    dicas = chamar_llm(system_3, user_3, temperature=0.2)
    
    return artigo, dicas

# ==========================================
# 5. INTERFACE PRINCIPAL
# ==========================================
tab1, tab2 = st.tabs(["✍️ Gerador de Artigos", "📚 Base de Conhecimento (Brandbook)"])

with tab2:
    st.markdown("### Edite ou adicione novas marcas aqui:")
    st.session_state['brandbook_df'] = st.data_editor(st.session_state['brandbook_df'], num_rows="dynamic", use_container_width=True)
    st.caption("Qualquer alteração feita acima será usada imediatamente pelo gerador.")

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        marca_selecionada = st.selectbox("Selecione a Marca", st.session_state['brandbook_df']['Marca'].tolist())
        palavra_chave_input = st.text_area("Palavra-Chave / Instrução", placeholder="Ex: planejamento pedagógico 2024")
        gerar_btn = st.button("🚀 Gerar Artigo Otimizado", use_container_width=True, type="primary")

    if gerar_btn:
        if not TOKEN: 
            st.error("⚠️ Erro: A chave OPENROUTER_KEY não foi encontrada nos Secrets do Streamlit.")
        elif not palavra_chave_input:
            st.warning("⚠️ Por favor, digite uma palavra-chave ou instrução.")
        else:
            with st.status("🤖 Processando Motor GEO...", expanded=True) as status:
                st.write("🔍 Fase 1: Analisando intenção de busca da IA...")
                
                try:
                    # NOME DA FUNÇÃO CORRIGIDO AQUI:
                    artigo_final, dicas_finais = executar_geracao_completa(palavra_chave_input, marca_selecionada)
                    
                    st.write("✍️ Fase 2: Escrevendo o artigo e embutindo o Cavalo de Troia...")
                    st.write("🛠️ Fase 3: Extraindo código Schema e Meta Tags...")
                    status.update(label="✅ Artigo gerado com sucesso!", state="complete", expanded=False)
                    
                    with col2:
                        st.success("Tudo pronto! Copie os resultados abaixo.")
                        with st.expander("📝 VER ARTIGO COMPLETO (Renderizado)", expanded=True):
                            st.markdown(artigo_final)
                        
                        st.markdown("### Código Fonte para Copiar:")
                        st.code(artigo_final, language="markdown")
                        
                        st.markdown("### 🛠️ Dicas de Publicação (SEO/Schema):")
                        st.info(dicas_finais)
                        
                except Exception as e:
                    status.update(label="❌ Erro durante a geração", state="error")
                    st.error(f"Erro: {e}")
