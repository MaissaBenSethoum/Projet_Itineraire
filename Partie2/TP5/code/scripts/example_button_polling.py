from utils import Button, LED
import time
from config import PORT_LED, PORT_BUTTON

button = Button(PORT_BUTTON)
led = LED(PORT_LED)
try:
    while True:
        button.wait_for_press()
        print("Bouton pressé")
        led.on()
        button.wait_for_release()
        led.off()
        time.sleep(0.05)

finally:
    button.cleanup()
    led.cleanup()