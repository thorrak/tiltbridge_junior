from typing import Dict

from TiltHydrometer import TiltHydrometer

from .legacy_fermentrack_target import LegacyFermentrackTarget

target_legacy_fermentrack = LegacyFermentrackTarget()


def process_data(tilts: Dict[str, TiltHydrometer]):
    # TODO - Make this asynchronous
    global target_legacy_fermentrack

    target_legacy_fermentrack.process(tilts)

def load_config():
    global target_legacy_fermentrack

    target_legacy_fermentrack.load_config()
