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


if __name__ == '__main__':
    unittest.main()
