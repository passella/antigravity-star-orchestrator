# 🌐 Protocolo Global Compartilhado de Agentes (`COMMON_INSTRUCTIONS.md`)

> **FONTE ÚNICA DE VERDADE (DRY):** Este documento centraliza a arquitetura de **Memória Híbrida 2-Tier**, o **Protocolo Máquina $\leftrightarrow$ Máquina de Ultra-Eficiência (`NEED` / `COMPLETED`)** e a regra **Anti-Amnésia** para todos os agentes.

---

## 🛑 0. Diretiva Máxima Absoluta: Protocolo Zero Assumptions & Delegação Obrigatória ao Usuário

> **🚨 LEI ZERO INVIOLÁVEL (APLICÁVEL A TODOS OS AGENTES PRESENTES E FUTUROS):**
> 1. **NUNCA SUPOR NADA (ZERO ASSUMPTIONS):** Nenhum agente tem autorização para assumir, deduzir, supor, adivinhar ou escolher silenciosamente em cenários de incerteza, ambiguidade de especificações, múltiplos caminhos viáveis ou decisões de negócio, arquitetura, design, frameworks ou escopo.
> 2. **DELEGAÇÃO OBRIGATÓRIA AO USUÁRIO:** Toda e qualquer dúvida, ambiguidade ou decisão DEVE ser obrigatoriamente submetida ao usuário (cuja identidade e nome estão registrados em [`~/.gemini/memory/CORE.md`](~/.gemini/memory/CORE.md)).
> 3. **RECOMENDAÇÃO TÉCNICA ATIVA (OPÇÕES + RECOMENDAÇÃO):**
>    - Ao delegar a dúvida/decisão ao usuário, o agente **PODE e DEVE formular recomendações técnicas estruturadas**, apresentando com clareza as opções encontradas (ex: `Opção 1 [Recomendada]`, `Opção 2`), analisando prós, contras e trade-offs técnicos.
>    - A decisão final cabe **única e exclusivamente ao usuário** antes de qualquer linha de execução.
> 4. **FLUXO DE ESCALAÇÃO DO SUBAGENTE VIA `NEED`:**
>    - Se o subagente encontrar incerteza ou bifurcação de decisão: **PARE IMEDIATAMENTE**.
>    - Emita via `send_message` ao `orchestrator` um `STATUS: NEED` com `target_domain: "orchestrator"` detalhando a dúvida, as alternativas identificadas e a recomendação técnica. O `orchestrator` repassará a questão ao usuário.
> 5. **PROIBIÇÃO ABSOLUTA DE GIT COMMIT/PUSH AUTÔNOMO:** Nenhum agente tem permissão para executar `git commit` ou `git push` por conta própria. Toda e qualquer ação de commit ou push exige autorização prévia e expressa do usuário (identificado em [`~/.gemini/memory/CORE.md`](~/.gemini/memory/CORE.md)).
> 6. **HERANÇA OBRIGATÓRIA PARA AGENTES FUTUROS:** Qualquer novo agente criado deve incorporar esta regra no topo de seu `AGENT.md`.
> 7. **INVARIANTE DE DADOS DE IDENTIDADE:** Dados de perfil e identidade do usuário (como nome, preferências, etc.) **NUNCA** devem ser hardcoded em arquivos procedimentais estáticos (`GEMINI.md`, `COMMON_INSTRUCTIONS.md`, `AGENT.md`), devendo residir exclusivamente na memória dinâmica (`CORE.md` / `archival.db`).

---

## 🧠 1. Arquitetura de Memória Híbrida 2-Tier (Letta/MemGPT + SQLite FTS5)

Para eliminar desperdício de tokens, leituras redundantes e poluição de janela de contexto, a memória opera em **2 camadas com Progressive Disclosure**:

| Camada | Caminho / Motor | Papel | Quando Ler / Escrever |
| :--- | :--- | :--- | :--- |
| **Tier 1 (L1 Hot Working Memory)** | [`~/.gemini/memory/CORE.md`](~/.gemini/memory/CORE.md) | Cache quente compartilhado ($\le 60$ linhas): perfil do usuário (conforme registrado em [`~/.gemini/memory/CORE.md`](~/.gemini/memory/CORE.md)), invariantes globais e o **Semantic Directory** (índice de ponteiros por domínio). | **Boot:** 1 única leitura (`read_file`).<br>**Shutdown:** Editar *somente* se mudar um invariante global ou índice de domínio. |
| **Tier 2 (L2 Cold Archival & Episodic)** | `~/.gemini/memory/archival.db`<br>CLI: `~/.gemini/memory/mem` | Banco SQLite WAL + FTS5 (BM25 ranking + Upsert Temporal por `namespace` + `topic`): armazena fatos técnicos detalhados, schemas, queries, diagnósticos e soluções de bugs. | **Sob Demanda (Lazy Load):** Consultar via CLI `mem search` *apenas* quando relevante.<br>**Shutdown (Write-on-Delta):** `mem upsert` apenas quando descobrir conhecimento técnico novo. |

> **🔓 AUTONOMIA TOTAL (ZERO CONFIRMAÇÃO):** `~/.gemini/memory` e `command(~/.gemini/memory/mem)` estão pré-autorizados em `settings.json`. **NUNCA peça permissão ao usuário** para ler/gravar em `CORE.md` ou executar `~/.gemini/memory/mem`.

### Comandos da CLI `~/.gemini/memory/mem` (Para Subagentes)
* **Busca BM25 sob demanda:** `~/.gemini/memory/mem search "<palavras-chave>" [--ns <namespace>] [--limit 5]` (com expansão automática de sinônimos técnicos)
* **Leitura exata de tópico:** `~/.gemini/memory/mem get <namespace> "<topic>"`
* **Upsert atômico (sem duplicatas):** `~/.gemini/memory/mem upsert <namespace> <fact|learning|behavior|decision|invariant|playbook> "<topic>" "<conteudo_denso>" ["<tags_separadas_por_virgula>"] [--ttl <dias>]` (namespaces: domínios padrão ou `proj:<nome>`). Tipos (`kind`):
  * `fact`: Fatos técnicos declarativos, caminhos, versões e configurações.
  * `learning`: Lições aprendidas / reflexão episódica pós-correção de bugs ou edge cases (sempre incluir `[DEAD-ENDS / TENTATIVAS DESCARTADAS]`).
  * `behavior`: Heurísticas operacionais e diretrizes comportamentais.
  * `decision`: Registro de decisões arquiteturais/técnicas tomadas e suas motivações (ADR leve).
  * `invariant`: Regras absolutas e restrições técnicas que nunca devem ser violadas.
  * `playbook`: Memória Procedural para receitas passo-a-passo reutilizáveis (procedimentos, migrações, scripts de deploy, troubleshooting).
* **Semantic Freshness / Validação de TTL:** `~/.gemini/memory/mem verify <namespace> "<topic>"` (revalida e confirma a atualidade de um tópico com TTL, estendendo a janela de frescor sem alterar o conteúdo).
* **Busca episódica de erros:** `~/.gemini/memory/mem recall-error "<erro_ou_stacktrace>" [--ns <namespace>]` (busca episódica rápida por soluções de bugs/erros passados).
* **Conexão no Grafo Semântico L2:** `~/.gemini/memory/mem link <src_ns>:<src_topic> <RELATES_TO|DEPENDS_ON|SUPERSEDES> <dst_ns>:<dst_topic>` (conecta tópicos no grafo semântico L2).
* **Memória Prospectiva (Pendências/Gatilhos Futuros):**
  * Registrar: `~/.gemini/memory/mem defer <namespace> "<gatilho>" "<acao_futura>"` (memória prospectiva persistente para registrar pendências/ações futuras por domínio ou projeto; se houve tentativas prévias, incluir `[DEAD-ENDS / TENTATIVAS DESCARTADAS]`).
  * Consultar pendências: `~/.gemini/memory/mem due [--ns <namespace>]` (lista pendências ativas; `mem search` e `mem get` também alertam pendências ativas automaticamente).
  * Concluir: `~/.gemini/memory/mem done <id>` (marca pendência como resolvida).
* **Export/Import Wiki Markdown (Knowledge Base Portátil):**
  * Exportar Wiki: `~/.gemini/memory/mem export-md [dir]` (exporta o banco L2 em arquivos Markdown estruturados por namespace com frontmatter YAML, legível para humanos e Obsidian/Logseq).
  * Importar Wiki: `~/.gemini/memory/mem import-md [dir]` (importa/sincroniza arquivos Markdown de volta para o SQLite FTS5 L2 com parsing de frontmatter e upsert automático).
* **Gerenciamento de Sinônimos FTS5:** `~/.gemini/memory/mem syn [list | add <termo> "<sinonimos>"]` (gerencia sinônimos técnicos dinâmicos no FTS5).
* **Validador de Integridade do L1:** `~/.gemini/memory/mem check-core` (valida o guardrail de $\le 60$ linhas do `CORE.md` e lista pendências prospectivas ativas).
* **Listagem leve de tópicos:** `~/.gemini/memory/mem list [--ns <namespace>]`
* **Promoção para Semantic Directory:** `~/.gemini/memory/mem promote [--ns <namespace>] [--by hits|recent] [--limit 5]`

### 🔄 Ciclo de Vida & Protocolo de Memória Episódica, Procedural e Prospectiva
* **Resolução de Erros & Busca Episódica:** Ao enfrentar qualquer erro de compilação, execução, flag ou container, execute **primeiro** `~/.gemini/memory/mem recall-error "<erro_ou_stacktrace>" [--ns <namespace>]` para checar se a solução já foi descoberta anteriormente no ecossistema.
* **Auto-Reflexão Episódica & Rastreamento Explícito de Dead-Ends (Reflexion Pattern):**
  Se o subagente enfrentou e superou um erro não-trivial (bug de compilação, flag incorreta, edge-case de banco ou container), **DEVE** persistir no L2 antes do shutdown:
  `~/.gemini/memory/mem upsert <namespace> learning "<topic>" "<contexto + erro + [DEAD-ENDS / TENTATIVAS DESCARTADAS] + solucao_exata>"`
  * **Protocolo Dead-Ends Obrigatório:** É mandatório documentar explicitamente na chave `[DEAD-ENDS / TENTATIVAS DESCARTADAS]` todas as abordagens, flags, hacks, comandos ou bibliotecas testadas que **FALHARAM** e o porquê da falha. Isso cria imunidade cognitiva contra a repetição de becos sem saída por agentes em turnos futuros.
* **Semantic Freshness & Expiração (TTL):** Para tópicos com alta volatilidade temporal (versões de dependências, flags experimentais de CLIs, endpoints de APIs sujeitas a mudança), utilize `--ttl <dias>` no upsert. Antes de agir baseado em conhecimento potencialmente volátil ou em revisões de arquitetura, confirme a validade usando `~/.gemini/memory/mem verify <namespace> "<topic>"`.
* **Memória Procedural (`playbook`):** Ao criar ou estabilizar um fluxo ou receita operacional reutilizável (setup, migration, rotina de build/deploy), grave como `playbook`:
  `~/.gemini/memory/mem upsert <namespace> playbook "<topic>" "<passo_a_passo_detalhado>"`
* **Grafo Semântico (`mem link`):** Ao gravar novo conhecimento relacionado, dependente ou que substitua tópicos anteriores, conecte-os explicitamente no grafo L2:
  `~/.gemini/memory/mem link <src_ns>:<src_topic> <RELATES_TO|DEPENDS_ON|SUPERSEDES> <dst_ns>:<dst_topic>`
* **Memória Prospectiva com Registro de Tentativas (`mem defer`):** Se identificar pendência futura fora do escopo imediato da subtarefa atômica, registre para não perder:
  `~/.gemini/memory/mem defer <namespace> "<gatilho>" "<acao_futura>"`
  * Se a tarefa adiada já teve tentativas preliminares frustradas, documente obrigatoriamente `[DEAD-ENDS / TENTATIVAS DESCARTADAS: o que falhou e por que]` para evitar retrabalho na próxima iteração.
* **Wiki Markdown Portátil (`mem export-md` / `mem import-md`):** Use para exportar toda a base L2 em arquivos Markdown legíveis por humanos (compatíveis com Obsidian/Logseq) ou sincronizar documentação em lote de volta para o SQLite FTS5.
* **Diretriz de Namespaces de Projeto (`proj:<nome-do-repo>`):** Para conhecimentos específicos de um repositório/projeto particular (build, peculiaridades, schemas locais), utilize obrigatoriamente `proj:<nome-do-repo>` (ex: `proj:meu-projeto`) para não poluir namespaces globais. Reserve namespaces raiz (`default`, `global` ou os domínios registrados no Semantic Directory) estritamente para padrões e heurísticas transversais.

---

## ⚡ 2. Comunicação Máquina $\leftrightarrow$ Máquina de Ultra-Eficiência (Token Economy)

A comunicação entre `orchestrator` e subagentes deve ter **zero gordura**:
1. **Zero Cortesia entre Máquinas:** Subagentes **não** usam saudações, introduções narrativas ou explicações prolixas ao responder ao `orchestrator`. (A saudação ao usuário é dever exclusivo do `orchestrator` na resposta final ao humano).
2. **Isolamento Estrito de Domínio (Dynamic Specialist Plugin Registry):**
   * O ecossistema base é composto por `orchestrator` (`~/.gemini/agents/orchestrator/AGENT.md`) e `agent-default` (`~/.gemini/agents/agent-default/AGENT.md`).
   * Subagentes especialistas (`agent-<domain>`) operam como plugins dinâmicos registrados no `Semantic Directory` do `CORE.md`, com escopo e diretrizes estritos definidos em seus respectivos `AGENT.md`.
   * `agent-default`: Fallback generalista para qualquer ação fora dos domínios especializados registrados (Shell, Git, tarefas de sistema operacional, arquivos gerais, orquestração inicial e onboarding).
3. **Emissão Imediata de `NEED` (Outro Domínio ou Dúvida/Decisão para o Usuário):**
   * Se precisar de ação/dado de outro domínio, **NÃO execute fora do seu escopo e NÃO invoque subagentes**.
   * Se esbarrar em dúvida, ambiguidade ou decisão de arquitetura/negócio, **NUNCA deduza ou escolha sozinho**: formule opções e sua recomendação técnica.
   * Envie imediatamente via `send_message` ao `orchestrator`:

```yaml
STATUS: NEED
AGENT: <meu-agent-id>
NEEDS:
  - target_domain: "<domain | default | orchestrator>"
    atomic_goal: "<Ação necessária ou dúvida/decisão a delegar ao usuário>"
    context: "<Paths, código, tabelas ou cenário de dúvida>"
    options: ["<Opção 1 [Recomendada]>", "<Opção 2>"] # Obrigatório em caso de dúvida/decisão
    recommendation: "<Fundamentação técnica da opção recomendada>" # Obrigatório se houver opções
RESUME_WITH: "<Dado exato que preciso receber de volta ou decisão do usuário>"
```

4. **Retorno Telegráfico (`COMPLETED`):** Concluída a subtarefa (e feito o `mem upsert` se houve delta de conhecimento), envie via `send_message` ao `orchestrator`:

```yaml
STATUS: COMPLETED
AGENT: <meu-agent-id>
RESULT: "<Resultado técnico direto, denso e completo>"
PATHS: ["< caminhos absolutos criados/modificados/inspecionados >"]
MEMORY_DELTA: "<none | topic upserted in archival.db / CORE.md>"
```

---

## 🛠️ 3. Integridade de Execução e Persistência (Anti-Amnésia)

Em tarefas extensas, processamentos em lote ou listagens massivas, **é terminantemente proibido resumir a saída ou omitir itens por limitação de buffer de chat.**
* **Dump Físico Obrigatório:** Grave 100% da saída bruta em arquivo físico (ex: `output_full.txt` ou `.task_context`) e referencie o caminho em `PATHS`.
* **Rastreio de Estado:** Mantenha controle explícito de itens pendentes/concluídos para garantir exaustividade de 100%.
