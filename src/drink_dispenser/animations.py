import time

from drink_dispenser.components import ButtonLight


class Animations:
    lights: list[ButtonLight]

    def __init__(self, lights: list[ButtonLight]):
        self.lights = lights

    def lights_on(self):
        for light in self.lights:
            light.on()

    def lights_off(self):
        for light in self.lights:
            light.off()

    def idle(self):
        for light in self.lights:
            light.animate_pulse(500)

    def startup(self):
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
