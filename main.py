#main.py
from motor_controller import OmniRobot
import time

if __name__ == "__main__":
    robot = OmniRobot()
    UPDATE_INTERVAL_MS = 20
    
    try:
        print("MRP3Mv4 스타일 제어 테스트를 시작합니다.")
        
        # --- 1. Holonomic 함수 테스트 ---
        # 45도 대각선 방향으로 0.2 m/s 속도로 3초간 이동
        # angle_deg=0: 오른쪽, angle_deg=90: 전진, angle_deg=180: 왼쪽, angle_deg=270: 후진
        print("\nHolonomic 테스트: 90도(전진) 방향 이동")
        robot.holonomic(speed=0.5, angle_deg=90)
        
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 30000:
            robot.update()
            time.sleep_ms(UPDATE_INTERVAL_MS)
        robot.stop()
        time.sleep(1)

        # --- 2. non_Holonomic 함수 테스트 ---
        # C 코드 예제와 동일: y방향 0.2m/s, 우회전 45deg/s 속도로 3초간 이동 (곡선 운동)
        # vx: 좌우 속도 (+:오른쪽), vy: 전후 속도 (+:전진)
        print("\nnon_Holonomic 테스트: 전진하며 시계방향 회전")
        robot.non_holonomic(vx=0, vy=0.2, angular_velocity_dps=-45)

        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 30000:
            robot.update()
            time.sleep_ms(UPDATE_INTERVAL_MS)
        robot.stop()

    except KeyboardInterrupt:
        print("\n제어를 종료합니다.")
    finally:
        robot.stop()