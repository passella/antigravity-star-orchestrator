#!/usr/bin/env python3
from collections.abc import Mapping
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
README_ENV_VAR = "GEMINI_README_PATH"
STANDARD_EXTENDS_PREFIX = "> **HERANÇA OBRIGATÓRIA (`EXTENDS`):** [agent-dev-base](~/.gemini/agents/agent-dev-base/AGENT.md)"


def resolve_readme_path(
    repo_root: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[Path, bool]:
    source_env = os.environ if env is None else env
    raw_override = source_env.get(README_ENV_VAR, "").strip()
    if raw_override:
        return Path(raw_override).expanduser(), True
    base_root = REPO_ROOT if repo_root is None else repo_root
    return base_root / "README.md", False


def discover_agents(agents_dir: str | Path) -> list[tuple[str, str]]:
    agents_path = Path(agents_dir)
    if not agents_path.is_dir():
        return []
    discovered: list[tuple[str, str]] = []
    for entry in sorted(os.listdir(agents_path)):
        if not entry.startswith("agent-") or entry in ("agent-dev-base", "orchestrator"):
            continue
        agent_md = agents_path / entry / "AGENT.md"
        if agent_md.is_file():
            discovered.append((entry, str(agent_md)))
    return discovered


def read_text(path: str | Path) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def declares_extends_dev_base(agent_content: str) -> bool:
    return bool(re.search(r"(?m)^>.*EXTENDS.*agent-dev-base", agent_content))


def has_standard_extends_header(agent_content: str) -> bool:
    return any(line.strip().startswith(STANDARD_EXTENDS_PREFIX) for line in agent_content.splitlines()[:10])


def extract_readme_section_8_1(readme_content: str) -> str:
    match = re.search(r"(?ms)^### 8\.1\..*?(?=^### 8\.2\.|^## |\Z)", readme_content)
    if not match:
        raise ValueError("Section 8.1 not found in README.md")
    return match.group(0)


def extract_readme_listed_agents(section_8_1: str) -> set[str]:
    return set(re.findall(r"\*\*`(agent-[a-z0-9-]+)`\*\*", section_8_1))


def parse_readme_inheritance_map(section_8_1: str) -> dict[str, str]:
    inheritance: dict[str, str] = {}
    in_local_catalog_table = False
    for raw_line in section_8_1.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            if in_local_catalog_table and line:
                in_local_catalog_table = False
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 4 and "Herança" in cells[3]:
            in_local_catalog_table = True
            continue
        if not in_local_catalog_table or len(cells) < 4:
            continue
        if set(cells[0].replace(":", "").replace("-", "").strip()) == set():
            continue
        id_match = re.search(r"\*\*`(agent-[a-z0-9-]+)`\*\*", cells[0])
        if id_match:
            inheritance[id_match.group(1)] = cells[3]
    return inheritance


def extract_dev_base_scope_agents(dev_base_content: str) -> set[str]:
    header_block = dev_base_content.split("\n---", 1)[0]
    scope_lines = [line for line in header_block.splitlines() if line.strip().startswith("> **Escopo:**")]
    target_text = "\n".join(scope_lines) if scope_lines else header_block
    return {name for name in re.findall(r"`(agent-[a-z0-9-]+)`", target_text) if name != "agent-dev-base"}


def is_agent_registered_in_core(core_content: str, agent_name: str) -> bool:
    clean_name = agent_name.removeprefix("agent-")
    return (
        f"agents/{agent_name}/AGENT.md" in core_content
        or f"**`{clean_name}`**" in core_content
        or f"**`{agent_name}`**" in core_content
    )


class TestCatalogParityHelpersUnit(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_missing_section_8_1_raises_value_error(self):
        with self.assertRaises(ValueError):
            extract_readme_section_8_1("# Title\n\n### 8.2. Next\n")

    def test_falsy_and_excluded_agents(self):
        self.assertEqual(discover_agents(os.path.join(self.test_dir, "missing")), [])
        agents_dir = os.path.join(self.test_dir, "agents")
        for name in ("orchestrator", "agent-dev-base", "agent-default", "empty-dir"):
            os.makedirs(os.path.join(agents_dir, name), exist_ok=True)
            if name != "empty-dir":
                with open(os.path.join(agents_dir, name, "AGENT.md"), "w", encoding="utf-8") as handle:
                    handle.write(f"# {name}\n")
        discovered = discover_agents(agents_dir)
        self.assertEqual([name for name, _ in discovered], ["agent-default"])

    def test_resolve_readme_path_env_override_and_fallback(self):
        fake_root = Path(self.test_dir)
        resolved_unset, from_env_unset = resolve_readme_path(repo_root=fake_root, env={})
        self.assertEqual(resolved_unset, fake_root / "README.md")
        self.assertFalse(from_env_unset)

        resolved_blank, from_env_blank = resolve_readme_path(
            repo_root=fake_root,
            env={README_ENV_VAR: "   "},
        )
        self.assertEqual(resolved_blank, fake_root / "README.md")
        self.assertFalse(from_env_blank)

        tilde_resolved, tilde_from_env = resolve_readme_path(
            repo_root=fake_root,
            env={README_ENV_VAR: " ~/custom/README.md "},
        )
        self.assertEqual(tilde_resolved, Path("~/custom/README.md").expanduser())
        self.assertTrue(tilde_from_env)

        explicit_path = fake_root / "alt-README.md"
        explicit_resolved, explicit_from_env = resolve_readme_path(
            repo_root=fake_root,
            env={README_ENV_VAR: str(explicit_path)},
        )
        self.assertEqual(explicit_resolved, explicit_path)
        self.assertTrue(explicit_from_env)

    def test_inheritance_detection_boundaries(self):
        self.assertFalse(declares_extends_dev_base("# Agent\n> **ID:** `agent-git`\n"))
        self.assertFalse(has_standard_extends_header("# Agent\n> **EXTENDS:** `~/.gemini/agents/agent-dev-base/AGENT.md`\n"))
        self.assertTrue(declares_extends_dev_base("# Agent\n> **EXTENDS:** `~/.gemini/agents/agent-dev-base/AGENT.md`\n"))
        standard = f"# Agent\n\n{STANDARD_EXTENDS_PREFIX} — Leia\n"
        self.assertTrue(declares_extends_dev_base(standard))
        self.assertTrue(has_standard_extends_header(standard))

    def test_clean_ci_readme_and_dev_base_parsing(self):
        sample_readme = (
            "### 8.1. Tabela\n\n"
            "| ID do Agente | Caminho | Status | Namespace | Papel |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **`agent-default`** | `agents/agent-default/AGENT.md` | OK | `default` | General |\n\n"
            "| ID do Agente | Caminho | Namespace | Herança (`EXTENDS`) | Escopo |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **`agent-qa`** | `agents/agent-qa/AGENT.md` | `qa` | `agent-dev-base` | QA |\n"
            "| **`agent-git`** | `agents/agent-git/AGENT.md` | `git` | Independente | Git |\n\n"
            "### 8.2. Modo 1\n"
        )
        section = extract_readme_section_8_1(sample_readme)
        listed = extract_readme_listed_agents(section)
        self.assertEqual(listed, {"agent-default", "agent-qa", "agent-git"})
        inh_map = parse_readme_inheritance_map(section)
        self.assertEqual(inh_map, {"agent-qa": "`agent-dev-base`", "agent-git": "Independente"})
        dev_base_md = (
            "# Base (`agent-dev-base`)\n"
            "> **Escopo:** SSOT para `agent-qa`, `agent-rust`.\n"
            "---\n"
        )
        self.assertEqual(extract_dev_base_scope_agents(dev_base_md), {"agent-qa", "agent-rust"})

    def test_is_agent_registered_in_core_patterns(self):
        self.assertFalse(is_agent_registered_in_core("", "agent-qa"))
        self.assertFalse(is_agent_registered_in_core("- **`rust`**: desc\n", "agent-qa"))
        self.assertTrue(is_agent_registered_in_core("- **`qa`**: desc\n", "agent-qa"))
        self.assertTrue(is_agent_registered_in_core("- **`agent-qa`**: desc\n", "agent-qa"))
        self.assertTrue(is_agent_registered_in_core("- (`~/.gemini/agents/agent-qa/AGENT.md`)\n", "agent-qa"))


class TestRepositoryCatalogParity(unittest.TestCase):

    def setUp(self):
        self.agents_dir = REPO_ROOT / "agents"
        self.readme_path, self.readme_from_env = resolve_readme_path()
        self.core_path = REPO_ROOT / "memory" / "CORE.md"
        self.dev_base_path = self.agents_dir / "agent-dev-base" / "AGENT.md"
        self.discovered = discover_agents(self.agents_dir)

    def _require_readme_content(self) -> str:
        if self.readme_from_env:
            self.assertTrue(
                self.readme_path.is_file(),
                f"{README_ENV_VAR} points to missing file: {self.readme_path}",
            )
            return read_text(self.readme_path)
        if not self.readme_path.is_file():
            self.skipTest(
                f"README.md not visible at {self.readme_path} (hidden by sandbox or absent; set {README_ENV_VAR} to override)"
            )
        return read_text(self.readme_path)

    def test_readme_resolution_respects_env_and_sandbox_gracefully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            case = TestRepositoryCatalogParity("test_agents_listed_in_readme_section_8_1")
            case.agents_dir = Path(tmpdir) / "agents"
            case.core_path = Path(tmpdir) / "CORE.md"
            case.dev_base_path = case.agents_dir / "agent-dev-base" / "AGENT.md"
            case.discovered = []

            case.readme_path, case.readme_from_env = resolve_readme_path(
                repo_root=Path(tmpdir),
                env={README_ENV_VAR: str(Path(tmpdir) / "missing-env.md")},
            )
            with self.assertRaises(AssertionError):
                case._require_readme_content()

            case.readme_path, case.readme_from_env = resolve_readme_path(
                repo_root=Path(tmpdir),
                env={},
            )
            with self.assertRaises(unittest.SkipTest):
                case._require_readme_content()

            valid_readme = Path(tmpdir) / "override.md"
            valid_readme.write_text("# Override\n", encoding="utf-8")
            case.readme_path, case.readme_from_env = resolve_readme_path(
                repo_root=Path(tmpdir),
                env={README_ENV_VAR: str(valid_readme)},
            )
            self.assertEqual(case._require_readme_content(), "# Override\n")

    def test_agents_registered_in_core_when_present(self):
        if not self.core_path.is_file():
            self.skipTest("CORE.md absent in clean CI environment")
        core_content = read_text(self.core_path)
        missing = [name for name, _ in self.discovered if not is_agent_registered_in_core(core_content, name)]
        self.assertEqual(missing, [], f"Agents missing in CORE.md: {missing}")

    def test_agents_listed_in_readme_section_8_1(self):
        section_8_1 = extract_readme_section_8_1(self._require_readme_content())
        listed_in_readme = extract_readme_listed_agents(section_8_1)
        missing = [name for name, _ in self.discovered if name not in listed_in_readme]
        self.assertEqual(missing, [], f"Agents missing in README.md Section 8.1: {missing}")

    def test_extending_agents_parity_with_dev_base_and_readme(self):
        extending_agents: set[str] = set()
        independent_local_agents: set[str] = set()
        for name, agent_md_path in self.discovered:
            content = read_text(agent_md_path)
            if declares_extends_dev_base(content):
                extending_agents.add(name)
                self.assertTrue(
                    has_standard_extends_header(content),
                    f"{name}/AGENT.md does not use standardized HERANÇA OBRIGATÓRIA header",
                )
            elif name != "agent-default":
                independent_local_agents.add(name)

        if extending_agents or self.dev_base_path.is_file():
            self.assertTrue(self.dev_base_path.is_file(), "agent-dev-base/AGENT.md not found")
            dev_base_scope_agents = extract_dev_base_scope_agents(read_text(self.dev_base_path))
            missing_in_dev_base = sorted(extending_agents - dev_base_scope_agents)
            self.assertEqual(
                missing_in_dev_base,
                [],
                f"Extending agents missing in agent-dev-base/AGENT.md scope: {missing_in_dev_base}",
            )
            unexpected_in_dev_base = sorted(dev_base_scope_agents - extending_agents)
            self.assertEqual(
                unexpected_in_dev_base,
                [],
                f"Agents listed in agent-dev-base/AGENT.md scope without EXTENDS declaration: {unexpected_in_dev_base}",
            )
            false_positive_independent = sorted(independent_local_agents & dev_base_scope_agents)
            self.assertEqual(
                false_positive_independent,
                [],
                f"Independent agents unexpectedly listed in agent-dev-base/AGENT.md scope: {false_positive_independent}",
            )

        section_8_1 = extract_readme_section_8_1(self._require_readme_content())
        inheritance_map = parse_readme_inheritance_map(section_8_1)
        for name in sorted(extending_agents):
            self.assertIn(name, inheritance_map, f"{name} missing from README.md Section 8.1 inheritance table")
            self.assertIn(
                "agent-dev-base",
                inheritance_map[name],
                f"{name} is not marked as inheriting agent-dev-base in README.md Section 8.1",
            )
        for name in sorted(independent_local_agents):
            self.assertIn(name, inheritance_map, f"{name} missing from README.md Section 8.1 inheritance table")
            self.assertNotIn(
                "agent-dev-base",
                inheritance_map[name],
                f"{name} should not be marked as inheriting agent-dev-base in README.md Section 8.1",
            )


if __name__ == "__main__":
    unittest.main()
