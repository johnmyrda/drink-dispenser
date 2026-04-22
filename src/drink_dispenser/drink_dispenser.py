import atexit
import subprocess
import threading
import time
from dataclasses import dataclass
from enum import Enum
from itertools import count
from typing import Callable

from gpiozero import Button, DigitalOutputDevice
import configparser

from drink_dispenser.animations import Animations
from drink_dispenser.components import ButtonLight

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
    status_callback: Callable[[SlotStatus], None] | None = None
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
        if self.status_callback:
            self.status_callback(state)

    def cleanup(self):
        self.button.close()
        self.light.close()
        self.pump.close()


class DrinkDispenser:
    slots: list[DrinkSlot] = []
    buttons: list[DrinkButton] = []
    lights: list[ButtonLight] = []
    animations: Animations
    last_off_time = time.time()

    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read("config.ini")
        print(config.sections())
        b1 = DrinkButton(config["Buttons"]["B1"], pull_up=False)
        b2 = DrinkButton(config["Buttons"]["B2"], pull_up=False)
        b3 = DrinkButton(config["Buttons"]["B3"], pull_up=True)
        l1 = ButtonLight(config["LEDs"]["L1"])
        l2 = ButtonLight(config["LEDs"]["L2"])
        l3 = ButtonLight(config["LEDs"]["L3"])
        m1 = Pump(config["Motors"]["M1"])
        m2 = Pump(config["Motors"]["M2"])
        m3 = Pump(config["Motors"]["M3"])
        self.slots.extend(
            [DrinkSlot(b1, l1, m1), DrinkSlot(b2, l2, m2), DrinkSlot(b3, l3, m3)]
        )
        self.buttons.extend([s.button for s in self.slots])
        self.lights.extend([s.light for s in self.slots])
        self.animations = Animations(self.lights)
        atexit.register(self.cleanup)

    def idle_check(self, state: SlotStatus):
        if state == SlotStatus.OFF:
            self.last_off_time = time.time()

    def disable_pumps(self, disabled: bool) -> None:
        for slot in self.slots:
            slot.pump.disabled = disabled

    def button_status(self):
        return "BUTTONS: " + " ".join([button.status() for button in self.buttons])

    def cleanup(self):
        for slot in self.slots:
            slot.cleanup()
        subprocess.run(["./gpio-reset.sh"])
