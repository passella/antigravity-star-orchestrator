# 🧠 Protocolo Operacional Compartilhado de Memória & Runtime (`COMMON_INSTRUCTIONS.md`)

> **Autonomia Total:** `~/.gemini/memory` e `~/.gemini/memory/mem` são pré-autorizados. Nunca peça permissão ao usuário para consultar ou gravar memórias técnicas.
> **Constituição Global (DRY):** A Lei Zero Inviolável (itens 1 a 6) e o Boot Polimórfico no Turno 1 (Seção 1.B) residem em [`~/.gemini/GEMINI.md`](~/.gemini/GEMINI.md) e são herdados automaticamente por todos os agentes.

---

## 1. Arquitetura de Memória 2-Tier & As 7 Memórias Cognitivas (`kind`)

1. **L1 Working Memory (`~/.gemini/memory/CORE.md`):** Orçamento estrito de **$\le 60$ linhas** (auditado por `mem check-core`).
   * **Regra Single-Writer:** Subagentes **NUNCA** editam `CORE.md` diretamente (evita conflitos de concorrência em Fan-Out).
   * Apenas o `orchestrator` atualiza `CORE.md` no fechamento do Fan-In quando surgem novos invariantes ou ponteiros de domínio.
2. **L2 Archival & Cognitive Engine (`~/.gemini/memory/mem` — Schema v3):**
   * Banco SQLite WAL + FTS5 com concorrência segura (`busy_timeout=30000`) e file locking cross-platform. Subagentes podem ler e gravar em paralelo.
   * **Schema L2 v3:** Versionamento histórico com trilha de auditoria (`memory_history`), proveniência (`source` e `confidence`), soft-delete reversível por padrão (`restore`), backups online consistentes (`backup`) e saída estruturada programática (`--json`).
   * **Namespaces:** Use `<dominio>` (ex: `postgres`, `rust`, `default`) para padrões reutilizáveis transversais e `proj:<repo>` para especificidades de um projeto local.
   * **Filtro Read-Only & Zero Poluição:** Subtarefas estritamente *read-only*, *discovery* ou *auditoria* sem novo conhecimento de domínio perene devem retornar obrigatoriamente `MEMORY_DELTA: "none"` e JAMAIS gravar chaves transitórias de auditoria no `archival.db`.
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
* **Coleta de Lixo & Purga de Registros Órfãos/Deletados:**
  `~/.gemini/memory/mem gc` *(ou `mem prune`: remove fisicamente registros soft-deleted e órfãos)*
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

## 3. Isolamento de Domínio & Protocolo de Retorno M2M (Zero Ruído)

Comunicação de retorno ao `orchestrator` é 100% direta, telegráfica e sem saudações (via `send_message`).

### A) Escalação de Dependência, Handoff de Qualidade/Segurança ou Dúvida/Decisão (`STATUS: NEED`)
Se a subtarefa pertencer a outro domínio registrado no `Semantic Directory` de `CORE.md`, houver dúvida/decisão técnica (Lei Zero) **OU** após qualquer alteração de código, configuração, infraestrutura ou scripts por agentes de dev (`EXTENDS: agent-dev-base`, exceto `agent-qa` e `agent-appsec` em auditoria), **PARE** imediatamente (ou encerre o trabalho de alteração) e envie:
```yaml
STATUS: NEED
AGENT: <meu-agent-id>
NEEDS:
  - target_domain: "<domain | default | orchestrator>" # String única OU lista de domínios (ex: ["qa", "appsec"])
    atomic_goal: "<Ação necessária de outro domínio/gates OU dúvida/decisão a delegar ao usuário>"
    context: "<Resumo objetivo das mudanças, comandos de build/test executados, riscos/pontos de atenção ou cenário técnico>"
    options: ["<Opção 1 [Recomendada]>", "<Opção 2>"] # Obrigatório para dúvidas/decisões (Lei Zero)
    recommendation: "<Fundamentação técnica objetiva da opção recomendada>" # Obrigatório para dúvidas/decisões
PATHS: ["<caminhos absolutos criados/modificados/inspecionados>"]
MEMORY_DELTA: "<none | ns/topic gravado no L2 via mem upsert/link/defer>"
RESUME_WITH: "<Dado/decisão necessária para prosseguir OU confirmação de aprovação QA+AppSec>"
```
* **Suporte a `target_domain` Único ou Múltiplo:** O campo `target_domain` aceita uma string única (ex: `"rust"`, `"orchestrator"`) **ou** uma lista de domínios (ex: `["qa", "appsec"]`).
* **Handoff Compulsório & Ciclo Bidirecional (`dev <-> qa / appsec`):**
  * **Dev $\rightarrow$ QA/AppSec:** Agentes de desenvolvimento (`EXTENDS: agent-dev-base`, exceto `agent-qa` e `agent-appsec` em suas auditorias) **DEVEM** encerrar toda alteração de código, configuração, infraestrutura ou scripts emitindo `STATUS: NEED` com `target_domain: ["qa", "appsec"]` (nunca `STATUS: COMPLETED` isolado), incluindo resumo objetivo das mudanças, `PATHS`, comandos de build/test executados e riscos/pontos de atenção para QA e AppSec (dispensado apenas em tarefas estritamente *read-only* ou ajustes textuais triviais sem código).
  * **QA/AppSec $\rightarrow$ Dev (`target_domain: "<dev-stack>"`):** Sempre que `agent-qa` ou `agent-appsec` encontrar qualquer falha, regressão, violação de invariante, bug, vulnerabilidade ou achado de segurança, **DEVE** emitir obrigatoriamente `STATUS: NEED` direcionado ao `target_domain` do agente dev especialista adequado à stack (ex: `"rust"`, `"python"`, `"go"`, `"react-ts"`, `"ts-mcp"`, `"kotlin"`, `"android-dev"`, `"web"`, `"docker-sandbox"`, `"ci-cd"`, `"llm-agents"`) com relatório forense acionável (arquivo, linha, causa raiz, severidade, reprodução/evidência e correção esperada) — sem encerrar com `STATUS: COMPLETED` enquanto houver achados abertos. Após corrigir, o dev reemite `STATUS: NEED` para `["qa", "appsec"]` até ambos aprovarem com `STATUS: COMPLETED`.

### B) Conclusão da Subtarefa (`STATUS: COMPLETED`)
Ao concluir a subtarefa, envie obrigatoriamente:
```yaml
STATUS: COMPLETED
AGENT: <meu-agent-id>
RESULT: "<Síntese técnica densa e direta do que foi executado/validado + sugestões estruturadas de melhorias se aplicável>"
PATHS: ["<caminhos absolutos criados/modificados/inspecionados>"]
MEMORY_DELTA: "<none | ns/topic gravado no L2 via mem upsert/link/defer>"
```

---

## 4. Eficiência de Execução, Sandbox & Host-Agnostic Runtime

1. **Zero Alucinação de Ferramentas no Discovery:** Sempre valide a existência real de binários no host (`command -v <bin>`) antes de reportar opções de build ou instalação ao `orchestrator`.
2. **Comandos `BypassSandbox: true` 100% Auto-Aprováveis:** NUNCA utilize operadores encadeados (`&&`, `;`, `||`), substituições de comando `$(...)`, backticks ou expansões complexas de variáveis em chamadas com `BypassSandbox: true`. Tais construções invalidam o prefix-matching de auto-aprovação do usuário e travam subagentes. Execute etapas preparatórias no sandbox (`BypassSandbox: false`) e isole estritamente apenas a chamada essencial fora do sandbox.
3. **Fast-Path Dual-Stack (IPv4) & Detecção Dinâmica do Host:** Em hosts com rotas IPv6 problemáticas ou instáveis para CDNs (PyPI/Fastly, Cloudflare, Akamai), force IPv4 (`curl -4`, `httpx.HTTPTransport(local_address="0.0.0.0")`). Detecte a distribuição (`/etc/os-release`) e o gerenciador de pacotes nativo (`command -v pacman apt dnf apk zypper`) dinamicamente ou consulte peculiaridades do host gravadas no L2 (`archival.db`). Priorize pacotes nativos e cache local (`venv --system-site-packages`, cache `~/.cache/pip`) para eliminar compilações C/Rust redundantes e falhas de rede.
4. **Encerramento M2M Obrigatório com Sugestões Proativas:** Nenhum subagente deve encerrar sua tarefa sem emitir `send_message` (`STATUS: COMPLETED` ou `STATUS: NEED`) ao `orchestrator`. Ao concluir a subtarefa, inclua obrigatoriamente no campo `RESULT` do payload de encerramento sugestões técnicas estruturadas de melhorias para repasse compulsório pelo `orchestrator` ao usuário na resposta final executiva.

---

## 5. Documentação de Projetos Finais (`README.md`)

Ao criar ou atualizar `README.md` de projetos finais (aplicativos, CLIs, ferramentas, bibliotecas, web apps, etc.), **NÃO** explique a arquitetura interna do código (ex.: Ports & Adapters, diagramas de camadas, árvore de `src/`), a menos que o próprio repositório seja um projeto de arquitetura ou ecossistema (como `~/.gemini/README.md`). O `README.md` de projetos finais deve ser profissional e focado no uso (estilo GitHub real): o que a ferramenta faz, recursos, pré-requisitos, instalação, exemplos práticos de uso, opções/flags e avisos úteis ao usuário final.

---

## 6. Controle Obrigatório de Versionamento SemVer (Manifesto SSOT)

Em **qualquer** projeto, sempre que o usuário solicitar uma alteração, avalie o impacto semântico e atualize automaticamente a versão no manifesto SSOT do projeto (`Cargo.toml` + `Cargo.lock`, `package.json`, `pyproject.toml`, `build.gradle.kts`, etc.), mantendo `--version` e metadados de runtime ligados ao manifesto (nunca hardcoded):
* **`MAJOR` (`X.0.0`):** Breaking changes em CLI, API pública, schemas ou comportamento incompatível.
* **`MINOR` (`0.X.0`):** Novas funcionalidades, subcomandos ou flags retrocompatíveis.
* **`PATCH` (`0.0.X`):** Correções de bugs, hardening de segurança e refatorações/otimizações com impacto em artefato/release.
* **Exceção documental:** Alterações puramente de documentação ou comentários sem entrega de código/artefato podem manter a versão, salvo pedido explícito do usuário.
* **Report de entrega:** Ao concluir, informe explicitamente no `RESULT` a versão atualizada e a tag sugerida (`vX.Y.Z`), respeitando a proibição absoluta de `git commit`, `git tag` ou `git push` autônomos.
