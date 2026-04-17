import atexit

from gpiozero import Device

from drink_dispenser import DrinkDispenser
import time


machine = DrinkDispenser()
machine.disable_pumps(disabled=True)
start_time = time.time()

try:
  while True:
    print(machine.button_status(), end="\r")
    time.sleep(.1)
except KeyboardInterrupt:
    print("Bar's Closed!")
    machine.cleanup()

