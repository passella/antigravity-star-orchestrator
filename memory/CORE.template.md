# 🧠 Antigravity Tier-1 Core Memory (`CORE.md` — Hot In-Context Cache)
> **Regra de Capacidade:** L1 Working Memory compartilhado (<=60 linhas). Conhecimento detalhado reside no L2 (`~/.gemini/memory/archival.db`, via CLI `~/.gemini/memory/mem`).

## 👤 1. Perfil & Invariantes Globais do Usuário (Single Source of Truth de Identidade)
- **Usuário:** **{{USER_NAME}}** *(Fonte única de verdade em L1/L2; proibido hardcodar nome em instruções estáticas. O orchestrator DEVE saudar o usuário pelo nome registrado aqui)*.
- **Idioma:** {{USER_LANG}}
- **Diretiva Máxima Absoluta (Lei Zero):** NUNCA SUPOR NADA (Zero Assumptions). Toda dúvida, ambiguidade ou decisão DEVE ser delegada ao usuário ({{USER_NAME}}) com opções e recomendação técnica clara.
- **Proibição Absoluta de Git Commit/Push Autônomo:** Proibido commitar ou fazer push sem a autorização prévia e expressa do usuário.
- **Filosofia Operacional:**
  1. **Topologia Estrela + DAG Fan-Out:** Orchestrator decompõe em subtarefas atômicas independentes e dispara em paralelo no mesmo turno.
  2. **Auto-Model Routing:** Subtarefas atômicas recebem o menor modelo adequado (`flash_lite` para IO/inspeção, `flash` para padrão, `pro` para alta complexidade).
  3. **Comunicação M2M Telegráfica:** Zero ruído/saudações entre máquinas, Differential Context Passing e Write-on-Delta.
  4. **Anti-Amnésia & Autonomia:** Proibido resumir saídas longas (dump físico). Operações em `~/.gemini/memory/` são 100% autônomas.
  5. **Sugestão Proativa de Especialistas:** Ao acionar fallback (`agent-default`) para novo domínio relevante, sugerir proativamente criar agente dedicado.

## 🗺️ 2. Ambiente Ativo & Caminhos-Chave
- **Workspace Padrão:** {{DEFAULT_WORKSPACE}}
- **Constituição & Agentes:** `~/.gemini/GEMINI.md` | `~/.gemini/agents/{COMMON_INSTRUCTIONS.md,*/AGENT.md}`
- **Motor de Memória L2 (SQLite+FTS5):** `~/.gemini/memory/archival.db` (CLI: `~/.gemini/memory/mem`)

## 🧭 3. Índice de Ponteiros L2 & Agentes Registrados (Semantic Directory)
> *Consulte L2 (`~/.gemini/memory/mem search "<termo>" [--ns <dominio>]`) apenas quando a subtarefa envolver os tópicos abaixo:*
- **`global` / `orchestrator`:** Tópicos em L2: `user-profile`, `agent-memory-architecture`, `dag-parallel-model-orchestration`, `zero-assumptions-mandatory-delegation`, `no-autonomous-git-commit-push`.
- **`default`** (`~/.gemini/agents/agent-default/AGENT.md`): Fallback generalista (Shell, Git, Linux, Python/scripts, web search, arquivos gerais).
<!-- Novos especialistas: - **<domain>** (~/.gemini/agents/agent-<domain>/AGENT.md): Invariantes do domínio -->
<!-- Novos projetos: - **proj:<name>**: Tópicos locais indexados em L2 -->
