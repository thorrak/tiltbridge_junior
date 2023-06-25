import datetime
import logging
import os
from typing import Dict

import sentry_sdk

from TiltHydrometer import TiltHydrometer
import requests


LOG = logging.getLogger("tilt")


class LegacyFermentrackTarget:

    FERMENTRACK_SEND_FREQUENCY = datetime.timedelta(seconds=3)

    def __init__(self):
        self.enabled = False  # type: bool
        self.target_url = None  # type: str or None
        self.data_last_sent = datetime.datetime.now()  # type: datetime.datetime

    def load_config(self):
        """Load the config file (called as part of the main setup process)"""
        enabled_env = os.environ.get("FERMENTRACK_LEGACY_TARGET_ENABLED", None)
        self.enabled = enabled_env.lower() == 'true' if enabled_env else False
        self.target_url = os.environ.get("FERMENTRACK_LEGACY_TARGET_URL", None)

        if not self.enabled:
            LOG.info("Logging to Legacy Fermentrack Target is disabled")
        else:
            if self.enabled and (self.target_url is None or len(self.target_url) <= 11):
                LOG.error("Logging to Legacy Fermentrack Target is enabled, but target URL is invalid")
            else:
                LOG.info(f"Logging to Legacy Fermentrack Target is enabled, with target URL {self.target_url}")

    @staticmethod
    def convert_tilts_to_list(tilts: Dict[str, TiltHydrometer]) -> list[dict]:
            """Loop through a list of TiltHydrometer objects and convert them to something serializable"""
            tilt_list = []
            for color, tilt in tilts.items():
                if not tilt.expired():
                    tilt_list.append(tilt.to_dict())
            return tilt_list

    def process(self, tilts: Dict[str, TiltHydrometer]):
        """This function is called by the main loop every time a new Tilt message is received to determine if we need
        to send a new message to Fermentrack - and if we do, to send that message. Data will be sent as a JSON object
        representing the dict returned by convert_tilts_to_dict(tilts) to a Fermentrack HTTP endpoint using requests
        every FERMENTRACK_SEND_FREQUENCY (timedelta)."""
        if not self.enabled:
            return

        if self.target_url is None or len(self.target_url) <= 11:
            return
        elif datetime.datetime.now() - self.data_last_sent > self.FERMENTRACK_SEND_FREQUENCY:
            target_dict = {
                'tilts': self.convert_tilts_to_list(tilts),
                'tiltbridge_junior': True,
            }

            try:
                r=requests.post(self.target_url, json=target_dict, timeout=5)
            except Exception as e:
                LOG.error(e)
                # sentry_sdk.capture_exception(e)
                self.data_last_sent = datetime.datetime.now()  # Prevent hammering the endpoint
                return

            if r.status_code != 200:
                LOG.error(f"Error sending data to Fermentrack: {r.text}")
            else:
                LOG.info("Sent {} Tilt(s) to Fermentrack".format(len(target_dict['tilts'])))
            self.data_last_sent = datetime.datetime.now()
