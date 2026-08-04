import unittest
from decimal import Decimal

from execution_size_normalizer import (
    MAX_SIZE_DECIMALS,
    NormalizationStatus,
    ReasonCode,
    RoundingPolicy,
    normalize_execution_size,
)


D = Decimal


class ExecutionSizeNormalizerContractTest(unittest.TestCase):
    def test_size_already_normalized(self):
        result = normalize_execution_size(D("1.234"), 3)

        self.assertEqual(result.schema_version, "1.0")
        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(
            result.reason_code,
            ReasonCode.SIZE_ALREADY_NORMALIZED,
        )
        self.assertEqual(result.raw_size, D("1.234"))
        self.assertEqual(result.normalized_size, D("1.234"))
        self.assertEqual(result.size_decimals, 3)
        self.assertEqual(result.size_quantum, D("0.001"))
        self.assertEqual(result.adjustment, D("0"))
        self.assertEqual(
            result.rounding_policy,
            RoundingPolicy.TRUNCATE_TOWARD_ZERO,
        )
        self.assertFalse(result.was_changed)

    def test_size_is_truncated_to_precision(self):
        result = normalize_execution_size(D("1.2349"), 3)

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(
            result.reason_code,
            ReasonCode.SIZE_TRUNCATED_TO_PRECISION,
        )
        self.assertEqual(result.normalized_size, D("1.234"))
        self.assertEqual(result.size_quantum, D("0.001"))
        self.assertEqual(result.adjustment, D("0.0009"))
        self.assertTrue(result.was_changed)

    def test_zero_decimal_precision_truncates_fraction(self):
        result = normalize_execution_size(D("3.9"), 0)

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(result.normalized_size, D("3"))
        self.assertEqual(result.size_quantum, D("1"))
        self.assertEqual(result.adjustment, D("0.9"))
        self.assertTrue(result.was_changed)

    def test_integer_is_valid_at_zero_precision(self):
        result = normalize_execution_size(D("3"), 0)

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(
            result.reason_code,
            ReasonCode.SIZE_ALREADY_NORMALIZED,
        )
        self.assertEqual(result.normalized_size, D("3"))
        self.assertEqual(result.size_quantum, D("1"))
        self.assertEqual(result.adjustment, D("0"))
        self.assertFalse(result.was_changed)

    def test_value_above_quantum_is_truncated(self):
        result = normalize_execution_size(D("0.0019"), 3)

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(result.normalized_size, D("0.001"))
        self.assertEqual(result.adjustment, D("0.0009"))
        self.assertTrue(result.was_changed)

    def test_value_equal_to_quantum_is_unchanged(self):
        result = normalize_execution_size(D("0.001"), 3)

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(result.normalized_size, D("0.001"))
        self.assertEqual(result.adjustment, D("0"))
        self.assertFalse(result.was_changed)

    def test_trailing_zeroes_do_not_count_as_change(self):
        result = normalize_execution_size(D("1.23000"), 3)

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(
            result.reason_code,
            ReasonCode.SIZE_ALREADY_NORMALIZED,
        )
        self.assertEqual(result.normalized_size, D("1.230"))
        self.assertEqual(result.adjustment, D("0"))
        self.assertFalse(result.was_changed)

    def test_large_size_is_normalized_exactly(self):
        result = normalize_execution_size(
            D("123456789.987654"),
            2,
        )

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(result.normalized_size, D("123456789.98"))
        self.assertEqual(result.size_quantum, D("0.01"))
        self.assertEqual(result.adjustment, D("0.007654"))

    def test_maximum_supported_precision(self):
        self.assertEqual(MAX_SIZE_DECIMALS, 18)

        result = normalize_execution_size(
            D("0.1234567890123456789"),
            MAX_SIZE_DECIMALS,
        )

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(
            result.normalized_size,
            D("0.123456789012345678"),
        )
        self.assertEqual(
            result.size_quantum,
            D("0.000000000000000001"),
        )
        self.assertEqual(
            result.adjustment,
            D("0.0000000000000000009"),
        )

    def test_exact_quantum_at_maximum_precision(self):
        result = normalize_execution_size(
            D("0.000000000000000001"),
            18,
        )

        self.assertEqual(result.status, NormalizationStatus.NORMALIZED)
        self.assertEqual(
            result.reason_code,
            ReasonCode.SIZE_ALREADY_NORMALIZED,
        )
        self.assertEqual(
            result.normalized_size,
            D("0.000000000000000001"),
        )


class ExecutionSizeRoundedToZeroTest(unittest.TestCase):
    def test_size_below_quantum_is_rejected(self):
        result = normalize_execution_size(D("0.0009"), 3)

        self.assertEqual(
            result.status,
            NormalizationStatus.SIZE_ROUNDED_TO_ZERO,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.SIZE_BELOW_PRECISION_QUANTUM,
        )
        self.assertEqual(result.raw_size, D("0.0009"))
        self.assertIsNone(result.normalized_size)
        self.assertEqual(result.size_decimals, 3)
        self.assertEqual(result.size_quantum, D("0.001"))
        self.assertEqual(result.adjustment, D("0.0009"))
        self.assertTrue(result.was_changed)

    def test_extremely_small_size_is_rejected(self):
        result = normalize_execution_size(
            D("0.0000000000000000009"),
            18,
        )

        self.assertEqual(
            result.status,
            NormalizationStatus.SIZE_ROUNDED_TO_ZERO,
        )
        self.assertIsNone(result.normalized_size)
        self.assertEqual(
            result.size_quantum,
            D("0.000000000000000001"),
        )
        self.assertEqual(
            result.adjustment,
            D("0.0000000000000000009"),
        )


class ExecutionSizeInvalidSizeTest(unittest.TestCase):
    def assert_invalid_size(
        self,
        raw_size,
        expected_reason,
        expected_raw,
    ):
        result = normalize_execution_size(raw_size, 3)

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_SIZE,
        )
        self.assertEqual(result.reason_code, expected_reason)
        self.assertEqual(result.raw_size, expected_raw)
        self.assertIsNone(result.normalized_size)
        self.assertEqual(result.size_decimals, 3)
        self.assertEqual(result.size_quantum, D("0.001"))
        self.assertIsNone(result.adjustment)
        self.assertFalse(result.was_changed)

    def test_zero_size_is_invalid(self):
        self.assert_invalid_size(
            D("0"),
            ReasonCode.SIZE_IS_ZERO,
            D("0"),
        )

    def test_negative_size_is_invalid(self):
        result = normalize_execution_size(D("-1.25"), 2)

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_SIZE,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.SIZE_IS_NEGATIVE,
        )
        self.assertEqual(result.raw_size, D("-1.25"))
        self.assertIsNone(result.normalized_size)
        self.assertEqual(result.size_quantum, D("0.01"))

    def test_nan_size_is_invalid(self):
        self.assert_invalid_size(
            D("NaN"),
            ReasonCode.SIZE_IS_NOT_FINITE,
            None,
        )

    def test_positive_infinity_is_invalid(self):
        self.assert_invalid_size(
            D("Infinity"),
            ReasonCode.SIZE_IS_NOT_FINITE,
            None,
        )

    def test_negative_infinity_is_invalid(self):
        self.assert_invalid_size(
            D("-Infinity"),
            ReasonCode.SIZE_IS_NOT_FINITE,
            None,
        )

    def test_float_size_is_invalid(self):
        self.assert_invalid_size(
            1.234,
            ReasonCode.SIZE_TYPE_INVALID,
            None,
        )

    def test_text_size_is_invalid(self):
        self.assert_invalid_size(
            "1.234",
            ReasonCode.SIZE_TYPE_INVALID,
            None,
        )

    def test_boolean_size_is_invalid(self):
        self.assert_invalid_size(
            True,
            ReasonCode.SIZE_TYPE_INVALID,
            None,
        )


class ExecutionSizeInvalidPrecisionTest(unittest.TestCase):
    def test_negative_precision_is_invalid(self):
        result = normalize_execution_size(D("1.234"), -1)

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_PRECISION,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.PRECISION_IS_NEGATIVE,
        )
        self.assertEqual(result.raw_size, D("1.234"))
        self.assertEqual(result.size_decimals, -1)
        self.assertIsNone(result.normalized_size)
        self.assertIsNone(result.size_quantum)
        self.assertIsNone(result.adjustment)
        self.assertFalse(result.was_changed)

    def test_fractional_decimal_precision_is_invalid(self):
        result = normalize_execution_size(D("1.234"), D("2.5"))

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_PRECISION,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.PRECISION_IS_NOT_INTEGER,
        )
        self.assertIsNone(result.normalized_size)
        self.assertIsNone(result.size_quantum)

    def test_float_precision_is_invalid(self):
        result = normalize_execution_size(D("1.234"), 3.0)

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_PRECISION,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.PRECISION_TYPE_INVALID,
        )

    def test_boolean_precision_is_invalid(self):
        result = normalize_execution_size(D("1.234"), True)

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_PRECISION,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.PRECISION_TYPE_INVALID,
        )
        self.assertIsNone(result.size_decimals)
        self.assertIsNone(result.size_quantum)

    def test_missing_precision_is_invalid(self):
        result = normalize_execution_size(D("1.234"), None)

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_PRECISION,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.PRECISION_TYPE_INVALID,
        )
        self.assertIsNone(result.size_decimals)

    def test_precision_above_supported_limit_is_invalid(self):
        result = normalize_execution_size(
            D("1.234"),
            MAX_SIZE_DECIMALS + 1,
        )

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_PRECISION,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.PRECISION_OUT_OF_RANGE,
        )
        self.assertEqual(
            result.size_decimals,
            MAX_SIZE_DECIMALS + 1,
        )
        self.assertIsNone(result.normalized_size)
        self.assertIsNone(result.size_quantum)


class ExecutionSizeUnsupportedPolicyTest(unittest.TestCase):
    def test_round_to_nearest_is_not_supported(self):
        result = normalize_execution_size(
            D("1.2349"),
            3,
            RoundingPolicy.ROUND_TO_NEAREST,
        )

        self.assertEqual(
            result.status,
            NormalizationStatus.UNSUPPORTED_ROUNDING_POLICY,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.ROUNDING_POLICY_NOT_SUPPORTED,
        )
        self.assertIsNone(result.normalized_size)
        self.assertIsNone(result.size_quantum)
        self.assertIsNone(result.adjustment)
        self.assertEqual(
            result.rounding_policy,
            RoundingPolicy.ROUND_TO_NEAREST,
        )
        self.assertFalse(result.was_changed)

    def test_round_up_is_not_supported(self):
        result = normalize_execution_size(
            D("1.2341"),
            3,
            RoundingPolicy.ROUND_UP,
        )

        self.assertEqual(
            result.status,
            NormalizationStatus.UNSUPPORTED_ROUNDING_POLICY,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.ROUNDING_POLICY_NOT_SUPPORTED,
        )
        self.assertIsNone(result.normalized_size)


class ExecutionSizeValidationPrecedenceTest(unittest.TestCase):
    def test_unsupported_policy_precedes_invalid_size(self):
        result = normalize_execution_size(
            D("-1"),
            3,
            RoundingPolicy.ROUND_UP,
        )

        self.assertEqual(
            result.status,
            NormalizationStatus.UNSUPPORTED_ROUNDING_POLICY,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.ROUNDING_POLICY_NOT_SUPPORTED,
        )

    def test_invalid_precision_precedes_invalid_size(self):
        result = normalize_execution_size(D("-1"), -1)

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_PRECISION,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.PRECISION_IS_NEGATIVE,
        )

    def test_invalid_size_follows_valid_precision(self):
        result = normalize_execution_size(D("-1"), 3)

        self.assertEqual(
            result.status,
            NormalizationStatus.INVALID_SIZE,
        )
        self.assertEqual(
            result.reason_code,
            ReasonCode.SIZE_IS_NEGATIVE,
        )
        self.assertEqual(result.size_quantum, D("0.001"))


class ExecutionSizeNormalizerInvariantTest(unittest.TestCase):
    VALID_CASES = (
        (D("1.2349"), 3),
        (D("3.9"), 0),
        (D("0.0019"), 3),
        (D("100.999999"), 4),
        (D("123456789.987654"), 2),
        (D("0.1234567890123456789"), 18),
    )

    INVALID_CASES = (
        (D("0"), 3),
        (D("-1"), 3),
        (D("0.0009"), 3),
        (D("NaN"), 3),
        (D("Infinity"), 3),
        (D("1"), -1),
        (D("1"), MAX_SIZE_DECIMALS + 1),
    )

    def test_normalized_size_never_exceeds_raw_size(self):
        for raw_size, size_decimals in self.VALID_CASES:
            with self.subTest(raw_size=raw_size, size_decimals=size_decimals):
                result = normalize_execution_size(raw_size, size_decimals)

                self.assertEqual(
                    result.status,
                    NormalizationStatus.NORMALIZED,
                )
                self.assertLessEqual(result.normalized_size, raw_size)

    def test_normalized_size_is_positive(self):
        for raw_size, size_decimals in self.VALID_CASES:
            with self.subTest(raw_size=raw_size, size_decimals=size_decimals):
                result = normalize_execution_size(raw_size, size_decimals)
                self.assertGreater(result.normalized_size, D("0"))

    def test_normalized_size_is_exact_quantum_multiple(self):
        for raw_size, size_decimals in self.VALID_CASES:
            with self.subTest(raw_size=raw_size, size_decimals=size_decimals):
                result = normalize_execution_size(raw_size, size_decimals)
                units = result.normalized_size / result.size_quantum
                self.assertEqual(units, units.to_integral_value())

    def test_adjustment_is_exact_and_non_negative(self):
        for raw_size, size_decimals in self.VALID_CASES:
            with self.subTest(raw_size=raw_size, size_decimals=size_decimals):
                result = normalize_execution_size(raw_size, size_decimals)
                self.assertEqual(
                    result.adjustment,
                    raw_size - result.normalized_size,
                )
                self.assertGreaterEqual(result.adjustment, D("0"))

    def test_quantum_matches_precision(self):
        expected_quantums = {
            0: D("1"),
            1: D("0.1"),
            2: D("0.01"),
            3: D("0.001"),
            6: D("0.000001"),
            18: D("0.000000000000000001"),
        }

        for size_decimals, expected_quantum in expected_quantums.items():
            with self.subTest(size_decimals=size_decimals):
                result = normalize_execution_size(D("10"), size_decimals)
                self.assertEqual(result.size_quantum, expected_quantum)

    def test_normalization_is_idempotent(self):
        for raw_size, size_decimals in self.VALID_CASES:
            with self.subTest(raw_size=raw_size, size_decimals=size_decimals):
                first = normalize_execution_size(raw_size, size_decimals)
                second = normalize_execution_size(
                    first.normalized_size,
                    size_decimals,
                )

                self.assertEqual(
                    second.status,
                    NormalizationStatus.NORMALIZED,
                )
                self.assertEqual(
                    second.reason_code,
                    ReasonCode.SIZE_ALREADY_NORMALIZED,
                )
                self.assertEqual(
                    second.normalized_size,
                    first.normalized_size,
                )
                self.assertEqual(second.adjustment, D("0"))
                self.assertFalse(second.was_changed)

    def test_was_changed_matches_numeric_difference(self):
        cases = (
            (D("1.234"), 3, False),
            (D("1.2349"), 3, True),
            (D("3"), 0, False),
            (D("3.9"), 0, True),
        )

        for raw_size, size_decimals, expected_change in cases:
            with self.subTest(raw_size=raw_size, size_decimals=size_decimals):
                result = normalize_execution_size(raw_size, size_decimals)
                self.assertEqual(result.was_changed, expected_change)

    def test_invalid_results_never_return_executable_size(self):
        for raw_size, size_decimals in self.INVALID_CASES:
            with self.subTest(raw_size=raw_size, size_decimals=size_decimals):
                result = normalize_execution_size(raw_size, size_decimals)
                self.assertNotEqual(
                    result.status,
                    NormalizationStatus.NORMALIZED,
                )
                self.assertIsNone(result.normalized_size)

    def test_same_inputs_produce_equivalent_results(self):
        first = normalize_execution_size(D("1.2349"), 3)
        second = normalize_execution_size(D("1.2349"), 3)
        self.assertEqual(first, second)

    def test_decimal_inputs_are_not_modified(self):
        raw_size = D("1.2349")
        original_size = D("1.2349")
        size_decimals = 3

        normalize_execution_size(raw_size, size_decimals)

        self.assertEqual(raw_size, original_size)
        self.assertEqual(size_decimals, 3)


if __name__ == "__main__":
    unittest.main()
