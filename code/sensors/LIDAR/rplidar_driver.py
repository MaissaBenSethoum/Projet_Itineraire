"""
Minimal low-level driver for RPLidar A1M8.

Supported scan mode:
- normal

This version is simplified for teaching purposes:
- no express mode
- no force mode
- explicit exceptions
- safer serial handling
"""

import codecs
import logging
import struct
import sys
import time
from typing import Optional

import serial


SYNC_BYTE = b"\xA5"
SYNC_BYTE2 = b"\x5A"

GET_INFO_BYTE = b"\x50"
GET_HEALTH_BYTE = b"\x52"

STOP_BYTE = b"\x25"
RESET_BYTE = b"\x40"
SCAN_BYTE = b"\x20"

DESCRIPTOR_LEN = 7
INFO_LEN = 20
HEALTH_LEN = 3
SCAN_RESPONSE_LEN = 5

INFO_TYPE = 4
HEALTH_TYPE = 6
SCAN_TYPE = 129

MAX_MOTOR_PWM = 1023
DEFAULT_MOTOR_PWM = 660
SET_PWM_BYTE = b"\xF0"

_HEALTH_STATUSES = {
    0: "Good",
    1: "Warning",
    2: "Error",
}


class RPLidarException(Exception):
    """Basic exception class for RPLidar."""


def _b2i(byte):
    """Convert a byte to integer."""
    return byte if int(sys.version[0]) == 3 else ord(byte)


def _showhex(signal):
    """Convert bytes to hex representation for debugging."""
    return [format(_b2i(b), "#02x") for b in signal]


def _process_scan(raw):
    """
    Decode one normal scan measurement packet.

    Returns
    -------
    tuple
        (new_scan, quality, angle, distance)
    """
    new_scan = bool(_b2i(raw[0]) & 0b1)
    inversed_new_scan = bool((_b2i(raw[0]) >> 1) & 0b1)
    quality = _b2i(raw[0]) >> 2

    if new_scan == inversed_new_scan:
        raise RPLidarException("New scan flags mismatch")

    check_bit = _b2i(raw[1]) & 0b1
    if check_bit != 1:
        raise RPLidarException("Check bit not equal to 1")

    angle = ((_b2i(raw[1]) >> 1) + (_b2i(raw[2]) << 7)) / 64.0
    distance = (_b2i(raw[3]) + (_b2i(raw[4]) << 8)) / 4.0

    return new_scan, quality, angle, distance


class RPLidar:
    """Low-level class for communicating with RPLidar A1M8."""

    def __init__(self, port, baudrate=115200, timeout=2.0, logger=None):
        self._serial: Optional[serial.Serial] = None
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self._motor_speed = DEFAULT_MOTOR_PWM
        self.motor_running = False

        self.scanning = False

        if logger is None:
            logger = logging.getLogger("rplidar")
        self.logger = logger

        self.connect()

    def _require_serial(self) -> serial.Serial:
        """Return the serial object or raise if the lidar is disconnected."""
        if self._serial is None:
            raise RPLidarException("RPLidar is not connected")
        return self._serial

    # ==================================================
    # Connection / motor
    # ==================================================

    def connect(self):
        """Connect to the serial port."""
        if self._serial is not None:
            self.disconnect()

        try:
            self._serial = serial.Serial(
                self.port,
                self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )
        except serial.SerialException as err:
            raise RPLidarException(f"Failed to connect to sensor: {err}") from err

    def disconnect(self):
        """Disconnect from the serial port."""
        if self._serial is None:
            return
        self._serial.close()
        self._serial = None

    def _set_pwm(self, pwm):
        payload = struct.pack("<H", pwm)
        self._send_payload_cmd(SET_PWM_BYTE, payload)

    @property
    def motor_speed(self):
        return self._motor_speed

    @motor_speed.setter
    def motor_speed(self, pwm):
        if not (0 <= pwm <= MAX_MOTOR_PWM):
            raise ValueError(f"motor_speed must be in [0, {MAX_MOTOR_PWM}]")
        self._motor_speed = pwm
        if self.motor_running:
            self._set_pwm(self._motor_speed)

    def start_motor(self):
        """Start sensor motor."""
        serial_port = self._require_serial()
        self.logger.info("Starting motor")
        serial_port.dtr = False         # A1
        self._set_pwm(self._motor_speed)  # A2
        self.motor_running = True

    def stop_motor(self):
        """Stop sensor motor."""
        if self._serial is None:
            return

        serial_port = self._require_serial()
        self.logger.info("Stopping motor")
        self._set_pwm(0)
        time.sleep(0.001)
        serial_port.dtr = True
        self.motor_running = False

    # ==================================================
    # Serial helpers
    # ==================================================

    def _send_payload_cmd(self, cmd, payload):
        serial_port = self._require_serial()

        size = struct.pack("B", len(payload))
        req = SYNC_BYTE + cmd + size + payload

        checksum = 0
        for v in struct.unpack("B" * len(req), req):
            checksum ^= v

        req += struct.pack("B", checksum)
        serial_port.write(req)
        self.logger.debug("Command sent: %s", _showhex(req))

    def _send_cmd(self, cmd):
        serial_port = self._require_serial()
        req = SYNC_BYTE + cmd
        serial_port.write(req)
        self.logger.debug("Command sent: %s", _showhex(req))

    def _read_exactly(self, nbytes):
        """
        Read exactly nbytes, respecting serial timeout.
        """
        serial_port = self._require_serial()
        deadline = time.time() + self.timeout
        chunks = bytearray()

        while len(chunks) < nbytes:
            remaining = nbytes - len(chunks)
            data = serial_port.read(remaining)

            if data:
                chunks.extend(data)
                continue

            if time.time() > deadline:
                raise RPLidarException(
                    f"Timeout while reading {nbytes} bytes "
                    f"(got {len(chunks)} bytes)"
                )

        return bytes(chunks)

    def _read_descriptor(self):
        """
        Read descriptor packet.

        Returns
        -------
        tuple
            (data_size, is_single, data_type)
        """
        descriptor = self._read_exactly(DESCRIPTOR_LEN)
        self.logger.debug("Received descriptor: %s", _showhex(descriptor))

        if len(descriptor) != DESCRIPTOR_LEN:
            raise RPLidarException("Descriptor length mismatch")
        if not descriptor.startswith(SYNC_BYTE + SYNC_BYTE2):
            raise RPLidarException("Incorrect descriptor starting bytes")

        is_single = _b2i(descriptor[-2]) == 0
        return _b2i(descriptor[2]), is_single, _b2i(descriptor[-1])

    def _read_response(self, dsize):
        self.logger.debug("Trying to read response: %d bytes", dsize)
        data = self._read_exactly(dsize)
        self.logger.debug("Received data: %s", _showhex(data))
        return data

    def _read_measurement(self):
        """
        Lit une mesure de 5 octets en se resynchronisant sur le flux si nécessaire.
        """
        window = bytearray(self._read_exactly(SCAN_RESPONSE_LEN))

        while True:
            try:
                return _process_scan(window)
            except RPLidarException:
                self.logger.warning(
                    "Invalid measurement packet, trying to resynchronize..."
                )
                window = window[1:] + self._read_exactly(1)

    # ==================================================
    # Public device commands
    # ==================================================

    def get_info(self):
        """Get device information."""
        serial_port = self._require_serial()

        if serial_port.in_waiting > 0:
            raise RPLidarException(
                "Cannot get info while unread data remains in serial buffer. "
                "Call clean_input() first."
            )

        self._send_cmd(GET_INFO_BYTE)
        dsize, is_single, dtype = self._read_descriptor()

        if dsize != INFO_LEN:
            raise RPLidarException("Wrong get_info reply length")
        if not is_single:
            raise RPLidarException("Not a single response mode")
        if dtype != INFO_TYPE:
            raise RPLidarException("Wrong response data type")

        raw = self._read_response(dsize)
        serialnumber = codecs.encode(raw[4:], "hex").upper()
        serialnumber = codecs.decode(serialnumber, "ascii")

        return {
            "model": _b2i(raw[0]),
            "firmware": (_b2i(raw[2]), _b2i(raw[1])),
            "hardware": _b2i(raw[3]),
            "serialnumber": serialnumber,
        }

    def get_health(self):
        """Get device health state."""
        serial_port = self._require_serial()

        if serial_port.in_waiting > 0:
            raise RPLidarException(
                "Cannot get health while unread data remains in serial buffer. "
                "Call clean_input() first."
            )

        self.logger.info("Asking for health")
        self._send_cmd(GET_HEALTH_BYTE)
        dsize, is_single, dtype = self._read_descriptor()

        if dsize != HEALTH_LEN:
            raise RPLidarException("Wrong get_health reply length")
        if not is_single:
            raise RPLidarException("Not a single response mode")
        if dtype != HEALTH_TYPE:
            raise RPLidarException("Wrong response data type")

        raw = self._read_response(dsize)
        status = _HEALTH_STATUSES[_b2i(raw[0])]
        error_code = (_b2i(raw[1]) << 8) + _b2i(raw[2])

        return status, error_code

    def clean_input(self):
        """Flush serial input buffer."""
        if self._serial is None:
            return

        serial_port = self._require_serial()
        serial_port.reset_input_buffer()

    def stop(self):
        """Stop scanning."""
        if self._serial is None:
            return

        self.logger.info("Stopping scan")
        self._send_cmd(STOP_BYTE)
        time.sleep(0.1)
        self.scanning = False
        self.clean_input()

    def reset(self):
        """Reset sensor core."""
        self.logger.info("Resetting sensor")
        self._send_cmd(RESET_BYTE)
        time.sleep(2.0)
        self.scanning = False
        self.clean_input()

    def start(self):
        """Start normal scan process."""
        if self.scanning:
            return

        status, error_code = self.get_health()
        self.logger.debug("Health status: %s [%d]", status, error_code)

        if status == _HEALTH_STATUSES[2]:
            self.logger.warning(
                "Trying to reset sensor due to error. Error code: %d", error_code
            )
            self.reset()
            status, error_code = self.get_health()
            if status == _HEALTH_STATUSES[2]:
                raise RPLidarException(
                    f"RPLidar hardware failure. Error code: {error_code}"
                )
        elif status == _HEALTH_STATUSES[1]:
            self.logger.warning(
                "Warning sensor status detected! Error code: %d", error_code
            )

        self.logger.info("Starting scan process in normal mode")
        self._send_cmd(SCAN_BYTE)

        dsize, is_single, dtype = self._read_descriptor()

        if dsize != SCAN_RESPONSE_LEN:
            raise RPLidarException("Wrong scan reply length")
        if is_single:
            raise RPLidarException("Not a multiple response mode")
        if dtype != SCAN_TYPE:
            raise RPLidarException("Wrong response data type")

        self.scanning = True

    # ==================================================
    # Iterators
    # ==================================================

    def iter_measures(self, max_buf_meas=3000):
        """
        Iterate over individual measurements.

        Yields
        ------
        tuple
            (new_scan, quality, angle, distance)
        """
        if not self.motor_running:
            raise RPLidarException("Motor is not running. Call start_motor() first.")

        if not self.scanning:
            raise RPLidarException("Scan is not running. Call start() first.")

        while True:
            serial_port = self._require_serial()

            if max_buf_meas:
                data_in_buf = serial_port.in_waiting
                if data_in_buf > max_buf_meas:
                    raise RPLidarException(
                        f"Too many bytes in input buffer: {data_in_buf}/{max_buf_meas}"
                    )

            yield self._read_measurement()

    def iter_scans(self, max_buf_meas=3000, min_len=5):
        """
        Iterate over scans.

        Yields
        ------
        list
            list of (quality, angle, distance)
        """
        scan_list = []

        for new_scan, quality, angle, distance in self.iter_measures(
            max_buf_meas=max_buf_meas
        ):
            if new_scan:
                if len(scan_list) >= min_len:
                    yield scan_list
                scan_list = []

            if distance > 0:
                scan_list.append((quality, angle, distance))