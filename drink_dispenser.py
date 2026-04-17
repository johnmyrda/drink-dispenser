import atexit
import subprocess
from dataclasses import dataclass
from itertools import count

from gpiozero import PWMLED, Button, DigitalOutputDevice
import configparser


class DrinkButton(Button):

    def status(self):
        if self.is_pressed:
            return "_"
        else: 
            return "o"

class ButtonLight(PWMLED):

    def animate(self):
        pass

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
        self.button.when_pressed  = lambda: self.activate()
        self.button.when_released  = lambda: self.stop()

    def activate(self):
        self.light.on()
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
    lights: list[PWMLED] = []

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
            [DrinkSlot(b1, l1, m1),
             DrinkSlot(b2, l2, m2),
             DrinkSlot(b3, l3, m3)
             ]
        )
        self.buttons.extend([s.button for s in self.slots])
        self.lights.extend([s.light for s in self.slots])
        atexit.register(self.cleanup)

    def disable_pumps(self, disabled: bool) -> None:
        for slot in self.slots:
            slot.pump.disabled = disabled


    def button_status(self):
        return "BUTTONS: " + ' '.join([button.status() for button in self.buttons])

    def cleanup(self):
        for slot in self.slots:
            slot.cleanup()
        subprocess.run(
            ["./gpio-reset.sh"],
            check=True
        )
