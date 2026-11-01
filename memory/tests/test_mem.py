"""
Unit and Integration Test Suite for Antigravity Tier-2 Archival Memory Engine (mem).
Tests Clean Architecture components, Schema v3 migrations, Versioning & History,
Soft-delete & Restore, BM25 confidence weighting, Hot Backup, JSON formatting,
and Resilient YAML Frontmatter Parsing using stdlib unittest.
"""
from importlib.machinery import SourceFileLoader
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

# Load 'mem' executable as Python module via SourceFileLoader
MEM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mem"))
loader = SourceFileLoader("mem_engine", MEM_PATH)
spec = importlib.util.spec_from_loader("mem_engine", loader)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load mem module from {MEM_PATH}")
mem_engine = importlib.util.module_from_spec(spec)
sys.modules["mem_engine"] = mem_engine
spec.loader.exec_module(mem_engine)

DomainPolicy = mem_engine.DomainPolicy
DomainValidationError = mem_engine.DomainValidationError
ResourceNotFoundError = mem_engine.ResourceNotFoundError
SqliteMemoryRepository = mem_engine.SqliteMemoryRepository
MarkdownWikiAdapter = mem_engine.MarkdownWikiAdapter
MemoryEngineController = mem_engine.MemoryEngineController
UtcClockAdapter = mem_engine.UtcClockAdapter
build_parser = mem_engine.build_parser
DEFAULT_CORE_TEMPLATE = mem_engine.DEFAULT_CORE_TEMPLATE


class TestDomainPolicy(unittest.TestCase):
    def test_validate_namespace_valid(self):
        for ns in ["global", "git", "default", "proj:my-app", "proj:foo.bar_123"]:
            DomainPolicy.validate_namespace(ns)

    def test_validate_namespace_invalid(self):
        for ns in ["", "Global", "invalid@namespace", "proj:", "proj:bad/slash"]:
            with self.assertRaises(DomainValidationError):
                DomainPolicy.validate_namespace(ns)

    def test_validate_kind_valid(self):
        for kind in ("fact", "learning", "behavior", "decision", "invariant", "playbook"):
            DomainPolicy.validate_kind(kind)

    def test_validate_kind_invalid(self):
        for kind in ("invalid", "todo", "note", ""):
            with self.assertRaises(DomainValidationError):
                DomainPolicy.validate_kind(kind)

    def test_validate_confidence_valid(self):
        for conf in (0.0, 0.5, 1.0, 0.999):
            DomainPolicy.validate_confidence(conf)

    def test_validate_confidence_invalid(self):
        for conf in (-0.1, 1.01, 2.0, -10.0):
            with self.assertRaises(DomainValidationError):
                DomainPolicy.validate_confidence(conf)

    def test_parse_ttl(self):
        self.assertEqual(DomainPolicy.parse_ttl("30", "fact"), (30, True))
        self.assertEqual(DomainPolicy.parse_ttl(None, "fact"), (30, True))
        self.assertEqual(DomainPolicy.parse_ttl(None, "decision"), (None, True))
        self.assertEqual(DomainPolicy.parse_ttl("none", "fact"), (None, True))
        self.assertEqual(DomainPolicy.parse_ttl("0", "fact"), (None, True))
        self.assertEqual(DomainPolicy.parse_ttl(None, "fact", is_verify=True), (None, False))

    def test_get_core_max_lines_env(self):
        old_val = os.environ.get("ANTIGRAVITY_CORE_MAX_LINES")
        try:
            os.environ["ANTIGRAVITY_CORE_MAX_LINES"] = "45"
            self.assertEqual(DomainPolicy.get_core_max_lines(), 45)
            os.environ["ANTIGRAVITY_CORE_MAX_LINES"] = "invalid"
            self.assertEqual(DomainPolicy.get_core_max_lines(), 60)
        finally:
            if old_val is not None:
                os.environ["ANTIGRAVITY_CORE_MAX_LINES"] = old_val
            else:
                os.environ.pop("ANTIGRAVITY_CORE_MAX_LINES", None)

    def test_fts_query_synonym_expansion(self):
        syn_map = {"docker": ["container", "containers"]}
        query, expanded = DomainPolicy.build_fts_query("docker issue", syn_map)
        self.assertIn('"container"', query)
        self.assertIn('"containers"', query)
        self.assertIn("container", expanded)

    def test_error_fts_query(self):
        snippet = "NullPointerException in MemoryEngineController.java line 42"
        query, keywords = DomainPolicy.build_error_fts_query(snippet)
        self.assertTrue(len(keywords) > 0)
        self.assertIn('"pointer"', query.lower())


class TestMarkdownWikiAdapter(unittest.TestCase):
    def test_parse_inline_array(self):
        self.assertEqual(MarkdownWikiAdapter.parse_inline_array("[]"), [])
        self.assertEqual(
            MarkdownWikiAdapter.parse_inline_array('["REL -> a:b", "OTHER -> c:d"]'),
            ["REL -> a:b", "OTHER -> c:d"],
        )
        self.assertEqual(
            MarkdownWikiAdapter.parse_inline_array("['tag:1', 'tag:2', simple]"),
            ["tag:1", "tag:2", "simple"],
        )

    def test_parse_multiline_block(self):
        lines = ["  line 1", "  line 2", "    line 3"]
        self.assertEqual(
            MarkdownWikiAdapter.parse_multiline_block("|", lines),
            "line 1\nline 2\n  line 3",
        )
        self.assertEqual(
            MarkdownWikiAdapter.parse_multiline_block(">", lines),
            "line 1 line 2   line 3",
        )

    def test_parse_frontmatter_resilient(self):
        fm = """
namespace: "proj:test-repo"
topic: "fix: solve colons: in topic: and values"
kind: "learning"
version: 2
source: "agent-test"
confidence: 0.85
tags: ["bug:1", "windows", test]
access_count: 10
ttl_days: 14
created_at: "2026-11-01T10:00:00Z"
updated_at: "2026-11-01T11:00:00Z"
links:
  - "RELATES_TO -> global:user-profile"
  - "DEPENDS_ON -> proj:core"
"""
        doc = MarkdownWikiAdapter.parse_frontmatter(fm)
        self.assertEqual(doc.namespace, "proj:test-repo")
        self.assertEqual(doc.topic, "fix: solve colons: in topic: and values")
        self.assertEqual(doc.kind, "learning")
        self.assertEqual(doc.version, 2)
        self.assertEqual(doc.source, "agent-test")
        self.assertEqual(doc.confidence, 0.85)
        self.assertEqual(doc.tags, "bug:1, windows, test")
        self.assertEqual(doc.access_count, 10)
        self.assertEqual(doc.ttl_days, 14)
        self.assertEqual(len(doc.links), 2)
        self.assertIn("RELATES_TO -> global:user-profile", doc.links)


class TestSqliteRepositorySchemaV3(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_archival.db")
        self.clock = UtcClockAdapter()
        self.repo = SqliteMemoryRepository(self.db_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_fresh_database_initialization_schema_v3(self):
        conn = self.repo._get_conn()
        user_ver = conn.execute("PRAGMA user_version;").fetchone()[0]
        self.assertEqual(user_ver, 3)

        # Verify schema_migrations table
        migrations = conn.execute("SELECT version, description FROM schema_migrations ORDER BY version").fetchall()
        self.assertEqual(len(migrations), 3)
        self.assertEqual(migrations[0]["version"], 1)
        self.assertEqual(migrations[1]["version"], 2)
        self.assertEqual(migrations[2]["version"], 3)

        # Verify memories table columns
        cols = {col["name"]: col["type"] for col in conn.execute("PRAGMA table_info(memories)").fetchall()}
        self.assertIn("version", cols)
        self.assertIn("source", cols)
        self.assertIn("confidence", cols)
        self.assertIn("deleted_at", cols)

        # Verify memory_history table exists
        hist_table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory_history'").fetchone()
        self.assertIsNotNone(hist_table)

    def test_migration_from_schema_v2_to_v3(self):
        v2_dir = tempfile.mkdtemp()
        v2_path = os.path.join(v2_dir, "v2.db")
        try:
            conn = sqlite3.connect(v2_path)
            conn.executescript("""
                CREATE TABLE memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    namespace TEXT NOT NULL,
                    kind TEXT NOT NULL CHECK(kind IN ('fact', 'learning', 'behavior', 'decision', 'invariant', 'playbook')),
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT DEFAULT '',
                    access_count INTEGER DEFAULT 0,
                    ttl_days INTEGER DEFAULT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(namespace, topic)
                );
                CREATE VIRTUAL TABLE memories_fts USING fts5(
                    topic, content, tags, namespace,
                    content='memories', content_rowid='id'
                );
                CREATE TRIGGER memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, topic, content, tags, namespace)
                    VALUES (new.id, new.topic, new.content, new.tags, new.namespace);
                END;
                INSERT INTO memories (namespace, kind, topic, content, created_at, updated_at)
                VALUES ('global', 'fact', 'v2-record', 'Content preserved across migration', '2026-01-01', '2026-01-01');
                PRAGMA user_version = 2;
            """)
            conn.close()

            # Now open with SqliteMemoryRepository
            v2_repo = SqliteMemoryRepository(v2_path)
            v2_conn = v2_repo._get_conn()
            self.assertEqual(v2_conn.execute("PRAGMA user_version;").fetchone()[0], 3)

            # Record must be intact
            row = v2_conn.execute("SELECT * FROM memories WHERE topic = 'v2-record'").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["version"], 1)
            self.assertEqual(row["source"], "manual")
            self.assertEqual(float(row["confidence"]), 1.0)
            self.assertIsNone(row["deleted_at"])

            # Search in FTS must work
            records = v2_repo.search_fts("Content preserved", None, 5)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].topic, "v2-record")
        finally:
            shutil.rmtree(v2_dir, ignore_errors=True)

    def test_upsert_versioning_and_history(self):
        ts = self.clock.now_iso()
        self.repo.upsert(
            namespace="default",
            kind="fact",
            topic="test-versioning",
            content="Version 1 content",
            tags="v1",
            ttl_days=30,
            ts=ts,
            source="manual",
            confidence=0.8,
        )

        rec, history = self.repo.get_history("default", "test-versioning")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.version, 1)
        self.assertEqual(rec.confidence, 0.8)
        self.assertEqual(len(history), 0)

        # Update to v2
        ts2 = self.clock.now_iso()
        self.repo.upsert(
            namespace="default",
            kind="fact",
            topic="test-versioning",
            content="Version 2 content updated",
            tags="v2",
            ttl_days=30,
            ts=ts2,
            source="agent-default",
            confidence=0.95,
        )

        rec2, history2 = self.repo.get_history("default", "test-versioning")
        self.assertEqual(rec2.version, 2)
        self.assertEqual(rec2.source, "agent-default")
        self.assertEqual(rec2.confidence, 0.95)
        self.assertEqual(len(history2), 1)
        self.assertEqual(history2[0].version, 1)
        self.assertEqual(history2[0].content, "Version 1 content")

    def test_soft_delete_and_restore(self):
        ts = self.clock.now_iso()
        self.repo.upsert(
            namespace="default",
            kind="learning",
            topic="test-soft-delete",
            content="UniqueSearchableTermForSoftDelete",
            tags="tag1",
            ttl_days=None,
            ts=ts,
        )

        # Verify searchable
        found = self.repo.search_fts("UniqueSearchableTermForSoftDelete", "default", 5)
        self.assertEqual(len(found), 1)

        # Soft delete
        deleted = self.repo.delete_record("default", "test-soft-delete", hard=False, ts=self.clock.now_iso())
        self.assertTrue(deleted)

        # Search must NOT find it
        found_after = self.repo.search_fts("UniqueSearchableTermForSoftDelete", "default", 5)
        self.assertEqual(len(found_after), 0)

        # get_by_topic must raise ResourceNotFoundError
        with self.assertRaises(ResourceNotFoundError):
            self.repo.get_by_topic("default", "test-soft-delete")

        # History still shows current soft-deleted state
        rec, hist = self.repo.get_history("default", "test-soft-delete")
        self.assertIsNotNone(rec)
        self.assertIsNotNone(rec.deleted_at)

        # Restore
        restored = self.repo.restore_record("default", "test-soft-delete", ts=self.clock.now_iso())
        self.assertTrue(restored)

        # Search must find it again
        found_restored = self.repo.search_fts("UniqueSearchableTermForSoftDelete", "default", 5)
        self.assertEqual(len(found_restored), 1)

    def test_hard_delete(self):
        ts = self.clock.now_iso()
        self.repo.upsert(
            namespace="default",
            kind="fact",
            topic="test-hard-delete",
            content="Temporary data",
            tags="temp",
            ttl_days=None,
            ts=ts,
        )
        self.assertTrue(self.repo.delete_record("default", "test-hard-delete", hard=True))
        rec, hist = self.repo.get_history("default", "test-hard-delete")
        self.assertIsNone(rec)

    def test_confidence_weighted_bm25_ranking(self):
        ts = self.clock.now_iso()
        # Insert two memories with exact same match term but different confidence
        self.repo.upsert(
            namespace="default",
            kind="fact",
            topic="high-confidence-doc",
            content="QuantumComputingAlgorithm is fascinating",
            tags="quantum",
            ttl_days=None,
            ts=ts,
            confidence=1.0,
        )
        self.repo.upsert(
            namespace="default",
            kind="fact",
            topic="low-confidence-doc",
            content="QuantumComputingAlgorithm is uncertain",
            tags="quantum",
            ttl_days=None,
            ts=ts,
            confidence=0.2,
        )

        results = self.repo.search_fts("QuantumComputingAlgorithm", "default", 5)
        self.assertEqual(len(results), 2)
        # High confidence doc must rank first and have higher score
        self.assertEqual(results[0].topic, "high-confidence-doc")
        self.assertEqual(results[1].topic, "low-confidence-doc")
        self.assertGreater(results[0].score, results[1].score * 2.0)

    def test_hot_backup_creates_valid_database(self):
        ts = self.clock.now_iso()
        self.repo.upsert(
            namespace="global",
            kind="decision",
            topic="backup-test",
            content="Valid content to backup",
            tags="backup",
            ttl_days=None,
            ts=ts,
        )
        backup_path = os.path.join(self.test_dir, "backup.db")
        saved = self.repo.hot_backup(backup_path)
        self.assertTrue(os.path.exists(saved))

        # Check backup content
        b_conn = sqlite3.connect(saved)
        b_conn.row_factory = sqlite3.Row
        row = b_conn.execute("SELECT * FROM memories WHERE topic = 'backup-test'").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["content"], "Valid content to backup")
        b_conn.close()


class TestControllerAndCliJson(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "archival.db")
        self.core_path = os.path.join(self.test_dir, "CORE.md")
        self.core_template_path = os.path.join(self.test_dir, "CORE.template.md")
        self.clock = UtcClockAdapter()
        self.repo = SqliteMemoryRepository(self.db_path)
        self.controller = MemoryEngineController(
            repo=self.repo,
            clock=self.clock,
            mem_dir=self.test_dir,
            db_path=self.db_path,
            core_path=self.core_path,
            core_template_path=self.core_template_path,
        )
        self.parser = build_parser(self.controller)

        # Seed foundational data
        args_init = self.parser.parse_args(["init", "--user", "Tester", "--lang", "pt-BR"])
        args_init.func(args_init)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_check_core_json_and_density(self):
        args = self.parser.parse_args(["check-core", "--json"])
        self.assertTrue(getattr(args, "json", False))
        # Call controller method directly
        old_stdout = sys.stdout
        from io import StringIO
        sys.stdout = StringIO()
        try:
            args.func(args)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        data = json.loads(output)
        self.assertEqual(data["status"], "OK")
        self.assertIn("line_count", data)
        self.assertIn("word_count", data)
        self.assertIn("byte_count", data)
        self.assertIn("estimated_tokens", data)

    def test_list_and_search_json(self):
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            args_list = self.parser.parse_args(["list", "--json"])
            args_list.func(args_list)
            list_output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        records = json.loads(list_output)
        self.assertTrue(len(records) >= 8)
        self.assertIn("version", records[0])
        self.assertIn("source", records[0])
        self.assertIn("confidence", records[0])

    def test_stats_json(self):
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            args_stats = self.parser.parse_args(["stats", "--json"])
            args_stats.func(args_stats)
            stats_output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        stats = json.loads(stats_output)
        self.assertIn("soft_deleted_count", stats)
        self.assertIn("history_versions_count", stats)
        self.assertIn("namespaces", stats)

    def test_cli_subprocess_clean_error_handling(self):
        # Test clean stderr on domain validation error
        res = subprocess.run(
            [sys.executable, MEM_PATH, "get", "INVALID_NAMESPACE@", "topic"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("Error: Invalid namespace", res.stderr)
        self.assertNotIn("Traceback", res.stderr)

        # Test clean JSON on error with --json
        res_json = subprocess.run(
            [sys.executable, MEM_PATH, "--json", "get", "INVALID_NAMESPACE@", "topic"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_json.returncode, 1)
        err_obj = json.loads(res_json.stderr)
        self.assertEqual(err_obj["status"], "error")
        self.assertIn("Invalid namespace", err_obj["error"])
        self.assertNotIn("Traceback", res_json.stderr)


if __name__ == "__main__":
    unittest.main()
