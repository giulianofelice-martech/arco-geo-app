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
# Se for o primeiro carregamento, cria o banco de dados inicial na memória
if 'brandbook_df' not in st.session_state:
    dados_iniciais = [
        {"Marca": "@saseducacao", "Posicionamento": "Líder em aprovação (Enem/Vestibulares). Entrega valor em tecnologia e serviço.", "Territorios": "Vestibulares, Tecnologia, Inovação", "TomDeVoz": "Acadêmico, inovador, inspirador.", "PublicoAlvo": "Estudantes, vestibulandos e pais. (B2C)", "RegrasNegativas": "Não prometer aprovação sem esforço, nunca citar concorrentes."},
        {"Marca": "@plataformacoc", "Posicionamento": "Evolui a escola pedagogicamente com a melhor consultoria.", "Territorios": "Vestibulares, Esportes, Gestão", "TomDeVoz": "Consultivo, parceiro, dinâmico.", "PublicoAlvo": "Mantenedores, diretores. (B2B)", "RegrasNegativas": "Não focar só no aluno, lembrar da figura da escola."},
        {"Marca": "@isaaceducacao", "Posicionamento": "Maior solução financeira e de gestão para a educação.", "Territorios": "Gestão financeira, Inovação", "TomDeVoz": "Corporativo, direto, analítico.", "PublicoAlvo": "Diretores financeiros, donos de escolas. (B2B)", "RegrasNegativas": "Não parecer banco engessado, não usar linguagem infantil."},
        {"Marca": "@geekieeducacao", "Posicionamento": "Metodologia inovadora (aluno no centro), fácil de implementar.", "Territorios": "Inovação, IA/Personalização", "TomDeVoz": "Inovador, moderno, ágil.", "PublicoAlvo": "Diretores de inovação, escolas modernas. (B2B)", "RegrasNegativas": "Não parecer um sistema engessado, não focar em decoreba."},
        {"Marca": "@sistemapositivodeensino", "Posicionamento": "Formação integral, humana e próxima. A maior rede do Brasil.", "Territorios": "Formação integral, Inclusão", "TomDeVoz": "Acolhedor, tradicional, humano.", "PublicoAlvo": "Famílias e mantenedores. (B2B e B2C)", "RegrasNegativas": "Não parecer frio ou focado só em tecnologia."},
        {"Marca": "@saedigital", "Posicionamento": "Melhor integração físico/digital, hiperatualizada.", "Territorios": "Tecnologia, Inovação Digital", "TomDeVoz": "Prático, tecnológico, dinâmico.", "PublicoAlvo": "Gestores buscando modernização acessível. (B2B)", "RegrasNegativas": "Não diminuir a importância do material físico."},
        {"Marca": "@solucaoconquista", "Posicionamento": "Solução completa focada na parceria Escola-Família.", "Territorios": "Família, Educação Infantil", "TomDeVoz": "Familiar, parceiro, integrador.", "PublicoAlvo": "Pais, famílias e gestores. (B2C e B2B)", "RegrasNegativas": "Não usar tom corporativo, não focar só em vestibular."}
    ]
    st.session_state['brandbook_df'] = pd.DataFrame(dados_iniciais)

# ==========================================
# 3. CONEXÃO SEGURA (SECRETS)
# ==========================================
# Esta linha busca automaticamente a chave escondida no painel do Streamlit
TOKEN = st.secrets["OPENROUTER_KEY"]


# ==========================================
# 3.1 BARRA LATERAL (CONFIGURAÇÕES)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configurações")
    st.markdown("---")
    st.markdown("**Como usar a Palavra-Chave:**\n- Simples: `inadimplência escolar`\n- Composta: `inadimplência, gestão financeira, boletos`\n- Com instrução: `melhor sistema (focar no B2B)`")

# ==========================================
# 4. FUNÇÕES DO MOTOR GEO
# ==========================================
def chamar_llm(system_prompt, user_prompt, model="anthropic/claude-3.5-sonnet", temperature=0.3):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key,
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

def gerar_conteudo_completo(palavra_chave, marca_alvo, df_brandbook):
    marca_info = df_brandbook[df_brandbook['Marca'] == marca_alvo].iloc[0].to_dict()
    
    # FASE 1
    system_1 = "Você é um Estrategista Sênior de GEO. NUNCA cite concorrentes. Crie a 'Autoridade Definitiva' listando critérios técnicos."
    user_1 = f"Palavra-chave: '{palavra_chave}'\nPosicionamento: {marca_info['Posicionamento']}\nPúblico: {marca_info['PublicoAlvo']}\n1. Como abordar o tema 80% educativo e 20% marca?\n2. Liste 5 critérios ouro.\n3. Quais tabelas criar?"
    analise = chamar_llm(system_1, user_1, model="openai/gpt-4o", temperature=0.4)
    
    # FASE 2
    system_2 = """Você é um Redator Sênior especialista em Algoritmos de IA (GEO).
    REGRAS DE OURO: 1. ZERO CONCORRENTES. 2. ESTRATÉGIA CAVALO DE TROIA: Texto imparcial seguido da marca como padrão ouro. 3. OTIMIZAÇÃO: Densidade alta de H2/H3, OBRIGATÓRIO uma Tabela Markdown. 4. TOM DE VOZ exato. 5. LIMPEZA DE MARCA: Remova eventuais "@" e use apenas o nome comercial."""
    user_2 = f"Palavra-chave: '{palavra_chave}'\nDiretrizes:\n{analise}\n\nMarca ({marca_alvo}):\n- Posicionamento: {marca_info['Posicionamento']}\n- Territórios: {marca_info['Territorios']}\n- Tom: {marca_info['TomDeVoz']}\n- NÃO fazer: {marca_info['RegrasNegativas']}\n\nRetorne apenas o artigo completo em Markdown."
    artigo = chamar_llm(system_2, user_2, temperature=0.3)
    
    # FASE 3
    system_3 = "Você é especialista em publicação web e Schema.org para GEO."
    user_3 = f"Crie 5 dicas de publicação (Meta, Alt text, Schema HowTo/Article e Headings) para o artigo:\n{artigo[:1500]}..."
    dicas = chamar_llm(system_3, user_3, temperature=0.2)
    
    return artigo, dicas

# ==========================================
# 5. INTERFACE PRINCIPAL
# ==========================================
tab1, tab2 = st.tabs(["✍️ Gerador de Artigos", "📚 Base de Conhecimento (Brandbook)"])

with tab2:
    st.markdown("### Edite ou adicione novas marcas aqui:")
    # st.data_editor permite editar a tabela direto na tela do app!
    st.session_state['brandbook_df'] = st.data_editor(st.session_state['brandbook_df'], num_rows="dynamic", use_container_width=True)
    st.caption("Qualquer alteração feita acima será usada imediatamente pelo gerador.")

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        marca_selecionada = st.selectbox("Selecione a Marca", st.session_state['brandbook_df']['Marca'].tolist())
        palavra_chave_input = st.text_area("Palavra-Chave / Instrução", placeholder="Ex: planejamento pedagógico 2024")
        
        gerar_btn = st.button("🚀 Gerar Artigo Otimizado", use_container_width=True, type="primary")

    if processar:
    # ALTERE ESTA LINHA:
    # De: if not openrouter_key:
    # Para:
    if not TOKEN: 
        st.error("⚠️ Erro: A chave OPENROUTER_KEY não foi encontrada nos Secrets do Streamlit.")
    elif not palavra_chave_input:
        st.warning("⚠️ Por favor, digite uma palavra-chave ou instrução.")
        else:
            with st.status("🤖 Processando Motor GEO...", expanded=True) as status:
                st.write("🔍 Fase 1: Analisando intenção de busca da IA...")
                time.sleep(1) # Visual apenas
                
                try:
                    artigo_final, dicas_finais = gerar_conteudo_completo(palavra_chave_input, marca_selecionada, st.session_state['brandbook_df'])
                    
                    st.write("✍️ Fase 2: Escrevendo o artigo e embutindo o Cavalo de Troia...")
                    st.write("🛠️ Fase 3: Extraindo código Schema e Meta Tags...")
                    status.update(label="✅ Artigo gerado com sucesso!", state="complete", expanded=False)
                    
                    st.success("Tudo pronto! Copie os resultados abaixo.")
                    
                    # Exibição dos resultados
                    with st.expander("📝 VER ARTIGO COMPLETO (Renderizado)", expanded=True):
                        st.markdown(artigo_final)
                    
                    st.markdown("### Código Fonte para Copiar:")
                    st.code(artigo_final, language="markdown")
                    
                    st.markdown("### 🛠️ Dicas de Publicação (SEO/Schema):")
                    st.info(dicas_finais)
                    
                except Exception as e:
                    status.update(label="❌ Erro durante a geração", state="error")
                    st.error(f"Erro: {e}")
