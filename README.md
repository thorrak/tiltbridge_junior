# TiltBridge Junior

TiltBridge Junior is a standalone daemon for reading data from a Tilt Hydrometer and sending it to a data target such
as [Fermentrack](http://www.fermentrack.com/). It is intended to be run on a Raspberry Pi, using the Pi's bluetooth
sensor, but likely can be run on any Linux system with a bluetooth sensor.

If you are looking for a standalone, hardware Tilt-to-WiFi bridge, check out the [TiltBridge](https://www.tiltbridge.com/) - 
my project to build a self-contained, single component, solder-free Tilt-to-WiFi bridge using an ESP-32.


### Installation with Docker



### Installation/Use outside Docker

#### Installation

TiltBridge Jr requires Python 3.8 or greater. To run it, install the dependencies in `requirements.txt`, create a .env
file containing the configuration options desired (see below), and then run `python3 -m tiltbridge_junior`.

This daemon requires either being run as root or being run in an instance of Python that has the necessary capability
flags set. To set these flags, do the following:

1. (Optional) Activate the virtualenv you wish to use TiltBridge Junior with
2. Determine the (potential symlink) location of your Python binary by running `which python3`
3. Determine the _true_ location of your python binary by running `readlink -e {path}`, replacing `{path}` with the
   path from step 2
4. Add the capability flags by running `sudo setcap 'cap_net_raw,cap_net_admin+eip' {path}`, replacing `{path}` with
   the path from step 3

Once the capability flags have been set, you can run TiltBridge Junior by running `python3 -m tiltbridge`


#### Configuration

TiltBridge Junior is configured via environment variables, which can be set using a `.env` file. A sample `.env` file is
provided as `.env.sample`. Copy/rename this file to `.env` and edit it in a text editor prior to using TiltBridge Jr.