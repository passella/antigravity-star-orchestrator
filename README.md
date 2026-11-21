# 🚀 Antigravity: Global Star-Topology Multi-Agent Ecosystem & Hybrid Cognitive Memory Engine

🌐 **Idiomas / Languages:** **Português (BR)** | [English](README.en.md) | [Español](README.es.md) | [简体中文](README.zh-CN.md)

[![Architecture: Star-Topology DAG](https://img.shields.io/badge/Architecture-Star--Topology_DAG-6f42c1?style=flat-square)](#2-pilares-arquiteturais)
[![Memory Engine: Tier-1 + Tier-2 Schema v3](https://img.shields.io/badge/Memory_Engine-2--Tier_SQLite_WAL_%2B_FTS5_(Schema_v3)-007ec6?style=flat-square)](#3-arquitetura-cognitiva-híbrida-das-7-memórias)
[![Design: Clean / Hexagonal](https://img.shields.io/badge/Design-Clean_%2F_Ports_%26_Adapters-2ea44f?style=flat-square)](#4-engenharia-interna-do-motor-l2-geminimemorymem)
[![Dependencies: Zero (Python 3 Stdlib)](https://img.shields.io/badge/Dependencies-Zero_(Python_3_Stdlib)-ffd343?style=flat-square)](#4-engenharia-interna-do-motor-l2-geminimemorymem)
[![Tests: 31 Passing (Unittest)](https://img.shields.io/badge/Tests-31_Passing_(Stdlib_Unittest)-brightgreen?style=flat-square)](#10-suíte-de-testes-automatizados)

O **Antigravity** é um framework de orquestração multi-agente em **Topologia Estrela Estrita** e um motor de **Memória Cognitiva Híbrida 2-Tier (Schema L2 v3)** projetado para operar nativamente sobre o diretório global `~/.gemini`. Ele transforma sessões isoladas de LLMs em um sistema distribuído determinístico de engenharia de software — combinando escalonamento paralelo em grafos acíclicos direcionados (**DAG Fan-Out / Fan-In**), roteamento cognitivo dinâmico de modelos (**Auto-Model Routing**), governança **Zero Assumptions (Lei Zero)** e persistência transacional concorrente em SQLite WAL + FTS5 sem nenhuma dependência externa.

---

## 📑 Sumário

1. [Proposta de Valor & Filosofia de Engenharia](#1-proposta-de-valor--filosofia-de-engenharia)
2. [Pilares Arquiteturais](#2-pilares-arquiteturais)
3. [Arquitetura Cognitiva Híbrida das 7 Memórias](#3-arquitetura-cognitiva-híbrida-das-7-memórias)
4. [Engenharia Interna do Motor L2 (`~/.gemini/memory/mem`)](#4-engenharia-interna-do-motor-l2-geminimemorymem)
5. [Ciclo de Vida End-to-End (Walkthrough em 4 Fases)](#5-ciclo-de-vida-end-to-end-walkthrough-em-4-fases)
6. [Estrutura do Repositório & Isolamento Git (Starter Kit)](#6-estrutura-do-repositório--isolamento-git-starter-kit)
7. [Instalação, Menor Privilégio & First-Boot Onboarding](#7-instalação-menor-privilégio--first-boot-onboarding)
8. [Ecossistema de Subagentes & Criação de Especialistas (`agent-<domain>`)](#8-ecossistema-de-subagentes--criação-de-especialistas-agent-domain)
9. [Referência Completa da CLI `~/.gemini/memory/mem`](#9-referência-completa-da-cli-geminimemorymem)
10. [Suíte de Testes Automatizados](#10-suíte-de-testes-automatizados)
11. [Governança de Git, Segurança & Invariantes de Código](#11-governança-de-git-segurança--invariantes-de-código)

---

## 1. Proposta de Valor & Filosofia de Engenharia

Assistentes baseados em LLMs convencionais sofrem de quatro falhas estruturais graves quando aplicados a projetos reais de engenharia de software:

| Patologia Clássica de Agentes LLM | Solução de Engenharia do Antigravity |
| :--- | :--- |
| **1. Amnésia Entre Sessões e Repetição de Erros** | **Memória Híbrida 2-Tier + Recall Episódico (`recall-error`):** Cache quente L1 (`CORE.md` $\le 60$ linhas) sempre em contexto pareado com um banco arquival L2 (`archival.db` em SQLite WAL + FTS5) que armazena fatos, decisões, grafos semânticos, versão histórica (`memory_history`) e lições aprendidas (`learning`) contendo obrigatoriamente a seção `[DEAD-ENDS / TENTATIVAS DESCARTADAS]`. |
| **2. Explosão de Contexto e Degradação de Atenção (*Context Rot*)** | **Topologia Estrela + Differential Context Passing (M2M):** O agente principal (`orchestrator`) nunca executa código diretamente nem acumula dumps brutos. Ele decompõe demandas em subtarefas atômicas e injeta nos subagentes exclusivamente os caminhos e invariantes necessários em formato telegráfico livre de ruído. Saídas extensas vão obrigatoriamente para disco (Anti-Amnésia). |
| **3. Race Conditions em Execução Multi-Agente Paralela** | **Single-Writer L1 + Concorrência Transacional L2:** Durante um Fan-Out paralelo, subagentes **jamais** editam `CORE.md`; eles gravam concorrentemente no SQLite L2 (protegido por `WAL`, `busy_timeout=30000` e transações reentrantes `BEGIN IMMEDIATE`) e retornam `MEMORY_DELTA`. Apenas o `orchestrator` atualiza `CORE.md` no Fan-In sob file lock exclusivo (`fcntl`/`msvcrt`). |
| **4. Alucinações Arquiteturais e Decisões Silenciosas** | **Lei Zero Inviolável (Protocolo Zero Assumptions):** Nenhum agente pode assumir requisitos, arquitetura, contratos públicos, adição de bibliotecas ou escopo. Diante de bifurcações técnicas, o subagente interrompe a execução com `STATUS: NEED`, e o `orchestrator` delega a decisão ao usuário com opções estruturadas e recomendação técnica fundamentada. |

---

## 2. Pilares Arquiteturais

### 2.1. Topologia Estrela Estrita (`orchestrator` Central)
O ecossistema proíbe comunicação lateral direta entre subagentes (*mesh* caótico). O **`orchestrator`** ocupa o centro da estrela como único ponto de contato com o usuário e único escalonador de tarefas:
* **Proibição Absoluta de Execução Direta pelo Orquestrador:** O `orchestrator` jamais edita código de projetos, cria queries SQL, executa comandos de terminal de domínio ou manipula containers.
* **Discovery Read-Only Leve no Turno 1 (Whitelist Semântica):** Quando o contexto inicial não informa a estrutura do projeto alvo, o `orchestrator` possui permissão estrita para realizar leitura leve de reconhecimento através de uma *whitelist* semântica — listagem do diretório raiz e leitura de manifestos ou configurações de topo (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `docker-compose.yml`, `Makefile`, `README.md`, etc.) respeitando um **teto seguro de `< 16 KB` (~400 linhas)** — exclusivamente para planejar o grafo DAG com precisão. Toda análise profunda e mutação são delegadas aos subagentes.
* **Saudação Obrigatória Limpa (Zero Boot/Status Report):** O `orchestrator` inicia sempre suas respostas saudando o usuário pelo nome registrado em `CORE.md`, sem jamais emitir relatórios robóticos de boot (como *"memória L1 sincronizada"* ou *"diretivas carregadas"*), a menos que explicitamente solicitado.

### 2.2. Decomposição Atômica em DAG & Paralelismo Fan-Out / Fan-In
Toda solicitação complexa é quebrada no maior número possível de **subtarefas atômicas, ortogonais e independentes**:
* **Fan-Out Simultâneo:** Todas as subtarefas com grau de entrada zero (sem dependências pendentes) são disparadas **simultaneamente no mesmo turno** via múltiplas chamadas paralelas a `invoke_subagent`.
* **Reúso Inteligente de Sessão vs. Paralelismo:** Subtarefas concorrentes utilizam instâncias paralelas via `invoke_subagent`; etapas sequenciais no mesmo domínio que se beneficiam do cache de contexto reutilizam o `conversationId` existente via `send_message`.

### 2.3. Auto-Model Routing Cognitivo
Ao invocar subagentes (`invoke_subagent(TypeName="self", Model=...)`) ou workers (`swarm`), o `orchestrator` seleciona o menor modelo e nível de esforço (`low`, `medium`, `high`, `xhigh`, `max`) capazes de resolver a subtarefa com excelência, otimizando latência e custo de tokens sobre o catálogo real de **23 modelos** do `agy`:

| Parâmetro `Model` | Complexidade & Esforço | Casos de Uso Ideais, Catálogo Completo (23 Modelos) & Regimes de Cota |
| :--- | :--- | :--- |
| **`"flash_lite"`** | **Tier 1: Baixa (Esforço `low` — I/O & Mecânica)** | Leitura de arquivos/configs/logs, listagens de diretórios, `git status`/`diff`, buscas rápidas no L2 (`mem search`), checagem de portas e formatação. **Reset Diário:** `gemini-3.8-flash-low`, `gemini-4-hydrogen-low`, `gemini-4-neon-low`, `claude-sonnet-5-5-low`, `claude-opus-5-5-low` \| **Reset Semanal (7d):** `gemini-4-argon-low`. |
| **`"flash"`** | **Tier 2: Média (Esforço `medium` — Operacional Padrão)** | Implementação de classes/funções delimitadas, testes unitários, scripts de automação, Dockerfiles, queries SQL (DDL/DML) e configurações de build. **Reset Diário:** `gemini-3.8-flash-medium`, `gemini-3.8-flash-high`, `gpt-oss-120b-medium`, `gemini-4-hydrogen-medium`, `gemini-4-neon-medium`, `claude-sonnet-5-5-medium`. |
| **`"pro"`** | **Tier 3: Alta (Esforço `high` / `xhigh` — Arquitetura Profunda)** | Clean Architecture / Ports & Adapters, concorrência crítica, refatoração estrutural pesada, BVA e debugging complexo preservando a cota semanal do Argon. **Reset Diário:** `gemini-4-neon-high`, `gemini-4-hydrogen-high`, `claude-sonnet-5-5-high`, `claude-opus-5-5-medium`, `gemini-4-neon-xhigh`, `gemini-4-hydrogen-xhigh`. |
| **`"inherit"`** | **Tier 4: Fronteira (Esforço `xhigh` / `max` / `high` Frontier)** | Decisões arquiteturais inéditas, desafios *frontier* extremos e auditoria adversarial. **Reset Diário:** `claude-opus-5-5-high`, `gemini-4-neon-xhigh`, `gemini-4-hydrogen-xhigh`, `gemini-pro-orchestrator-neon` \| **Reset Semanal (7d):** `gemini-4-argon-medium`, `gemini-4-argon-high`, `gemini-pro-orchestrator-g1-pro`. |

* **Auto-Failover Inteligente de Cota (429 / Quota Exhaustion):** Como o catálogo possui 23 modelos e 5 níveis de esforço (`low`, `medium`, `high`, `xhigh`, `max`) distribuídos em pools de cota independentes, se um worker encontrar exaustão de cota (`RESOURCE_EXHAUSTED` / HTTP 429) antes ou no meio de uma tarefa, o `orchestrator` redireciona automaticamente a execução para um modelo/tier de capacidade e esforço equivalentes com cota disponível (`flash_lite` $\leftrightarrow$ `flash` $\leftrightarrow$ `pro` $\leftrightarrow$ `inherit`, ou troca *in-place* entre as famílias Gemini 3.8 Flash, Gemini 4 Neon/Hydrogen/Argon, GPT-OSS, Claude Sonnet/Opus 5.5 e Orchestrator preservando o progresso parcial), concluindo a tarefa de forma transparente sem interromper o fluxo.

### 2.4. Lei Zero Inviolável (Protocolo Zero Assumptions)
Nenhum agente (`orchestrator` ou subagente) pode deduzir ou escolher silenciosamente diante de incertezas em:
1. **Requisitos e Regras de Negócio**
2. **Arquitetura de Software** (camadas, Ports & Adapters, contratos internos)
3. **Contratos Públicos de API e Schemas de Banco de Dados**
4. **Escolha ou Adição de Bibliotecas, Frameworks e Dependências**
5. **Segurança, Permissões e Escopo**

* **Calibragem Operacional:** Detalhes puramente mecânicos ou sintáticos internos que sigam estritamente os princípios SOLID e as convenções já existentes no repositório possuem autonomia técnica e não geram interrupções desnecessárias.
* **Fluxo de Delegação Ativa:** Diante de dúvida ou decisão estrutural, o subagente para imediatamente e emite `STATUS: NEED` (`target_domain: "orchestrator"`) listando `options: ["Opção 1 [Recomendada]", "Opção 2"]` e `recommendation`. O `orchestrator` pausa o fluxo e submete as opções e a recomendação técnica ao usuário, a quem pertence exclusivamente a decisão final.

### 2.5. Regra Single-Writer L1 & Invariante de Sincronia Tripla 1:1
* **Single-Writer de `CORE.md`:** Apenas o `orchestrator` possui permissão de escrita em `~/.gemini/memory/CORE.md` durante o fechamento do turno (*Shutdown Write-on-Delta* no Fan-In), validando obrigatoriamente o orçamento de $\le 60$ linhas via `~/.gemini/memory/mem check-core`.
* **Invariante de Sincronia Tripla 1:1 (`core-template-sync-invariant`):** Sempre que `~/.gemini/memory/CORE.template.md` for atualizado, o `orchestrator` deve atualizar no mesmo turno `~/.gemini/memory/CORE.md` e a constante `DEFAULT_CORE_TEMPLATE` dentro de `~/.gemini/memory/mem` (e vice-versa), garantindo paridade estrita linha a linha (variando unicamente nos placeholders `{{USER_NAME}}`, `{{USER_LANG}}` e `{{DEFAULT_WORKSPACE}}`).
* **SSOT de Identidade:** Dados pessoais do usuário (nome, idioma, caminhos de projetos privados) residem exclusivamente em `CORE.md` e no registro `global:user-profile` do banco L2 (`archival.db`), sendo proibido hardcodá-los em arquivos procedimentais versionados (`GEMINI.md`, `COMMON_INSTRUCTIONS.md`, `AGENT.md`, `README.md`).

### 2.6. Protocolo M2M Telegráfico (Differential Context Passing)
A comunicação Máquina $\leftrightarrow$ Máquina elimina 100% de preâmbulos conversacionais:

````carousel
```markdown
# 1. Disparo de Subtarefa Atômica (orchestrator -> Subagente)
[SUBAGENT_TASK]
AGENT_ID: <agent-<domain> | agent-default>
AGENT_DEF: ~/.gemini/agents/<agent-id>/AGENT.md
ATOMIC_GOAL: <Objetivo único, direto e verificável>
CONTEXT: <Apenas paths, snippets e invariantes estritamente necessários>
```
<!-- slide -->
```yaml
# 2. Escalação de Dúvida / Dependência / Handoff QA+AppSec (Subagente -> orchestrator)
STATUS: NEED
AGENT: <meu-agent-id>
NEEDS:
  - target_domain: "<domain | default | orchestrator>" # String única OU lista (ex: ["qa", "appsec"])
    atomic_goal: "<Ação necessária de outro domínio/gates OU dúvida/decisão a delegar ao usuário>"
    context: "<Resumo de mudanças, comandos de build/test, riscos ou cenário técnico>"
    options: ["<Opção 1 [Recomendada]>", "<Opção 2>"] # Obrigatório para dúvidas/decisões
    recommendation: "<Fundamentação técnica objetiva da opção recomendada>"
PATHS: ["<caminhos absolutos criados/modificados/inspecionados>"]
MEMORY_DELTA: "<none | namespace/topic gravado no L2 via mem upsert/link/defer>"
RESUME_WITH: "<Dado/decisão exata necessária para prosseguir OU confirmação QA+AppSec>"
```
<!-- slide -->
```yaml
# 3. Conclusão de Subtarefa (Subagente -> orchestrator)
STATUS: COMPLETED
AGENT: <meu-agent-id>
RESULT: "<Síntese técnica densa e direta do que foi executado/validado>"
PATHS: ["<caminhos absolutos criados/modificados/inspecionados>"]
MEMORY_DELTA: "<none | namespace/topic gravado no L2 via mem upsert/link/defer>"
```
````

> [!NOTE]
> O campo `target_domain` em `STATUS: NEED` aceita tanto uma string única (ex: `"rust"`, `"orchestrator"`) quanto uma lista de domínios (ex: `["qa", "appsec"]`). Todo agente de desenvolvimento (`EXTENDS: agent-dev-base`, exceto `agent-qa` e `agent-appsec` em auditoria) encerra alterações de código/config/infra/scripts emitindo obrigatoriamente `STATUS: NEED` com `target_domain: ["qa", "appsec"]`; reciprocamente, diante de qualquer falha ou vulnerabilidade, `agent-qa` e `agent-appsec` emitem `STATUS: NEED` com `target_domain: "<dev-stack>"` para correção no código, repetindo o ciclo até duplo `STATUS: COMPLETED`.

### 2.7. Dynamic Specialist Plugin Registry & Revisão de Fim de Conversa
Subagentes especialistas (`~/.gemini/agents/agent-<domain>/AGENT.md`) funcionam como plugins dinâmicos indexados na Seção 3 (`Semantic Directory`) de `CORE.md`.
* **Análise Obrigatória de Fim de Conversa & Sugestão Proativa de Especialistas (`end-of-conversation-specialist-review` / `proactive-specialist-suggestion`):** Ao final de **toda** conversa ou entrega com o usuário — independentemente de ter ocorrido fallback para `agent-default` ou não — o `orchestrator` analisa a conversa como um todo para verificar se compensa criar novos agentes especialistas (ex.: novo domínio/stack/workflow recorrente, ferramenta especializada ou sobrecarga de um especialista existente). Quando compensar, o `orchestrator` é **obrigado** a incluir na resposta final uma proposta estruturada dos especialistas recomendados, especificando:
  1. **Nome do Agente:** `agent-<domain>`
  2. **Caminho:** `~/.gemini/agents/agent-<domain>/AGENT.md`
  3. **Herança (`EXTENDS`):** Aplicável ao domínio, se houver
  4. **Escopo e Invariantes do Domínio**
  5. **Namespace L2 Primário:** `<domain>`
  6. **Justificativa do Benefício**
* *Calibragem Anti-Ruído:* Quando não compensar (domínio já bem coberto pelos especialistas atuais ou demanda puramente trivial/pontual), o `orchestrator` não deve forçar sugestões artificiais.

### 2.8. Pipeline Universal de Qualidade (`dev <-> qa / appsec`)
Toda demanda de desenvolvimento de software no ecossistema (independentemente da linguagem ou stack tecnológica) executa um ciclo bidirecional obrigatório no DAG antes da entrega final ao usuário:
1. **`dev` (Especialista da Linguagem/Stack):** Implementação ou refatoração aderente a SOLID, Clean Architecture / Ports & Adapters e invariantes do domínio. Antes de encerrar alterações de código (features, fixes, contratos, CLI/flags, APIs, dependências ou configs), verifica e atualiza obrigatoriamente as documentações impactadas (`README.md`, `docs/`, `CHANGELOG.md`, guias/schemas) no mesmo turno (**Doc-Sync Gate**) e executa o **Local CI Gate** (simulação local 1:1 de `.github/workflows/*.yml` com `zizmor` pedântico, `actionlint`, checagem de SHAs em Git Tags imutáveis/Node.js e execução real de linters/testes/SCA/`run:` do CI). Ao concluir qualquer alteração de código, configuração, infraestrutura ou scripts (mesmo após passar nos testes locais), todo agente que herda de `agent-dev-base` DEVE encerrar emitindo obrigatoriamente `STATUS: NEED` com `target_domain: ["qa", "appsec"]` (e não `STATUS: COMPLETED` isolado), informando resumo objetivo das mudanças, `PATHS`, comandos de build/test executados, status do Doc-Sync Gate, evidências do Local CI Gate e riscos/pontos de atenção.
2. **`qa` (`agent-qa`):** Quality Gate adversarial independente com testes de borda (BVA), *fuzzing*/*chaos*, linters, auditoria estrita de invariantes, execução obrigatória do **Local CI Gate** 1:1 com `.github/workflows/*.yml` antes de declarar `COMPLETED` e verificação de aderência documental (detecção de *drift* entre código e docs/schemas).
3. **`appsec` (`agent-appsec`):** Revisão contínua de segurança cobrindo OWASP/CWE, SAST, higienização de entradas e hardening de *supply-chain*.
* **Devolução Obrigatória & Loop de Bloqueio (`qa/appsec -> "<dev-stack>"`):** Sempre que `agent-qa` ou `agent-appsec` encontrar **qualquer** falha, regressão, violação de invariante, bug, vulnerabilidade ou achado de segurança, DEVE emitir obrigatoriamente `STATUS: NEED` direcionado ao `target_domain: "<dev-stack>"` do agente dev especialista adequado com relatório forense acionável (arquivo, linha, causa raiz, severidade, reprodução/evidência e correção esperada) para que o dev corrija o código — jamais encerrando com `STATUS: COMPLETED` com achados abertos. Após corrigir, o dev reemite `STATUS: NEED` (`target_domain: ["qa", "appsec"]`), repetindo o ciclo até que ambos aprovem com `STATUS: COMPLETED`.
* **Salvaguarda Anti-Loop:** `agent-qa` e `agent-appsec` (que também herdam de `agent-dev-base`) são isentos do handoff `["qa", "appsec"]` ao concluírem suas validações/auditorias — emitem `STATUS: COMPLETED` apenas quando 100% aprovado (zero achados abertos) ou `STATUS: NEED` para `"<dev-stack>"` quando houver achados.
* **Exceções Estritas de Escopo:** O handoff e o encadeamento completo são dispensados apenas em tarefas estritamente *read-only* (sem edição de arquivos), geração de mensagens de commit/PR ou ajustes textuais triviais sem alteração de código/config/infra/scripts.

### 2.9. Diagrama Arquitetural Completo

```mermaid
flowchart TB
    User(["👤 Usuário (SSOT em CORE.md)"])

    subgraph StarCenter["🎯 Centro da Topologia Estrela (Sessão Principal)"]
        Orch["<b>orchestrator</b><br/>DAG Scheduler & Auto-Model Router<br/><i>Zero Execução Direta de Domínio</i>"]
        Discovery["🔍 <b>Discovery Read-Only Leve (Turno 1)</b><br/>Whitelist Semântica (Manifestos/Configs)<br/>Teto Estrito: &lt; 16 KB / ~400 linhas"]
        Orch --> Discovery
    end

    subgraph Tier1["🔥 Memória L1 (Hot In-Context Cache)"]
        CoreMD["<b>~/.gemini/memory/CORE.md</b><br/>Orçamento Estrito: &le; 60 linhas<br/>1. Perfil &amp; Invariantes<br/>2. Ambiente &amp; Caminhos<br/>3. Semantic Directory"]
        CoreTpl["<b>CORE.template.md</b> &amp;<br/><b>DEFAULT_CORE_TEMPLATE</b>"]
        CoreLock["🔒 <b>.core.lock</b><br/>POSIX fcntl / Win msvcrt"]
        CoreTpl <-->|"Sincronia Tripla 1:1"| CoreMD
        CoreLock -.->|"Protege I/O"| CoreMD
    end

    subgraph DAGFanOut["⚡ DAG Fan-Out / Fan-In Paralelo (Protocolo M2M Telegráfico)"]
        SubDefault["⚙️ <b>agent-default</b><br/>Fallback Generalista (De Fábrica no Starter Kit)<br/>Model: flash_lite | flash | pro | inherit"]
        SubDomain["🧩 <b>agent-&lt;domain&gt;</b><br/>Plugins Especialistas Sob Demanda (Locais)<br/><i>Ex: agent-postgres, agent-rust, agent-k8s</i>"]
    end

    subgraph Tier2["🏛️ Motor Cognitivo L2 (~/.gemini/memory/mem — Arquitetura Hexagonal / Schema v3)"]
        Controller["<b>Driving Adapter</b><br/>MemoryEngineController &amp; CLI Parser (--json)"]
        Domain["<b>Pure Domain Core</b><br/>DomainPolicy, Entities &amp; Architectural Ports"]
        Repo["<b>Driven Adapters</b><br/>SqliteMemoryRepository | MarkdownWikiAdapter | UtcClockAdapter"]
        DB[("<b>archival.db (SQLite WAL)</b><br/>busy_timeout=30000 | BEGIN IMMEDIATE<br/>• memories + memories_fts (BM25 * confidence)<br/>• memory_history (Snapshots v1..vN)<br/>• memory_edges (Grafo Semântico)<br/>• prospective_tasks (Defer/Due/Done)<br/>• synonyms (N-Grams) | schema_migrations")]

        Controller --> Domain
        Domain --> Repo
        Repo --> DB
    end

    User <-->|"1. Demanda / 6. Resposta Executiva +<br/>Opções Lei Zero / Sugestão Proativa"| Orch
    Orch -->|"Leitura L1 no Turno 1"| CoreMD
    Orch ==>|"2. Fan-Out Paralelo: [SUBAGENT_TASK]<br/>Auto-Model Routing"| SubDefault & SubDomain
    SubDefault & SubDomain -.->|"Leitura Read-Only no Boot"| CoreMD
    SubDefault & SubDomain ==>|"3. Acesso Concorrente Seguro<br/>search / recall-error / upsert / link / defer"| Controller
    SubDefault & SubDomain ==>|"4. Fan-In: STATUS: COMPLETED (MEMORY_DELTA)<br/>ou STATUS: NEED (Opções Lei Zero)"| Orch
    Orch ==>|"5. Single-Writer Shutdown Write-on-Delta<br/>+ Validação mem check-core (&le; 60 linhas)"| CoreMD
```

---

## 3. Arquitetura Cognitiva Híbrida das 7 Memórias

Inspirada na convergência entre arquiteturas cognitivas modernas (*Letta/MemGPT, CoALA, Mem0 e Zep/Graphiti*), a camada de persistência do Antigravity divide o conhecimento em **2 Tiers físicos** e **7 subsistemas cognitivos especializados**:

```mermaid
flowchart LR
    subgraph SevenMemories["🧠 Arquitetura Cognitiva das 7 Memórias"]
        M1["<b>1. Working Memory (L1)</b><br/>CORE.md (&le; 60 linhas)<br/>+ Scratchpad Anti-Amnésia"]
        M2["<b>2. Semantic / Declarative (L2)</b><br/>fact, decision, invariant, behavior<br/>Grafo (memory_edges) + TTL + History v3"]
        M3["<b>3. Episodic Memory (L2)</b><br/>kind='learning' + [DEAD-ENDS]<br/>mem recall-error (episodic_boost)"]
        M4["<b>4. Procedural Memory</b><br/>AGENT.md enxutos<br/>+ Receitas L2 (kind='playbook')"]
        M5["<b>5. Retrieval Memory (L2)</b><br/>FTS5 unicode61 + Sinônimos N-Gram<br/>BM25 Normalizado * Confidence"]
        M6["<b>6. Parametric Memory</b><br/>Auto-Model Routing Cognitivo<br/>flash_lite / flash / pro / inherit"]
        M7["<b>7. Prospective Memory (L2)</b><br/>prospective_tasks (defer/due/done)<br/>Alertas Reativos em search &amp; get"]
    end

    M1 -->|"Semantic Directory<br/>(Lazy Loading)"| M5
    M5 --> M2 & M3 & M4
    M7 -.->|"Injeta 🔔 PROSPECTIVE DUE"| M5
    M6 -.->|"Calibra Capacidade<br/>do Worker"| M1
```

### 3.1. Working Memory (Memória de Trabalho L1 + Scratchpad Físico Anti-Amnésia)
* **Cache Quente L1 (`~/.gemini/memory/CORE.md`):** Mantido sob orçamento rigoroso de **$\le 60$ linhas** (auditado via `mem check-core`, configurável por `--max-lines` ou pela variável de ambiente `ANTIGRAVITY_CORE_MAX_LINES`). Estruturado em 3 seções fixas:
  1. *Perfil & Invariantes Globais do Usuário (SSOT de Identidade)*
  2. *Ambiente Ativo & Caminhos-Chave*
  3. *Semantic Directory (Ponteiros L2 & Plugins Especialistas)*
* **Persistência Física Anti-Amnésia:** É proibido truncar ou resumir saídas volumosas no chat. Qualquer processamento extenso, log ou diff longo deve ser gravado integralmente em arquivo físico (ex: `output_full.txt` ou `.task_context`) e ter seu caminho absoluto retornado no array `PATHS` do payload M2M.

### 3.2. Semantic & Declarative Memory (Memória Semântica, Grafo, Proveniência & Versionamento L2 v3)
Reside na tabela `memories` do SQLite L2 (`archival.db`) organizada por `namespace` (`<domain>` ou `proj:<repo>`) e `topic`:
* **Tipos Declarativos (`kind`):**
  * `fact`: Fatos objetivos, versões, portas, caminhos e configurações (recebe **TTL padrão de 30 dias** automaticamente se `--ttl` for omitido).
  * `decision`: Decisões arquiteturais e técnicas aprovadas (ADRs enxutos, TTL infinito por padrão).
  * `invariant`: Regras técnicas invioláveis e restrições permanentes do domínio.
  * `behavior`: Heurísticas operacionais e preferências de execução.
* **Semantic Freshness (TTL & Revalidação):** Registros com `ttl_days` definido são monitorados continuamente. Quando $\text{elapsed\_days} > \text{ttl\_days}$, leituras via `search`, `get` ou `recall-error` emitem automaticamente o alerta:
  `⚠️ STALE MEMORY (verificada há Xd, TTL=Yd — revalide no ambiente e rode 'mem verify <ns> "<topic>"')`.
* **Grafo Semântico Direcionado (`memory_edges`):** Tópicos são conectados por arestas tipadas (`DEPENDS_ON`, `RELATES_TO`, `SUPERSEDES`, etc.) via `mem link`, com exclusão em cascata (`ON DELETE CASCADE`) e exibição bidirecional (`out` `--(REL)-->` e `in` `<--(REL)--`) no comando `mem get`.
* **Versionamento Automático, Proveniência & Soft-Delete (Schema v3):**
  * Cada registro possui `version` (iniciado em `1` e auto-incrementado a cada `upsert` ou `import-md`), `source` (identificador do agente ou autor, ex: `--source "agent-default"`) e `confidence` (fator de confiança no intervalo $[0.0, 1.0]$).
  * Antes de qualquer atualização ou soft-delete, o estado anterior completo é arquivado de forma imutável na tabela **`memory_history`**, auditável via `mem history <ns> "<topic>" [--json]`.
  * O comando `mem delete <ns> "<topic>"` executa **soft-delete por padrão** (preenchendo `deleted_at` e removendo a entrada do índice FTS5 ativo sem perder o registro ou seu histórico), permitindo recuperação imediata via `mem restore <ns> "<topic>"`. A remoção física ocorre apenas quando `--hard` é explicitamente informado.
* **Interoperabilidade Wiki Markdown (`export-md` / `import-md`):** Exporta e importa todo o banco L2 (incluindo metadados v3 e arestas do grafo convertidas em WikiLinks `[[ns/topic]]`) para arquivos Markdown compatíveis com Obsidian/Logseq e índice `INDEX.md`. Para evitar colisões de nomes em tópicos que diferem apenas por pontuação ou caixa, o `MarkdownWikiAdapter` aplica um sufixo determinístico de **6 caracteres hexadecimais SHA-256** (`<slug>_<sha256[:6]>.md`).

### 3.3. Episodic Memory (Memória Episódica & Diagnóstico de Erros)
* **Registros `kind='learning'` com Dead-Ends Obrigatórios:** Toda lição aprendida após a resolução de um bug ou problema complexo deve conter a seção **`[DEAD-ENDS / TENTATIVAS DESCARTADAS]`**, documentando o que falhou e por quê, evitando que futuros agentes repitam hipóteses inválidas.
* **Motor `mem recall-error "<snippet_ou_stacktrace>"`:**
  1. Extrai palavras alfanuméricas ($\ge 3$ caracteres) do stacktrace ou mensagem de erro.
  2. Realiza *split* automático de identificadores `CamelCase` (`CAMEL_CASE_SPLIT`) e `snake_case`, preservando tanto o token composto quanto suas partes elementares.
  3. Filtra ruídos contra um conjunto estrito de **46 `ERROR_STOPWORDS`** de linguagens e runtimes (`error`, `exception`, `traceback`, `null`, `java`, `lang`, `runtime`, `function`, `method`, etc.).
  4. Ordena os candidatos por especificidade (comprimento decrescente `(-len(x), x)`), seleciona até **24 termos** e executa a busca FTS5 com **`prioritize_episodic=True`**, ativando a coluna calculada `episodic_boost = 1` para posicionar registros `learning` e `playbook` no topo absoluto dos resultados.

### 3.4. Procedural Memory (Memória Procedural)
Dividida em duas camadas complementares:
1. **Instruções Estáticas Enxutas (`AGENT.md`):** Definições de papéis, fronteiras de domínio e invariantes operacionais em `~/.gemini/agents/<agent-id>/AGENT.md`.
2. **Playbooks Dinâmicos (`kind='playbook'` no L2):** Receitas passo a passo reutilizáveis (procedimentos de build, migrações, deploys, checklists de diagnóstico) gravadas e versionadas no banco `archival.db`.

### 3.5. Retrieval Memory (Motor de Busca Híbrida FTS5, Sinônimos N-Gram & Ranking BM25)
* **Indexação Léxica Diacrítico-Insensível:** Utiliza a tabela virtual `memories_fts` com `fts5(..., content='memories', content_rowid='id', tokenize='unicode61 remove_diacritics 2')`. Termos simples de no mínimo 2 caracteres (`MIN_TOKEN_LENGTH = 2`) recebem busca por prefixo (`"termo"*`), enquanto frases ou termos entre aspas duplas realizam busca exata (`"termo"`).
* **Expansão Dinâmica de Sinônimos (1-Gram, 2-Gram e 3-Gram):** Antes de consultar o FTS5, `DomainPolicy.build_fts_query` analisa a query completa, trigramas, bigramas e unigramas contra a tabela `synonyms` (pré-populada no boot com **12 grupos de sinônimos técnicos** `DEFAULT_SYNONYM_GROUPS`, como `k8s` $\leftrightarrow$ `kubernetes`, `loom` $\leftrightarrow$ `virtual threads`, `hexagonal` $\leftrightarrow$ `ports and adapters` $\leftrightarrow$ `clean architecture`, `postgres` $\leftrightarrow$ `postgresql` $\leftrightarrow$ `psql`, etc., e extensível via `mem syn add`).
* **Fórmula Matemática de Ranking Híbrido (BM25 Normalizado + Hits + Confiança + Decaimento Temporal):**
  Como a função nativa `bm25()` do SQLite FTS5 retorna valores negativos (onde valores mais negativos indicam maior relevância), multiplicá-la diretamente por fatores de boost inverteria a ordenação. O motor `mem` normaliza o score invertendo seu sinal (`-1.0 * bm25(...)`) com piso `0.0001`, aplica pesos diferenciados por coluna (`topic=5.0`, `content=1.0`, `tags=3.0`, `namespace=0.5`), escala logaritmicamente/linearmente pelos acessos (`access_count` com teto em 30 hits), pondera pelo fator `confidence` do Schema v3 e aplica decaimento temporal suave em dias:

$$\text{relevance\_score} = \frac{\max\left(0.0001,\; -1.0 \times \text{bm25}(\text{memories\_fts},\; 5.0,\; 1.0,\; 3.0,\; 0.5)\right) \times \left(1.0 + 0.15 \times \min(\text{access\_count},\; 30)\right) \times \text{confidence}}{1.0 + 0.02 \times \max\left(0.0,\; \text{julianday}(\text{'now'}) - \text{julianday}(\text{updated\_at})\right)}$$

> [!NOTE]
> Toda leitura bem-sucedida via `mem get`, `mem search` ou `mem recall-error` incrementa transacionalmente o contador `access_count` dos registros retornados, retroalimentando a relevância dos conhecimentos mais úteis e habilitando sua promoção para o `CORE.md` via `mem promote`.

### 3.6. Parametric Memory (Memória Paramétrica via Auto-Model Routing)
Trata a capacidade intrínseca dos diferentes pesos de modelos (`flash_lite`, `flash`, `pro`, `inherit` / **Gemini 4 Argon**) como um recurso cognitivo roteável por subtarefa pelo `orchestrator` (conforme detalhado na [Seção 2.3](#23-auto-model-routing-cognitivo)).

### 3.7. Prospective Memory (Memória Prospectiva & Gatilhos Assíncronos)
Gerenciada na tabela `prospective_tasks` através dos comandos `mem defer`, `mem due` e `mem done`:
* Permite que qualquer subagente agende lembretes técnicos ou ações futuras atreladas a uma condição de disparo (`trigger_cond`) dentro de um `namespace`.
* **Injeção Reativa Automática:** Sempre que um agente executa `mem search` ou `mem get` (em modo texto padrão) sobre um namespace que possui tarefas prospectivas com `status = 'pending'`, o controlador injeta automaticamente no topo da saída o alerta:
  `🔔 PROSPECTIVE DUE [<namespace>]: #<id> [<trigger_cond>] -> <action>`
* Tarefas pendentes também são consolidadas e reportadas globalmente na auditoria `mem check-core`.

---

## 4. Engenharia Interna do Motor L2 (`~/.gemini/memory/mem`)

O executável [`~/.gemini/memory/mem`](memory/mem) (~2.600 linhas) foi desenhado como um binário Python 3 autocontido (**zero dependências externas**, utilizando exclusivamente a biblioteca padrão: `argparse`, `contextlib`, `hashlib`, `json`, `os`, `re`, `sqlite3`, `sys`, `dataclasses`, `datetime`, `typing`, `fcntl`/`msvcrt`), estruturado rigorosamente segundo **Clean Architecture (Ports & Adapters)** e os princípios **SOLID**.

### 4.1. Camadas da Arquitetura Hexagonal em Arquivo Único

| Seção Arquitetural no Código | Componentes Principais | Responsabilidade Estrita |
| :--- | :--- | :--- |
| **1. Domain Exceptions & Entities** | `DomainValidationError`, `ResourceNotFoundError`, `MemoryRecord`, `MemoryHistoryRecord`, `SemanticEdge`, `ProspectiveTask`, `NamespaceStat`, `StorageStats`, `WikiDocument` | Objetos de valor imutáveis (`@dataclass(frozen=True, slots=True)`) e exceções semânticas de negócio sem acoplamento de I/O. |
| **2. Architectural Ports** | `ClockPort`, `MemoryRepositoryPort` (`typing.Protocol`) | Contratos abstratos (Interfaces) que invertem a dependência (DIP) entre as regras de negócio/controlador e a infraestrutura física. |
| **3. Pure Domain Policies** | `DomainPolicy` | Validação de namespaces (`^[a-z0-9][a-z0-9_-]*$` ou `^proj:[a-zA-Z0-9._-]+$`), `VALID_KINDS`, `confidence` ($[0.0, 1.0]$), parsing de TTL, cálculo de *staleness*, construção de queries FTS5 com n-grams de sinônimos e tokenização de stacktraces. |
| **4. Driven Adapters (Infra)** | `file_lock`, `immediate_transaction`, `UtcClockAdapter`, `SqliteMemoryRepository`, `MarkdownWikiAdapter` | Persistência SQLite WAL + FTS5, migrações automáticas de schema, bloqueio de arquivo cross-platform e parser resiliente de YAML Frontmatter / WikiLinks. |
| **5. Driving Adapter (App/CLI)** | `MemoryEngineController`, `build_parser`, `main` | Orquestração de casos de uso, formatação de saída dual (Humana ou JSON estruturado via `--json`) e tratamento limpo de erros na borda (`sys.exit(1)` sem expor tracebacks brutos ao agente). |

### 4.2. Controle de Concorrência, Transações Reentrantes & File Locking
Para suportar dezenas de subagentes executando em paralelo durante um Fan-Out do DAG sem erros de `SQLITE_BUSY` ou corrupção de arquivos:
1. **Pragmas de Alta Concorrência:** Na abertura de cada conexão, `SqliteMemoryRepository._get_conn()` aplica:
   * `PRAGMA busy_timeout=30000;` (30 segundos de espera ativa em contenção de escrita)
   * `PRAGMA journal_mode=WAL;` (*Write-Ahead Logging* permitindo leituras paralelas sem bloqueio durante escritas)
   * `PRAGMA synchronous=NORMAL;`, `PRAGMA temp_store=MEMORY;` e `PRAGMA foreign_keys=ON;`
2. **Context Manager Reentrante `immediate_transaction(conn)`:** Utiliza conexões em modo `isolation_level=None` (autocommit nativo do driver) e gerencia transações explicitamente com `BEGIN IMMEDIATE;`. Ao verificar `is_outer = not conn.in_transaction`, permite composição segura de métodos internos com commit/rollback atômico apenas no escopo mais externo.
3. **File Lock Cross-Platform (`file_lock`):** Operações sobre `CORE.md` (`init` e `check-core`) adquirem um lock exclusivo de sistema operacional sobre `~/.gemini/memory/.core.lock`, utilizando `fcntl.flock(fd, fcntl.LOCK_EX)` em sistemas POSIX (Linux/macOS) e `msvcrt.locking(fd, msvcrt.LK_LOCK, 1)` no Windows (`nt`).
4. **Hot Backup Online (`mem backup`):** Utiliza a API nativa `sqlite3.Connection.backup()` para copiar páginas do banco de forma transacionalmente consistente para `~/.gemini/memory/backups/archival_<timestamp>.db` (ou caminho customizado) sem interromper escritas concorrentes.

### 4.3. Máquina de Estados dos Triggers FTS5 External Content (Guarda de 5 Transições)
A tabela virtual `memories_fts` utiliza `content='memories'` (*External Content Table*) para evitar duplicação de texto no disco. No SQLite FTS5, emitir o comando `'delete'` na tabela virtual para um `rowid` que já havia sido removido em um soft-delete anterior **não é idempotente** — isso gera inconsistência na B-Tree invertida e corrompe o banco com `SQLITE_CORRUPT (database disk image is malformed)`.

Para resolver isso matematicamente, os triggers `memories_ai`, `memories_ad` e `memories_au` implementam uma **Máquina de Estados Determinística com Guarda Dupla** (`WHERE old.deleted_at IS NULL` e `WHERE new.deleted_at IS NULL`):

```sql
CREATE TRIGGER IF NOT EXISTS memories_au
AFTER UPDATE OF topic, content, tags, namespace, deleted_at ON memories BEGIN
    -- Só remove do índice FTS5 se o estado ANTERIOR estava ATIVO:
    INSERT INTO memories_fts(memories_fts, rowid, topic, content, tags, namespace)
    SELECT 'delete', old.id, old.topic, old.content, old.tags, old.namespace
    WHERE old.deleted_at IS NULL;

    -- Só insere no índice FTS5 se o estado NOVO permanece/passa a ser ATIVO:
    INSERT INTO memories_fts(rowid, topic, content, tags, namespace)
    SELECT new.id, new.topic, new.content, new.tags, new.namespace
    WHERE new.deleted_at IS NULL;
END;
```

Esta guarda cobre com 100% de segurança todas as **5 transições de estado possíveis**:
1. **Criação (`None` $\rightarrow$ `Ativo`):** `memories_ai` insere no FTS5 (`WHEN new.deleted_at IS NULL`).
2. **Atualização Ativa (`Ativo` $\rightarrow$ `Ativo`):** `memories_au` remove os termos antigos (`old.deleted_at IS NULL`) e indexa os novos (`new.deleted_at IS NULL`).
3. **Soft-Delete (`Ativo` $\rightarrow$ `Soft-Deleted`):** `memories_au` remove os termos antigos do FTS5 (`old.deleted_at IS NULL`) e omite a reinserção (`new.deleted_at IS NOT NULL`).
4. **Mutação de Registro Arquivado (`Soft-Deleted` $\rightarrow$ `Soft-Deleted`):** `memories_au` opera como **NO-OP** puro (nenhum `SELECT` retorna linhas), prevenindo dupla deleção e corrupção da B-Tree.
5. **Reativação via `restore` ou `upsert` (`Soft-Deleted` $\rightarrow$ `Ativo`):** `memories_au` omite a deleção (`old.deleted_at IS NOT NULL`) e indexa apenas o novo estado ativo (`new.deleted_at IS NULL`).

---

## 5. Ciclo de Vida End-to-End (Walkthrough em 4 Fases)

```mermaid
sequenceDiagram
    autonumber
    actor U as 👤 Usuário
    participant O as 🎯 orchestrator
    participant L1 as 📄 CORE.md (L1)
    participant W1 as ⚡ Subagente A (flash_lite)
    participant W2 as 🧠 Subagente B (pro)
    participant L2 as 🏛️ Motor L2 (mem / archival.db)

    U->>O: Envia solicitação complexa de engenharia
    O->>L1: 1. Lê Perfil, Invariantes e Semantic Directory
    O->>O: 2. Discovery Read-Only Leve (<16 KB) se necessário
    O->>W1: 3a. Fan-Out Paralelo [SUBAGENT_TASK] (Inspeção/Logs)
    O->>W2: 3b. Fan-Out Paralelo [SUBAGENT_TASK] (Arquitetura/Código)
    par Boot & Execução Concorrente 2-Tier
        W1->>L1: Lê CORE.md + COMMON_INSTRUCTIONS + AGENT.md
        W1->>L2: mem search / mem recall-error --json
        W2->>L1: Lê CORE.md + COMMON_INSTRUCTIONS + AGENT.md
        W2->>L2: mem get / mem history
    end
    alt Bifurcação Arquitetural Detectada (Lei Zero)
        W2-->>O: STATUS: NEED (options + recommendation)
        O-->>U: Saudação pelo nome + Opções Estruturadas + Recomendação
        U->>O: Aprova Opção 1
        O->>W2: send_message (RESUME_WITH: Opção 1 aprovada)
    end
    W1->>L2: mem upsert (source="agent-...", confidence=1.0)
    W2->>L2: mem upsert + mem link
    W1-->>O: STATUS: COMPLETED (RESULT, PATHS, MEMORY_DELTA)
    W2-->>O: STATUS: COMPLETED (RESULT, PATHS, MEMORY_DELTA)
    O->>L1: 4. Single-Writer Fan-In: Atualiza CORE.md (se houver delta L1)
    O->>L2: 5. Valida orçamento: mem check-core (<= 60 linhas)
    O-->>U: 6. Saudação Limpa + Síntese Executiva + Revisão de Especialistas (se compensar)
```

1. **Fase 1 — Boot L1 & Discovery Leve (Turno 1):** O `orchestrator` recebe a mensagem do usuário, lê `~/.gemini/memory/CORE.md` para identificar o nome do usuário, seus invariantes e os especialistas disponíveis no `Semantic Directory`. Se precisar reconhecer a estrutura do repositório alvo, lê apenas manifestos de topo dentro da whitelist semântica (`< 16 KB`).
2. **Fase 2 — Decomposição DAG, Auto-Model Routing & Lei Zero:** O `orchestrator` divide o problema em subtarefas ortogonais, seleciona o `Model` ideal (`flash_lite`, `flash`, `pro` ou `inherit`) e dispara múltiplos subagentes em paralelo com o cabeçalho `[SUBAGENT_TASK]`. Se surgir qualquer dúvida de negócio, contrato ou arquitetura, o fluxo pausa via `STATUS: NEED` e consulta o usuário com opções e recomendação técnica.
3. **Fase 3 — Execução 2-Tier & Persistência L2 Concorrente:** Cada subagente realiza o boot enxuto lendo em paralelo `CORE.md`, `COMMON_INSTRUCTIONS.md` e seu `AGENT.md`. Consulta o L2 sob demanda (`mem search`, `mem get` ou `mem recall-error` diante de falhas), executa sua tarefa estritamente dentro do domínio, grava novos aprendizados no L2 (`mem upsert` com `--source` e `--confidence`) sem tocar no `CORE.md`, e retorna `STATUS: COMPLETED` informando `MEMORY_DELTA` e `PATHS`.
4. **Fase 4 — Fan-In Single-Writer, Auditoria `check-core` & Resposta Final:** O `orchestrator` consolida os resultados, atualiza o `CORE.md` se houver novos ponteiros estruturais (mantendo a sincronia tripla 1:1 caso altere o template), executa `mem check-core` para atestar o limite de $\le 60$ linhas e entrega a resposta iniciando com a saudação limpa pelo nome do usuário — incluindo a revisão de fim de conversa com sugestão estruturada de novos `agent-<domain>` sempre que o contexto demonstrar benefício real (sem forçar sugestões artificiais em demandas triviais ou já bem cobertas).

---

## 6. Estrutura do Repositório & Isolamento Git (Starter Kit)

O arquivo [`.gitignore`](.gitignore) adota uma política **Default-Deny (`*`) com Whitelist Explícita**, separando rigorosamente o **Starter Kit Portável** (versionado no Git — que inclui de fábrica **apenas** os agentes `orchestrator` e `agent-default`) do **Estado Local e Privado do Usuário** (ignorado pelo Git, incluindo o banco de dados, `CORE.md` e quaisquer especialistas `agent-<domain>` criados sob demanda):

```text
~/.gemini/
├── .gitignore                        # ✅ [Versionado - Starter Kit] Regra '*' + Whitelist estrita do Starter Kit
├── GEMINI.md                         # ✅ [Versionado - Starter Kit] Constituição Global (Lei Zero, Estrela, M2M, 7 Memórias)
├── README.md                         # ✅ [Versionado - Starter Kit] Documentação Arquitetural e Operacional Completa
├── README.en.md                      # ✅ [Versionado - Starter Kit] Documentação Arquitetural e Operacional (English)
├── README.es.md                      # ✅ [Versionado - Starter Kit] Documentação Arquitetural e Operacional (Español)
├── README.zh-CN.md                   # ✅ [Versionado - Starter Kit] Documentação Arquitetural e Operacional (简体中文)
│
├── agents/
│   ├── COMMON_INSTRUCTIONS.md        # ✅ [Versionado - De Fábrica] Protocolo compartilhado 2-Tier, CLI mem e M2M
│   ├── orchestrator/
│   │   └── AGENT.md                  # ✅ [Versionado - De Fábrica] Escalonador DAG, Auto-Model Router e Single-Writer L1
│   ├── agent-default/
│   │   └── AGENT.md                  # ✅ [Versionado - De Fábrica] Subagente Generalista Executor (Fallback & Bootstrap)
│   ├── agent-dev-base/               # 🔒 [Ignorado - Local] Base abstrata SSOT (EXTENDS) com 9 invariantes de engenharia
│   │   └── AGENT.md
│   └── agent-<domain>/               # 🔒 [Ignorado - Local] Plugins especialistas criados sob demanda pelo usuário
│       └── AGENT.md                  #    (19 plugins locais ativos: 15 EXTENDS agent-dev-base + 4 independentes — ver Seção 8.1)
│
├── memory/
│   ├── mem                           # ✅ [Versionado - Starter Kit] Motor Cognitivo L2 Hexagonal em Python 3 (Schema v3)
│   ├── CORE.template.md              # ✅ [Versionado - Starter Kit] Template canônico da Memória Quente L1 (<= 60 linhas)
│   ├── tests/
│   │   ├── test_mem.py               # ✅ [Versionado - Starter Kit] Suíte com 21 testes automatizados do motor L2 (unittest stdlib)
│   │   └── test_catalog_parity.py    # ✅ [Versionado - Starter Kit] Suíte de paridade de catálogo (agentes/CORE/dev-base/README)
│   ├── CORE.md                       # 🔒 [Ignorado - Local] Cache L1 renderizado com a identidade real do usuário
│   ├── .core.lock                    # 🔒 [Ignorado - Local] Lockfile cross-platform de exclusão mútua do CORE.md
│   ├── archival.db                   # 🔒 [Ignorado - Local] Banco SQLite WAL + FTS5 local ( + -wal / -shm )
│   ├── backups/                      # 🔒 [Ignorado - Local] Snapshots online gerados por 'mem backup'
│   └── wiki/                         # 🔒 [Ignorado - Local] Exportações Markdown geradas por 'mem export-md'
│
└── antigravity-cli/                  # 🔒 [Ignorado - Local] Configurações locais do cliente CLI (settings.json)
```

---

## 7. Instalação, Menor Privilégio & First-Boot Onboarding

### 7.1. Requisitos de Sistema
* **Sistema Operacional:** Linux, macOS ou Windows.
* **Runtime:** `python3` ($\ge 3.10$) com o módulo padrão `sqlite3` compilado com suporte à extensão **FTS5** (habilitado por padrão nas distribuições modernas de Python 3).
* **Dependências Externas (`pip`):** **Nenhuma** (Zero dependências).

### 7.2. Instalação Rápida
```bash
# 1. Clone o Starter Kit diretamente em ~/.gemini (ou copie os arquivos para lá)
git clone <url-do-repositorio> ~/.gemini

# 2. Garanta permissão de execução para a CLI do motor de memória L2
chmod +x ~/.gemini/memory/mem

# 3. Execute a suíte de testes para validar o ambiente Python + SQLite FTS5
python3 -m unittest discover -s ~/.gemini/memory/tests/ -v
```

### 7.3. Configuração de Menor Privilégio (`~/.gemini/antigravity-cli/settings.json`)
Para que o `orchestrator` e os subagentes leiam/gravem memórias técnicas sem fricção e operem com o modelo de fronteira padrão (**Gemini 4 Argon**), configure as permissões explícitas em `~/.gemini/antigravity-cli/settings.json` (substituindo `<seu_usuario>` pelo seu usuário do sistema):

```json
{
  "allowNonWorkspaceAccess": true,
  "model": "Gemini 4 Argon (Medium)",
  "permissions": {
    "allow": [
      "read_file(/home/<seu_usuario>/.gemini/memory)",
      "write_file(/home/<seu_usuario>/.gemini/memory)",
      "read_file(/home/<seu_usuario>/.gemini/agents)",
      "write_file(/home/<seu_usuario>/.gemini/agents)",
      "read_file(/home/<seu_usuario>/.gemini/GEMINI.md)",
      "write_file(/home/<seu_usuario>/.gemini/GEMINI.md)",
      "command(/home/<seu_usuario>/.gemini/memory/mem)",
      "command(ls)",
      "command(grep)",
      "command(wc)"
    ]
  },
  "trustedWorkspaces": [
    "/home/<seu_usuario>/.gemini",
    "/home/<seu_usuario>/.gemini/memory",
    "/home/<seu_usuario>/.gemini/agents"
  ]
}
```

### 7.4. First-Boot Onboarding (2 Modos)

#### Opção A: Onboarding Interativo Automático via Chat
Ao iniciar a primeira conversa quando `CORE.md` ainda não existe ou contém `Usuário: [UNCONFIGURED]`, o `orchestrator` executa automaticamente o **First-Boot Onboarding Protocol**:
1. Aciona o `agent-default` para inicializar a infraestrutura (`~/.gemini/memory/mem init`).
2. Pergunta ao usuário seu **Nome de exibição**, **Idioma preferido** e **Workspace padrão**.
3. Renderiza `~/.gemini/memory/CORE.md` e grava o registro `global:user-profile` no banco L2.

#### Opção B: Onboarding Direto via Terminal (CLI)
Você pode inicializar o banco `archival.db` (populando os 8 registros fundacionais do namespace `global` e suas arestas semânticas) e gerar o `CORE.md` em um único comando:

```bash
~/.gemini/memory/mem init \
  --user "SeuNome" \
  --lang "pt-BR" \
  --workspace "/home/<seu_usuario>/workspace" \
  --force
```

### 7.5. Variáveis de Ambiente Suportadas pelo Motor `mem`
O motor `~/.gemini/memory/mem` permite sobrescrever seus caminhos e limites via variáveis de ambiente (útil para isolamento de testes ou workspaces customizados):

| Variável de Ambiente | Valor Padrão | Descrição |
| :--- | :--- | :--- |
| `ANTIGRAVITY_DB_PATH` | `~/.gemini/memory/archival.db` | Caminho absoluto do arquivo de banco SQLite L2. |
| `ANTIGRAVITY_CORE_PATH` | `~/.gemini/memory/CORE.md` | Caminho absoluto do arquivo de Memória Quente L1. |
| `ANTIGRAVITY_CORE_TEMPLATE_PATH` | `~/.gemini/memory/CORE.template.md` | Caminho do template base usado pelo comando `mem init`. |
| `ANTIGRAVITY_CORE_LOCK_PATH` | `~/.gemini/memory/.core.lock` | Caminho do arquivo de lock exclusivo cross-platform. |
| `ANTIGRAVITY_CORE_MAX_LINES` | `60` | Orçamento máximo de linhas validado por `mem check-core`. |

---

## 8. Ecossistema de Subagentes & Criação de Especialistas (`agent-<domain>`)

Apenas **dois agentes vêm de fábrica no Starter Kit versionado no Git**: o **`orchestrator`** e o **`agent-default`**. Todos os demais subagentes especialistas (`~/.gemini/agents/agent-<domain>/AGENT.md`) funcionam como **Plugins Especialistas Dinâmicos criados sob demanda pelo usuário** (e permanecem ignorados no Git via `.gitignore` para preservar a customização local de cada ambiente).

### 8.1. Tabela de Agentes do Ecossistema (De Fábrica vs. Plugins Sob Demanda)

| ID do Agente | Caminho da Definição | Status no Starter Kit (`.gitignore`) | Namespace L2 Primário | Papel e Escopo Operacional |
| :--- | :--- | :--- | :--- | :--- |
| **`orchestrator`** | [`~/.gemini/agents/orchestrator/AGENT.md`](agents/orchestrator/AGENT.md) | ✅ **De Fábrica (Versionado)** | `global` | **Agente Default da Sessão Principal:** Escalonador DAG, Auto-Model Router cognitivo, Discovery Read-Only Leve (`< 16 KB`), Single-Writer exclusivo do `CORE.md` e interface executiva com o usuário. |
| **`agent-default`** | [`~/.gemini/agents/agent-default/AGENT.md`](agents/agent-default/AGENT.md) | ✅ **De Fábrica (Versionado)** | `default` *(ou `proj:<repo>`)* | **Subagente Generalista Executor:** Fallback para domínios sem especialista dedicado (Discovery, Shell, automação genérica, Web Search), bootstrap de novos especialistas e First-Boot Onboarding. |
| **`agent-<domain>`**<br/>*(Plugins locais sob demanda)* | `~/.gemini/agents/agent-<domain>/AGENT.md` | 🔒 **Plugin Criado Sob Demanda pelo Usuário (Ignorado no Git)** | `<domain>` | **Plugins Especialistas Dinâmicos:** Criados sob demanda (via sugestão proativa na revisão de fim de conversa do `orchestrator` ou manualmente) para isolar invariantes profundas de uma stack, linguagem ou arquitetura recorrente. Especialistas de engenharia de software herdam a base abstrata [`agent-dev-base`](~/.gemini/agents/agent-dev-base/AGENT.md) via `EXTENDS`. |

#### Catálogo Completo de Especialistas Locais Registrados (19 Plugins Sob Demanda)

Todos os especialistas abaixo residem localmente em `~/.gemini/agents/agent-<domain>/AGENT.md` (ignorados no Git pelo `.gitignore` Default-Deny). Os **15 especialistas de engenharia** herdam integralmente as 9 invariantes de [`agent-dev-base`](~/.gemini/agents/agent-dev-base/AGENT.md) (SOLID, Ports & Adapters, KISS, DRY, Extrema Performance, Zero-Comments Gate, Sugestão Proativa, Matriz Exaustiva de Testes Failure-First e GoF on-demand), enquanto os **4 especialistas independentes** (`agent-android-re`, `agent-git`, `agent-linux-desktop`, `agent-linux-gaming`) operam com diretrizes próprias focadas em análise estática, versionamento, sistema e otimização de jogos:

| ID do Agente | Caminho da Definição | Namespace L2 Primário | Herança (`EXTENDS`) | Escopo & Invariantes Especializadas |
| :--- | :--- | :--- | :--- | :--- |
| **`agent-android-dev`** | `~/.gemini/agents/agent-android-dev/AGENT.md` | `android-dev` | `agent-dev-base` | Desenvolvimento Android nativo (Kotlin, Jetpack Compose, Coroutines/Flow, Gradle Kotlin DSL), Clean Architecture/MVVM, reconstrução *clean-room*, serviços de sistema (`MediaProjection`, `AccessibilityService`, overlays) e IA *on-device* (ML Kit, ONNX Runtime, OpenCV). |
| **`agent-android-re`** | `~/.gemini/agents/agent-android-re/AGENT.md` | `android-re` | Independente | Engenharia reversa estática defensiva e triagem *read-only* de pacotes Android (`.apk`, `.apkm`, `.xapk`, `.aab`): decodificação binária AXML, inventário de splits/DEX/bibliotecas `.so`, extração de assets e JADX headless (`rea inspect-android-package`). |
| **`agent-appsec`** | `~/.gemini/agents/agent-appsec/AGENT.md` | `appsec` | `agent-dev-base` | Engenharia AppSec e pentesting autônomo: skills ofensivas (OWASP/API/LLM/Agentic), regras SAST (`OpenGrep`/`Semgrep`/`AST-grep`), modelagem `STRIDE`, calibração `CVSS 3.1`, `SARIF 2.1.0` com URIs seguros, proxy `Caido`/`HTTPQL`, `Strix` CLI/Cloud, PoC reproduzível e higienização `CWE-1236`. |
| **`agent-ci-cd`** | `~/.gemini/agents/agent-ci-cd/AGENT.md` | `ci-cd` | `agent-dev-base` | Engenharia de pipelines CI/CD e GitHub Actions: derivação estrita ao manifesto/CLI (anti-copy-paste), hardening de supply-chain (`zizmor --persona=pedantic` com 0 findings/suppressed, SHA-40 em Git Tag imutável e zero Node.js depreciado, `actionlint`, `permissions: contents: read`, `persist-credentials: false`, `concurrency`, anti-injection via `env:`, SCA), Local CI Gate 1:1 pré-commit, builds reproduzíveis/estáticos `musl` multi-arch (`--locked`, cache segregado, `strip`, `SHA256SUMS.txt`), smoke tests por arquitetura e `.github/dependabot.yml`. |
| **`agent-docker-sandbox`** | `~/.gemini/agents/agent-docker-sandbox/AGENT.md` | `docker-sandbox` | `agent-dev-base` | Engenharia Docker/OCI e sandboxing seguro: Dockerfiles multi-stage pinados por `@sha256:`, *least privilege* (não-root, zero `sudo NOPASSWD:ALL`, `cap_drop=["ALL"]`, zero CA/chaves bakeadas), `.git` `:ro`, proteção TOCTOU e `tar --no-same-owner`, isolamento de rede, cgroups/log-rotation, PKI efêmera, sidecars e `docker-py` anti-drift. |
| **`agent-epub-translator`** | `~/.gemini/agents/agent-epub-translator/AGENT.md` | `epub-translator` | `agent-dev-base` | Tradução autônoma de EPUBs via CLI global `epub-translator-google` (`--headless`, provedores `antigravity`/`google-free`/`google-cloud`), conformidade IDPF OCF, validação `verify`, controle de concorrência, cache ZSTD + SQLite WAL e manutenção da base Rust Hexagonal. |
| **`agent-git`** | `~/.gemini/agents/agent-git/AGENT.md` | `git` | Independente | Controle de versão Git (*read-only* por padrão): mensagens *Conventional Commits* (3 blocos) e PRs (4 blocos) gravadas em `/tmp/` (retornando o caminho absoluto literal sem despejar o conteúdo), auditoria proativa de versão SemVer no manifesto SSOT (`commit-semver-audit`), gestão de branches/worktrees/conflitos e auditoria anti-vazamento SSOT pré-commit. |
| **`agent-go`** | `~/.gemini/agents/agent-go/AGENT.md` | `go` | `agent-dev-base` | Engenharia Go 1.24+ idiomática: CLIs/TUIs Charmbracelet (`bubbletea`/`bubbles`/`lipgloss`/`chroma`), sidecars IPC (`socketpair` POSIX / TCP loopback + HMAC-SHA256 no Windows, framing length-prefixed JSON, deltas), concorrência segura (`context`/`errgroup`), Ports & Adapters e builds estáticos `CGO_ENABLED=0`. |
| **`agent-kotlin`** | `~/.gemini/agents/agent-kotlin/AGENT.md` | `kotlin` | `agent-dev-base` | Engenharia Kotlin 2.x (JVM/KMP, Gradle Kotlin DSL, Coroutines & Flow) alinhada às *Kotlin Coding Conventions* oficiais, modelagem algébrica de domínio, `@JvmInline value class`, Ports & Adapters e testes com JUnit 5 e MockK. |
| **`agent-linux-desktop`** | `~/.gemini/agents/agent-linux-desktop/AGENT.md` | `linux-desktop` | Independente | Administração Linux Desktop *host-agnostic*: detecção dinâmica de distro/gerenciador (`pacman`/`apt`/`dnf`/`zypper`/Flatpak `--user`), padrões XDG, servidores gráficos Wayland/X11, rede dual-stack (IPv4/IPv6) e supervisão de processos de usuário. |
| **`agent-linux-gaming`** | `~/.gemini/agents/agent-linux-gaming/AGENT.md` | `linux-gaming` | Independente | Otimização de performance e compatibilidade de jogos no Linux *host-agnostic* (Steam/Proton, Heroic, Lutris, VKD3D-Proton, DXVK, NVIDIA PRIME/RADV/ANV, `ntsync`, `gamemode`, `gamescope`, `mangohud`, `scx`, `protontricks`, shader caches e tweaks por engine), com edição VDF segura, backups `.bak.<timestamp>`, gestão de VRAM e persistência por AppID em L2. |
| **`agent-llm-agents`** | `~/.gemini/agents/agent-llm-agents/AGENT.md` | `llm-agents` | `agent-dev-base` | Arquiteturas multi-agente e sistemas LLM: `openai-agents`, LiteLLM, MCP sob demanda, roteamento multi-modelo, Jinja (`StrictUndefined`) + prefix caching (`<cache_point>`), coerção JSON Schema, spill de outputs, compactação segura `tool_call`/`tool_result`, guardrails determinísticos, `RunContext`, RBAC real e LLM-as-a-Judge. |
| **`agent-oreilly-dl`** | `~/.gemini/agents/agent-oreilly-dl/AGENT.md` | `oreilly-dl` | `agent-dev-base` | Engenharia e pipeline da CLI Python `oreilly-dl` (`oreilly-epub-downloader`): `click`/`rich`, fast-path direto, validação JWT (`orm-jwt`), scraping resiliente IPv4/Firefox UA, download concorrente (`httpx`/`asyncio`), higienização XHTML e empacotamento EPUB 3.0 (`ebooklib`). |
| **`agent-python`** | `~/.gemini/agents/agent-python/AGENT.md` | `python` | `agent-dev-base` | Engenharia Python 3.11+ moderna: empacotamento PEP 517/621 (`hatchling`/`uv`/`venv`), CLIs (`click`/`rich`), HTTP/scraping resiliente (`httpx` IPv4/WAF, `beautifulsoup4`, `lxml`), geração de EPUB (`ebooklib`) e arquitetura Ports & Adapters. |
| **`agent-qa`** | `~/.gemini/agents/agent-qa/AGENT.md` | `qa` | `agent-dev-base` | Quality Gate adversarial independente: fuzzing, *chaos engineering*, BVA, simulação de falhas de I/O/concorrência, auditoria estrita de invariantes (zero comentários, linters, `audit` de CVEs), Local CI Gate 1:1 pré-commit (`.github/workflows/*.yml`), validação E2E e benchmarks/stress testing. |
| **`agent-react-ts`** | `~/.gemini/agents/agent-react-ts/AGENT.md` | `react-ts` | `agent-dev-base` | Engenharia SPA moderna: React 19+, TypeScript estrito (`strict: true`, zero `any`), Vite, Tailwind CSS v4, `@xyflow/react`, Markdown anti-XSS (AST React / `DOMPurify`), polling/streaming com `AbortController`, auth `HttpOnly`/`SameSite=Strict` (zero segredos em `localStorage`) e WCAG 2.1 AA. |
| **`agent-rust`** | `~/.gemini/agents/agent-rust/AGENT.md` | `rust` | `agent-dev-base` | Engenharia Rust 2024/2021 de alta performance: Ports & Adapters, borrow checker, runtime Tokio (concorrência/semáforos), tratamento explícito `Result`/`Option` (zero panics), `clap`, `reqwest`, streaming ZIP/EPUB e persistência `rusqlite`. |
| **`agent-ts-mcp`** | `~/.gemini/agents/agent-ts-mcp/AGENT.md` | `ts-mcp` | `agent-dev-base` | Engenharia TypeScript/Node.js moderna: servidores e clientes Model Context Protocol (MCP), CLIs, ferramentas de análise (REA), contratos JSON Schema, álgebra `Result`, proveniência de evidências e arquitetura Ports & Adapters. |
| **`agent-web`** | `~/.gemini/agents/agent-web/AGENT.md` | `web` | `agent-dev-base` | Engenharia Web Frontend moderna e aplicações estáticas: HTML5 semântico, CSS3 responsivo (Flexbox/Grid/`sticky`), Vanilla JS ES6+/ES Modules, Web APIs, a11y, Core Web Vitals, GitHub Pages e uso da skill `modern-web-guidance`. |

### 8.2. Modo 1: Criação Automática via Revisão de Fim de Conversa & Sugestão Proativa
1. Você solicita tarefas envolvendo um novo domínio/stack/workflow recorrente, ferramenta especializada, ou que sobrecarregam um especialista existente (com ou sem fallback para `agent-default`; exemplos ilustrativos: otimizar queries em PostgreSQL, criar um serviço em Rust ou configurar manifests Kubernetes).
2. Ao final da conversa/entrega, o `orchestrator` analisa todo o contexto e, quando compensar, apresenta a **Sugestão Proativa de Especialista** propondo estruturadamente a criação dos plugins recomendados (Nome, Caminho, Herança `EXTENDS`, Escopo/Invariantes, Namespace L2 e justificativa do benefício). Quando não compensar, não força sugestão artificial.
3. Ao receber seu *"Sim / Pode criar"*, o `orchestrator` delega ao `agent-default` a criação de `~/.gemini/agents/agent-<domain>/AGENT.md`, inicializa o namespace `<domain>` no L2 e registra o novo ponteiro no `Semantic Directory` de `CORE.md` (validando `mem check-core`).

### 8.3. Modo 2: Criação Manual Passo a Passo (Padrão Schema L2 v3)
Para criar manualmente um plugin especialista local (ex: `agent-postgres`):

**Passo 1:** Crie o arquivo `~/.gemini/agents/agent-<domain>/AGENT.md` seguindo o padrão enxuto compatível com o **Schema L2 v3** (herdando a Lei Zero e as instruções compartilhadas por referência DRY, idêntico ao padrão de [`agents/agent-default/AGENT.md`](agents/agent-default/AGENT.md)):

```markdown
# 🧩 Subagente Especialista em <Domínio> (`agent-<domain>`)

> **ID:** `agent-<domain>` | **Namespace L2 Primário:** `<domain>` (ou `proj:<repo>` para projetos locais)
> **Escopo:** <Descrição concisa das responsabilidades exclusivas do especialista e o que deve ser delegado a outros agentes>.
> **Constituição:** Herda integralmente a Lei Zero e normas de [`~/.gemini/GEMINI.md`](~/.gemini/GEMINI.md) e [`~/.gemini/agents/COMMON_INSTRUCTIONS.md`](~/.gemini/agents/COMMON_INSTRUCTIONS.md).

---

## 🛠️ Diretrizes Operacionais de Execução

1. **Herança da Lei Zero (Zero Assumptions):**
   * **NUNCA SUPOR NADA.** Diante de qualquer incerteza, ambiguidade de requisitos, decisões de arquitetura/negócio ou múltiplos caminhos viáveis, pare imediatamente.
   * Emita `STATUS: NEED` com `target_domain: "orchestrator"` expondo as opções identificadas (`Opção 1 [Recomendada]`, `Opção 2`) e recomendação técnica fundamentada para deliberação do usuário.
2. **Proibição Absoluta de Git Commit/Push Autônomo:**
   * Jamais execute `git commit` ou `git push` sem autorização prévia e expressa do usuário no turno atual.
3. **Invariantes Técnicas Específicas do Domínio (`<domain>`):**
   * <Invariante 1 específica do domínio>
   * <Invariante 2 específica do domínio>
4. **Engenharia de Software Rigorosa (SOLID & Clean Architecture):**
   * Todo código escrito ou refatorado deve obedecer estritamente a **SOLID**, **Clean Architecture / Ports & Adapters**, tipagem estrita e tratamento explícito de erros.
5. **Regra Single-Writer de `CORE.md` & Curadoria L2 (Schema v3):**
   * O `agent-<domain>` **NUNCA** edita `CORE.md` diretamente.
   * Conhecimentos adquiridos (configurações, playbooks, dead-ends) devem ser gravados em L2 via `~/.gemini/memory/mem upsert` informando proveniência (`--source "agent-<domain>"` e `--confidence 1.0`), ou via `link`/`defer`, e reportados no campo `MEMORY_DELTA` do payload `STATUS: COMPLETED`.
   * **Governança & Resiliência L2 v3:** Utilize `mem history <domain> "<topic>" [--json]` para auditar versões anteriores antes de sobrescrever, `mem delete` (soft-delete seguro) e `mem restore` para recuperação se necessário, `mem backup` para snapshots preventivos e a flag `--json` para integração determinística sem parsing manual.
6. **Anti-Amnésia & M2M Telegráfico:**
   * Proibido resumir saídas extensas no chat (faça dump físico e aponte em `PATHS`). Comunicação com o `orchestrator` 100% telegráfica e sem saudações.
```

**Passo 2:** Adicione o ponteiro na Seção 3 (`Semantic Directory`) de `~/.gemini/memory/CORE.md` e valide o orçamento de linhas:
```bash
~/.gemini/memory/mem check-core
```

---

## 9. Referência Completa da CLI `~/.gemini/memory/mem`

Todos os comandos abaixo refletem exatamente a especificação implementada em `build_parser()` de [`~/.gemini/memory/mem`](memory/mem).
> [!TIP]
> **Flag Global/Subcomando `--json`:** Pode ser passada tanto antes do subcomando (`mem --json get ...`) quanto após os subcomandos compatíveis (`search`, `get`, `list`, `history`, `backup`, `stats`/`status`, `due`, `recall-error`, `check-core`). Quando `--json` está presente e ocorre um erro de domínio, SQLite ou I/O, o motor escreve `{"status": "error", "error": "<mensagem>"}` em `stderr` e encerra com código `1`.

### 9.1. Tabela Resumo de Comandos e Flags Exatas

| Subcomando | Sintaxe Exata & Flags Suportadas | Descrição Funcional |
| :--- | :--- | :--- |
| **`init`** | `mem init [--user <nome>] [--lang <idioma>] [--workspace <path>] [--force]` | Inicializa `archival.db` no Schema v3, popula os 8 registros fundacionais em `global` (e suas arestas) e gera `CORE.md` a partir de `CORE.template.md` (`--force` sobrescreve `CORE.md` existente). |
| **`search`** | `mem search "<query>" [--ns <ns>] [--limit <N>] [--json]` | Busca híbrida FTS5 BM25 normalizada ponderada por `confidence`, `access_count` e recência, com expansão automática de sinônimos n-gram (padrão `--limit 5`). |
| **`get`** | `mem get <namespace> "<topic>" [--json]` | Recupera um registro ativo exato, incrementa `access_count`, verifica alertas `STALE` / `PROSPECTIVE DUE` e exibe arestas de entrada/saída do grafo (`memory_edges`). |
| **`upsert`** | `mem upsert <namespace> <kind> "<topic>" "<content>" ["<tags>"] [--ttl <dias\|0\|none>] [--source "<origem>"] [--confidence <0.0..1.0>]` | Insere ou atualiza atomicamente um registro (`kind` $\in$ `{fact, learning, behavior, decision, invariant, playbook}`). Se já existir, arquiva a versão anterior em `memory_history` e incrementa `version`. |
| **`verify`** | `mem verify <namespace> "<topic>" [--ttl <dias\|0\|none>]` | Revalida o frescor semântico de um registro ativo atualizando `updated_at` para o timestamp UTC atual e opcionalmente redefinindo seu `ttl_days`. |
| **`list`** | `mem list [--ns <ns>] [--json]` | Lista todos os registros ativos (`deleted_at IS NULL`), opcionalmente filtrados por namespace, ordenados por `namespace, topic`. |
| **`delete`** | `mem delete <namespace> "<topic>" [--hard]` | Realiza **soft-delete por padrão** (arquiva snapshot em `memory_history`, define `deleted_at` e remove do índice FTS5). Com `--hard`, executa `DELETE` físico permanente. |
| **`restore`** | `mem restore <namespace> "<topic>"` | Restaura um registro soft-deleted (`deleted_at = NULL`), reindexando-o automaticamente no FTS5 via trigger `memories_au`. |
| **`history`** | `mem history <namespace> "<topic>" [--json]` | Exibe o estado atual (ativo, soft-deleted ou removido) e todas as versões anteriores arquivadas em `memory_history` em ordem cronológica de versão (`version ASC`). |
| **`backup`** | `mem backup [dest_path] [--json]` | Cria um hot backup online consistente usando `sqlite3.Connection.backup()`. Se `dest_path` for omitido, salva em `~/.gemini/memory/backups/archival_<timestamp>.db`. |
| **`promote`** | `mem promote [--ns <ns>] [--limit <N>] [--by {hits,recent}] [--min-hits <N>]` | Identifica candidatos de alto tráfego ou recência no L2 e gera um snippet Markdown pronto para colar no `Semantic Directory` do `CORE.md`. |
| **`stats`** *(ou `status`)* | `mem stats [--json]` / `mem status [--json]` | Exibe métricas consolidadas por namespace, contagem de registros *stale*, tarefas prospectivas, arestas semânticas, sinônimos, soft-deletes, versões no histórico e Top 5 registros mais acessados. |
| **`link`** | `mem link <src_ns>:<src_topic> <RELATION> <dst_ns>:<dst_topic>` | Cria uma aresta direcionada na tabela `memory_edges` entre dois tópicos ativos (ex: `RELATES_TO`, `DEPENDS_ON`, `SUPERSEDES`). |
| **`defer`** | `mem defer <namespace> "<trigger_cond>" "<action>"` | Agenda uma tarefa na Memória Prospectiva (`prospective_tasks`) com `status='pending'`. |
| **`due`** | `mem due [--ns <ns>] [--json]` | Lista todas as tarefas prospectivas pendentes (globalmente ou filtradas por `--ns`). |
| **`done`** | `mem done <task_id>` | Marca a tarefa prospectiva `<task_id>` como concluída (`status='done'`, preenchendo `completed_at`). |
| **`syn`** *(ou `syn-list`)* | `mem syn [list \| add <term> "<syn1,syn2,...>"]` | Lista os sinônimos dinâmicos configurados no FTS5 (`mem syn` / `mem syn list` / `mem syn-list`) ou adiciona/atualiza expansões (`mem syn add <termo> "s1,s2"`). |
| **`recall-error`** | `mem recall-error "<error_snippet>" [--ns <ns>] [--limit <N>] [--json]` | Tokeniza mensagens de erro ou stacktraces (split `CamelCase`/`snake_case` + filtro de 46 stopwords) e busca soluções no L2 priorizando `learning` e `playbook` (`episodic_boost`). |
| **`check-core`** | `mem check-core [--max-lines <N>] [--json]` | Audita o orçamento de linhas de `CORE.md` (padrão `60` ou `$ANTIGRAVITY_CORE_MAX_LINES`), calcula densidade de palavras/bytes/tokens estimados e lista tarefas prospectivas pendentes. Retorna **exit code `1`** se exceder o limite. |
| **`export-md`** | `mem export-md [dir] [--ns <ns>]` | Exporta memórias ativas para arquivos Markdown com YAML Frontmatter e WikiLinks `[[ns/topic]]` + `INDEX.md` (padrão `~/.gemini/memory/wiki`). Em exportação completa (sem `--ns`), remove arquivos `.md` órfãos. |
| **`import-md`** | `mem import-md [dir]` | Importa arquivos Markdown da Wiki (padrão `~/.gemini/memory/wiki`) preservando histórico em `memory_history`, incrementando `version` e reconstruindo arestas em `memory_edges`. |

### 9.2. Exemplos Práticos de Uso da CLI

```bash
# 1. Gravar um aprendizado episódico (learning) com proveniência e Dead-Ends obrigatórios
~/.gemini/memory/mem upsert postgres learning "pgbouncer-prepared-statements-error" \
  "Transaction pooling no PgBouncer exige protocol-level prepared statements ou desativação no driver.
[DEAD-ENDS / TENTATIVAS DESCARTADAS]:
- Aumentar max_prepared_transactions no postgresql.conf não resolve porque o erro ocorre no multiplexador de sessão do PgBouncer." \
  "postgres,pgbouncer,pooling" --source "agent-default" --confidence 0.95

# 2. Consultar soluções para uma exceção/stacktrace via Recall Episódico em JSON
~/.gemini/memory/mem recall-error "PSQLException: prepared statement S_1 already exists in PgBouncer" --ns postgres --json

# 3. Conectar dois tópicos no Grafo Semântico e inspecionar os links
~/.gemini/memory/mem link postgres:pgbouncer-prepared-statements-error RELATES_TO global:agent-memory-architecture
~/.gemini/memory/mem get postgres "pgbouncer-prepared-statements-error"

# 4. Auditar o histórico de versões (Schema v3) e realizar um Hot Backup preventivo
~/.gemini/memory/mem history postgres "pgbouncer-prepared-statements-error" --json
~/.gemini/memory/mem backup --json

# 5. Agendar, listar e concluir uma pendência na Memória Prospectiva
~/.gemini/memory/mem defer proj:api-pagamentos "Ao migrar para PostgreSQL 17" "Revalidar parâmetros de vacuum e rodar mem verify"
~/.gemini/memory/mem due --ns proj:api-pagamentos
~/.gemini/memory/mem done 1

# 6. Validar o orçamento da Memória Quente L1 (<= 60 linhas)
~/.gemini/memory/mem check-core --json
```

---

## 10. Suíte de Testes Automatizados

O ecossistema conta com suítes automatizadas construídas sobre o módulo padrão `unittest` (sem dependências externas):

### 10.1. Como Executar os Testes
```bash
# Suítes do motor L2 e paridade de catálogo
python3 -m unittest discover -s ~/.gemini/memory/tests/ -v
```

* **`GEMINI_README_PATH` (opcional):** Sobrescreve o caminho do `README.md` na suíte [`test_catalog_parity.py`](memory/tests/test_catalog_parity.py). Quando não definida e o arquivo padrão `~/.gemini/README.md` estiver oculto por isolamento de sandbox, os checks específicos de `README.md` fazem `skip` gracioso mantendo a verificação de paridade entre `agents/` e `agent-dev-base`.

### 10.2. Cobertura das Suítes (`test_mem.py` e `test_catalog_parity.py`)

* **[`~/.gemini/memory/tests/test_mem.py`](memory/tests/test_mem.py) (21 testes):** Cobertura unitária, de componente, CLI `--json`/texto, BVA de orçamento (`59`/`60`/`61` linhas) e estresse concorrente SQLite WAL (`TestDomainPolicyUnit`, `TestMarkdownWikiAdapterUnit`, `TestSqliteRepositoryComponent`, `TestControllerAndCliIntegration`, `TestConcurrencyAndStress`).
* **[`~/.gemini/memory/tests/test_catalog_parity.py`](memory/tests/test_catalog_parity.py) (10 testes):** Validação de resolução de `README.md` via `GEMINI_README_PATH` / `Path(__file__).resolve().parents[2]`, registro em `CORE.md`, listagem na Seção 8.1 do `README.md` e paridade bidirecional com `agent-dev-base/AGENT.md`.

---

## 11. Governança de Git, Segurança & Invariantes de Código

### 11.1. Proibição Absoluta de Commit e Push Autônomos
Conforme determinado pela **Lei Zero (Cláusula 3 de `GEMINI.md`)**, nenhum agente (`orchestrator`, `agent-default` ou qualquer subagente especialista `agent-<domain>`) possui permissão para executar `git commit` ou `git push` por iniciativa própria. Toda operação que altere o histórico ou envie código ao repositório remoto exige autorização prévia e expressa do usuário no turno atual.

### 11.2. Padrão Obrigatório de Mensagens de Commit (3 Blocos)
Toda mensagem de commit gerada no ecossistema deve conter **obrigatoriamente 3 blocos estruturados nesta ordem exata** (sendo terminantemente proibido saltar da linha de título diretamente para a lista de bullets):

```text
<type>(<scope>): <título imperativo conciso em até 72 caracteres>

<Bloco 2 — Descrição em Prosa: Parágrafo denso contextualizando o PORQUÊ da alteração, o problema ou limitação do estado anterior e a decisão arquitetural/técnica adotada.>

- <Bloco 3 — Lista de Alterações: Ação concreta realizada, arquivos/classes afetados e justificativa>
- <Item adicional detalhando mudanças de schema, flags ou testes>
```
* **Types válidos:** `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `style`, `ci`, `build`.

### 11.3. Padrão Obrigatório de Pull Requests (4 Blocos)
Toda descrição de Pull Request (PR) deve estruturar obrigatoriamente **4 blocos**:
1. **Título do PR:** No formato Conventional Commits `<type>(<scope>): <título imperativo>`.
2. **Contexto & Motivação:** Parágrafo em prosa detalhando o problema de engenharia/negócio e o impacto da solução.
3. **Alterações Realizadas:** Lista organizada por módulo/componente detalhando as modificações técnicas.
4. **Como Foi Validado / Testes:** Comandos exatos executados, suítes de testes unitários/integração e evidências de verificação.

### 11.4. Diretrizes de Engenharia de Software & Segurança
* **Clean Architecture & SOLID:** Todo código produzido ou refatorado pelos agentes deve respeitar separação estrita de responsabilidades (SRP), inversão de dependências via portas/protocolos (DIP), tipagem estrita e tratamento explícito de erros.
* **Local CI Gate (Paridade e Simulação Local 1:1 de CI/CD Pré-Commit):** Sempre que um repositório possuir workflows em `.github/workflows/*.yml`, os agentes `agent-dev-base`, `agent-ci-cd` e `agent-qa` devem executar localmente todos os gates equivalentes aos steps do GitHub Actions antes de declarar `COMPLETED`: (1) `zizmor --persona=pedantic --min-severity=informational --min-confidence=low .github/workflows/` (0 findings e 0 suppressed) + checagem via API/git de SHA-40 em Git Tag imutável (nunca em branch, evitando `stale-action-refs` exit code 13) e ausência de runtime Node.js depreciado (ex.: Node.js 20); (2) `actionlint` em `.github/workflows/*.yml`; e (3) execução real local dos linters, testes, *smoke tests*, scanners SCA e blocos `run:` de instalação/verificação (`sha256sum -c`) com as mesmas flags estritas do CI.
* **Versionamento SemVer (Manifesto SSOT + Tag `vX.Y.Z` + Auditoria Pré-Commit):** Em toda alteração funcional/fix/breaking de projeto, os agentes avaliam o impacto semântico (`MAJOR`/`MINOR`/`PATCH`) e atualizam o manifesto SSOT (+ lockfile) mantendo `--version` ligado ao manifesto; ao gerar mensagens de commit, o `agent-git` audita obrigatoriamente o manifesto SSOT frente ao diff e às tags existentes (`commit-semver-audit`), alertando explicitamente o usuário sobre bumps pendentes (`atual -> sugerida`, tag `vX.Y.Z`) e oferecendo aplicá-los automaticamente antes do commit. Workflows de Release disparam por padrão no push da branch principal + tag SemVer com checagem estrita de paridade ao manifesto, sem nunca executar `git commit`/`git tag`/`git push` autônomos.
* **Preservação de Integridade Documental:** Comentários arquiteturais relevantes (como a explicação da máquina de estados dos triggers FTS5 em `memory/mem`) e docstrings existentes jamais devem ser removidos silenciosamente.
* **Proteção contra Vazamento de Identidade (SSOT):** Antes de qualquer preparação de commit no Starter Kit (`~/.gemini`), verifique via `git status` e `git diff` que nenhum dado pessoal de `CORE.md` ou `archival.db` foi introduzido nos arquivos versionados.
