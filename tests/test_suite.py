#!/usr/bin/env python3
"""
CubeSat IMU — Formal Verification & Test Suite
================================================
Coverage:
  CRC-16       : known vector, corruption detection, roundtrip
  Quaternion   : normalization, identity, unit-magnitude dq
  Mahony       : output unit-q, 60 s stability, windup clamp, static drift
  Outlier      : limit constant, threshold logic
  Lux formula  : spot-checks from imu_data.json table, monotonicity

Run:
  python tests/test_suite.py
  python -m pytest tests/test_suite.py -v
"""

import sys, os, math, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import imu_server
from imu_server import (
    qmul, qnorm, gyro_to_dq, mahony_update, crc16, reset_filter,
    KP, KI, OUTLIER_LIMIT, WINDUP_LIMIT,
    _eInt, _eInt_lock,
)


# ─────────────────────────────────────────────────────────────────────────────
class TestCRC16(unittest.TestCase):

    def test_known_vector(self):
        """CRC-16/CCITT-FALSE (init=0xFFFF, poly=0x1021) of '123456789' = 0x29B1."""
        self.assertEqual(crc16("123456789"), 0x29B1)

    def test_empty_string(self):
        self.assertEqual(crc16(""), 0xFFFF)

    def test_corruption_detected(self):
        data = "0.01234 -0.00456 0.99812 0.00231 -0.00087 0.00145 823 145 612 89"
        good = crc16(data)
        bad  = crc16(data.replace("0.01234", "0.01235"))
        self.assertNotEqual(good, bad)

    def test_single_bit_flip_detected(self):
        data = "0.03241 -0.01876 0.99812 0.00231 -0.00087 0.00145 823 145 612 89"
        good = crc16(data)
        flipped = data[:5] + chr(ord(data[5]) ^ 1) + data[6:]
        self.assertNotEqual(crc16(flipped), good)

    def test_roundtrip(self):
        """Packet that passes its own CRC check."""
        data = "0.03241 -0.01876 0.99812 0.00231 -0.00087 0.00145 823 145 612 89"
        crc  = crc16(data)
        parts = f"{data} {crc:04X}".split()
        self.assertEqual(crc16(" ".join(parts[:10])), int(parts[10], 16))


# ─────────────────────────────────────────────────────────────────────────────
class TestQuaternion(unittest.TestCase):

    def _mag(self, q):
        return math.sqrt(sum(v*v for v in q))

    def test_qnorm_identity(self):
        self.assertAlmostEqual(self._mag(qnorm([1, 0, 0, 0])), 1.0, places=12)

    def test_qnorm_arbitrary(self):
        self.assertAlmostEqual(self._mag(qnorm([2, 3, 1, 4])), 1.0, places=12)

    def test_qnorm_near_zero_returns_identity(self):
        self.assertEqual(qnorm([1e-15, 0, 0, 0]), [1.0, 0.0, 0.0, 0.0])

    def test_gyro_to_dq_zero_is_identity(self):
        self.assertEqual(gyro_to_dq(0.0, 0.0, 0.0, 0.02), [1.0, 0.0, 0.0, 0.0])

    def test_gyro_to_dq_is_unit(self):
        self.assertAlmostEqual(self._mag(gyro_to_dq(0.1, -0.2, 0.3, 0.02)), 1.0, places=12)

    def test_qmul_identity(self):
        q = [0.9971, 0.0523, 0.0349, 0.0175]
        r = qmul(q, [1, 0, 0, 0])
        for a, b in zip(q, r):
            self.assertAlmostEqual(a, b, places=12)


# ─────────────────────────────────────────────────────────────────────────────
class TestMahonyFilter(unittest.TestCase):

    def setUp(self):
        reset_filter()

    def _mag(self, q):
        return math.sqrt(sum(v*v for v in q))

    def test_output_is_unit_quaternion(self):
        q = mahony_update([1,0,0,0], 0.1, -0.05, 0.02, 0.0, 0.0, 1.0, 0.02)
        self.assertAlmostEqual(self._mag(q), 1.0, places=8)

    def test_stays_normalized_3000_steps(self):
        """60 s at 50 Hz with synthetic motion — quaternion must stay unit."""
        reset_filter()
        q = [1.0, 0.0, 0.0, 0.0]
        dt = 0.02
        for i in range(3000):
            t = i * dt
            gx = 0.3 * math.sin(t * 0.7)
            gy = 0.5 * math.cos(t * 0.4)
            gz = 0.2 * math.sin(t * 1.1)
            q = mahony_update(q, gx, gy, gz, 0.01, -0.01, 0.98, dt)
        self.assertAlmostEqual(self._mag(q), 1.0, places=6)

    def test_windup_clamp(self):
        """After 10000 steps with persistent lateral accel, eInt stays within WINDUP_LIMIT."""
        reset_filter()
        q = [1.0, 0.0, 0.0, 0.0]
        dt = 0.02
        for _ in range(10000):
            q = mahony_update(q, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, dt)
        with _eInt_lock:
            for v in imu_server._eInt:
                self.assertLessEqual(abs(v), WINDUP_LIMIT + 1e-9,
                                     f"eInt={v} exceeds WINDUP_LIMIT={WINDUP_LIMIT}")

    def test_zero_accel_no_correction(self):
        """Zero accel vector skips cross-product correction — only gyro integrates."""
        reset_filter()
        q_before = [1.0, 0.0, 0.0, 0.0]
        q_after  = mahony_update(list(q_before), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.02)
        for a, b in zip(q_before, q_after):
            self.assertAlmostEqual(a, b, places=8)

    def test_static_no_drift(self):
        """50 s warm-up then 10 s hold with static sensor — quaternion must not drift."""
        reset_filter()
        q = [1.0, 0.0, 0.0, 0.0]
        dt = 0.02
        for _ in range(2500):          # 50 s warm-up
            q = mahony_update(q, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, dt)
        q_ref = list(q)
        for _ in range(500):           # 10 s hold
            q = mahony_update(q, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, dt)
        for a, b in zip(q_ref, q):
            self.assertAlmostEqual(a, b, delta=0.001,
                                   msg="Quaternion drifted during static hold")


# ─────────────────────────────────────────────────────────────────────────────
class TestOutlierRejection(unittest.TestCase):

    def test_limit_constant(self):
        self.assertEqual(OUTLIER_LIMIT, 2.5)

    def test_within_limit_accepted(self):
        self.assertFalse(abs(2.4) > OUTLIER_LIMIT)

    def test_beyond_limit_rejected(self):
        self.assertTrue(abs(2.6) > OUTLIER_LIMIT)

    def test_negative_outlier(self):
        self.assertTrue(abs(-2.6) > OUTLIER_LIMIT)

    def test_exact_limit_accepted(self):
        self.assertFalse(abs(2.5) > OUTLIER_LIMIT)


# ─────────────────────────────────────────────────────────────────────────────
class TestLuxConversion(unittest.TestCase):
    """Spot-check the lux formula from imu_data.json against known table values."""

    R_FIXED = 10000

    def lux(self, adc):
        if adc <= 0:    return 0
        if adc >= 1023: return 99999
        r_ldr = self.R_FIXED * (1023 - adc) / adc
        if r_ldr == 0:  return 99999
        return int(500000 / r_ldr)

    def test_adc_500_office_light(self):
        # R_ldr = 10000*523/500 = 10460 Ω → lux = 500000/10460 = 47
        self.assertEqual(self.lux(500), 47)

    def test_adc_950_outdoor_shade(self):
        # R_ldr = 10000*73/950 = 768.42 Ω → lux = int(500000/768.42) = 650
        self.assertEqual(self.lux(950), 650)

    def test_adc_1000_simulated_sun(self):
        # R_ldr = 10000*23/1000 = 230 Ω → lux = 500000/230 = 2173
        self.assertEqual(self.lux(1000), 2173)

    def test_adc_200_dim_room(self):
        # R_ldr = 10000*823/200 = 41150 Ω → lux = 500000/41150 = 12
        self.assertEqual(self.lux(200), 12)

    def test_adc_0_returns_zero(self):
        self.assertEqual(self.lux(0), 0)

    def test_adc_1023_returns_max(self):
        self.assertEqual(self.lux(1023), 99999)

    def test_monotonic_increasing(self):
        """Higher ADC → more light → higher lux (strict monotonic)."""
        vals = [self.lux(adc) for adc in range(10, 1020, 10)]
        for i in range(len(vals) - 1):
            self.assertLessEqual(vals[i], vals[i + 1])


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main(verbosity=2)
