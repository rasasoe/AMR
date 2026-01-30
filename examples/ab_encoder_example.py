# Example showing how to use A/B encoder inputs with the existing OmniRobot class
from lib.motor_controller import OmniRobot, Encoder
import time

robot = OmniRobot()
# Replace the first encoder with an A/B encoder instance (pin numbers are examples)
robot.encoders[0] = Encoder(pin_a=3, pin_b=4)
robot.encoders[1] = Encoder(pin_a=9, pin_b=10)
robot.encoders[2] = Encoder(pin_a=13, pin_b=14)

robot.holonomic(speed=0.1, angle_deg=90)
robot.last_update_time = 0
for _ in range(100):
    # Normally hardware triggers the encoder IRQs; here we simulate pulses
    for enc in robot.encoders:
        enc.count += 1
    robot.update()
    time.sleep(0.02)
