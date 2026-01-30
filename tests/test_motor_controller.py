import sys
import types
import importlib
import unittest

# Inject a simple 'machine' module mock before importing target module
mock_machine = types.ModuleType('machine')
from tests.machine_mock import Pin, PWM
mock_machine.Pin = Pin
mock_machine.PWM = PWM
sys.modules['machine'] = mock_machine

# Import the module under test
mc = importlib.import_module('lib.motor_controller')

# Provide a simple time mock so update() sees enough dt
class FakeTime:
    def __init__(self):
        self._ms = 0
        self._us = 0
    def ticks_ms(self):
        self._ms += 20
        return self._ms
    def ticks_us(self):
        self._us += 20000
        return self._us
    def ticks_diff(self, a, b):
        return a - b
    def sleep_ms(self, ms):
        pass

fake_time = FakeTime()
mc.time = fake_time

class TestMotorController(unittest.TestCase):
    def test_motor_move_normalized(self):
        m = mc.Motor(2, 0, 1)
        # Normalized positive
        m.move(0.5)
        self.assertTrue(m.en._duty > 0)
        # Normalized negative
        m.move(-0.25)
        self.assertTrue(m.en._duty > 0)
        # Zero
        m.move(0)
        self.assertEqual(m.en._duty, 0)

    def test_encoder_direction(self):
        enc = mc.Encoder(3, pin_b=4)
        # Simulate B = 0 (forward)
        enc.pin_b.value(0)
        enc._pulse(None)
        self.assertEqual(enc.get_count(), 1)
        # Simulate B = 1 (reverse)
        enc.pin_b.value(1)
        enc._pulse(None)
        self.assertEqual(enc.get_count(), 0)

    def test_update_changes_rpm_and_pwm_outputs(self):
        robot = mc.OmniRobot()
        # Replace encoders with mocks so we can adjust counts directly
        for i in range(3):
            robot.encoders[i] = mc.Encoder(i+3)  # single-channel
        # Set a target and simulate pulses
        robot.holonomic(speed=0.1, angle_deg=90)
        # initial last_update_time small so update runs
        robot.last_update_time = 0
        # Simulate some pulses each loop
        for _ in range(5):
            for enc in robot.encoders:
                enc.count += 5
            robot.update()
        # After some updates, at least one motor must have a non-zero pwm output
        self.assertTrue(any(abs(p) > 0 for p in robot.pwm_outputs))

if __name__ == '__main__':
    unittest.main()
