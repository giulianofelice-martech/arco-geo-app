# ==========================================
# 9. DASHBOARD DE RESULTADOS (NOVA ABA 6)
# ==========================================
elif st.session_state['current_page'] == "Dashboard SEO":
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; margin-top: -1rem;">
            <div class="arco-tag" style="margin-bottom: 0.5rem; background-color: #ECFDF5; color: #10B981 !important;">RESULTADOS</div>
            <h1 style="font-size: 2.2rem; margin-top: 0;">Performance do <span style="color: #F05D23;">Motor</span></h1>
            <p style="color: #6B7280; font-size: 1.1rem;">Visão diária extraída automaticamente do Google Sheets.</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Função de Carregamento de Dados
    @st.cache_data(ttl=3600, show_spinner=False)
    def carregar_dados_sheets():
        # AQUI VOCÊ CONECTA O GOOGLE SHEETS DE VERDADE
        # Exemplo Simples (Planilha Pública):
        # url_csv = "https://docs.google.com/spreadsheets/d/SEU_ID/export?format=csv&gid=SEU_GID"
        # df = pd.read_csv(url_csv)
        
        # --- DADOS SIMULADOS PARA TESTE DE DESIGN ---
        import random
        from datetime import datetime, timedelta
        
        datas = [(datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14, -1, -1)]
        df_mock = pd.DataFrame({
            "Data": datas,
            "Tráfego Orgânico": [int(x) for x in sorted([random.uniform(500, 3000) for _ in range(15)])],
            "Artigos Publicados": [random.randint(1, 5) for _ in range(15)],
            "Keywords no Top 3": [int(x) for x in sorted([random.uniform(10, 150) for _ in range(15)])]
        })
        
        df_artigos_recentes = pd.DataFrame({
            "Artigo (Keyword)": ["Metodologia Bilíngue", "Gestão Escolar 2026", "Retenção de Alunos", "ECA Atualizado", "Novo Ensino Médio"],
            "Marca": ["International School", "Activesoft", "Isaac", "SAS Educação", "Arco Educação"],
            "GEO Score": [98, 92, 88, 95, 85],
            "Posição Google": ["2º", "1º", "5º", "1º", "3º"]
        })
        return df_mock, df_artigos_recentes
    
    with st.spinner("Sincronizando com Google Sheets..."):
        df_tendencia, df_artigos = carregar_dados_sheets()

    # 2. KPIs no Topo (Métricas de Vaidade e Resultados)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="📈 Tráfego Orgânico (Mês)", value="45.2K", delta="12.5%", help="Acessos vindos diretamente do Google.")
    with kpi2:
        st.metric(label="✍️ Artigos Gerados", value="142", delta="8 nesta semana")
    with kpi3:
        st.metric(label="🏆 Palavras no Top 3", value="89", delta="15 posições ganhas", delta_color="normal")
    with kpi4:
        st.metric(label="⭐ GEO Score Médio", value="92/100", delta="-1 ponto", delta_color="inverse")

    st.markdown("<hr style='border: 1px solid #E5E7EB; margin: 2rem 0;'>", unsafe_allow_html=True)

    # 3. Gráficos de Tendência
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.markdown("### 🚀 Evolução de Tráfego Orgânico")
        # Usando chart nativo do Streamlit alimentado pelo Pandas
        df_chart = df_tendencia.set_index("Data")
        st.line_chart(df_chart["Tráfego Orgânico"], color="#F05D23", height=300)

    with col_chart2:
        st.markdown("### 📊 Produção Diária")
        st.bar_chart(df_chart["Artigos Publicados"], color="#418EDE", height=300)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Tabela de Detalhamento dos Últimos Artigos
    st.markdown("### 📌 Radar de Visibilidade dos Artigos")
    st.caption("Acompanhamento das URLs geradas e sua performance de indexação.")
    
    # Renderiza o dataframe de forma bonita e interativa
    st.dataframe(
        df_artigos,
        use_container_width=True,
        hide_index=True,
        column_config={
            "GEO Score": st.column_config.ProgressColumn(
                "GEO Score",
                help="Nota matemática de estrutura do artigo",
                format="%d",
                min_value=0,
                max_value=100,
            ),
            "Posição Google": st.column_config.TextColumn("Posição no Google")
        }
    )
