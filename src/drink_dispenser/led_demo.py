from gpiozero import PWMLED
from time import sleep

led1 = PWMLED(10)
led2 = PWMLED(17)
led3 = PWMLED(3)

leds = [led1, led2, led3]


def reset():
    for led in leds:
        led.value = 0


def self_test(led):
    led.value = 1  # LED fully on
    sleep(0.5)
    led.value = 0.5  # LED half-brightness
    sleep(0.5)
    led.value = 0  # LED fully off
    sleep(0.5)


self_test(led1)
self_test(led2)
self_test(led3)
reset()
exit("All Done!")

# try:
#   # fade in and out forever
#   while True:
#     #fade in
#     for duty_cycle in range(0, 100, 1):
#       led.value = duty_cycle/100.0
#       sleep(0.05)

#     #fade out
#     for duty_cycle in range(100, 0, -1):
#       led.value = duty_cycle/100.0
#       sleep(0.05)

# except KeyboardInterrupt:
#   print("Stop the program and turning off the LED")
#   reset()
#   pass
