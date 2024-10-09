import RPi.GPIO as GPIO  # Importa la librería para controlar los GPIO en Raspberry Pi
import time  # Importa la librería para manejar tiempos y retardos
import serial  # Importa la librería para comunicación serial
import smtplib  # Importa la librería para enviar correos electrónicos
from email.message import EmailMessage  # Importa la clase para construir mensajes de correo
from abc import ABC, abstractmethod  # Importa la funcionalidad para trabajar con clases abstractas

# Clase abstracta para manejar la fase de espera del vehículo
class VehicleState(ABC):
    @abstractmethod
    def standby(self):
        pass  # Método abstracto que debe ser implementado por las subclases

# Clase que implementa la fase de espera del vehículo
class StandbyMode(VehicleState):
    def _init_(self):  # Constructor que inicializa el modo de espera
        self.is_standby = True  # Variable que indica si el vehículo está en modo de espera

    def standby(self):  # Método que implementa el modo de espera
        if self.is_standby:  # Si está en modo de espera
            print("El vehículo está en modo de espera.")  # Imprime un mensaje indicando que está en modo de espera
            time.sleep(1)  # Pausa de 1 segundo

# Configuración de pines para motores y sensor ultrasónico
en = [14, 15, 27, 22]  # Pines de habilitación del motor
o1 = 13  # Pin para controlar la dirección del motor 1
o2 = 19  # Pin para controlar la dirección del motor 2
trig = 23  # Pin de activación del sensor ultrasónico (trigger)
echo = 24  # Pin de recepción del sensor ultrasónico (echo)

# Variables globales para controlar el sentido de giro, distancia, y estado de envío de email
sense = 0  # Sentido de giro del motor
dist = 0  # Distancia medida por el sensor
mail = 0  # Estado del envío de correo electrónico

# Credenciales de email (vacías inicialmente)
emaildir = ""  # Dirección de correo electrónico
emailpass = ""  # Contraseña de correo electrónico

# Configura la librería GPIO para que no muestre advertencias y use el esquema de numeración BCM
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Configura la comunicación serial a través del puerto ttyACM0 con una velocidad de 9600 baudios
ser = serial.Serial('/dev/ttyACM0', 9600)

# Mensajes y asuntos de email para los diferentes eventos del vehículo
messages = ["The car was stopped\nA nearby object was detected", "Car functioning"]  # Mensajes de correo
subjects = ["Stopped Car", "Car initialized"]  # Asuntos de los correos

# Configura los pines de salida para los motores y el sensor ultrasónico
GPIO.setup(en, GPIO.OUT, initial=0)  # Pines de habilitación de motores
GPIO.setup(o1, GPIO.OUT)  # Pin de control del motor 1
GPIO.setup(o2, GPIO.OUT)  # Pin de control del motor 2
GPIO.setup(trig, GPIO.OUT, initial=0)  # Pin de trigger del sensor ultrasónico
GPIO.setup(echo, GPIO.IN)  # Pin de echo del sensor ultrasónico

# Inicializa los pines PWM para los motores con una frecuencia de 100 Hz
out1 = GPIO.PWM(o1, 100)
out2 = GPIO.PWM(o2, 100)
out1.start(0)  # Inicia el PWM del motor 1 con 0% de ciclo de trabajo (detenido)
out2.start(0)  # Inicia el PWM del motor 2 con 0% de ciclo de trabajo (detenido)

# Función que controla el movimiento del vehículo
def movement(val, d):
    global sense  # Usa la variable global 'sense' para el sentido del motor
    if val == '0':  # Si el valor es '0', detiene los motores
        out1.ChangeDutyCycle(0)  # Detiene el motor 1
        out2.ChangeDutyCycle(0)  # Detiene el motor 2
    elif val == '3':  # Si el valor es '3', el vehículo gira a la derecha
        GPIO.output(en, 0)  # Desactiva todos los motores
        GPIO.output(en[3] if sense == 1 else en[0], 1)  # Activa el motor adecuado según el sentido
        out1.ChangeDutyCycle(50)  # Configura el motor 1 al 50% de potencia
        out2.ChangeDutyCycle(50)  # Configura el motor 2 al 50% de potencia

# Función para medir la distancia usando el sensor ultrasónico
def distance():
    GPIO.output(trig, GPIO.HIGH)  # Activa el pin de trigger
    time.sleep(0.00001)  # Espera 10 microsegundos
    GPIO.output(trig, GPIO.LOW)  # Desactiva el pin de trigger
    while GPIO.input(echo) == GPIO.LOW:  # Espera hasta que el pulso de echo comience
        pulso_inicio = time.time()  # Registra el tiempo de inicio
    while GPIO.input(echo) == GPIO.HIGH:  # Espera hasta que el pulso de echo termine
        pulso_fin = time.time()  # Registra el tiempo de fin
    duracion = pulso_fin - pulso_inicio  # Calcula la duración del pulso
    return (34300 * duracion) / 2  # Calcula la distancia basándose en la velocidad del sonido

# Función que envía un email cuando el vehículo se detiene
def emailSent(mess, sub):
    global mail  # Usa la variable global 'mail' para el estado de envío
    if mail != 0:  # Solo envía el email si el valor de 'mail' no es 0
        msg = EmailMessage()  # Crea un nuevo mensaje de correo
        msg['From'] = "Raspberry Pi Car"  # Establece el remitente
        msg['To'] = "emmanuel.idiaquez@ucb.edu.bo"  # Establece el destinatario
        msg['Subject'] = sub[mail - 1]  # Establece el asunto basado en el estado
        msg.set_content(mess[mail - 1])  # Establece el contenido del mensaje basado en el estado
        s = smtplib.SMTP('smtp.gmail.com', 587)  # Conecta al servidor SMTP de Gmail
        s.starttls()  # Inicia la comunicación cifrada TLS
        s.login(emaildir, emailpass)  # Inicia sesión en la cuenta de correo
        s.send_message(msg)  # Envía el mensaje
        s.quit()  # Cierra la conexión SMTP
        mail = 0  # Reinicia el estado de envío de email

# Crear una instancia de la clase StandbyMode para manejar el estado de espera
standby_mode = StandbyMode()

# Bucle principal del programa
while True:
    try:
        dist = round(distance(), 2)  # Mide la distancia y la redondea a 2 decimales

        # Si la distancia es menor a 5 cm, detiene el vehículo y envía un email
        if dist < 5:
            movement('0', dist)  # Detiene el vehículo
            mail = 1  # Establece que se debe enviar un email
            emailSent(messages, subjects)  # Envía el email
            standby_mode.standby()  # Activa el modo de espera del vehículo

        # Si la distancia es mayor o igual a 5 cm, gira a la derecha
        elif dist >= 5:
            movement('3', dist)  # El vehículo gira a la derecha

        # Envía la distancia por el puerto serial
        d = str(dist * 100) + '\n'
        ser.write(d.encode('utf-8'))  # Envía la distancia al puerto serial
        
    except Exception as e:  # Si ocurre algún error
        print(e)  # Imprime el mensaje de error
