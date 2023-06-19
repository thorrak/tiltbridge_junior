import datetime
from typing import Dict
from collections import deque
from decimal import Decimal


class TiltHydrometer:
    # These are all the UUIDs currently available as Tilt colors
    tilt_colors = {
        'Red':    "a495bb10-c5b1-4b44-b512-1370f02d74de",
        'Green':  "a495bb20-c5b1-4b44-b512-1370f02d74de",
        'Black':  "a495bb30-c5b1-4b44-b512-1370f02d74de",
        'Purple': "a495bb40-c5b1-4b44-b512-1370f02d74de",
        'Orange': "a495bb50-c5b1-4b44-b512-1370f02d74de",
        'Blue':   "a495bb60-c5b1-4b44-b512-1370f02d74de",
        'Yellow': "a495bb70-c5b1-4b44-b512-1370f02d74de",
        'Pink':   "a495bb80-c5b1-4b44-b512-1370f02d74de",
    }  # type: Dict[str, str]


    # color_lookup is created at first use in color_lookup
    color_lookup_table = {}  # type: Dict[str, str]
    color_lookup_table_no_dash = {}  # type: Dict[str, str]

    def __init__(self, color: str):
        if color not in self.tilt_colors:
            raise ValueError("Invalid color specified")

        self.color = color  # type: str

        # The smoothing_window is set in the TiltConfiguration object - just defaulting it here for now
        self.smoothing_window = 60  # type: int
        self.gravity_list = deque(maxlen=self.smoothing_window)  # type: deque[float]
        self.temp_list = deque(maxlen=self.smoothing_window)  # type: deque[int]

        self.last_value_received = datetime.datetime.now() - self._cache_expiry_seconds()  # type: datetime.datetime

        # raw_gravity and raw_temp are the values we get from the Tilt (Note - Temp is always in Fahrenheit)
        self.raw_gravity = Decimal(0.0)  # type: Decimal
        self.raw_temp = Decimal(0.0)  # type: Decimal

        # gravity and temp have calibration applied in theory
        # For now, we are not applying calibration -- it's up to the target system to do that
        self.gravity = Decimal(0.0)  # type: Decimal
        self.temp = Decimal(0.0)  # type: Decimal

        self.rssi = 0  # type: int

        # v3 and newer Tilts use the tx_pwr field to send the battery life
        self.sends_battery = False  # type: bool
        self.weeks_on_battery = 0  # type: int
        self.firmware_version = 0

        # Tilt Pros are determined when we receive a gravity reading > 5000
        self.tilt_pro = False  # type: bool

        self.temp_format = 'F'  # Defaulting to Fahrenheit as that's what the Tilt sends

    def __str__(self):
        return self.color

    def _cache_expiry_seconds(self) -> datetime.timedelta:
        # Assume we get 1 out of every 4 readings
        return datetime.timedelta(seconds=(self.smoothing_window * 1.2 * 4))

    def expired(self) -> bool:
        """Returns true if the Tilt has not checked in recently, and the cached data should be considered no longer
        valid"""
        return self.last_value_received <= datetime.datetime.now() - self._cache_expiry_seconds()

    def _add_to_list(self, gravity, temp):
        # This adds a gravity/temp value to the list for smoothing/averaging
        if self.expired():
            # The cache expired (we lost contact with the Tilt for too long). Clear the lists.
            self.gravity_list.clear()
            self.temp_list.clear()

        # Thankfully, deque enforces queue length, so all we need to do is add the value
        self.last_value_received = datetime.datetime.now()
        self.gravity_list.append(gravity)
        self.temp_list.append(temp)

    def process_decoded_values(self, sensor_gravity: int, sensor_temp: int, rssi: int, tx_pwr: int):
        if sensor_temp == 999:
            # For the latest Tilts, this is now actually a special code indicating that the gravity is the version info.
            # Regardless of whether we end up doing anything with that information, we definitely do not want to add it
            # to the list
            self.firmware_version = sensor_gravity
            return

        if sensor_gravity >= 5000:
            # Tilt Pro support
            self.tilt_pro = True
            self.raw_gravity = Decimal(sensor_gravity) / 10000
            self.raw_temp = Decimal(sensor_temp) / 10
        else:
            # Tilt "Classic" support
            self.tilt_pro = False
            self.raw_gravity = Decimal(sensor_gravity) / 1000
            self.raw_temp = Decimal(sensor_temp)

        # v3 Tilts send battery age in weeks using the tx_pwr field, but they have a hack in place to maintain
        # compatibility with iPhones where they alternate sending "197" (unsigned) or "-59" (signed) with the actual
        # number of weeks since the battery was changed. If we see the 197 (-59) then we'll set "sends_battery" to true
        # and then update the weeks_on_battery the next time we see a beacon
        if tx_pwr == 197:
            self.sends_battery = True
        elif self.sends_battery:
            self.weeks_on_battery = tx_pwr

        # For now, we aren't calibrating either gravity or temp inside this daemon. It's up to the system we are
        # communicating with (e.g. Fermentrack) to apply any necessary calibration.
        self.gravity = self.raw_gravity
        self.temp = self.raw_temp

        self.rssi = rssi
        # If we ever start applying calibration, we want to smooth the calibrated values, not the raw values
        self._add_to_list(self.gravity, self.temp)

    @staticmethod
    def _average_deque(d: deque) -> float:
        if len(d) <= 0:
            return 0.0
        return sum(d) / len(d)

    def smoothed_gravity(self) -> Decimal:
        # Return the average gravity in gravity_list
        return Decimal(self._average_deque(self.gravity_list)).quantize(Decimal('.0001' if self.tilt_pro else '.001'))

    def smoothed_temp(self) -> Decimal:
        # Return the average temp in temp_list
        return Decimal(self._average_deque(self.temp_list)).quantize(Decimal('.1' if self.tilt_pro else '1.'))

    @classmethod
    def color_lookup(cls, color):
        if len(cls.color_lookup_table) <= 0:
            cls.color_lookup_table = {cls.tilt_colors[x]: x for x in cls.tilt_colors}
        if len(cls.color_lookup_table_no_dash) <= 0:
            cls.color_lookup_table_no_dash = {cls.tilt_colors[x].replace("-", ""): x for x in cls.tilt_colors}
        # This is a static method that returns the color name for a given color UUID (either with or without a dash)
        return cls.color_lookup_table.get(color, cls.color_lookup_table_no_dash.get(color))

    def print_data(self):
        print("{} Tilt: {} ({}) / {} F".format(self.color, self.smoothed_gravity(), self.gravity, self.temp))

    def to_dict(self):
        """Return a JSON-serializable dictionary representation of the object"""
        return {
            "color": self.color,
            "raw_gravity": self.raw_gravity,
            # "gravity": self.gravity,
            "raw_temp": self.raw_temp,
            # "temp": self.temp,
            "rssi": self.rssi,
            "tilt_pro": self.tilt_pro,
            "sends_battery": self.sends_battery,
            "weeks_on_battery": self.weeks_on_battery,
            "firmware_version": self.firmware_version,
            # "gravity_list": self.gravity_list,
            # "temp_list": self.temp_list,
            "smoothed_gravity": self.smoothed_gravity(),
            "smoothed_temp": self.smoothed_temp(),
            "smoothing_window": self.smoothing_window,
        }