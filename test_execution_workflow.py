import unittest
from unittest.mock import patch, MagicMock

import execution_workflow


class ExecutionWorkflowTest(unittest.TestCase):

    @patch("execution_workflow.can_execute_live")
    @patch("execution_workflow.get_info")
    def test_successful_execution_with_protection(
        self,
        mock_info,
        mock_live,
    ):
        mock_live.return_value = True

        mock_info.return_value.meta.return_value = {
            "universe": [
                {
                    "name": "BTC",
                    "szDecimals": 3,
                }
            ]
        }

        exchange = MagicMock()

        exchange.market_open.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [
                        {
                            "filled": {
                                "oid": 12345,
                                "avgPx": "60000",
                            }
                        }
                    ]
                }
            }
        }

        exchange.order.return_value = {
            "response": {
                "data": {
                    "statuses": [
                        {
                            "resting": {
                                "oid": 555
                            }
                        }
                    ]
                }
            }
        }

        with patch(
            "execution_workflow.exchange",
            exchange,
        ):

            result = execution_workflow.execute(
                asset="BTC",
                direction="LONG",
                position_size=0.01,
            )

        self.assertTrue(result.success)
        self.assertTrue(result.position_open)

        self.assertEqual(
            result.exchange_order_id,
            "12345",
        )

        self.assertIsNotNone(
            result.stop_loss_order_id
        )

        self.assertIsNotNone(
            result.take_profit_order_id
        )


if __name__ == "__main__":
    unittest.main()
