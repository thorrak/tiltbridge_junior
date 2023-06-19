#!/usr/bin/python

import os, sys
import sentry_sdk
import time, datetime, getopt
from typing import List, Dict
import asyncio
import aioblescan as aiobs
from TiltHydrometer import TiltHydrometer
import logging

# Initialize logging
sentry_sdk.init(
    "http://ed5037d74b6e45a4b971dccccd95aace@sentry.optictheory.com:9000/11",
    traces_sample_rate=1.0 # TODO - Set this to 0.0 before release
)
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("tilt")
LOG.setLevel(logging.INFO)

# TODO - Parse some kind of configuration here
# Script Defaults
verbose = False  # Should the script print out what it's doing to the logs?
bluetooth_device = 0  # Default to /dev/hci0


def print_to_stderr(*objs):
    print("", *objs, file=sys.stderr)


#### The main loop

# Create a list of TiltHydrometer objects for us to use
tilts = {x: TiltHydrometer(x) for x in TiltHydrometer.tilt_colors}  # type: Dict[str, TiltHydrometer]

# Create the default
reload_objects_at = datetime.datetime.now() + datetime.timedelta(seconds=15)


def processBLEBeacon(data):
    # While I'm not a fan of globals, not sure how else we can store state here easily
    global verbose
    global reload_objects_at
    global tilts

    ev = aiobs.HCI_Event()
    xx = ev.decode(data)

    # To make things easier, let's convert the byte string to a hex string first
    if ev.raw_data is None:
        if verbose:
            LOG.error("Event has no raw data")
        return False

    raw_data_hex = ev.raw_data.hex()

    if len(raw_data_hex) < 80:  # Very quick filter to determine if this is a valid Tilt device
        if verbose:
            LOG.debug("Small raw_data_hex: {}".format(raw_data_hex))
        return False
    if "1370f02d74de" not in raw_data_hex:  # Another very quick filter (honestly, might not be faster than just looking at uuid below)
        if verbose:
            LOG.debug("Missing key in raw_data_hex: {}".format(raw_data_hex))
        return False

    # For testing/viewing raw announcements, uncomment the following
    # print("Raw data (hex) {}: {}".format(len(raw_data_hex), raw_data_hex))
    # ev.show(0)

    # try:
    #     mac_addr = ev.retrieve("peer")[0].val
    # except:
    #     pass

    try:
        # Let's use some of the functions of aioblesscan to tease out the mfg_specific_data payload

        manufacturer_data = ev.retrieve("Manufacturer Specific Data")
        payload = manufacturer_data[0].payload
        payload = payload[1].val.hex()

        # ...and then dissect said payload into a UUID, temp, and gravity
        uuid = payload[4:36]
        temp = int.from_bytes(bytes.fromhex(payload[36:40]), byteorder='big')
        gravity = int.from_bytes(bytes.fromhex(payload[40:44]), byteorder='big')
        # On the latest tilts, TX power is used for battery age in weeks
        tx_pwr = int.from_bytes(bytes.fromhex(payload[44:46]), byteorder='big', signed=False)
        rssi = ev.retrieve("rssi")[-1].val

    except Exception as e:
        LOG.error(e)
        sentry_sdk.capture_exception(e)
        exit(1)

    if verbose:
        LOG.info("Tilt Payload (hex): {}".format(raw_data_hex))

    color = TiltHydrometer.color_lookup(uuid)  # Map the uuid back to our TiltHydrometer object
    tilts[color].process_decoded_values(gravity, temp, rssi, tx_pwr)  # Process the data sent from the Tilt

    if verbose:
        # LOG.info("Color {} - MAC {}".format(color, mac_addr))
        LOG.info("Raw Data: `{}`".format(raw_data_hex))
        LOG.info(f"{color} - Temp: {temp}, Gravity: {gravity}, RSSI: {rssi}, TX Pwr: {tx_pwr}")

    # TODO - Process sending the data here




async def amain(args=None):
    global bluetooth_device

    event_loop = asyncio.get_running_loop()

    # First create and configure a raw socket
    try:
        mysocket = aiobs.create_bt_socket(bluetooth_device)
    except OSError as e:
        LOG.error("Unable to create socket - {}. Is there a bluetooth adapter attached in this configuration?".format(e))
        sentry_sdk.capture_exception(e)  # TODO - Remove the log to sentry here
        time.sleep(60)  # Sleep for 60 seconds, so we don't spam the logs
        exit(1)

    # create a connection with the raw socket (Uses _create_connection_transport instead of create_connection as this now
    # requires a STREAM socket) - previously was fac=event_loop.create_connection(aiobs.BLEScanRequester,sock=mysocket)
    conn, btctrl = await event_loop._create_connection_transport(mysocket, aiobs.BLEScanRequester, None, None)
    # Attach your processing
    btctrl.process = processBLEBeacon  # Attach the handler to the bluetooth control loop
    # Begin probing
    await btctrl.send_scan_request()
    try:
        while True:
            await asyncio.sleep(3600)
            # TODO - Potentially check if we haven't detected anything here and restart the loop
    except KeyboardInterrupt:
        if verbose:
                LOG.info('Keyboard interrupt')
    finally:
        if verbose:
            LOG.info('Closing event loop')
        # event_loop.run_until_complete(btctrl.stop_scan_request())
        await btctrl.stop_scan_request()
        command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
        await btctrl.send_command(command)
        conn.close()

asyncio.run(amain())
