# 🚀 Arco Martech | Motor GEO v7.1 (AI Search Native)

O **Motor GEO (Generative Engine Optimization)** é uma aplicação Python avançada construída com arquitetura multi-agentes (GPT-4o e Claude 3.7 Sonnet) e heurísticas matemáticas. Seu objetivo é gerar, auditar e otimizar conteúdo editorial corporativo com foco máximo em **E-E-A-T** (Experiência, Especialidade, Autoridade e Confiabilidade) e otimização nativa para motores de busca baseados em IA (Perplexity, SearchGPT, SGE).

---

## 🧠 Arquitetura do Sistema (Pipeline de 7 Passos)

O motor opera através de um pipeline rígido projetado para zerar alucinações e maximizar a autoridade tópica:

1. **Search:** Escaneamento em tempo real do Top 3 do Google (via Serper + Jina Reader) e baseline de consenso de IAs.
2. **Intent Map:** Engenharia reversa das dúvidas ocultas dos usuários e do raciocínio interno das IAs (Reverse Queries).
3. **Entity Graph:** Mapeamento de buracos semânticos (Entity Gap) e jargões obrigatórios de mercado.
4. **Writer:** Redação em HTML purista operada pelo Claude 3.7 Sonnet, aplicando regras estritas de Brandbook, tom de voz corporativo e neutralidade competitiva (veto a rivais).
5. **Schema & Media:** Injeção automatizada de código JSON-LD (FAQPage) e imagens via API (Unsplash/Pollinations).
6. **Math Heuristics:** Algoritmos proprietários em Python que calculam notas exatas para formatação de texto (*Chunk Citability*), densidade de evidências (*Evidence Density*) e resposta antecipada (*Answer-First*).
7. **RAG Simulation:** Simulação semântica via GPT-4o para prever o risco de *Citation Hijacking* e a probabilidade de o texto ser usado como fonte primária por LLMs.

---

## ⚙️ Funcionalidades Principais (Módulos)

A interface é dividida em 4 abas principais:

* **✍️ Gerador de Artigos:** Onde a mágica acontece. Recebe a keyword e o público-alvo, executa o pipeline, injeta *RAG Reverso* (buscando links internos no CMS da marca) e devolve o HTML pronto para postagem direta.
* **📚 Brandbook:** Um banco de dados em memória contendo o DNA de todas as marcas da Arco (Posicionamento, Tom de Voz, Regras Positivas/Negativas e Territórios).
* **🔍 Monitor de GEO:** Um auditor que cruza heurísticas matemáticas com análise do GPT-4o para dar uma nota E-E-A-T a qualquer HTML colado, gerando insights de melhoria (Engenharia de Prompt Contínua).
* **📝 Revisor GEO CMS:** Módulo de otimização de legado. Puxa artigos antigos do blog e os reescreve no padrão GEO (Assimetria Visual, Answer-First), preservando **intactas** todas as tags `<a>` (links) e `<img>` originais (A *Regra Intocável*).

---

## 🔌 Configuração Multi-CMS (WordPress & Drupal)

O Motor v7.1 possui um roteador dinâmico (`obter_credenciais_cms`) capaz de se comunicar via REST API com WordPress e via JSON:API com Drupal. 

Para que a postagem direta e o RAG Reverso funcionem, o arquivo `.streamlit/secrets.toml` deve estar configurado na raiz do projeto com a seguinte estrutura:

```toml
# Chaves Globais de API
OPENROUTER_KEY = "sk-or-v1-sua-chave-aqui"
SERPAPI_KEY = "sua-chave-serper-aqui"
UNSPLASH_KEY = "sua-chave-unsplash-aqui"

# Integrações de CMS por Marca (Exemplo WP)
[wordpress."SAS Educação"]
WP_URL = "[https://www.saseducacao.com.br/jsonapi/node/quark_blog](https://www.saseducacao.com.br/jsonapi/node/quark_blog)"
WP_USER = "usuario_api"
WP_APP_PASSWORD = "senha_ou_app_password"
CMS_TYPE = "drupal" # Define o roteamento: "drupal" ou "wp"

[wordpress."ClassApp"]
WP_URL = "[https://www.classapp.com.br/wp-json/wp/v2/posts](https://www.classapp.com.br/wp-json/wp/v2/posts)"
WP_USER = "usuario_api"
WP_APP_PASSWORD = "app_password_do_wp"
CMS_TYPE = "wp"

---

##  🛠️ Stack Tecnológico
Linguagem Principal: Python 3.x

Frontend: Streamlit

Estruturação de Dados: Pydantic (Validação JSON e Schemas) e Pandas (Brandbook)

LLMs: OpenAI GPT-4o (Planejamento, Auditoria e Simulações) e Anthropic Claude 3.7 Sonnet (Redação HTML de altíssima fidelidade). Acessados via OpenRouter.

APIs Externas: Serper.dev (Google Search), Jina AI Reader (Raspagem Web), Unsplash (Mídia).

---

##🛡️ Guardrails e Segurança (Anti-Alucinação)
Veto de Dados Órfãos: A IA é bloqueada de inventar estatísticas absolutas (ex: "aumento de 37%") caso o dado não possua uma URL referencial (href) comprovada no contexto orgânico.

Assimetria Visual Obrigatória: Prevenção contra Wall of Text (textos massivos gerados por IA). O motor exige que parágrafos longos sejam intercalados com frases de impacto isoladas.

Lazy Linking Banido: Todo link gerado deve ser um Deep Link (página específica do estudo/artigo) e nunca uma home page genérica.
