"""Regression tests for the v1.2 review fixes (one class per review item)."""
import tempfile
import unittest
from pathlib import Path

from sports_os.application import ApplicationService
from sports_os.application import schemas
from sports_os_legacy.models.demo import make_demo


class Base(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.app = ApplicationService(t.name)
        self.p = self.app.migrate_v10(make_demo())

    def edit_price(self, p=None, value=731):
        return self.app.apply_changeset(p or self.p, 'ticketing.pricing', [dict(path=['rows', 0, 'price'], value=value)])

    def approve(self, p, key):
        return self.app.approve_module(p, key, 'REVIEW-REF', p.states[key].data_version)


class ApprovalOutsidePayloadTests(Base):
    RULES = ('ticketing.refund', 'ticketing.launch', 'ticketing.identity', 'ticketing.transfer', 'ticketing.rights_return')

    def test_rows_hold_business_facts_only(self):
        for key in ('ticketing.pricing',) + self.RULES:
            for row in self.p.states[key].payload['rows']:
                self.assertFalse({'status', 'approval_ref', 'version', 'price_version'} & set(row), key)

    def test_one_price_edit_is_one_diff_fact(self):
        facts = self.app.compare_versions(self.p, self.edit_price())['business']['ticketing.pricing']
        self.assertEqual([f['path'] for f in facts], ['/S01/VIP/price'])

    def test_approval_does_not_touch_payload_or_business_diff(self):
        draft = self.edit_price()
        approved = self.approve(draft, 'ticketing.pricing')
        self.assertEqual(draft.states['ticketing.pricing'].payload, approved.states['ticketing.pricing'].payload)
        self.assertNotIn('ticketing.pricing', self.app.compare_versions(draft, approved)['business'])

    def _as_v111(self, project):
        """Rebuild the v1.1.1 on-disk shape: row lifecycle fields and old module versions."""
        old = project.states['ticketing.pricing']
        old.module_version, old.schema_version = '1.1.0', '1'
        for row in old.payload['rows']:
            row.update(price_version=old.data_version, status=old.status, approval_ref=old.approval_ref)
        for key in self.RULES:
            state = project.states[key]
            state.module_version, state.schema_version = '1.1.1', '2'
            for row in state.payload['rows']:
                row.update(version=state.data_version, status=state.status, approval_ref=state.approval_ref)
        return project

    def test_migrate_project_strips_lifecycle_fields(self):
        old = self._as_v111(self.app.migrate_v10(make_demo()))
        self.assertEqual(self.app.validate_project(old).status, 'BLOCK')
        migrated = self.app.migrate_project(old)
        self.assertEqual(migrated.states['ticketing.pricing'].payload, self.p.states['ticketing.pricing'].payload)
        for key in self.RULES:
            self.assertEqual(migrated.states[key].payload, self.p.states[key].payload)
            self.assertEqual(migrated.states[key].status, 'DRAFT')
        self.assertEqual(self.app.validate_project(migrated).status, 'PASS')

    def test_v10_unbacked_row_approval_still_blocks(self):
        from tests.cases import case_data
        p = self.app.migrate_v10(case_data('TEST-010'))
        self.assertEqual(p.states['ticketing.pricing'].approval_ref, None)
        self.assertEqual(self.app.validate_project(p).status, 'BLOCK')

    def test_published_schemas_match_code(self):
        directory = Path(__file__).resolve().parents[1] / 'data/schemas/modules'
        self.assertEqual(schemas.drift(self.app.registry, directory), [])

    def test_data_dictionary_tables_match_code(self):
        path = Path(__file__).resolve().parents[1] / 'docs/DATA_DICTIONARY.md'
        text = path.read_text(encoding='utf-8')
        self.assertEqual(schemas.dictionary_text(self.app.registry, text), text)



class CollectedFindingsTests(Base):
    def test_all_errors_in_a_module_are_reported_with_field_sources(self):
        p = self.app.apply_changeset(self.p, 'ticketing.pricing', [
            dict(path=['rows', 0, 'price'], value=10.001),
            dict(path=['rows', 1, 'session_id'], value='NOPE'),
            dict(path=['rows', 2, 'valid_from'], value='not-a-time'),
        ])
        found = {(f.rule_id, f.source) for f in self.app.validate_project(p).findings}
        self.assertLessEqual({
            ('PRICE_PRECISION', 'ticketing.pricing/rows/0/price'),
            ('PRICE_UNKNOWN_SESSION', 'ticketing.pricing/rows/1/session_id'),
            ('INVALID_TIME', 'ticketing.pricing/rows/2/valid_from'),
        }, found)

    def test_every_duplicate_key_is_reported(self):
        rows = self.app.get_module_data(self.p, 'core.venue')['rows']
        p = self.app.update_module_data(self.p, 'core.venue', dict(rows=rows + [dict(rows[0]), dict(rows[0])]))
        dupes = [f.source for f in self.app.validate_project(p).findings if f.rule_id == 'DUPLICATE_KEY']
        self.assertEqual(dupes, ['core.venue/rows/1', 'core.venue/rows/2'])

    def test_downstream_modules_wait_for_blocked_upstream(self):
        p = self.app.apply_changeset(self.p, 'core.schedule', [dict(path=['rows', 0, 'start_time'], value='bad')])
        findings = self.app.validate_project(p).findings
        self.assertIn(('INVALID_TIME', 'core.schedule/rows/0/start_time'), {(f.rule_id, f.source) for f in findings})
        waiting = {f.source: f.actual for f in findings if f.rule_id == 'DEPENDENCY_BLOCKED'}
        self.assertEqual(waiting['ticketing.pricing'], ['core.schedule'])
        self.assertIn('finance.revenue', waiting)
        self.assertFalse(any(f.rule_id in ('M_INPUT', 'M_CROSS') for f in findings))

    def test_cross_module_findings_point_at_rows(self):
        p = self.app.apply_changeset(self.p, 'ticketing.inventory', [dict(path=['rows', 0, 'quantity'], value=1)])
        finding = next(f for f in self.app.validate_project(p).findings if f.rule_id == 'INVENTORY_POOL_TOTAL')
        self.assertEqual(finding.source, 'ticketing.inventory/rows/0/quantity')



class UnifiedStorageTests(Base):
    def setUp(self):
        super().setUp()
        self.app.demo()

    def blocking_edit(self, app):
        project = app.open_project()
        return app.apply_changeset(project, 'ticketing.pricing', [dict(path=['rows', 0, 'price'], value=10.001)])

    def test_cli_and_desktop_open_the_same_working_copy(self):
        desktop = ApplicationService(self.root)
        result = desktop.persist_desktop_project(self.blocking_edit(desktop))
        self.assertEqual(result['storage'], 'DRAFT')
        cli = ApplicationService(self.root).open_project()
        self.assertEqual(cli.states['ticketing.pricing'].payload['rows'][0]['price'], 10.001)
        self.assertEqual(self.app.validate_project(cli).status, 'BLOCK')
        self.assertFalse((self.root / 'data/desktop-draft.json').exists())

    def test_stale_copy_cannot_overwrite_newer_save(self):
        from sports_os.kernel.store import ConflictError
        first, second = ApplicationService(self.root), ApplicationService(self.root)
        a, b = first.open_project(), second.open_project()
        first.save_project(self.edit_price(a, 731))
        with self.assertRaises(ConflictError):
            second.save_project(self.edit_price(b, 732))
        self.assertEqual(ApplicationService(self.root).open_project().states['ticketing.pricing'].payload['rows'][0]['price'], 731)

    def test_saved_copy_keeps_writing_after_its_own_save(self):
        app = ApplicationService(self.root)
        p = app.open_project()
        app.save_project(p := self.edit_price(p, 731))
        app.save_project(self.edit_price(p, 732))

    def test_valid_save_clears_draft_and_discard_restores_saved(self):
        app = ApplicationService(self.root)
        app.persist_desktop_project(self.blocking_edit(app))
        self.assertTrue(app.has_draft())
        restored = app.discard_draft()
        self.assertFalse(app.has_draft())
        self.assertEqual(restored.states['ticketing.pricing'].payload['rows'][0]['price'], 730)
        draft = self.blocking_edit(app)
        app.persist_desktop_project(draft)
        fixed = app.apply_changeset(draft, 'ticketing.pricing', [dict(path=['rows', 0, 'price'], value=735)])
        self.assertEqual(app.persist_desktop_project(fixed)['storage'], 'SAVED')
        self.assertFalse(app.has_draft())

    def test_legacy_draft_file_is_moved_into_the_store(self):
        from sports_os.kernel.data import digest
        app = ApplicationService(self.root)
        draft = self.blocking_edit(app)
        record = draft.to_dict()
        (self.root / 'data/desktop-draft.json').write_text(app.json_text(dict(project=record, content_hash=digest(record))))
        opened = ApplicationService(self.root).open_project()
        self.assertEqual(opened.to_dict(), record)
        self.assertFalse((self.root / 'data/desktop-draft.json').exists())
        self.assertTrue(app.has_draft())

    def test_desktop_reports_conflict_and_keeps_session(self):
        import json
        from sports_os.desktop.server import DesktopSession
        session = DesktopSession()
        call = lambda i, method, **params: session.handle(json.dumps(dict(id=str(i), method=method, params=params)))
        self.assertTrue(call(1, 'open_project', workspace=str(self.root))['ok'])
        before = session.project.to_dict()
        other = ApplicationService(self.root)
        other.save_project(self.edit_price(other.open_project(), 731))
        response = call(2, 'apply_changeset', module_id='ticketing.pricing', changes=[dict(path=['rows', 0, 'price'], value=732)])
        self.assertEqual(response['error']['code'], 'CONFLICT')
        self.assertEqual(session.project.to_dict(), before)



class CliTests(Base):
    def cli(self, *args):
        import contextlib
        import io
        from sports_os.cli import main
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main([*args, '--workspace', str(self.root)])
        return code, out.getvalue(), err.getvalue()

    def setUp(self):
        super().setUp()
        self.app.demo()
        (self.root / 'patch.json').write_text('[{"path": ["rows", 0, "price"], "value": 731}]')

    def test_exit_codes_separate_blocked_from_input_errors(self):
        self.assertEqual(self.cli('patch', 'ticketing.pricing', 'patch.json')[0], 0)
        code, _, err = self.cli('snapshot')
        self.assertEqual(code, 1)
        code, out, err = self.cli('validate', '--data', 'missing.json')
        self.assertEqual((code, out), (2, ''))
        self.assertIn('ERROR', err)

    def test_conflict_exit_code(self):
        from unittest.mock import patch
        from sports_os.kernel.store import ConflictError
        with patch.object(ApplicationService, 'save_project', side_effect=ConflictError('changed elsewhere')):
            code, _, err = self.cli('patch', 'ticketing.pricing', 'patch.json')
        self.assertEqual(code, 3)
        self.assertIn('CONFLICT', err)

    def test_status_lists_exact_approval_steps(self):
        import json
        self.cli('patch', 'ticketing.pricing', 'patch.json')
        code, out, _ = self.cli('status', '--json')
        report = json.loads(out)
        self.assertEqual(code, 0)
        pending = [m['module_id'] for m in report['modules'] if m['needs_approval']]
        self.assertEqual(pending, ['ticketing.pricing'])
        version = next(m['data_version'] for m in report['modules'] if m['module_id'] == 'ticketing.pricing')
        self.assertIn(f'approve-module ticketing.pricing --version {version}', report['next_steps'][0])
        self.assertIn('approve-project', report['next_steps'][1])
        self.assertIn('snapshot', report['next_steps'][2])
        # Following the printed steps (with a real reference) produces a snapshot.
        project_version = report['project']['version']
        self.assertEqual(self.cli('approve-module', 'ticketing.pricing', '--version', version, '--approval-ref', 'REF-M')[0], 0)
        self.assertEqual(self.cli('approve-project', '--version', project_version, '--approval-ref', 'REF-P')[0], 0)
        self.assertEqual(self.cli('snapshot')[0], 0)
        self.assertEqual(json.loads(self.cli('status', '--json')[1])['snapshots']['count'], 1)

    def test_status_while_blocked_suggests_fixing_or_discarding(self):
        import json
        app = ApplicationService(self.root)
        app.persist_desktop_project(app.apply_changeset(app.open_project(), 'ticketing.pricing', [dict(path=['rows', 0, 'price'], value=1.001)]))
        report = json.loads(self.cli('status', '--json')[1])
        self.assertTrue(report['draft'])
        self.assertIn('discard-draft', report['next_steps'][0])
        self.assertEqual(self.cli('discard-draft')[0], 0)
        self.assertFalse(json.loads(self.cli('status', '--json')[1])['draft'])

    def test_diff_working_copy_against_snapshot(self):
        import json
        snapshot = self.app.create_snapshot(self.app.open_project())['snapshot_id']
        self.cli('patch', 'ticketing.pricing', 'patch.json')
        code, out, _ = self.cli('diff', snapshot, 'WORKING')
        self.assertEqual(code, 0)
        facts = json.loads(out)['business']['ticketing.pricing']
        self.assertEqual([f['path'] for f in facts], ['/S01/VIP/price'])



class RobustnessTests(Base):
    def registry_with(self, module):
        from sports_os.kernel import Registry
        registry = Registry.discover()
        registry.register(module)
        return registry

    def test_unexpected_plugin_exception_becomes_a_finding(self):
        from sports_os.kernel import Module

        class Buggy(Module):
            module_id = 'synthetic.buggy'
            def schema(self):
                return {'type': 'object', 'properties': {}, 'additionalProperties': False}
            def validate(self, context, gate):
                return [][1]  # IndexError: previously escaped the gate and crashed the caller
            def cross_validate(self, context, gate):
                return None.missing  # AttributeError

        app = ApplicationService(self.root, self.registry_with(Buggy()))
        p = app.enable_module(self.p, 'synthetic.buggy', {})
        findings = app.validate_project(p).findings
        self.assertTrue(any(f.rule_id == 'M_INPUT' and 'IndexError' in f.actual for f in findings))

    def test_broken_plugin_does_not_hide_the_others(self):
        import sys
        root = self.root / 'plugins'
        dist = root / 'broken_extension-0.1.dist-info'
        dist.mkdir(parents=True)
        (dist / 'METADATA').write_text('Metadata-Version: 2.1\nName: broken-extension\nVersion: 0.1\n')
        (dist / 'entry_points.txt').write_text('[sports_os.modules]\nsynthetic.broken = broken_extension:Missing\n')
        (root / 'broken_extension.py').write_text('raise RuntimeError("synthetic import failure")\n')
        sys.path.insert(0, str(root))
        self.addCleanup(lambda: sys.path.remove(str(root)))
        from sports_os.kernel import Registry
        from sports_os.kernel.data import KernelError
        registry = Registry.discover()
        self.assertIn('ticketing.pricing', {m['module_id'] for m in registry.list()})
        self.assertIn('synthetic.broken', registry.load_errors)
        self.assertIn('RuntimeError', registry.load_errors['synthetic.broken'])
        with self.assertRaisesRegex(KernelError, '无法加载'):
            registry.get('synthetic.broken')

    def test_store_closes_connections(self):
        import gc
        import warnings
        self.app.demo()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', ResourceWarning)
            for _ in range(3):
                ApplicationService(self.root).open_project()
            gc.collect()
        self.assertFalse([w for w in caught if 'sqlite3.Connection' in str(w.message)])

    def test_sidecar_missing_param_is_protocol_error(self):
        import json
        from sports_os.desktop.server import DesktopSession
        session = DesktopSession()
        r = session.handle(json.dumps(dict(id='1', method='open_project', params={})))
        self.assertEqual(r['error']['code'], 'PROTOCOL')
        self.assertIn('workspace', r['error']['message'])



class StructureTests(unittest.TestCase):
    def test_core_does_not_import_legacy(self):
        import subprocess
        import sys
        code = ('import sys, sports_os.kernel, sports_os.application, sports_os.cli, sports_os.desktop.server;'
                'from sports_os.kernel import Registry; Registry.discover();'
                'print(sorted(m for m in sys.modules if m.startswith("sports_os_legacy")))')
        out = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(out, '[]')

    def test_modules_publish_display_metadata(self):
        from sports_os.kernel import Registry
        for info in Registry.discover().list():
            self.assertNotEqual(info['display_name'], info['module_id'], info['module_id'])
            self.assertNotEqual(info['category'], 'Other', info['module_id'])
            self.assertTrue(info['description'], info['module_id'])

    def test_third_party_module_without_metadata_falls_back_to_id(self):
        from sports_os.kernel import Module, Registry

        class Plain(Module):
            module_id = 'synthetic.plain'
            def schema(self):
                return {'type': 'object', 'properties': {}, 'additionalProperties': False}

        registry = Registry()
        registry.register(Plain())
        self.assertEqual(registry.list()[0]['display_name'], 'synthetic.plain')
        self.assertEqual(registry.list()[0]['category'], 'Other')


if __name__ == '__main__':
    unittest.main()
