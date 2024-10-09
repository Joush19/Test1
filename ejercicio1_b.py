import RPi.GPIO as GPIO
import time
import serial
import smtplib # Se utiliza para mandar los mensajes
from email.message import EmailMessage # Se utiliza para configurar los mensajes de email
from abc import ABC, abstractmethod  # Importar las clases base abstractas

# Clase abstracta para manejar la fase de espera del vehículo
class VehicleState(ABC):
    @abstractmethod
    def standby(self):
        pass

# Clase que implementa la fase de espera
class StandbyMode(VehicleState):
    def __init__(self):
        self.is_standby = True

    def standby(self):
        if self.is_standby:
            print("El vehículo está en modo de espera.")
            # Aquí puedes agregar más lógica si es necesario
            time.sleep(1)  # Mantener en espera un segundo

en = [14, 15, 27, 22]  # El orden para conectar al puente H es EN1, EN4, EN2, EN3
o1 = 13  # Se conecta al ENA en el puente H
o2 = 19  # Se conecta al ENB en el puente H

trig = 23
echo = 24

sense = 0  # Variable para controlar el sentido de giro
mail = 0  # Variable para controlar el envío del mensaje
dist = 0  # Variable para almacenar el valor del sensor de distancia
value = '0'  # Valor con el que se controla el movimiento del auto por UART o SSH
m = '0'  # Valor para cambiar la recepción del movimiento por SSH o por UART
s = '0'  # Valor para almacenar el modo en el que se reciben los datos 0: UART, 1: SSH

emaildir = ""  # Almacena la dirección del correo electrónico para enviar el mail
emailpass = ""  # La contraseña tiene que ser la configurada para aplicaciones de terceros del email configurado

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ser = serial.Serial('/dev/ttyACM0', 9600)

# Mensajes y encabezados para el mensaje email
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

def emailSent(mess, sub):
    global mail
    global emaildir
    global emailpass
    if mail != 0:
        msg = EmailMessage()
        msg['From'] = "Raspberry Pi Car"
        msg['To'] = "emmanuel.idiaquez@ucb.edu.bo"
        if mail == 1:
            msg['Subject'] = sub[0]
            msg.set_content(mess[0])
        elif mail == 2:
            msg['Subject'] = sub[1]
            msg.set_content(mess[1])

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(emaildir, emailpass)
        s.send_message(msg)
        s.quit()
        mail = 0
        del msg

# Crear una instancia de StandbyMode
standby_mode = StandbyMode()

while True:
    try:
        file = open("config.txt", 'r')
        config = file.readlines()
        m = config[0].rstrip()[-1]
        s = config[1].rstrip()[-1]
        dist = round(distance(), 2)
        if dist < 5:
            value = '0'
            # emailSent(messages, subjects)
            print("Email sent")
        else:
            if m == '0':
                if ser.in_waiting > 0:
                    value = ser.readline().decode('utf-8').rstrip()
            elif m == '1':
                value = s
            else:
                out1.ChangeDutyCycle(0)
                out2.ChangeDutyCycle(0)
                print('Incorrect mode value')

        # Nueva lógica para girar a la derecha cuando no se detecta un objeto
        if dist >= 5:  # Si no se detecta un objeto
            movement('3', dist)  # Girar a la derecha (valor '3')
        else:
            movement(value, dist)
            
        # Lógica para la fase de espera
        if value == '0':
            standby_mode.standby()  # Entrar en modo de espera si el vehículo está detenido
            
        d = str(dist * 100) + '\n'
        ser.write(d.encode('utf-8'))
        file.close()
    except Exception as e:
        print(e)
