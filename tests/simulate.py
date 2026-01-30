# 간단한 시뮬레이터: 실제 하드웨어 없이 update() 흐름을 확인
try:
    from lib.motor_controller import OmniRobot
except Exception as e:
    print("This simulate script requires the MicroPython environment (or a machine mock).", e)
    import sys
    sys.exit(1)
import time

robot = OmniRobot()
# 가상 목표 설정
robot.holonomic(speed=0.1, angle_deg=90)
# 가상 엔코더 펄스(정상적으로 회전 중이라고 가정)
for i in range(5):
    # 시뮬레이션: 각 엔코더에 약간의 펄스 추가
    for enc in robot.encoders:
        enc.count += 5  # 임의 펄스 수
    robot.update()
    time.sleep(0.02)
print('\nSimulation complete.')
