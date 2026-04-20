from typing import Optional

from gpiozero import PWMOutputDevice, Factory


class ButtonLight(PWMOutputDevice):
    def __init__(
        self,
        pin: int | str,
        *,
        active_high: bool = True,
        initial_value: float = 0,
        pin_factory: Optional[Factory] = None,
    ):
        super().__init__(
            pin=pin,
            active_high=active_high,
            initial_value=initial_value,
            frequency=3000,  # 2kHz or higher needed to avoid flicker
            pin_factory=pin_factory,
        )

    def animate_pulse(self, speed: int = 100):
        """
        :param speed: Speed scale - higher is slower, lower is faster.
        """
        fade_time = speed * 0.005
        self.pulse(fade_in_time=fade_time, fade_out_time=fade_time, background=True)
