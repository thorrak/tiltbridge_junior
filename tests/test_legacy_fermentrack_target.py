import unittest
from datetime import datetime, timedelta
from unittest import mock

from TiltHydrometer import TiltHydrometer
from data_targets.legacy_fermentrack_target import LegacyFermentrackTarget


class LegacyFermentrackTargetTests(unittest.TestCase):
    def setUp(self):
        self.target = LegacyFermentrackTarget()
        self.target.enabled = True
        self.target.target_url = "https://example.com"

    def test_convert_tilts_to_dict(self):
        tilts = {
            'Red': TiltHydrometer('Red'),
            'Green': TiltHydrometer('Green')
        }
        tilts['Red'].process_decoded_values(4000, 72, -80, 197)
        tilts['Green'].process_decoded_values(5000, 68, -85, 190)

        expected_list = [
            tilts['Red'].to_dict(),
            tilts['Green'].to_dict()
        ]

        converted_dict = self.target.convert_tilts_to_list(tilts)
        self.assertEqual(converted_dict, expected_list)

    @mock.patch('data_targets.legacy_fermentrack_target.requests')
    def test_process_data_last_sent_updates_when_sent(self, mock_requests):
        tilts = {
            'Red': TiltHydrometer('Red'),
            'Green': TiltHydrometer('Green')
        }

        # Set the data_last_sent value to oustide the FERMENTRACK_SEND_FREQUENCY window and cache it
        self.target.data_last_sent = datetime.now() - self.target.FERMENTRACK_SEND_FREQUENCY - timedelta(seconds=1)
        old_last_sent = self.target.data_last_sent

        self.target.process(tilts)
        self.assertGreater(self.target.data_last_sent, old_last_sent)
        mock_requests.post.assert_called_once()


    @mock.patch('data_targets.legacy_fermentrack_target.requests')
    def test_process_data_last_sent_doesnt_update_when_not_sent(self, mock_requests):
        """Test that the data_last_sent value doesn't update when we don't send data (because we're not due to send
        data)"""
        tilts = {
            'Red': TiltHydrometer('Red'),
            'Green': TiltHydrometer('Green')
        }

        # Cache the data_last_sent value and make sure we have time to process the test
        self.target.data_last_sent = datetime.now()
        old_last_sent = self.target.data_last_sent
        self.assertGreater(self.target.FERMENTRACK_SEND_FREQUENCY, timedelta(seconds=2))  # The test won't work if we don't have time to process

        self.target.process(tilts)

        # Requests.post shouldn't be called & the data_last_sent shouldn't change since we're inside the window
        self.assertEqual(self.target.data_last_sent, old_last_sent)
        mock_requests.post.assert_not_called()


    @mock.patch('data_targets.legacy_fermentrack_target.requests')
    def test_process_data_doesnt_send_when_no_url(self, mock_requests):
        tilts = {
            'Red': TiltHydrometer('Red'),
            'Green': TiltHydrometer('Green')
        }

        # Set the data_last_sent value to oustide the FERMENTRACK_SEND_FREQUENCY window and cache it
        self.target.target_url = None
        self.target.data_last_sent = datetime.now() - self.target.FERMENTRACK_SEND_FREQUENCY - timedelta(seconds=1)
        old_last_sent = self.target.data_last_sent

        self.target.process(tilts)

        self.assertEqual(self.target.data_last_sent, old_last_sent)
        mock_requests.post.assert_not_called()


    @mock.patch('data_targets.legacy_fermentrack_target.requests')
    def test_process_data_doesnt_send_when_not_enabled(self, mock_requests):
        tilts = {
            'Red': TiltHydrometer('Red'),
            'Green': TiltHydrometer('Green')
        }

        # Set the data_last_sent value to oustide the FERMENTRACK_SEND_FREQUENCY window and cache it
        self.target.enabled = False
        self.target.data_last_sent = datetime.now() - self.target.FERMENTRACK_SEND_FREQUENCY - timedelta(seconds=1)
        old_last_sent = self.target.data_last_sent

        self.target.process(tilts)

        self.assertEqual(self.target.data_last_sent, old_last_sent)
        mock_requests.post.assert_not_called()


    @mock.patch('data_targets.legacy_fermentrack_target.requests')
    def test_process_send_data(self, mock_requests):
        tilts = {
            'Red': TiltHydrometer('Red'),
            'Green': TiltHydrometer('Green')
        }
        tilts['Red'].process_decoded_values(4000, 72, -80, 197)
        tilts['Green'].process_decoded_values(5000, 68, -85, 190)

        # In order to ensure that the data is sent, we need to set the last sent time to be longer than the send frequency
        self.target.data_last_sent = datetime.now() - self.target.FERMENTRACK_SEND_FREQUENCY - timedelta(seconds=1)
        self.target.process(tilts)

        expected_tilt_dict = {'tilts': self.target.convert_tilts_to_list(tilts), 'tiltbridge_junior': True,}
        mock_requests.post.assert_called_once_with(self.target.target_url, json=expected_tilt_dict, timeout=5)


if __name__ == '__main__':
    unittest.main()
