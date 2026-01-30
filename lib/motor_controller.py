#motor_controller.py
from machine import Pin, PWM
import time
import math

class Motor:
    """단일 모터를 제어하는 클래스"""
    def __init__(self, en_pin, in1_pin, in2_pin, pwm_freq=10000):
        self.en = PWM(Pin(en_pin))
        self.en.freq(pwm_freq)
        self.in1 = Pin(in1_pin, Pin.OUT)
        self.in2 = Pin(in2_pin, Pin.OUT)
        self.stop()

    def move(self, speed):
        """Accepts either a normalized value in [-1.0, 1.0] or a raw integer magnitude up to 65535.
        - If abs(speed) <= 1.0: treat as normalized duty and scale to 0..65535
        - Else: treat as raw duty value (clamped to 65535)
        """
        if speed == 0:
            self.stop()
            return

        # Normalize or clamp
        if abs(speed) <= 1.0:
            duty = int(min(abs(speed), 1.0) * 65535)
        else:
            duty = int(min(abs(speed), 65535))

        if duty == 0:
            self.stop()
            return

        if speed > 0:
            self.in1.value(1)
            self.in2.value(0)
        else:
            self.in1.value(0)
            self.in2.value(1)

        self.en.duty_u16(duty)  # set PWM duty (0..65535)

    def stop(self):
        self.in1.value(0)
        self.in2.value(0)
        self.en.duty_u16(0)

class Encoder:
    """단일 엔코더의 펄스 수를 세는 클래스"""
    def __init__(self, pin_a, pin_b=None):
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP) if pin_b is not None else None
        self.count = 0
        self.last_tick = 0
        # Attach IRQ to channel A (rising edge). If channel B exists, its state is used to determine direction.
        self.pin_a.irq(trigger=Pin.IRQ_RISING, handler=self._pulse)

    def _pulse(self, pin):
        # 디바운싱 로직: 최소 200us 간격의 펄스만 카운트
        current_tick = time.ticks_us()
        if time.ticks_diff(current_tick, self.last_tick) > 200:
            if self.pin_b is None:
                # 단채널 엔코더: 펄스를 증가시키기만 함 (방향 정보 없음)
                self.count += 1
            else:
                # 쿼드러처(A rising, check B) 기반 방향 판별
                # 주의: 하드웨어에 따라 조건(0/1)이 반대일 수 있으니 실제 하드웨어에서 확인하세요.
                if self.pin_b.value() == 0:
                    self.count += 1
                else:
                    self.count -= 1
        self.last_tick = current_tick

    def get_count(self):
        return self.count

    def reset(self):
        self.count = 0

class OmniRobot:
    """옴니휠 로봇의 모든 제어를 총괄하는 클래스"""
    def __init__(self):
        # 로봇 사양
        self.WHEEL_DIAMETER_M = 0.06
        self.GEAR_RATIO = 30
        self.PPR = 11
        self.PULSE_PER_WHEEL_REV = self.PPR * self.GEAR_RATIO
        self.WHEEL_CIRCUMFERENCE = self.WHEEL_DIAMETER_M * math.pi
        self.WHEEL_DISTANCE_FROM_CENTER = 0.1
        self.MOTOR_ANGLES_DEG = [330, 90, 210] # 사진 속 로봇(Kiwi Drive) 기준
        
        # P 제어 게인 (권장 초기값: 10.0). 하드웨어에 따라 이 값을 낮게 시작해 점차 올리세요.
        self.kp = 10.0
        
        # 하드웨어 초기화 (M1, M2, M3 순서)
        self.motors = [Motor(2, 0, 1), Motor(8, 6, 7), Motor(12, 10, 11)]
        # 엔코더: 듀얼 채널(A/B)이 있으면 Encoder(pin_a, pin_b) 형태로 전달하세요.
        self.encoders = [Encoder(3), Encoder(9), Encoder(13)]
        
        # 상태 변수 초기화
        self.target_rpms = [0.0, 0.0, 0.0]
        self.current_rpms = [0.0, 0.0, 0.0]
        self.pwm_outputs = [0.0, 0.0, 0.0]
        self.last_update_time = time.ticks_ms()
        self.last_encoder_counts = [0, 0, 0]

    def _calculate_target_rpms(self, vx, vy, angular_velocity_radps):
        """vx, vy, omega 값을 바탕으로 각 바퀴의 목표 RPM을 계산하는 내부 함수"""
        L = self.WHEEL_DISTANCE_FROM_CENTER
        for i in range(3):
            motor_angle_rad = math.radians(self.MOTOR_ANGLES_DEG[i])
            wheel_linear_velocity = -math.sin(motor_angle_rad) * vx + math.cos(motor_angle_rad) * vy + L * angular_velocity_radps
            self.target_rpms[i] = (wheel_linear_velocity / self.WHEEL_CIRCUMFERENCE) * 60

    def holonomic(self, speed, angle_deg, angular_velocity_dps=0):
        """[방향, 속도] 기반으로 로봇의 목표 속도를 설정합니다. (C 코드의 Holonomic 함수)"""
        angle_rad = math.radians(angle_deg)
        # 로봇 좌표계 기준: Y축이 전진(90도), X축이 오른쪽(0도)
        # 사용자가 생각하는 일반 좌표계(X축이 전진)와 맞추기 위해 90도 회전 변환
        vy = speed * math.sin(angle_rad) 
        vx = speed * math.cos(angle_rad)
        angular_velocity_radps = math.radians(angular_velocity_dps)
        self._calculate_target_rpms(vx, vy, angular_velocity_radps)

    def non_holonomic(self, vx, vy, angular_velocity_dps=0):
        """[X축 속도, Y축 속도] 기반으로 로봇의 목표 속도를 설정합니다. (C 코드의 non_Holonomic 함수)"""
        angular_velocity_radps = math.radians(angular_velocity_dps)
        self._calculate_target_rpms(vx, vy, angular_velocity_radps)

    def stop(self):
        """모든 모터를 정지시킵니다."""
        for motor in self.motors:
            motor.stop()
        self.target_rpms = [0.0, 0.0, 0.0]

    def update(self):
        """매 루프마다 호출되어 목표 RPM을 유지하도록 P제어를 수행합니다."""
        current_time = time.ticks_ms()
        dt_ms = time.ticks_diff(current_time, self.last_update_time)
        if dt_ms < 10:
            return
        dt_s = dt_ms / 1000.0

        for i in range(3):
            current_count = self.encoders[i].get_count()
            pulse_diff = current_count - self.last_encoder_counts[i]
            
            revolutions = pulse_diff / self.PULSE_PER_WHEEL_REV
            # pulse_diff can be signed when using a quadrature encoder implementation
            self.current_rpms[i] = (revolutions / dt_s) * 60 if dt_s > 0 else 0
            self.last_encoder_counts[i] = current_count
            
            # 올바른 P제어 로직 (오차를 누적하지 않음)
            error = self.target_rpms[i] - self.current_rpms[i]
            self.pwm_outputs[i] = self.kp * error
            
            # PWM 출력 제한
            self.pwm_outputs[i] = max(-65535, min(65535, self.pwm_outputs[i]))
            
            self.motors[i].move(self.pwm_outputs[i])
            
        self.last_update_time = current_time
        
        # 디버깅용 출력
        print(f"\rM1 T:{self.target_rpms[0]:.1f} C:{self.current_rpms[0]:.1f} | M2 T:{self.target_rpms[1]:.1f} C:{self.current_rpms[1]:.1f} | M3 T:{self.target_rpms[2]:.1f} C:{self.current_rpms[2]:.1f}", end="")