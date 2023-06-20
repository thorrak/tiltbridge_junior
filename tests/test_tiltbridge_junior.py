import unittest
from unittest import mock
from aiounittest import AsyncTestCase

from tiltbridge_junior import process_ble_beacon, tilts

class TestProcessBLEBeacon(AsyncTestCase):
    async def test_process_ble_beacon_with_data(self):
        # Fixture data - This is a real packet from a Tilt Pro Hydrometer
        # Color: Yellow
        # UUID: a495bb70c5b14b44b5121370f02d74de
        # Gravity: 10345
        # Temperature: 728
        # TX Pwr: 197
        # RSSI: -65
        mock_data = b'\x04>*\x02\x01\x03\x01\xc9\xf7\xd0\xcfz\xdf\x1e\x02\x01\x04\x1a\xffL\x00\x02\x15\xa4\x95\xbbp\xc5\xb1KD\xb5\x12\x13p\xf0-t\xde\x02\xd8(i\xc5\xbf'

        tilts['Yellow'].raw_gravity = 0

        # mock the call to tilts['Yellow'].process_decoded_values as that is what we want to test was called
        # (the functionality of process_decoded_values is tested elsewhere)
        with mock.patch('tiltbridge_junior.TiltHydrometer.process_decoded_values') as mock_process_decoded_values:
            with mock.patch('tiltbridge_junior.data_target_handler.process_data') as mock_process_data:
                process_ble_beacon(mock_data)  # Call the function under test

                # Assert that process_decoded_values was called with the correct values
                mock_process_decoded_values.assert_called_with(10345, 728, -65, 197)
                mock_process_data.assert_called_once_with(tilts)


    async def test_process_ble_beacon_no_data(self):
        """Check that if no data is sent, it doesn't get processed"""
        mock_data = b''

        with mock.patch('tiltbridge_junior.TiltHydrometer.process_decoded_values') as mock_process_decoded_values:
            with mock.patch('tiltbridge_junior.data_target_handler.process_data') as mock_process_data:
                self.assertFalse(process_ble_beacon(mock_data))  # Since there was no data, this should return false
                mock_process_decoded_values.assert_not_called()  # ...and we should never get to this point
                mock_process_data.assert_not_called()


    async def test_process_ble_beacon_small_data(self):
        """Test that when a small data packet is sent, it doesn't get processed"""
        mock_data = b'1234567890'

        with mock.patch('tiltbridge_junior.TiltHydrometer.process_decoded_values') as mock_process_decoded_values:
            with mock.patch('tiltbridge_junior.data_target_handler.process_data') as mock_process_data:
                self.assertFalse(process_ble_beacon(mock_data))  # Since the data was small, this should return false
                mock_process_decoded_values.assert_not_called()  # ...and we should never get to this point
                mock_process_data.assert_not_called()


    async def test_process_ble_beacon_invalid_color(self):
        """Test that when a small data packet is sent, it doesn't get processed"""
        # Fixture data - This is a real packet from a Tilt Pro Hydrometer
        # but the UUID has been changed to a495bb71-c5b1-4b44-b512-1370f02d74de (note the last digit before the first
        # dash is different from the color Yellow's UUID, which is a495bb70-c5b1-4b44-b512-1370f02d74de)
        mock_data = b'\x04>*\x02\x01\x03\x01\xc9\xf7\xd0\xcfz\xdf\x1e\x02\x01\x04\x1a\xffL\x00\x02\x15\xa4\x95\xbbq\xc5\xb1KD\xb5\x12\x13p\xf0-t\xde\x02\xd8(i\xc5\xbf'

        with mock.patch('tiltbridge_junior.TiltHydrometer.process_decoded_values') as mock_process_decoded_values:
            with mock.patch('tiltbridge_junior.data_target_handler.process_data') as mock_process_data:
                self.assertFalse(process_ble_beacon(mock_data))  # Since the color wasn't valid, this should return false
                mock_process_decoded_values.assert_not_called()  # ...and we should never get to this point
                mock_process_data.assert_not_called()




if __name__ == "__main__":
    unittest.main()
