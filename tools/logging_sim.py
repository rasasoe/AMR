"""Simulate a simple logging/tuning run and write CSV. Runs on host Python using mocks.
Usage: python3 tools/logging_sim.py --duration 5 --dt 0.02 --out logs/tuning.csv
If matplotlib is installed, a PNG plot will be produced.
"""
import csv
import argparse
import os
import importlib
import sys

# Use machine mock when running on host
if 'machine' not in sys.modules:
    try:
        import tests.machine_mock as machine
        sys.modules['machine'] = machine
    except Exception:
        pass

from lib.motor_controller import OmniRobot
import time

parser = argparse.ArgumentParser()
parser.add_argument('--duration', type=float, default=10.0, help='Duration in seconds')
parser.add_argument('--dt', type=float, default=0.02, help='Loop dt in seconds')
parser.add_argument('--out', type=str, default='logs/tuning.csv', help='CSV output file')
args = parser.parse_args()

os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
robot = OmniRobot()
robot.holonomic(speed=0.2, angle_deg=90)

# Logging header
with open(args.out, 'w', newline='') as f:
    writer = csv.writer(f)
    header = ['time_s', 'm1_target_rpm', 'm1_current_rpm', 'm2_target_rpm', 'm2_current_rpm', 'm3_target_rpm', 'm3_current_rpm']
    writer.writerow(header)

start = time.time()
now = start
while now - start < args.duration:
    # Simulate encoder pulses proportional to target rpm
    dt = args.dt
    for i in range(3):
        target_rpm = robot.target_rpms[i]
        pulses_per_sec = (target_rpm / 60.0) * robot.PULSE_PER_WHEEL_REV
        # Add pulses proportional to dt
        robot.encoders[i].count += int(pulses_per_sec * dt)

    robot.update()

    with open(args.out, 'a', newline='') as f:
        writer = csv.writer(f)
        row = [round(now - start, 3), robot.target_rpms[0], robot.current_rpms[0], robot.target_rpms[1], robot.current_rpms[1], robot.target_rpms[2], robot.current_rpms[2]]
        writer.writerow(row)

    time.sleep(dt)
    now = time.time()

print(f"Logged tuning data to {args.out}")

# Try to plot if matplotlib available
try:
    import matplotlib.pyplot as plt
    import numpy as np
    data = list(csv.reader(open(args.out)))
    columns = list(zip(*data[1:]))
    t = [float(x) for x in columns[0]]
    m1_c = [float(x) for x in columns[2]]
    m2_c = [float(x) for x in columns[4]]
    m3_c = [float(x) for x in columns[6]]
    plt.plot(t, m1_c, label='M1 current RPM')
    plt.plot(t, m2_c, label='M2 current RPM')
    plt.plot(t, m3_c, label='M3 current RPM')
    plt.xlabel('Time (s)')
    plt.ylabel('RPM')
    plt.legend()
    png = os.path.splitext(args.out)[0] + '.png'
    plt.savefig(png)
    print(f"Saved plot to {png}")
except Exception:
    print('matplotlib not available or plotting failed; CSV saved only.')
