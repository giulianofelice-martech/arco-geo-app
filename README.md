# 🚀 Arco Martech | Motor GEO v7.0 (AI Search Native)

O **Motor GEO (Generative Engine Optimization)** é uma aplicação Python avançada construída com arquitetura **multi-agentes** (GPT-4o, Claude 4 Sonnet e Gemini 2.5 Pro) e heurísticas matemáticas proprietárias. Seu objetivo é gerar, auditar e otimizar conteúdo editorial corporativo com foco máximo em **E-E-A-T** (Experiência, Especialidade, Autoridade e Confiabilidade) e otimização nativa para motores de busca baseados em IA (Perplexity, ChatGPT, SGE, Gemini).

---

## 🧠 Arquitetura do Sistema (Pipeline de 7 Passos)

O motor opera através de um pipeline rígido projetado para zerar alucinações e maximizar a autoridade tópica:

1. **Search:** Escaneamento em tempo real do Top 3 do Google (via Serper + Jina Reader) e baseline de consenso de IAs. Execução paralela com `concurrent.futures`.
2. **Intent Map:** Engenharia reversa das dúvidas ocultas dos usuários e do raciocínio interno das IAs (*Reverse Queries*), geradas via GPT-4o-mini.
3. **Entity Graph:** Mapeamento de buracos semânticos (*Entity Gap*) e jargões obrigatórios de mercado para cobertura tópica completa.
4. **Voice Synthesis (Gemini):** Agente Gemini 2.5 Pro lê documentos de referência da marca (`/referencias_tom`) e gera um *Manual de Clonagem de Voz* cirúrgico antes da redação.
5. **Writer (Claude 4 Sonnet):** Redação em HTML purista com dois modos: **GEO Restrito** (compliance estrutural máximo) e **Empático** (cadência humana e fluidez). Aplica regras do Brandbook, RAG Reverso (links internos do CMS) e ghostwriting por especialista.
6. **Schema & Media:** Extração de metadados via Pydantic, injeção de JSON-LD (FAQPage) e imagens via Unsplash (com fallback para Pollinations AI). Guardrail Python anti-conteúdo sensível nas imagens.
7. **Math Heuristics + RAG Simulation:** Algoritmos proprietários calculam 8 métricas exatas (*Chunk Citability*, *Answer-First*, *Evidence Density*, *Information Gain*, *Entity Coverage*, *GEO Score*, *Retrieval Simulation* e *Citation Hijacking*).

---

## ⚙️ Funcionalidades Principais (5 Módulos)

### ✍️ Gerador de Artigos
O núcleo do sistema. Recebe keyword, marca, público-alvo e instruções opcionais e executa o pipeline completo. Entrega o HTML pronto com:
- Publicação direta no CMS (rascunho) via botão
- Editor manual e refinamento pontual por IA ("cirurgia no texto")
- 4 sub-abas de análise: **Dashboard Rápido**, **Raio-X Técnico de SEO**, **Como as IAs Enxergam** e visualização de pré-leitura com botão de cópia formatada

Recursos adicionais do formulário:
- **Pautas em Alta** (🔥): trending topics em tempo real via Google News / RSS do MEC
- **Modo Empático**: prompt alternativo focado em fluidez e cadência humana
- **Ghostwriting**: clona o tom de voz de um especialista a partir de artigos reais do LinkedIn
- **Conteúdo Proprietário Inegociável**: força inclusão literal de trechos exatos no artigo
- **Prompt Livre**: instrução direta de estrutura de H2s e formato (estilo ChatGPT)

### 📚 BrandBook
Banco de dados em memória (Pandas DataFrame) com o DNA editorial de **16 marcas** da Arco. Editável em tempo real via `st.data_editor`. Contém: Posicionamento, Tom de Voz, Territórios, Público-Alvo e Regras Positivas/Negativas. Inclui também a base de **Especialistas para Ghostwriting**.

### 🔍 Monitor de GEO
Auditor que cruza 3 heurísticas matemáticas (Chunk Citability, Answer-First, Evidence Density) com análise semântica do GPT-4o para gerar uma **nota E-E-A-T de 0 a 100** com críticas técnicas e sugestões de guardrails para melhoria contínua do prompt.

### ♻️ Revisor & Adaptador
Módulo duplo:
- **Revisão GEO de CMS:** puxa artigos antigos do blog e reescreve no padrão GEO (Assimetria Visual, Answer-First), preservando **intactas** todas as tags `<a>` e `<img>` originais — a *Regra Intocável*.
- **Adaptação de Documentos:** transforma PDFs, DOCX e TXT em artigos HTML. Modo **Teaser/Spoiler** (captura de leads) quando sem instrução, ou **Síntese Customizada** quando com prompt do usuário.

### 📊 Auditor de Visibilidade
Verifica se um artigo publicado está ranqueando no Google ou sendo recomendado por IAs. Funciona em 3 etapas:
1. Gera um *Intent Map* (Reverse Queries) a partir da keyword
2. Dispara buscas paralelas no Google e em **3 LLMs simultaneamente** (Perplexity Sonar Pro, Gemini Flash, Claude 3.7 Sonnet)
3. Rastreia a URL do artigo nas respostas e exibe o **Placar de Citação por agente**

---

## 🔌 Configuração Multi-CMS

O Motor v7.0 possui um roteador dinâmico (`obter_credenciais_cms`) capaz de se comunicar com **WordPress** (REST API), **Drupal** (JSON:API) e **Webflow** (CMS API). O roteamento é automático via campo `CMS_TYPE` nos secrets.

Configure o arquivo `.streamlit/secrets.toml`:

```toml
# Chaves Globais de API
OPENROUTER_KEY  = "sk-or-v1-sua-chave-aqui"
SERPAPI_KEY     = "sua-chave-serper-aqui"
UNSPLASH_KEY    = "sua-chave-unsplash-aqui"

# Exemplo: Drupal (SAS Educação)
[wordpress."SAS Educação"]
WP_URL          = "https://www.saseducacao.com.br/jsonapi/node/quark_blog"
WP_USER         = "usuario_api"
WP_APP_PASSWORD = "senha_ou_app_password"
CMS_TYPE        = "drupal"

# Exemplo: WordPress (ClassApp)
[wordpress."ClassApp"]
WP_URL          = "https://www.classapp.com.br/wp-json/wp/v2/posts"
WP_USER         = "usuario_api"
WP_APP_PASSWORD = "app_password_do_wp"
CMS_TYPE        = "wp"

# Exemplo: Webflow (Isaac)
[wordpress."Isaac"]
WP_URL          = "https://api.webflow.com/v2/collections/SEU_COLLECTION_ID/items"
WP_USER         = ""
WP_APP_PASSWORD = "seu_bearer_token_webflow"
CMS_TYPE        = "webflow"
```

---

## 🛠️ Stack Tecnológico

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.x |
| Frontend | Streamlit |
| Validação de Dados | Pydantic v2 |
| Manipulação de Dados | Pandas |
| LLM Estrategista | OpenAI GPT-4o (planejamento, auditoria, simulações) |
| LLM Redator | Anthropic Claude 4 Sonnet (redação HTML, revisão, refinamento) |
| LLM Voz de Marca | Google Gemini 2.5 Pro (síntese de tom de voz) |
| LLM Auditoria de IA | Perplexity Sonar Pro, Gemini Flash, Claude 3.7 Sonnet (multi-agentes) |
| Gateway de LLMs | OpenRouter |
| Busca Orgânica | Serper.dev (Google Search) |
| Raspagem Web | Jina AI Reader |
| Mídia | Unsplash API + Pollinations AI (fallback) |
| Analytics | Google Analytics 4 (GA4) via injeção de script no iframe pai |
| Resiliência | Tenacity (retry com backoff exponencial) |
| Leitura de Docs | PyPDF2, python-docx |
| Trending Topics | feedparser (Google News RSS + G1) |

---

## 🛡️ Guardrails e Segurança (Anti-Alucinação)

1. **Veto de Dados Órfãos:** A IA é bloqueada de citar estatísticas absolutas (ex: "aumento de 37%") sem uma URL referencial (`href`) comprovada extraída do contexto orgânico.
2. **Blacklist de Vocabulário IA:** Lista permanente de jargões banidos ("no cenário atual", "cada vez mais", "divisor de águas") injetada em todos os prompts de redação.
3. **Veto de URLs Alucinadas:** O redator é obrigado a declarar em `<thought_process>` (bloco removido por regex antes da entrega) quais URLs usará, podendo usar apenas as fornecidas no briefing.
4. **Assimetria Visual Obrigatória:** Prevenção contra *Wall of Text*. O motor exige intercalação de parágrafos longos com frases de impacto isoladas.
5. **Lazy Linking Banido:** Todo link externo deve ser um *Deep Link* para a página/estudo específico, nunca uma homepage genérica.
6. **Proteção de Legado (Revisor):** Tags `<a>` e `<img>` preexistentes são intocáveis no módulo de revisão — a *Regra Intocável*.
7. **Guardrail de Imagens (Python):** Antes de injetar imagens do Unsplash, o código verifica a `alt_description` contra uma blacklist de termos sensíveis (`pray`, `church`, `protest`, `war`, etc.) e redireciona para o fallback se necessário.
8. **Guilhotina de HTML:** Regex em Python que garante que o output do LLM começa na primeira tag `<` e termina na última tag `>`, cortando qualquer auto-avaliação ou comentário gerado após o HTML.

---

## 📁 Estrutura de Arquivos

```
arco-geo-app/
├── app.py                    # Aplicação principal
├── requirements.txt          # Dependências Python
├── config.toml               # Configurações visuais do Streamlit
├── .streamlit/
│   └── secrets.toml          # Credenciais (não sobe para o GitHub)
└── referencias_tom/          # Documentos de referência de tom de voz por marca
    ├── sas_educacao/         # PDFs, DOCXs ou TXTs de referência
    ├── coc/
    └── ...                   # Uma pasta por marca (slug sem acentos)
```

---

## 📊 Métricas Matemáticas Geradas por Artigo

| Métrica | O que mede | Escala |
|---|---|---|
| **GEO Score** | Nota final ponderada (35% Citation + 25% LLM Citability + 25% Entity + 15% Originality) | 0–100 |
| **Chunk Citability** | Facilidade de IAs extraírem chunks citáveis (listas, definições curtas, parágrafos curtos) | 0–100 |
| **Answer-First** | A resposta direta está nas 3 primeiras linhas? | 0–100 |
| **Evidence Density** | Densidade de números, porcentagens e links no texto | 0–100 |
| **Information Gain** | Palavras únicas trazidas em relação ao Top 3 do Google | 0–100 |
| **Entity Coverage** | % das entidades obrigatórias do nicho presentes no texto | 0–100 |
| **Retrieval Simulation** | Probabilidade de uma IA usar o texto como fonte primária | 0–100 |
| **Citation Hijacking Risk** | Risco de um concorrente "roubar" a citação por ser mais direto | baixo/médio/alto |
