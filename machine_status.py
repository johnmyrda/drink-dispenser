import atexit

from gpiozero import Device

from drink_dispenser import DrinkDispenser
from time import sleep


def activate(led, motor):
    led.on()
    motor.on()

def stop(led, motor):
    led.off()
    motor.off()

machine = DrinkDispenser()

print(Device.pin_factory)

for i, button in enumerate(machine.buttons):
    print("Number " + str(i))
    print(button)
    print(machine.leds[i])
    print(machine.motors[i])
    led = machine.leds[i]
    motor = machine.motors[i]
    button.when_pressed  = lambda l=led,m=motor: activate(l, m)
    button.when_released  = lambda l=led,m=motor: stop(l, m)

atexit.unregister(Device.pin_factory.close)

try:
  while True:
    print(machine.button_status(), end="\r")
    sleep(.1)
except KeyboardInterrupt:
    print("Bar's Closed!")
    machine.cleanup()

