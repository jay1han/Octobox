from periphery import GPIO

_GPIO_FLASH = 76
_GPIO_FAN   = 260
_GPIO_POWER = 259
    
class Peripheral:
    def __init__(self):
        self._flash = 0
        self._flashGpio = GPIO("/dev/gpiochip0", _GPIO_FLASH, "out")
        self._fan = 0
        self._fanGpio = GPIO("/dev/gpiochip0", _GPIO_FAN, "out")
        self._relay = 0
        self._relayGpio = GPIO("/dev/gpiochip0", _GPIO_POWER, "out")
        
    def flash(self, state = None) -> int:
        if state is not None:
            if state == -1:
                self._flash = 1 - self._flash
            else:
                self._flash = state
            self._flashGpio.write(bool(self._flash))
        return self._flash
    
    def fan(self, state = None) -> int:
        if state is not None:
            if state == -1:
                self._fan = 1 - self._fan
            else:
                self._fan = state
            self._fanGpio.write(bool(self._fan))
        return self._fan

    def relay(self, state = None) -> int:
        if state is not None:
            if state == -1:
                self._relay = 1 - self._relay
            else:
                self._relay = state
            self._relayGpio.write(bool(self._relay))
        return self._relay

    def __del__(self):
        self.flash(0)
        self.fan(0)
        self.relay(0)
