import RPi.GPIO as GPIO

class LED:
    """
    Classe pour l'utilisation d'une LED 
    
    Branchement:
    
    +   : PORT GPIO
    -   : GND
    N : /
    
    Exemple d'utilisation:
    led = LED(17)  # Connexion au port GPIO 17
    led.on() # Allume la LED
    time.sleep(1)
    led.off() # Eteint la LED
    led.toggle() # Inverse l'état de la LED et donc l'allume
    led.toggle() # Inverse l'état de la LED et donc l'éteint
    led.cleanup() # Libère les ressources
    
    """
    def __init__(self, pin):
        """
        Initialise le module LED Adeept.
        
        Arguments:
        - pin: Numéro du GPIO auquel la LED est connectée.
        """
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.state = False  # État initial de la LED (éteinte)

    def on(self):
        """Allume la LED."""
        GPIO.output(self.pin, GPIO.HIGH)
        self.state = True

    def off(self):
        """Éteint la LED."""
        GPIO.output(self.pin, GPIO.LOW)
        self.state = False

    def toggle(self):
        """Inverse l'état de la LED."""
        if self.state:
            self.off()
        else:
            self.on()
    
    def is_on(self):
        """Retourne True si la LED est allumée, False sinon."""
        return self.state
    
    def cleanup(self):
        """Nettoie les ressources GPIO."""
        GPIO.cleanup(self.pin)