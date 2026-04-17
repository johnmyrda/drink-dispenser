from gpiozero.pins.mock import MockFactory

from drink_dispenser.drink_dispenser import DrinkButton


def test_button_status_test():
    button = DrinkButton(1, pin_factory=MockFactory(), pull_up=False)
    button.pin.drive_high()
    assert button.status() == "_"
    button.pin.drive_low()
    assert button.status() == "o"
