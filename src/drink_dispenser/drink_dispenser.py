import atexit
import subprocess
import threading
import time
from dataclasses import dataclass
from enum import Enum
from itertools import count
from typing import Optional

from gpiozero import Button, DigitalOutputDevice, PWMOutputDevice, Factory
import configparser

DEBUG = False


class DrinkButton(Button):
    def __init__(
        self,
        pin=None,
        *,
        pull_up,
        active_state=None,
        hold_repeat=False,
        pin_factory=None,
    ):
        bounce_time = 0.02
        super().__init__(
            pin=pin,
            pull_up=pull_up,
            active_state=active_state,
            bounce_time=bounce_time,
            hold_repeat=hold_repeat,
            pin_factory=pin_factory,
        )

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


class SlotStatus(Enum):
    OFF = 0
    AUTO_DISPENSE = 1
    MANUAL_DISPENSE = 2


@dataclass
class DrinkSlot:
    button: DrinkButton
    light: ButtonLight
    pump: Pump
    status: SlotStatus = SlotStatus.OFF
    id: int = -1
    _ids = count(0)
    last_transition_time = time.time()

    def __post_init__(self):
        self.id = next(self._ids)
        if DEBUG:
            print("Slot number " + str(self.id))
            print(self)
        self.default_action()

    def default_action(self):
        self.button.when_pressed = self.button_pressed
        self.button.when_released = self.button_released
        self.button.when_held = self.manual_dispense

    def manual_dispense(self):
        self.set_state(SlotStatus.MANUAL_DISPENSE)
        threading.Thread(target=self._manual_dispense, daemon=True).start()

    def _manual_dispense(self):
        # Flash as a visual indicator of mode change
        self.light.animate_pulse(10)
        time.sleep(0.2)
        if self.button.is_active:
            # Go back to previous state
            self.light.animate_pulse()

    def auto_dispense(self, seconds: float):
        self.set_state(SlotStatus.AUTO_DISPENSE)
        threading.Thread(
            target=self._auto_dispense, args=[seconds], daemon=True
        ).start()

    def _auto_dispense(self, seconds: float):
        self.activate()
        time.sleep(seconds)
        if self.status == SlotStatus.AUTO_DISPENSE:
            self.stop()

    def button_pressed(self):
        if DEBUG:
            print("Button pressed - status: " + str(self.status))
        if self.status == SlotStatus.AUTO_DISPENSE:
            self.manual_dispense()
        if self.status == SlotStatus.OFF:
            self.auto_dispense(4.5)

    def button_released(self):
        if self.status == SlotStatus.MANUAL_DISPENSE:
            self.stop()

    def activate(self):
        self.light.animate_pulse()
        self.pump.on()
        # self.activation_start_time = time.time()

    def stop(self):
        self.light.off()
        self.pump.off()
        self.set_state(SlotStatus.OFF)

    def set_state(self, state: SlotStatus):
        now = time.time()
        transition_time = now - self.last_transition_time
        self.last_transition_time = now
        if DEBUG:
            print(f"Slot {self.id}: {self.status} -> {state} ({transition_time:.2f}s)")
        self.status = state

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
