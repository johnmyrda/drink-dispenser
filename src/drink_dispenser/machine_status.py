from drink_dispenser.drink_dispenser import DrinkDispenser
import time


def main():
    machine = DrinkDispenser()
    machine.disable_pumps(disabled=True)
    machine.startup_lights()

    try:
        while True:
            print(machine.button_status(), end="\r")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Bar's Closed!")
