from RPLCD.i2c import CharLCD

class LCD:
    """
    Une classe pour l'affichage sur un LCD, connecté en I2C sur la Raspberry.
    """
    
    def __init__(self,LCD_address):
        """
        Initialise l'afficheur LCD.
        
        Arguments:
        - LCD_address: L'addresse I2C où communique l'afficheur LCD.
        """
        self.lcd = CharLCD(i2c_expander='PCF8574', address=LCD_address, port=1, cols=16, rows=2, dotsize=8)
        self.lcd.clear()
        
    def afficher(self,message):
        """
        Affiche un message sur un LCD.
        
        Arguments:
        - message: le message à afficher sur le LCD.
        """
        self.lcd.clear()
        self.lcd.write_string(message)
        
    def effacer(self):
        """
        Efface l'affichage.
        """
        self.lcd.clear()