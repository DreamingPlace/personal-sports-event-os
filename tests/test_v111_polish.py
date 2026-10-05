"""Regression tests for validator gaps found in the review (rights, refund, launch, products)."""
import tempfile
import unittest
from sports_os.application import ApplicationService
from sports_os.application.migration import migrate_v10
from sports_os.models.demo import make_demo


class ValidatorPolishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = ApplicationService(self.temp.name)
        self.p = migrate_v10(make_demo(), self.app.registry)

    def payload(self, key):
        return self.p.states[key].payload

    def gate(self):
        return self.app.validate_project(self.p)

    def rule_ids(self, gate):
        return {f.rule_id for f in gate.findings}

    def test_baseline_is_clean(self):
        self.assertEqual(self.gate().status, 'PASS')

    def test_fixed_price_rejects_more_than_two_decimals(self):
        row = self.payload('ticketing.rights')['rows'][0]
        row.update(strategy='FIXED_PRICE', value=333.3333)
        self.assertEqual(self.gate().status, 'BLOCK')
        row['value'] = 333.33
        self.assertEqual(self.gate().status, 'PASS')

    def test_face_value_requires_value_one(self):
        row = self.payload('ticketing.rights')['rows'][0]
        row['value'] = 999
        self.assertEqual(self.gate().status, 'BLOCK')

    def test_launch_round_cannot_be_zero(self):
        rounds = self.payload('ticketing.launch')['rows'][0]['content']['rounds']
        rounds[0]['fraction'] = 0
        rounds[1]['fraction'] = 0.7
        self.assertEqual(self.gate().status, 'BLOCK')

    def test_refund_fee_decreasing_is_a_warning(self):
        windows = self.payload('ticketing.refund')['rows'][0]['content']['windows']
        windows[0]['fee_rate'], windows[2]['fee_rate'] = 1, 0
        gate = self.gate()
        self.assertEqual(gate.status, 'WARNING')
        self.assertIn('REFUND_FEE_DECREASING', self.rule_ids(gate))

    def test_refund_fee_increasing_has_no_warning(self):
        self.assertNotIn('REFUND_FEE_DECREASING', self.rule_ids(self.gate()))

    def test_pass_below_face_is_a_warning_with_amounts(self):
        for row in self.payload('product.pass')['rows']:
            if row['product_id'] == 'PASS-DEMO':
                row.update(price=1.0, price_claim='INDEPENDENT')
        gate = self.gate()
        self.assertEqual(gate.status, 'WARNING')
        finding = next(f for f in gate.findings if f.rule_id == 'PRODUCT_BELOW_FACE')
        self.assertEqual(finding.source, 'product.pass/PASS-DEMO')

    def test_pass_at_or_above_face_has_no_warning(self):
        for row in self.payload('product.pass')['rows']:
            if row['product_id'] == 'PASS-DEMO':
                row.update(price=13720, price_claim='INDEPENDENT')
        self.assertNotIn('PRODUCT_BELOW_FACE', self.rule_ids(self.gate()))


class DesktopTracebackTests(unittest.TestCase):
    def test_default_error_details_do_not_include_traceback(self):
        import os
        from unittest.mock import patch
        from sports_os.desktop.server import DesktopSession
        session = DesktopSession()
        line = '{"id":"t1","method":"health","params":{}}'
        with patch.object(session, 'dispatch', side_effect=RuntimeError('boom')), \
                patch.dict(os.environ, {}, clear=False):
            os.environ.pop('SPORTS_OS_DEBUG', None)
            r = session.handle(line)
        self.assertEqual(r['error']['details']['technical'], 'RuntimeError: boom')
        self.assertNotIn('Traceback', r['error']['details']['technical'])


if __name__ == '__main__':
    unittest.main()
