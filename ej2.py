import RPi.GPIO as GPIO
import time
import serial
import smtplib #Se utiliza para mandar los mensajes
from email.message import EmailMessage #Se utilliza para configurar los mensajes de email
from datetime import datetime
from abc import ABC, abstractmethod

class VehicleState(ABC):
    @abstractmethod
    def standby(self):
        pass

class time_capture:
    def ___init__(self):
        self.date
        self.time
    def save(self, file_name):
        file = open(file_name, 'a')
        file.writelines(["\nAn object was detected",self.date, '\n'+self.time])
        file.close()

en = [14,15,27,22] #el orden en para conectar al puente H es EN1, EN4, EN2, EN3
o1 = 13 #Se conecta al ENA en el puente H
o2 = 19 #Se conecta al ENB en el puente H
buzz = 17
buzz_st = True

trig = 23
echo = 24

sense = 0 #Variable para controlar el sentido de giro
mail = 0 #Variable para controlar el envio del mensaje
dist = 0 #Variable para almacenar el valor del sensor de distancia
value = '0' #Valor con el que se controla el moviiento del auto por uart o ssh
m = '0' #Valor para cambiar la recepcion del movimiento por ssh o por uart
s = '0' #Valor para almacenar el modo en el que se reciben los datos 0:uart, 1:ssh
d = 0

emaildir = "joushigrit@gmail.com" #Almacena la direccion del correo electronico para enviar el mail
emailpass = "kewj paoq axca yqdw" #La contrasegna tiene que ser la configurada para aplicaciones de terceros del email configurado

#Mensajes y encabezados para el mensaje email
messages = ["The car was stopped\nA nearby object was detected", "Car functionaiting"]
subjects = ["Stopped Car", "Car initializated"]

ser = serial.Serial('/dev/ttyACM0', 9600)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(en, GPIO.OUT, initial=0)
GPIO.setup(o1, GPIO.OUT)
GPIO.setup(o2, GPIO.OUT)
GPIO.setup(trig, GPIO.OUT, initial = 0)
GPIO.setup(echo, GPIO.IN)
GPIO.setup(buzz, GPIO.OUT)

out1 = GPIO.PWM(o1,100)
out2 = GPIO.PWM(o2,100)
out1.start(0)
out2.start(0)

def movement(val, d):
    global sense
    global mail
    if val == '0':
        if d < 5:
            mail = 1
        out1.ChangeDutyCycle(0)
        out2.ChangeDutyCycle(0)
    elif val == '1':
        sense = 0
        if mail == 1:
            mail = 2
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
    elif val == '3':
        if sense == 1:
            GPIO.output(en, 0)
            GPIO.output(en[3], 1)
        else:
            GPIO.output(en, 0)
            GPIO.output(en[0], 1)
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)
    elif val == '4':
        if sense == 1:
            GPIO.output(en, 0)
            GPIO.output(en[2], 1)
        else:
            GPIO.output(en, 0)
            GPIO.output(en[1], 1)
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)

def distance():
    GPIO.output(trig, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(trig, GPIO.LOW)
    while True:
        pulso_inicio = time.time()
        if GPIO.input(echo) == GPIO.HIGH:
            break
    while True:
        pulso_fin = time.time()
        if GPIO.input(echo) == GPIO.LOW:
            break
    duracion = pulso_fin - pulso_inicio
    distancia = (34300 * duracion) / 2

    return distancia

def toogle(state):
    GPIO.output(buzz, state)
    time.sleep(2)

def emailSent(mess, sub):
    global mail
    global emaildir
    global emailpass
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
    mail = 0
    del msg

txt = time_capture()

while True:
    dist = round(distance(),2)
    if dist <= 5:
        out1.ChangeDutyCycle(0)
        out2.ChangeDutyCycle(0)
        emailSent(messages[0], subjects[0])
        c = datetime.now()
        d = str(c)
        txt.date = d[0:10]
        txt.time = d[11:19]
        txt.save('config.txt')
        while dist <= 5:
            toogle(buzz_st)
            buzz_st = not buzz_st
            dist = round(distance(),2)
        GPIO.output(buzz, False)
    else:
        value = '1'
    movement(value, dist)
    time.sleep(0.1)
    print(dist)
