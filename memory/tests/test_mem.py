#!/usr/bin/env python3
import importlib.util
from importlib.machinery import SourceFileLoader
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
if os.path.isfile(os.path.join(os.path.dirname(__file__), "mem")):
    MEM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "mem"))
else:
    MEM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mem"))
loader = SourceFileLoader('mem_engine', MEM_PATH)
spec = importlib.util.spec_from_loader('mem_engine', loader)
if spec is None or spec.loader is None:
    raise ImportError(f'Cannot load mem module from {MEM_PATH}')
mem_engine = importlib.util.module_from_spec(spec)
sys.modules['mem_engine'] = mem_engine
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

class TestDomainPolicyUnit(unittest.TestCase):

    def test_validate_namespace_exceptions(self):
        invalid_namespaces = ['', 'Global', 'invalid@namespace', 'proj:', 'proj:bad/slash', 'has space', '-startdash']
        for ns in invalid_namespaces:
            with self.assertRaises(DomainValidationError):
                DomainPolicy.validate_namespace(ns)

    def test_validate_kind_exceptions(self):
        invalid_kinds = ['', 'unknown', 'FACT', 'note', 'task']
        for kind in invalid_kinds:
            with self.assertRaises(DomainValidationError):
                DomainPolicy.validate_kind(kind)

    def test_validate_confidence_exceptions(self):
        invalid_confidences = [-0.1, -1.0, 1.01, 2.5]
        for conf in invalid_confidences:
            with self.assertRaises(DomainValidationError):
                DomainPolicy.validate_confidence(conf)

    def test_parse_ttl_exceptions(self):
        with self.assertRaises(DomainValidationError):
            DomainPolicy.parse_ttl('invalid', 'fact', is_verify=False)
        with self.assertRaises(DomainValidationError):
            DomainPolicy.parse_ttl('-5', 'fact', is_verify=False)

    def test_falsy_and_guards(self):
        query, syns = DomainPolicy.build_fts_query('', {})
        self.assertEqual(query, '')
        self.assertEqual(syns, [])
        query2, words = DomainPolicy.build_error_fts_query('')
        self.assertEqual(query2, '')
        self.assertEqual(words, [])
        missing, present = DomainPolicy.check_agents_registered('some content', '/nonexistent/agents/path')
        self.assertEqual(missing, [])
        self.assertEqual(present, [])

    def test_limits_and_boundaries(self):
        DomainPolicy.validate_confidence(0.0)
        DomainPolicy.validate_confidence(1.0)
        DomainPolicy.validate_confidence(0.5)
        ttl_zero, _ = DomainPolicy.parse_ttl('0', 'fact', is_verify=False)
        self.assertIsNone(ttl_zero)
        ttl_one, _ = DomainPolicy.parse_ttl('1', 'fact', is_verify=False)
        self.assertEqual(ttl_one, 1)
        ttl_def, _ = DomainPolicy.parse_ttl(None, 'fact', is_verify=False)
        self.assertEqual(ttl_def, 30)
        ttl_learn, _ = DomainPolicy.parse_ttl(None, 'learning', is_verify=False)
        self.assertIsNone(ttl_learn)
        ok_parity, errors = DomainPolicy.check_structural_parity('a\nb', 'a', 'a\nb')
        self.assertFalse(ok_parity)
        self.assertTrue(len(errors) > 0)
        ok_hdr, hdr_errors = DomainPolicy.check_structural_parity('## H1', '## H2', '## H1')
        self.assertFalse(ok_hdr)
        self.assertTrue(len(hdr_errors) > 0)

    def test_happy_path_validation_and_parsing(self):
        valid_namespaces = ['global', 'git', 'default', 'dev-base', 'proj:my-app', 'proj:foo.bar_123']
        for ns in valid_namespaces:
            DomainPolicy.validate_namespace(ns)
        for kind in ('fact', 'learning', 'behavior', 'decision', 'invariant', 'playbook'):
            DomainPolicy.validate_kind(kind)
        summary = DomainPolicy.make_summary('Line 1\nLine 2\nLine 3', 'tag1,tag2')
        self.assertEqual(summary, 'Line 1')
        fts_q, syns = DomainPolicy.build_fts_query('hexagonal architecture', {'hexagonal': ['ports and adapters']})
        self.assertIn('hexagonal', fts_q)
        self.assertIn('ports and adapters', syns)
        err_q, words = DomainPolicy.build_error_fts_query('NullPointerException at com.example.service.UserService.find')
        self.assertIn('nullpointerexception', words)
        ok, errs = DomainPolicy.check_structural_parity('line1\n## Sec\nline3', 'line1\n## Sec\nline3', 'line1\n## Sec\nline3')
        self.assertTrue(ok)
        self.assertEqual(errs, [])
        core_with_proj = 'line1\n## Sec\nline3\n- **proj:test**: description\n- **`proj:another`**: description'
        ok_proj, errs_proj = DomainPolicy.check_structural_parity(core_with_proj, 'line1\n## Sec\nline3', 'line1\n## Sec\nline3')
        self.assertTrue(ok_proj)
        self.assertEqual(errs_proj, [])
        agent_ref = 'agents/' + 'agent-git'
        core_with_agents = f'line1\n## 🧭 3. Semantic Directory\nline3\n- **`global`**: desc\n- **`git`** ({agent_ref}/AGENT.md): desc'
        tpl_clean = 'line1\n## 🧭 3. Semantic Directory\nline3\n- **`global`**: desc'
        ok_agents, errs_agents = DomainPolicy.check_structural_parity(core_with_agents, tpl_clean, tpl_clean)
        self.assertTrue(ok_agents)
        self.assertEqual(errs_agents, [])

class TestMarkdownWikiAdapterUnit(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_exceptions_and_malformed(self):
        bad_file = os.path.join(self.test_dir, 'bad.md')
        with open(bad_file, 'w', encoding='utf-8') as f:
            f.write('---\nnamespace: InvalidNamespaceWithCapital\ntopic: test\n---\nbody\n')
        docs, warnings = MarkdownWikiAdapter.read_wiki_directory(self.test_dir)
        self.assertEqual(len(docs), 0)
        self.assertEqual(len(warnings), 1)

    def test_falsy_and_empty(self):
        docs, warnings = MarkdownWikiAdapter.read_wiki_directory(self.test_dir)
        self.assertEqual(docs, [])
        self.assertEqual(warnings, [])
        non_md = os.path.join(self.test_dir, 'note.txt')
        with open(non_md, 'w', encoding='utf-8') as f:
            f.write('just text')
        docs2, warnings2 = MarkdownWikiAdapter.read_wiki_directory(self.test_dir)
        self.assertEqual(docs2, [])
        self.assertEqual(warnings2, [])

    def test_limits_and_boundaries(self):
        empty_body = os.path.join(self.test_dir, 'empty_body.md')
        with open(empty_body, 'w', encoding='utf-8') as f:
            f.write('---\nnamespace: global\nkind: fact\ntopic: empty\n---\n')
        docs, warnings = MarkdownWikiAdapter.read_wiki_directory(self.test_dir)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].body, '')

    def test_happy_path_export_and_import(self):
        record = mem_engine.MemoryRecord(id=1, namespace='global', kind='fact', topic='wiki-test', content='Markdown body content with [[git:commit-rule]]', tags='wiki,test', access_count=5, ttl_days=30, created_at='2026-01-01T00:00:00Z', updated_at='2026-01-02T00:00:00Z', version=1, source='manual', confidence=1.0)
        edge = mem_engine.SemanticEdge(relation='RELATES_TO', namespace='git', topic='commit-rule', direction='outgoing')
        export_items = [(record, [edge], [])]
        count, index_path = MarkdownWikiAdapter.export_wiki(wiki_dir=self.test_dir, items=export_items, is_full_export=True, now_iso='2026-01-02T00:00:00Z')
        self.assertEqual(count, 1)
        self.assertTrue(os.path.exists(index_path))
        docs, warnings = MarkdownWikiAdapter.read_wiki_directory(self.test_dir)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].namespace, 'global')
        self.assertEqual(docs[0].topic, 'wiki-test')
        self.assertIn('RELATES_TO -> git:commit-rule', docs[0].links)

class TestSqliteRepositoryComponent(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_archival.db')
        self.repo = SqliteMemoryRepository(self.db_path)
        self.clock = UtcClockAdapter()

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_exceptions_and_integrity_failure(self):
        bad_db_path = os.path.join(self.test_dir, 'corrupted.db')
        with open(bad_db_path, 'wb') as f:
            f.write(b'not a valid sqlite database header at all')
        bad_repo = SqliteMemoryRepository(bad_db_path)
        with self.assertRaises(sqlite3.Error):
            bad_repo.check_integrity()
        bad_repo.close()

    def test_falsy_and_nonexistent(self):
        with self.assertRaises(ResourceNotFoundError):
            self.repo.get_by_topic('global', 'nonexistent-topic')
        deleted = self.repo.delete_record('global', 'nonexistent-topic', hard=False)
        self.assertFalse(deleted)
        restored = self.repo.restore_record('global', 'nonexistent-topic', '2026-01-01T00:00:00Z')
        self.assertFalse(restored)
        done = self.repo.complete_task(999999, '2026-01-01T00:00:00Z')
        self.assertFalse(done)
        results = self.repo.search_fts('completely_unmatched_term_xyz_12345', None, limit=5)
        self.assertEqual(len(results), 0)

    def test_limits_and_boundaries(self):
        ts = self.clock.now_iso()
        self.repo.upsert('global', 'fact', 'bva-test', 'Initial content', 'bva', 1, ts, confidence=0.0)
        rec, _ = self.repo.get_by_topic('global', 'bva-test')
        self.assertIsNotNone(rec)
        self.assertEqual(rec.confidence, 0.0)
        self.assertEqual(rec.version, 1)
        self.repo.upsert('global', 'fact', 'bva-test', 'Updated content', 'bva', 1, ts, confidence=1.0)
        rec2, _ = self.repo.get_by_topic('global', 'bva-test')
        self.assertEqual(rec2.version, 2)
        self.assertEqual(rec2.confidence, 1.0)
        stale_status = DomainPolicy.check_stale(rec2.updated_at, rec2.ttl_days, self.clock)
        self.assertIsNone(stale_status)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        stale_old = DomainPolicy.check_stale(old_ts, 1, self.clock)
        self.assertIsNotNone(stale_old)

    def test_happy_path_lifecycle_and_gc(self):
        ts = self.clock.now_iso()
        self.repo.upsert('global', 'fact', 'topic-a', 'Alpha content', 'test', 30, ts)
        self.repo.upsert('global', 'fact', 'topic-b', 'Beta content', 'test', 30, ts)
        rec_a, _ = self.repo.get_by_topic('global', 'topic-a')
        rec_b, _ = self.repo.get_by_topic('global', 'topic-b')
        self.assertIsNotNone(rec_a)
        self.assertIsNotNone(rec_b)
        self.repo.link_topics('global', 'topic-a', 'RELATES_TO', 'global', 'topic-b', ts)
        rec_a_fetched, edges = self.repo.get_by_topic('global', 'topic-a')
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].topic, 'topic-b')
        task_id = self.repo.defer_task('global', 'on-boot', 'run verification', ts)
        self.assertGreater(task_id, 0)
        due_tasks = self.repo.list_due_tasks(['global'])
        self.assertEqual(len(due_tasks), 1)
        completed = self.repo.complete_task(task_id, ts)
        self.assertTrue(completed)
        self.assertEqual(len(self.repo.list_due_tasks(['global'])), 0)
        ok, msg = self.repo.check_integrity()
        self.assertTrue(ok)
        self.assertEqual(msg, 'ok')
        del_ok = self.repo.delete_record('global', 'topic-b', hard=False, ts=ts)
        self.assertTrue(del_ok)
        purged_rec, purged_hist, purged_edges, freelist_rec = self.repo.purge_garbage(days=None, force=True, ts=ts)
        self.assertGreaterEqual(freelist_rec, 0)
        self.assertEqual(purged_rec, 1)
        with self.assertRaises(ResourceNotFoundError):
            self.repo.get_by_topic('global', 'topic-b')

    def test_incremental_vacuum_and_freelist_reclaim(self):
        ts = self.clock.now_iso()
        for i in range(150):
            self.repo.upsert('default', 'fact', f'vac-topic-{i}', 'X' * 2000, 'vacuum', 30, ts)
        for i in range(120):
            self.repo.delete_record('default', f'vac-topic-{i}', hard=False, ts=ts)
        purged_rec, purged_hist, purged_edges, freelist_rec = self.repo.purge_garbage(days=None, force=False, ts=ts)
        self.assertEqual(purged_rec, 120)
        self.assertGreater(freelist_rec, 0)
        purged_rec2, _, _, freelist_rec2 = self.repo.purge_garbage(days=None, force=True, ts=ts)
        self.assertEqual(purged_rec2, 0)
        self.assertGreaterEqual(freelist_rec2, 0)

class TestControllerAndCliIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'archival.db')
        self.core_path = os.path.join(self.test_dir, 'CORE.md')
        self.core_template_path = os.path.join(self.test_dir, 'CORE.template.md')
        self.lock_path = os.path.join(self.test_dir, '.core.lock')
        self.agents_dir = os.path.join(self.test_dir, 'agents')
        os.makedirs(self.agents_dir, exist_ok=True)
        agent_dir = os.path.join(self.agents_dir, 'agent-test')
        os.makedirs(agent_dir, exist_ok=True)
        with open(os.path.join(agent_dir, 'AGENT.md'), 'w', encoding='utf-8') as f:
            f.write('# Agent Test\n')
        self.repo = SqliteMemoryRepository(self.db_path)
        self.clock = UtcClockAdapter()
        self.controller = MemoryEngineController(repo=self.repo, clock=self.clock, mem_dir=self.test_dir, db_path=self.db_path, core_path=self.core_path, core_template_path=self.core_template_path, lock_path=self.lock_path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_exceptions_missing_core_and_corrupt_db(self):
        parser = build_parser(self.controller)
        args_check = parser.parse_args(['check-core', '--skip-agents-check', '--skip-db-check'])
        with self.assertRaises(ResourceNotFoundError):
            args_check.func(args_check)
        with open(self.core_path, 'w', encoding='utf-8') as f:
            f.write('# Dummy\n')
        with open(self.db_path, 'wb') as f:
            f.write(b'not sqlite')
        args_corrupt = parser.parse_args(['check-core', '--skip-agents-check'])
        with self.assertRaises(sqlite3.Error):
            args_corrupt.func(args_corrupt)

    def test_falsy_and_guards_cli(self):
        with open(self.core_path, 'w', encoding='utf-8') as f:
            f.write('# Dummy\n')
        parser = build_parser(self.controller)
        args_gc = parser.parse_args(['gc', '--json'])
        args_gc.func(args_gc)
        args_due = parser.parse_args(['due', '--json'])
        args_due.func(args_due)

    def test_limits_bva_59_60_61_lines(self):
        parser = build_parser(self.controller)
        for line_count, expected_status, should_exit in [(59, 'OK', False), (60, 'OK', False), (61, 'EXCEEDED', True)]:
            lines = [f'line {i + 1}\n' for i in range(line_count)]
            with open(self.core_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            args = parser.parse_args(['check-core', '--json', '--skip-agents-check', '--skip-db-check'])
            if should_exit:
                with self.assertRaises(SystemExit) as cm:
                    args.func(args)
                self.assertEqual(cm.exception.code, 1)
            else:
                args.func(args)

    def test_happy_path_cli_operations(self):
        parser = build_parser(self.controller)
        args_init = parser.parse_args(['init', '--user', 'Tester', '--lang', 'pt-BR', '--workspace', '~/test'])
        args_init.func(args_init)
        self.assertTrue(os.path.exists(self.core_path))
        args_upsert = parser.parse_args(['upsert', 'global', 'fact', 'cli-test', 'CLI content', 'cli'])
        args_upsert.func(args_upsert)
        args_search = parser.parse_args(['search', 'CLI content', '--json'])
        args_search.func(args_search)
        args_stats = parser.parse_args(['stats', '--json'])
        args_stats.func(args_stats)
        args_backup = parser.parse_args(['backup', '--json'])
        args_backup.func(args_backup)
        args_gc = parser.parse_args(['gc', '--force', '--json'])
        args_gc.func(args_gc)

class TestConcurrencyAndStress(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'stress_archival.db')
        init_repo = SqliteMemoryRepository(self.db_path)
        init_repo.initialize([], '2026-01-01T00:00:00Z')
        init_repo.close()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_upserts_and_reads(self):

        def worker(idx: int):
            thread_repo = SqliteMemoryRepository(self.db_path)
            clock = UtcClockAdapter()
            ts = clock.now_iso()
            thread_repo.upsert('global', 'fact', f'worker-{idx}', f'Content from worker {idx}', 'stress', 30, ts)
            rec, _ = thread_repo.get_by_topic('global', f'worker-{idx}')
            thread_repo.close()
            return rec is not None
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker, i) for i in range(12)]
            results = [f.result() for f in futures]
        self.assertTrue(all(results))
        check_repo = SqliteMemoryRepository(self.db_path)
        ok, msg = check_repo.check_integrity()
        check_repo.close()
        self.assertTrue(ok)
        self.assertEqual(msg, 'ok')
if __name__ == '__main__':
    unittest.main()
