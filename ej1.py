import RPi.GPIO as GPIO
import time
import serial
import smtplib
from email.message import EmailMessage
from abc import ABC, abstractmethod
from datetime import datetime

# Clase abstracta para manejar la fase de espera del vehículo
class VehicleState(ABC):
    @abstractmethod
    def standby(self):
        pass

# Clase que implementa la fase de espera
class StandbyMode(VehicleState):
    def _init_(self):
        self.value
        self.st

    def save(self,file_name, date, time):
        file = open(file_name, 'a')
        file.writelines(['\nAn object is near', f"\nDate: {date}", f"\nTime: {time}"])
        file.close()
    def standby(self, dist):
        if dist <= 5:
            ser.write('0\n'.encode('utf-8'))
            self.st = True
            out1.ChangeDutyCycle(0)
            out2.ChangeDutyCycle(0)
            c = str(datetime.now())
            emailSent(f"A nearby object was detected in time\nIn time: {c[11:19]}\nIn date: {c[:10]}", "Car stopped")
            self.save('date.txt', c[0:10], c[11:19])
            while(dist <= 5):
                toogle(self.st)
                self.st = not self.st
                dist = round(distance(),2)
            self.st = False
        elif dist<= 15:
            ser.write('0\n'.encode('utf-8'))
            self.value = '1'
        else:
            ser.write('1\n'.encode('utf-8'))
            self.value = '3'
        movement(self.value,30)
        time.sleep(0.5)

# Pines para motor y sensor
en = [14, 15, 27, 22]
o1 = 13
o2 = 19
trig = 23
echo = 24
buzz = 17

sense = 0  # Sentido de giro
dist = 0  # Distancia del sensor
mail = 0  # Estado de envío de email
value = ''

emaildir = "joushigrit@gmail.com"  # Dirección de email
emailpass = "kewj paoq axca yqdw"  # Contraseña de email

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ser = serial.Serial('/dev/ttyACM0', 9600)

messages = ["The car was stopped\nA nearby object was detected", "Car functioning"]
subjects = ["Stopped Car", "Car initialized"]

GPIO.setup(en, GPIO.OUT, initial=0)
GPIO.setup(o1, GPIO.OUT)
GPIO.setup(o2, GPIO.OUT)
GPIO.setup(trig, GPIO.OUT, initial=0)
GPIO.setup(buzz, GPIO.OUT, initial=0)
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
    elif val == '1':
        sense = 0
        GPIO.output(en[:2], 1)
        GPIO.output(en[2:], 0)
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)
    elif val == '2':
        sense = 1
        GPIO.output(en[:2], 0)
        GPIO.output(en[2:], 1)
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)
    elif val == '3':  # Girar a la derecha
        if sense == 1:
            GPIO.output(en, 0)
            GPIO.output(en[3], 1)
        else:
            GPIO.output(en, 0)
            GPIO.output(en[0], 1)
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)
    elif val == '4':  # Girar a la derecha
        GPIO.output(en, 0)
        GPIO.output(en[2] if sense == 1 else en[1], 1)
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
    msg = EmailMessage()
    msg['From'] = "Raspberry Pi Car"
    msg['To'] = "emmanuel.idiaquez@ucb.edu.bo"
    msg['Subject'] = sub
    msg.set_content(mess)
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(emaildir, emailpass)
    s.send_message(msg)
    s.quit()
    del msg

def toogle(state):
    GPIO.output(buzz,state)
    time.sleep(2)

# Crear una instancia de StandbyMode
standby_mode = StandbyMode()

while True:
    try:
        dist = round(distance(), 2)
        standby_mode.standby(dist)
        print(dist)
        d = str(dist * 100) + '\n'
        ser.write(d.encode('utf-8'))

    except Exception as e:
        print(e)
