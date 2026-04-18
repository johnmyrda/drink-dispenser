import atexit
import subprocess
import time
from dataclasses import dataclass
from itertools import count
from typing import Optional

from gpiozero import Button, DigitalOutputDevice, PWMOutputDevice, Factory
import configparser


class DrinkButton(Button):
    def status(self):
        if self.is_active:
            return "_"
        else:
            return "o"


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


class Pump(DigitalOutputDevice):
    disabled: bool = False

    def on(self):
        if self.disabled:
            return
        else:
            super().on()


@dataclass
class DrinkSlot:
    button: DrinkButton
    light: ButtonLight
    pump: Pump
    id: int = -1
    _ids = count(0)

    def __post_init__(self):
        self.id = next(self._ids)
        print("Slot number " + str(self.id))
        print(self)
        self.default_action()

    def default_action(self):
        self.button.when_pressed = lambda: self.activate()
        self.button.when_released = lambda: self.stop()

    def activate(self):
        # self.light.on()
        self.light.animate_pulse()
        self.pump.on()

    def stop(self):
        self.light.off()
        self.pump.off()

    def cleanup(self):
        self.button.close()
        self.light.close()
        self.pump.close()


class DrinkDispenser:
    slots: list[DrinkSlot] = []
    buttons: list[DrinkButton] = []
    lights: list[ButtonLight] = []

    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read("config.ini")
        print(config.sections())
        b1 = DrinkButton(config["Buttons"]["B1"], pull_up=False)
        b2 = DrinkButton(config["Buttons"]["B2"], pull_up=False)
        b3 = DrinkButton(config["Buttons"]["B3"], pull_up=None, active_state=True)
        l1 = ButtonLight(config["Leds"]["L1"])
        l2 = ButtonLight(config["Leds"]["L2"])
        l3 = ButtonLight(config["Leds"]["L3"])
        m1 = Pump(config["Motors"]["M1"])
        m2 = Pump(config["Motors"]["M2"])
        m3 = Pump(config["Motors"]["M3"])
        self.slots.extend(
            [DrinkSlot(b1, l1, m1), DrinkSlot(b2, l2, m2), DrinkSlot(b3, l3, m3)]
        )
        self.buttons.extend([s.button for s in self.slots])
        self.lights.extend([s.light for s in self.slots])
        atexit.register(self.cleanup)

    def disable_pumps(self, disabled: bool) -> None:
        for slot in self.slots:
            slot.pump.disabled = disabled

    def button_status(self):
        return "BUTTONS: " + " ".join([button.status() for button in self.buttons])

    def lights_on(self):
        for light in self.lights:
            light.on()

    def lights_off(self):
        for light in self.lights:
            light.off()

    def startup_lights(self):
        scaling_factor = 1
        crossover_time = 0.1
        for i in range(1, 5):
            sleep_time = 0.5 * scaling_factor
            for j, light in enumerate(self.lights):
                pulse_speed = int(100 * (sleep_time + crossover_time)) + 10
                light.animate_pulse(pulse_speed)
                time.sleep(crossover_time)
                self.lights[j - 1].off()
                time.sleep(sleep_time)
            scaling_factor = max(0.1, scaling_factor - 0.2)
            self.lights_off()
        time.sleep(0.3)
        for i in range(1, 4):
            self.lights_on()
            time.sleep(0.3)
            self.lights_off()
            time.sleep(0.1)

    def cleanup(self):
        for slot in self.slots:
            slot.cleanup()
        subprocess.run(["./gpio-reset.sh"], check=True)
