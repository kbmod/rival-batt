import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import rival_batt as app


class Device:
    def __init__(self, response):
        self.response = response
        self.closed = False
        self.writes = []
    def open_path(self, path):
        self.path = path
    def write(self, data):
        self.writes.append(data)
        return 65
    def read(self, length, timeout):
        return self.response
    def close(self):
        self.closed = True


class HID:
    def __init__(self, response, connected=True):
        self.handle = Device(response)
        self.connected = connected
    def enumerate(self, vid, pid):
        assert (vid, pid) == (0x1038, 0x1830)
        return ([{"interface_number": 0, "path": b"mouse"},
                 {"interface_number": 3, "path": b"battery"}] if self.connected else [])
    def device(self):
        return self.handle


class BatteryTests(unittest.TestCase):
    def test_second_instance_is_rejected_and_lock_releases(self):
        with tempfile.TemporaryDirectory() as directory, patch("rival_batt.state_dir", return_value=Path(directory)):
            with app.InstanceLock():
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    with app.InstanceLock():
                        self.fail("Second instance acquired lock")
            with app.InstanceLock():
                pass

    def test_valid_levels_including_empty_battery(self):
        for value in [0, 1, 30, 99, 100]:
            self.assertEqual(app.decode_response([value, 0, 0] + [0] * 61), value)

    def test_bad_responses(self):
        for response in [[], [30], [30, 0], [101, 0, 0], [255, 0, 0]]:
            with self.assertRaises(ValueError):
                app.decode_response(response)

    @patch("rival_batt.time.sleep")
    def test_query_uses_only_battery_command_and_correct_interface(self, sleep):
        hid = HID([30, 0, 0])
        reading = app.poll(hid)
        self.assertEqual(reading.level, 30)
        self.assertEqual(hid.handle.path, b"battery")
        self.assertEqual(hid.handle.writes, [bytes([0, 0xaa, 1])])
        self.assertTrue(hid.handle.closed)

    @patch("rival_batt.time.sleep")
    def test_timeout_closes_device_and_does_not_claim_zero(self, sleep):
        hid = HID([])
        self.assertIsNone(app.poll(hid).level)
        self.assertTrue(hid.handle.closed)

    def test_no_receiver(self):
        self.assertIsNone(app.poll(HID([], connected=False)).level)

    @patch("rival_batt.time.sleep")
    def test_access_denied_is_reported(self, sleep):
        hid = HID([])
        hid.handle.open_path = lambda _: (_ for _ in ()).throw(OSError("Permission denied"))
        self.assertIn("Permission denied", app.poll(hid).status)
        self.assertTrue(hid.handle.closed)


if __name__ == "__main__":
    unittest.main()
