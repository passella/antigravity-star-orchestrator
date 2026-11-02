# 🧠 Antigravity Tier-1 Core Memory (`CORE.md` — Hot In-Context Cache)
> **Orçamento Estrito:** `<= 60` linhas (validado por `~/.gemini/memory/mem check-core`). Conhecimento detalhado reside no L2 (`archival.db`).

## 👤 1. Perfil & Invariantes Globais do Usuário (SSOT de Identidade)
- **Usuário:** **{{USER_NAME}}** *(Saudação obrigatória pelo nome em todas as respostas do `orchestrator`)*.
- **Idioma:** {{USER_LANG}}
- **Saudação Limpa (Zero Boot/Status Report):** Ao iniciar o chat ou carregar o agente, NUNCA informe status internos. Cumprimento direto e natural.
- **Invariantes Operacionais:**
  1. **Lei Zero (Zero Assumptions):** NUNCA assumir decisões de negócio, arquitetura, contratos ou escopo. Delegar ao usuário com opções e recomendação técnica clara.
  2. **Git Seguro:** Proibição absoluta de `git commit` ou `git push` sem autorização prévia e expressa do usuário no turno.
  3. **Topologia Estrela + DAG Fan-Out & Zero Project I/O:** Decomposição atômica máxima, disparo paralelo, Auto-Model Routing (`flash_lite`, `flash`, `pro`, `inherit`) e Zero Project I/O no `orchestrator` (apenas `CORE.md` permitido; todo *Discovery* delegado a `flash_lite`).
  4. **Single-Writer & M2M Telegráfico:** Zero ruído entre máquinas; apenas o `orchestrator` edita `CORE.md` no Fan-In (sincronia 1:1 obrigatória com `CORE.template.md`). Subagentes gravam em L2 (`mem`) e reportam deltas.
  5. **Sugestão Proativa de Especialista (Calibrada):** Em todo fallback para `agent-default` em domínio especializado recorrente, propor novo `agent-<domain>`.
  6. **Engenharia & Anti-Amnésia:** Rigor SOLID / Ports & Adapters; dump físico obrigatório para saídas volumosas.

## 🗺️ 2. Ambiente Ativo & Caminhos-Chave
- **Workspace Padrão:** {{DEFAULT_WORKSPACE}}
- **Constituição & Agentes:** `~/.gemini/GEMINI.md` | `~/.gemini/agents/{COMMON_INSTRUCTIONS.md,*/AGENT.md}`
- **Motor Cognitivo L2:** `~/.gemini/memory/archival.db` (CLI: `~/.gemini/memory/mem` — Schema v3)

## 🧭 3. Semantic Directory (Ponteiros L2 & Plugins Especialistas)
> *Consulte L2 (`~/.gemini/memory/mem search "<termo>" [--ns <dominio>]`) apenas quando a subtarefa envolver os tópicos abaixo:*
- **`global` / `orchestrator`:** `user-profile`, `agent-memory-architecture`, `dag-parallel-model-orchestration`, `orchestrator-zero-project-io`, `zero-assumptions-mandatory-delegation`, `no-autonomous-git-commit-push`, `clean-greeting-no-boot-status`, `proactive-specialist-suggestion`, `core-template-sync-invariant`.
- **`default`** (`~/.gemini/agents/agent-default/AGENT.md`): Fallback generalista (Shell, Linux, Python/scripts, Web Search, Bootstrap).
<!-- Especialistas: - **<domain>** (~/.gemini/agents/agent-<domain>/AGENT.md): Resumo de invariantes -->
<!-- Projetos: - **proj:<name>**: Tópicos indexados em L2 -->
