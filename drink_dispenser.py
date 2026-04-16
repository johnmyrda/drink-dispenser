import subprocess

from gpiozero import LED, PWMLED, Button
import configparser


class DrinkButton(Button):

    def status(self):
        if self.is_pressed:
            return "_"
        else: 
            return "o"

class DrinkDispenser:

    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read("config.ini")
        print(config.sections())
        self.b1 = DrinkButton(config["Buttons"]["B1"], pull_up=False)
        self.b2 = DrinkButton(config["Buttons"]["B2"], pull_up=False)
        self.b3 = DrinkButton(config["Buttons"]["B3"], pull_up=None, active_state=True)
        self.l1 = PWMLED(config["Leds"]["L1"])
        self.l2 = PWMLED(config["Leds"]["L2"])
        self.l3 = PWMLED(config["Leds"]["L3"])
        self.m1 = LED(config["Motors"]["M1"])
        self.m2 = LED(config["Motors"]["M2"])
        self.m3 = LED(config["Motors"]["M3"])
        self.buttons = [self.b1, self.b2, self.b3]
        self.leds = [self.l1, self.l2, self.l3]
        self.motors = [self.m1, self.m2, self.m3]


    def button_status(self):
        return "BUTTONS: " + ' '.join([button.status() for button in self.buttons])

    def cleanup(self):
        pins = [*self.buttons, *self.leds, *self.motors]
        for pin in pins:
            pin.close()
        subprocess.run(
            ["./gpio-reset.sh"],
            check=True
        )
