import unittest
from unittest.mock import patch
from decimal import Decimal

from account_snapshot import get_account_snapshot
from margin_admission import AccountNormalizationStatus


TEST_ADDRESS = "0x1111111111111111111111111111111111111111"


class AccountSnapshotTest(unittest.TestCase):

    def valid_state(self):
        return {
            "time": 1785844800000,
            "marginSummary": {
                "accountValue": "100.5",
                "totalMarginUsed": "10.25",
            },
            "withdrawable": "90.25",
            "assetPositions": [],
        }

    @patch("account_snapshot._get_account_address")
    @patch("account_snapshot._get_account_state")
    def test_valid_snapshot(self, mock_state, mock_address):
        mock_address.return_value = TEST_ADDRESS
        mock_state.return_value = self.valid_state()

        snapshot = get_account_snapshot()

        self.assertEqual(
            snapshot.normalization_status,
            AccountNormalizationStatus.VALID,
        )

        self.assertEqual(
            snapshot.account_value,
            Decimal("100.5"),
        )

        self.assertEqual(
            snapshot.total_margin_used,
            Decimal("10.25"),
        )

        self.assertEqual(
            snapshot.withdrawable,
            Decimal("90.25"),
        )

        self.assertEqual(
            snapshot.account_address,
            TEST_ADDRESS,
        )


    @patch("account_snapshot._get_account_address")
    @patch("account_snapshot._get_account_state")
    def test_missing_margin_summary_invalid(self, mock_state, mock_address):
        mock_address.return_value = TEST_ADDRESS
        mock_state.return_value = {
            "time": 1785844800000,
            "withdrawable": "90",
            "assetPositions": [],
        }

        snapshot = get_account_snapshot()

        self.assertEqual(
            snapshot.normalization_status,
            AccountNormalizationStatus.INVALID,
        )

        self.assertIn(
            "MARGIN_SUMMARY_MISSING",
            snapshot.normalization_errors,
        )


    @patch("account_snapshot._get_account_address")
    @patch("account_snapshot._get_account_state")
    def test_missing_withdrawable_invalid(self, mock_state, mock_address):
        mock_address.return_value = TEST_ADDRESS
        mock_state.return_value = {
            "time": 1785844800000,
            "marginSummary": {
                "accountValue": "100",
                "totalMarginUsed": "0",
            },
            "assetPositions": [],
        }

        snapshot = get_account_snapshot()

        self.assertEqual(
            snapshot.normalization_status,
            AccountNormalizationStatus.INVALID,
        )

        self.assertIn(
            "WITHDRAWABLE_MISSING",
            snapshot.normalization_errors,
        )


    @patch("account_snapshot._get_account_address")
    @patch("account_snapshot._get_account_state")
    def test_invalid_account_state(self, mock_state, mock_address):
        mock_address.return_value = TEST_ADDRESS
        mock_state.return_value = None

        snapshot = get_account_snapshot()

        self.assertEqual(
            snapshot.normalization_status,
            AccountNormalizationStatus.INVALID,
        )


    @patch("account_snapshot._get_account_address")
    @patch("account_snapshot._get_account_state")
    def test_negative_values_invalid(self, mock_state, mock_address):
        mock_address.return_value = TEST_ADDRESS

        mock_state.return_value = {
            "time": 1785844800000,
            "marginSummary": {
                "accountValue": "-1",
                "totalMarginUsed": "0",
            },
            "withdrawable": "10",
            "assetPositions": [],
        }

        snapshot = get_account_snapshot()

        self.assertEqual(
            snapshot.normalization_status,
            AccountNormalizationStatus.INVALID,
        )

        self.assertIn(
            "ACCOUNT_VALUE_INVALID",
            snapshot.normalization_errors,
        )


if __name__ == "__main__":
    unittest.main()
