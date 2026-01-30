# Simple machine mock for host-side testing
class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 2
    IRQ_RISING = 1

    def __init__(self, pin, mode=IN, pull=None):
        self.pin = pin
        self._mode = mode
        self._pull = pull
        self._val = 0
        self._irq = None

    def value(self, v=None):
        if v is None:
            return self._val
        self._val = v

    def irq(self, trigger=None, handler=None):
        # store handler for tests to call if needed
        self._irq = handler
        return None

class PWM:
    def __init__(self, pin):
        self.pin = pin
        self._duty = 0
        self._freq = None

    def duty_u16(self, val):
        self._duty = int(val)

    def freq(self, f):
        self._freq = f

    def __repr__(self):
        return f"PWM(duty={self._duty}, freq={self._freq})"
