import argparse

from drink_dispenser.drink_dispenser import DrinkDispenser
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")

    machine = DrinkDispenser()
    if parser.parse_args().test:
        machine.disable_pumps(disabled=True)
        print("Testing mode. Pumps disabled.")
    print("Bar's Open! Press Ctrl+C to exit.")
    machine.startup_lights()

    try:
        while True:
            print(machine.button_status(), end="\r")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Bar's Closed!")


if __name__ == "__main__":
    main()
