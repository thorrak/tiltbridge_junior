import unittest
from decimal import Decimal
from datetime import datetime, timedelta
from collections import deque
from TiltHydrometer import TiltHydrometer


class TiltHydrometerTests(unittest.TestCase):
    def setUp(self):
        self.color = 'Red'
        self.tilt = TiltHydrometer(self.color)

    def test_init(self):
        self.assertEqual(self.tilt.color, self.color)
        self.assertEqual(self.tilt.smoothing_window, 60)
        self.assertIsInstance(self.tilt.gravity_list, deque)
        self.assertIsInstance(self.tilt.temp_list, deque)
        self.assertIsInstance(self.tilt.last_value_received, datetime)
        self.assertEqual(self.tilt.raw_gravity, Decimal(0.0))
        self.assertEqual(self.tilt.raw_temp, Decimal(0.0))
        self.assertEqual(self.tilt.gravity, Decimal(0.0))
        self.assertEqual(self.tilt.temp, Decimal(0.0))
        self.assertEqual(self.tilt.rssi, 0)
        self.assertFalse(self.tilt.sends_battery)
        self.assertEqual(self.tilt.weeks_on_battery, 0)
        self.assertEqual(self.tilt.firmware_version, 0)
        self.assertFalse(self.tilt.tilt_pro)
        self.assertEqual(self.tilt.temp_format, 'F')

    def test_expired(self):
        self.assertTrue(self.tilt.expired())  # Tilts should be expired when first generated

        self.tilt.last_value_received = datetime.now()
        self.assertFalse(self.tilt.expired())  # Tilts should not be expired if they have been updated recently

        self.tilt.last_value_received = datetime.now() - timedelta(hours=24)
        self.assertTrue(self.tilt.expired())  # Tilts should be expired if not updated recently

    def test_process_decoded_values_non_pro(self):
        gravity = 1242  # Not a Tilt Pro
        temp = 72  # Not a Tilt Pro
        rssi = -80
        tx_pwr = 197  # TX 197 means that battery is being sent
        self.tilt.process_decoded_values(gravity, temp, rssi, tx_pwr)
        self.assertEqual(self.tilt.raw_gravity, Decimal(gravity) / 1000)
        self.assertEqual(self.tilt.raw_temp, Decimal(temp))
        self.assertFalse(self.tilt.tilt_pro)  # Should be false because gravity is below 5000
        self.assertEqual(self.tilt.gravity, self.tilt.raw_gravity)
        self.assertEqual(self.tilt.temp, self.tilt.raw_temp)
        self.assertEqual(self.tilt.rssi, rssi)
        self.assertTrue(self.tilt.sends_battery)  # Should be true because TX power is 197

    def test_process_decoded_values_pro(self):
        gravity = 12420  # Tilt Pro
        temp = 720  # Tilt Pro
        rssi = -80
        tx_pwr = 50  # Since this is not 197 (and has never been 197) sends_battery should be false
        self.tilt.process_decoded_values(gravity, temp, rssi, tx_pwr)
        self.assertEqual(self.tilt.raw_gravity, Decimal(gravity) / 10000)
        self.assertEqual(self.tilt.raw_temp, Decimal(temp) / 10)
        self.assertTrue(self.tilt.tilt_pro)
        self.assertEqual(self.tilt.rssi, rssi)
        self.assertFalse(self.tilt.sends_battery)  # Since 197 should not have been received at amy point

    def test_smoothed_gravity(self):
        gravity_list = deque([1000, 2000, 3000])
        self.tilt.gravity_list = gravity_list
        expected_average = Decimal(sum(gravity_list)) / len(gravity_list)
        self.assertEqual(self.tilt.smoothed_gravity(), expected_average.quantize(Decimal('.001')))

    def test_smoothed_temp(self):
        temp_list = deque([65, 68, 70])
        self.tilt.temp_list = temp_list
        expected_average = Decimal(sum(temp_list)) / len(temp_list)
        self.assertEqual(self.tilt.smoothed_temp(), expected_average.quantize(Decimal('1.')))

    def test_color_lookup(self):
        # self.assertEqual(TiltHydrometer.color_lookup(self.color), 'Red')
        uuid_with_dash = 'a495bb10-c5b1-4b44-b512-1370f02d74de'
        self.assertEqual(TiltHydrometer.color_lookup(uuid_with_dash), 'Red')
        uuid_no_dash = 'a495bb10c5b14b44b5121370f02d74de'
        self.assertEqual(TiltHydrometer.color_lookup(uuid_no_dash), 'Red')
        unknown_uuid = '12345678-abcd-efgh-ijkl-abcdefghijkl'
        self.assertIsNone(TiltHydrometer.color_lookup(unknown_uuid))

    def test_print_data(self):
        # Redirect stdout to capture printed data
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            self.tilt.print_data()
        output = f.getvalue()
        expected_output = f"Red Tilt: 0.000 ({self.tilt.gravity}) / {self.tilt.temp} F\n"
        self.assertEqual(output, expected_output)

if __name__ == '__main__':
    unittest.main()
