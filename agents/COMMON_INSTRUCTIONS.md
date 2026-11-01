# 🧠 Protocolo Operacional Compartilhado de Memória & M2M (`COMMON_INSTRUCTIONS.md`)

> **Autonomia Total:** `~/.gemini/memory` e `~/.gemini/memory/mem` são pré-autorizados. Nunca peça permissão ao usuário para consultar ou gravar memórias técnicas.
> **Constituição Global (DRY):** A Lei Zero Inviolável (Zero Assumptions, delegação com opções/recomendação, proibição de commit/push autônomo e SSOT de identidade) reside em [`~/.gemini/GEMINI.md`](~/.gemini/GEMINI.md) e é herdada automaticamente por todos os agentes.

---

## 1. Arquitetura de Memória Híbrida 2-Tier & Regra Single-Writer

1. **L1 Working Memory (`~/.gemini/memory/CORE.md`):** Orçamento estrito de **$\le 60$ linhas** (auditado por `mem check-core`).
   * **Regra Single-Writer:** Subagentes **NUNCA** editam `CORE.md` diretamente (evita conflitos de concorrência em Fan-Out).
   * Apenas o `orchestrator` atualiza `CORE.md` no fechamento do Fan-In quando surgem novos invariantes ou ponteiros de domínio.
2. **L2 Archival & Cognitive Engine (`~/.gemini/memory/mem` — Schema v3):**
   * Banco SQLite WAL + FTS5 com concorrência segura (`busy_timeout=30000`) e file locking cross-platform. Subagentes podem ler e gravar em paralelo.
   * **Schema L2 v3:** Suporte a versionamento histórico com trilha de auditoria (`memory_history`), proveniência de dados (`source` e `confidence`), soft-delete reversível por padrão (`restore`), backups online consistentes (`backup`) e saída estruturada programática (`--json`).
   * **Namespaces:** Use `<dominio>` (ex: `postgres`, `rust`, `default`) para padrões reutilizáveis transversais e `proj:<repo>` para especificidades de um projeto local.
3. **As 7 Memórias Cognitivas (`kind`):**
   * `fact`: Fatos declarativos, versões, portas, paths e configs (TTL padrão: 30 dias).
   * `learning`: Diagnósticos e lições aprendidas pós-correção de bugs. **Obrigatório** incluir a seção `[DEAD-ENDS / TENTATIVAS DESCARTADAS]` com abordagens que falharam e o motivo.
   * `behavior`: Heurísticas operacionais e diretrizes comportamentais.
   * `decision`: Decisões arquiteturais e técnicas aprovadas (ADR enxuto).
   * `invariant`: Regras técnicas invioláveis e restrições permanentes do domínio.
   * `playbook`: Memória Procedural para fluxos passo a passo reutilizáveis (builds, migrations, deploys).
   * **Memória Prospectiva (`defer` / `due` / `done`):** Fila persistente de pendências e gatilhos futuros com tracking de tentativas.

---

## 2. Referência Rápida da CLI `~/.gemini/memory/mem` (Schema v3)

* **Busca Híbrida (BM25 + Recência + Hits + Sinônimos):**
  `~/.gemini/memory/mem search "<query>" [--ns <ns>] [--limit 5] [--json]`
* **Leitura Exata + Links do Grafo:**
  `~/.gemini/memory/mem get <ns> "<topic>" [--json]`
* **Gravação Atômica (Upsert) com Proveniência & Versionamento:**
  `~/.gemini/memory/mem upsert <ns> <kind> "<topic>" "<conteudo>" ["<tags>"] [--ttl <dias|none>] [--source "<agente>"] [--confidence <0.0..1.0>]`
* **Histórico de Alterações & Auditoria (Versionamento L2 v3):**
  `~/.gemini/memory/mem history <ns> "<topic>" [--limit 10] [--json]`
* **Remoção Segura (Soft-Delete por Padrão) & Restauração:**
  `~/.gemini/memory/mem delete <ns> "<topic>" [--hard]` *(sem `--hard`, marca `deleted_at` permitindo rollback)*
  `~/.gemini/memory/mem restore <ns> "<topic>"` *(recupera tópico soft-deleted de volta ao índice ativo)*
* **Backup Consistente Online (Zero Downtime / Sem Lock Exclusivo):**
  `~/.gemini/memory/mem backup [caminho_destino.db]`
* **Revalidação de Frescor (TTL):**
  `~/.gemini/memory/mem verify <ns> "<topic>" [--ttl <dias|none>]`
* **Recall Episódico de Erros/Stacktraces:**
  `~/.gemini/memory/mem recall-error "<snippet_ou_stacktrace>" [--ns <ns>] [--json]`
* **Grafo Semântico (Arestas Direcionadas):**
  `~/.gemini/memory/mem link <src_ns>:<src_topic> <DEPENDS_ON|RELATES_TO|SUPERSEDES> <dst_ns>:<dst_topic>`
* **Memória Prospectiva (Pendências Futuras):**
  * Agendar: `~/.gemini/memory/mem defer <ns> "<gatilho>" "<acao_futura_e_dead_ends>"`
  * Listar: `~/.gemini/memory/mem due [--ns <ns>] [--json]`
  * Concluir: `~/.gemini/memory/mem done <task_id>`
* **Sinônimos Técnicos Dinâmicos:**
  `~/.gemini/memory/mem syn [list | add <termo> "<sin1,sin2,...>"]`
* **Auditoria de Orçamento L1 (`<= 60` linhas) e Promoção:**
  `~/.gemini/memory/mem check-core` | `~/.gemini/memory/mem promote [--ns <ns>]`
* **Interoperabilidade Wiki Markdown (Obsidian/Logseq):**
  `~/.gemini/memory/mem export-md [dir] [--ns <ns>]` | `~/.gemini/memory/mem import-md [dir]`
* **Integração Programática M2M (`--json`):**
  A flag `--json` está disponível em `search`, `get`, `recall-error`, `due`, `history`, `list` e `stats` para consumo estruturado sem parsing de texto.

---

## 3. Protocolo Máquina $\leftrightarrow$ Máquina (M2M — Zero Ruído)

Comunicação entre `orchestrator` e subagentes é 100% direta, telegráfica e sem saudações.

### A) Escalação de Dependência ou Dúvida/Decisão (Subagente $\rightarrow$ `orchestrator`)
Se precisar de ação de outro domínio OU esbarrar em dúvida/ambiguidade/decisão (Lei Zero), **PARE** e envie via `send_message`:

```yaml
STATUS: NEED
AGENT: <meu-agent-id>
NEEDS:
  - target_domain: "<domain | default | orchestrator>"
    atomic_goal: "<Ação necessária de outro domínio OU dúvida/decisão para o usuário>"
    context: "<Paths, código, contexto ou cenário técnico>"
    options: ["<Opção 1 [Recomendada]>", "<Opção 2>"] # Obrigatório para dúvidas/decisões
    recommendation: "<Fundamentação técnica da opção recomendada>" # Obrigatório se houver opções
RESUME_WITH: "<Dado exato que preciso receber de volta ou decisão do usuário>"
```

### B) Conclusão de Subtarefa (Subagente $\rightarrow$ `orchestrator`)
Ao concluir a tarefa e registrar novos fatos no L2, envie via `send_message`:

```yaml
STATUS: COMPLETED
AGENT: <meu-agent-id>
RESULT: "<Síntese técnica densa e direta do que foi executado/validado>"
PATHS: ["<caminhos absolutos criados/modificados/inspecionados>"]
MEMORY_DELTA: "<none | ns/topic gravado via mem upsert/link/defer>"
```
*(O `orchestrator` consolidará os `MEMORY_DELTA` no Fan-In e atualizará o `CORE.md` se necessário).*

---

## 4. Integridade de Execução e Persistência (Anti-Amnésia)

Em listagens ou saídas volumosas, **é terminantemente proibido resumir ou truncar dados no chat**:
* Grave 100% da saída em arquivo físico (ex: `output_full.txt` ou `.task_context`).
* Retorne o caminho absoluto do arquivo no campo `PATHS` do payload de conclusão.
