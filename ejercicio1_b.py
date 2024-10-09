import RPi.GPIO as GPIO
import time
import serial
import smtplib
from email.message import EmailMessage
from abc import ABC, abstractmethod

# Clase abstracta para manejar la fase de espera del vehículo
class VehicleState(ABC):
    @abstractmethod
    def standby(self):
        pass

# Clase que implementa la fase de espera
class StandbyMode(VehicleState):
    def _init_(self):
        self.is_standby = True

    def standby(self):
        if self.is_standby:
            print("El vehículo está en modo de espera.")
            time.sleep(1)

# Pines para motor y sensor
en = [14, 15, 27, 22]
o1 = 13
o2 = 19
trig = 23
echo = 24

sense = 0  # Sentido de giro
dist = 0  # Distancia del sensor
mail = 0  # Estado de envío de email

emaildir = ""  # Dirección de email
emailpass = ""  # Contraseña de email

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ser = serial.Serial('/dev/ttyACM0', 9600)

messages = ["The car was stopped\nA nearby object was detected", "Car functioning"]
subjects = ["Stopped Car", "Car initialized"]

GPIO.setup(en, GPIO.OUT, initial=0)
GPIO.setup(o1, GPIO.OUT)
GPIO.setup(o2, GPIO.OUT)
GPIO.setup(trig, GPIO.OUT, initial=0)
GPIO.setup(echo, GPIO.IN)

out1 = GPIO.PWM(o1, 100)
out2 = GPIO.PWM(o2, 100)
out1.start(0)
out2.start(0)

def movement(val, d):
    global sense
    if val == '0':  # Detener
        out1.ChangeDutyCycle(0)
        out2.ChangeDutyCycle(0)
    elif val == '3':  # Girar a la derecha
        GPIO.output(en, 0)
        GPIO.output(en[3] if sense == 1 else en[0], 1)
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)

def distance():
    GPIO.output(trig, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(trig, GPIO.LOW)
    while GPIO.input(echo) == GPIO.LOW:
        pulso_inicio = time.time()
    while GPIO.input(echo) == GPIO.HIGH:
        pulso_fin = time.time()
    duracion = pulso_fin - pulso_inicio
    return (34300 * duracion) / 2

def emailSent(mess, sub):
    global mail
    if mail != 0:
        msg = EmailMessage()
        msg['From'] = "Raspberry Pi Car"
        msg['To'] = "emmanuel.idiaquez@ucb.edu.bo"
        msg['Subject'] = sub[mail - 1]
        msg.set_content(mess[mail - 1])
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(emaildir, emailpass)
        s.send_message(msg)
        s.quit()
        mail = 0

# Crear una instancia de StandbyMode
standby_mode = StandbyMode()

while True:
    try:
        dist = round(distance(), 2)

        # Si la distancia es menor a 5, el auto se detiene y envía un email
        if dist < 5:
            movement('0', dist)
            mail = 1  # Indica que se debe enviar un email
            emailSent(messages, subjects)
            standby_mode.standby()  # Entra en modo de espera

        # Si la distancia es mayor o igual a 5, el auto gira a la derecha
        elif dist >= 5:
            movement('3', dist)  # Gira a la derecha

        d = str(dist * 100) + '\n'
        ser.write(d.encode('utf-8'))
        
    except Exception as e:
        print(e)
