import RPi.GPIO as GPIO
import time


class Button:
    """
    Classe pour l'utilisation d'un bouton.

    Deux modes d'utilisation sont proposés :
    
    1. Mode événementiel / polling
    
        button = Button(17)
        try:
            while True:
                button.wait_for_press()
                print("Bouton pressé")
                button.wait_for_release()
                time.sleep(0.05)
        finally:
            button.cleanup()

    2. Mode callback

        button = Button(17)
        def on_button_press():
            print("Appui détecté !")
        button.on_press(on_button_press)
        try:
            while True:
                time.sleep(0.1)
        finally:
            button.cleanup()

    Branchement
    -----------
    + : VCC 3.3V
    - : GND
    S : PORT GPIO
    """

    def __init__(self, pin, debounce_time=0.05, pull_up=True):
        """
        Initialise le bouton sur un GPIO donné.

        Parameters
        ----------
        pin : int
            Pin GPIO où communique le bouton.
        debounce_time : float
            Temps anti-rebond en secondes.
        pull_up : bool
            True pour utiliser une résistance de pull-up interne.
        """
        self.pin = pin
        self.debounce_time = debounce_time
        self.pull_up = pull_up

        self.last_pressed = 0.0
        self.callback = None
        self._cleaned = False

        GPIO.setmode(GPIO.BCM)

        pud = GPIO.PUD_UP if self.pull_up else GPIO.PUD_DOWN
        self._pressed_state = GPIO.LOW if self.pull_up else GPIO.HIGH
        edge = GPIO.FALLING if self.pull_up else GPIO.RISING

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=pud)

        GPIO.add_event_detect(
            self.pin,
            edge,
            callback=self._handle_press,
            bouncetime=int(self.debounce_time * 1000)
        )

    def _handle_press(self, channel):
        """
        Méthode interne appelée automatiquement par RPi.GPIO
        lorsqu'un appui est détecté.
        """
        current_time = time.time()

        if current_time - self.last_pressed > self.debounce_time:
            self.last_pressed = current_time

            if self.callback is not None:
                self.callback()

    ##################################################
    #        MODE EVENEMENTIEL / POLLING
    ##################################################

    def is_pressed(self):
        """
        Vérifie si le bouton est actuellement pressé.

        Returns
        -------
        bool
        """
        return GPIO.input(self.pin) == self._pressed_state

    def wait_for_press(self, poll_interval=0.01):
        """
        Attend qu'un appui soit détecté.

        Parameters
        ----------
        poll_interval : float
            Temps d'attente entre deux lectures GPIO.
        """
        while not self.is_pressed():
            time.sleep(poll_interval)

    def wait_for_release(self, poll_interval=0.01):
        """
        Attend que le bouton soit relâché.

        Parameters
        ----------
        poll_interval : float
            Temps d'attente entre deux lectures GPIO.
        """
        while self.is_pressed():
            time.sleep(poll_interval)

    ##################################################
    #              MODE CALLBACK
    ##################################################

    def on_press(self, callback):
        """
        Définit une fonction callback appelée lors d'un appui.

        Parameters
        ----------
        callback : callable
            Fonction sans argument à exécuter lors d'un appui.
        """
        self.callback = callback

    def remove_callback(self):
        """
        Supprime la fonction callback associée au bouton.
        """
        self.callback = None

    ##################################################
    #                 NETTOYAGE
    ##################################################

    def cleanup(self):
        """
        Libère les ressources GPIO associées au bouton.
        """
        if not self._cleaned:
            GPIO.cleanup(self.pin)
            self._cleaned = True