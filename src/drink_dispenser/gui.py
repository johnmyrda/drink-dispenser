"""
Drink Dispenser GUI
===================
A tkinter-based control panel simulating a 3-channel drink dispensing machine.

Layout per channel:
  - Brightness LED  : variable-brightness indicator (0–100%)
  - On/Off Light    : binary status indicator (green = ON, grey = OFF)
  - Dispense Button : triggers a dispense action

GPIO hook points are clearly marked so you can wire in gpiozero later.
"""
import threading

import tkinter as tk
from tkinter import font as tkfont
import colorsys

from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPWMPin, MockPin

from drink_dispenser.drink_dispenser import DrinkDispenser

# ── Drink definitions ──────────────────────────────────────────────────────────
DRINKS = [
    {"name": "RUM",   "hue": 1,  "accent": "#E8430A"},   # amber-orange
    {"name": "VODKA", "hue": 1,  "accent": "#B5D900"},   # yellow-green
    {"name": "MALÖRT",  "hue": 1,  "accent": "#8A2BE2"},   # violet
]

BG        = "#1A1A1E"
PANEL_BG  = "#111114"
BORDER    = "#2E2E38"
TEXT_DIM  = "#5A5A6E"
TEXT_MAIN = "#D0D0E0"


# ── Color helpers ─────────────────────────────────────────────────────────────
def hue_to_hex(h, s=0.9, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))

def brightness_color(hue, brightness):
    """Map 0-100 brightness to a color from near-black → full-saturation."""
    v = 0.05 + 0.95 * (brightness / 100)
    s = 0.2  + 0.80 * (brightness / 100)
    return hue_to_hex(hue, s, v)


Device.pin_factory = MockFactory(pin_class=MockPWMPin)
machine = DrinkDispenser()

# ── GPIO hook stubs ────────────────────────────────────────────────────────────
# Replace these with your gpiozero calls when wiring to hardware.

def gpio_set_led_brightness(channel: int, brightness: float):
    """Set PWM LED on channel (0-indexed) to brightness 0.0–1.0."""
    pass  # e.g. led_devices[channel].value = brightness

def gpio_set_pump(channel: int, state: bool):
    """Turn pump on channel on (True) or off (False)."""
    pass  # e.g. pump_devices[channel].value = state


# ── Channel widget ─────────────────────────────────────────────────────────────
class ChannelPanel(tk.Frame):
    def __init__(self, parent, channel_idx, drink, **kw):
        super().__init__(parent, bg=PANEL_BG, **kw)
        self.idx: int = channel_idx
        self.drink    = drink
        self.hue      = drink["hue"]
        self.accent   = drink["accent"]

        self._brightness = 75       # 0–100
        self._pump_on    = False

        self._build()

    # ── build ──────────────────────────────────────────────────────────────────
    def _build(self):
        self.config(
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18, pady=20,
        )

        title_font  = tkfont.Font(family="Courier", size=11, weight="bold")
        label_font  = tkfont.Font(family="Courier", size=8)
        value_font  = tkfont.Font(family="Courier", size=10, weight="bold")

        # ── channel title ──────────────────────────────────────────────────────
        tk.Label(
            self, text=f"CH{self.idx+1}\n·{self.drink['name']}·",
            bg=PANEL_BG, fg=self.accent,
            font=title_font,
        ).pack(anchor="w", pady=(0, 14))

        # ── LED Button section ─────────────────────────────────────────────
        tk.Label(self, text="LED Button",
                 bg=PANEL_BG, fg=TEXT_DIM, font=label_font).pack(anchor="w")

        led_row = tk.Frame(self, bg=PANEL_BG)
        led_row.pack(fill="x", pady=(4, 0))

        self.led_button_canvas = tk.Canvas(
            led_row, width=44, height=44,
            bg=PANEL_BG, highlightthickness=0,
        )
        self.led_button_canvas.pack(side="left")
        self._led_outer = self.led_button_canvas.create_oval(
            4, 4, 40, 40, outline=BORDER, width=2, fill="#0D0D10"
        )
        self._led_inner = self.led_button_canvas.create_oval(
            10, 10, 34, 34, fill="#0D0D10", outline=""
        )
        self.led_button_canvas.tag_bind(self._led_inner, '<ButtonPress-1>', self._button_press)
        self.led_button_canvas.tag_bind(self._led_inner, '<ButtonRelease-1>', self._button_release)
        self.led_button_canvas.tag_bind(self._led_inner, '<Enter>', self._btn_hover_on)
        self.led_button_canvas.tag_bind(self._led_inner, '<Leave>', self._btn_hover_off)

        # ── separator ─────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", pady=14)

        # ── on/off indicator section ───────────────────────────────────────────
        tk.Label(self, text="PUMP STATUS",
                 bg=PANEL_BG, fg=TEXT_DIM, font=label_font).pack(anchor="w")

        indicator_row = tk.Frame(self, bg=PANEL_BG)
        indicator_row.pack(fill="x", pady=(6, 0))

        self.onoff_canvas = tk.Canvas(
            indicator_row, width=28, height=28,
            bg=PANEL_BG, highlightthickness=0,
        )
        self.onoff_canvas.pack(side="left", anchor="center")
        self._onoff_dot = self.onoff_canvas.create_oval(
            4, 4, 24, 24, fill="#1C2C1C", outline="#243024", width=1
        )

        self.onoff_label = tk.Label(
            indicator_row, text="OFF",
            bg=PANEL_BG, fg=TEXT_DIM,
            font=tkfont.Font(family="Courier", size=9, weight="bold"),
        )
        self.onoff_label.pack(side="left", padx=(8, 0), anchor="center")

        # init visuals
        self._update_brightness_led()
        self._update_onoff_indicator()

    # ── event handlers ─────────────────────────────────────────────────────────
    def _on_brightness_change(self, value):
        self._brightness = int(float(value))
        # self.brightness_label.config(text=f"{self._brightness}%")
        self._update_brightness_led()
        # ── GPIO hook ──
        gpio_set_led_brightness(self.idx, self._brightness / 100)

    def _button_press(self, _):
        # print(f"Button {self.idx} pressed")
        button_pin: MockPin = machine.slots[self.idx].button.pin
        if button_pin.pull == "up":
            button_pin.drive_low()
        else:
            button_pin.drive_high()

    def _button_release(self, _):
        # print(f"Button {self.idx} released")
        button_pin: MockPin = machine.slots[self.idx].button.pin
        if button_pin.pull == "up":
            button_pin.drive_high()
        else:
            button_pin.drive_low()

    def _on_dispense(self):
        self._pump_on = not self._pump_on
        self._update_onoff_indicator()
        # ── GPIO hook ──
        gpio_set_pump(self.idx, self._pump_on)

    def _btn_hover_on(self, _):
        self.led_button_canvas.config(cursor="hand2")
        # self.btn.config(bg=self.accent, fg=BG)

    def _btn_hover_off(self, _):
        self.led_button_canvas.config(cursor="")
        # self.btn.config(bg="#1A1A24", fg=self.accent)

    # ── visual updaters ────────────────────────────────────────────────────────
    def _update_brightness_led(self):
        color = brightness_color(self.hue, self._brightness)
        self.led_button_canvas.itemconfig(self._led_inner, fill=color)
        # glow ring brightens with value
        glow = brightness_color(self.hue, max(0, self._brightness - 20))
        self.led_button_canvas.itemconfig(self._led_outer, outline=glow)

    def _update_onoff_indicator(self):
        if self._pump_on:
            self.onoff_canvas.itemconfig(
                self._onoff_dot, fill="#00E550", outline="#00FF60"
            )
            self.onoff_label.config(text="ON ", fg="#00E550")
            # self.btn.config(text=f"STOP {self.drink['name']}")
        else:
            self.onoff_canvas.itemconfig(
                self._onoff_dot, fill="#1C2C1C", outline="#243024"
            )
            self.onoff_label.config(text="OFF", fg=TEXT_DIM)

    # ── public API (call from gpiozero callbacks) ─────────────────────────────
    def set_brightness(self, value: int):
        """Set brightness programmatically (0–100)."""
        self._on_brightness_change(value)

    def set_pump(self, state: bool):
        """Set pump state programmatically."""
        if self._pump_on != state:
            self._pump_on = state
            self._update_onoff_indicator()


# ── Main application ───────────────────────────────────────────────────────────
class DispenserApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DRINK DISPENSER · CONTROL PANEL")
        self.configure(bg=BG)
        self.resizable(False, False)

        self._build_header()
        self._build_channels()
        self._build_footer()

        # Center on screen
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 10))

        title_font = tkfont.Font(family="Courier", size=14, weight="bold")
        tk.Label(
            hdr, text="◈  DISPENSER CONTROL PANEL  ◈",
            bg=BG, fg=TEXT_MAIN, font=title_font,
        ).pack(side="left")

        sub_font = tkfont.Font(family="Courier", size=8)
        tk.Label(
            hdr, text="SIM MODE",
            bg="#2A1A00", fg="#FFA040",
            font=sub_font, padx=8, pady=3,
        ).pack(side="right", anchor="center")

    def _build_channels(self):
        row = tk.Frame(self, bg=BG)
        row.pack(padx=20, pady=(0, 20))

        self.channels: list[ChannelPanel] = []
        for i, drink in enumerate(DRINKS):
            panel = ChannelPanel(row, i, drink)
            panel.grid(row=0, column=i, padx=8, pady=4, sticky="nsew")
            self.channels.append(panel)

    def _build_footer(self):
        ft = tk.Frame(self, bg=PANEL_BG, highlightbackground=BORDER,
                      highlightthickness=1)
        ft.pack(fill="x", padx=20, pady=(0, 20))

        foot_font = tkfont.Font(family="Courier", size=7)
        tk.Label(
            ft,
            text="Bar's Open!",
            bg=PANEL_BG, fg=TEXT_DIM, font=foot_font,
            pady=6,
        ).pack()


def main():
    app = DispenserApp()
    def update_machine():
        for channel in app.channels:
            slot = machine.slots[channel.idx]
            channel.set_pump(slot.pump.is_active)
            channel.set_brightness(slot.light.value * 100)
        app.after(16, update_machine)
    update_machine()
    threading.Thread(target=machine.animations.startup).start()
    app.mainloop()

if __name__ == "__main__":
    main()
