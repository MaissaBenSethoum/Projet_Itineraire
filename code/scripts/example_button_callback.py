from utils import Button, LED
import time
from config import PORT_LED, PORT_BUTTON

button = Button(PORT_BUTTON)
led = LED(PORT_LED)

def on_button_press():
    print("Appui détecté !")
    led.toggle()

button.on_press(on_button_press)

try:
    while True:
        time.sleep(0.1)

finally:
    button.cleanup()
    led.cleanup()