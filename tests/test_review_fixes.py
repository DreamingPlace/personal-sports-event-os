"""Regression tests for the v1.2 review fixes (one class per review item)."""
import tempfile
import unittest
from pathlib import Path

from sports_os.application import ApplicationService
from sports_os.application import schemas
from sports_os.models.demo import make_demo


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


if __name__ == '__main__':
    unittest.main()
