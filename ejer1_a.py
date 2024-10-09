import RPi.GPIO as GPIO  # Importa la biblioteca para manejar los pines GPIO de la Raspberry Pi
import time  # Importa la biblioteca para manejar retrasos temporales
import serial  # Importa la biblioteca para comunicación serie (UART)
import smtplib  # Importa la biblioteca para enviar correos electrónicos
from email.message import EmailMessage  # Importa la clase para crear mensajes de correo electrónico

en = [14, 15, 27, 22]  # Pines GPIO conectados al puente H para controlar los motores
o1 = 13  # Conexión a ENA (control de velocidad) del puente H
o2 = 19  # Conexión a ENB (control de velocidad) del puente H

trig = 23  # Pin GPIO para enviar la señal de disparo del sensor ultrasónico
echo = 24  # Pin GPIO para recibir la señal de eco del sensor ultrasónico

sense = 0  # Variable para controlar el sentido de giro del vehículo
mail = 0  # Variable para controlar si se debe enviar un correo electrónico
dist = 0  # Variable que almacena la distancia medida por el sensor ultrasónico
value = '0'  # Controla el movimiento del vehículo mediante UART o SSH
m = '0'  # Variable que indica si se reciben comandos por UART o SSH
s = '0'  # Variable que almacena el valor recibido por SSH

emaildir = ""  # Dirección de correo desde la cual se enviará el email
emailpass = ""  # Contraseña del correo configurada para aplicaciones de terceros

GPIO.setwarnings(False)  # Desactiva las advertencias de GPIO
GPIO.setmode(GPIO.BCM)  # Configura el modo de numeración de pines en BCM (Broadcom)

ser = serial.Serial('/dev/ttyACM0', 9600)  # Configura la comunicación serie a 9600 baudios con un dispositivo en /dev/ttyACM0

# Definición de mensajes y temas para los correos electrónicos
messages = ["The car was stopped\nA nearby object was detected", "Car functioning"]  # Contenidos de los correos
subjects = ["Stopped Car", "Car initialized"]  # Asuntos de los correos

# Configura los pines GPIO como salidas con valor inicial 0
GPIO.setup(en, GPIO.OUT, initial=0)
GPIO.setup(o1, GPIO.OUT)  # Configura el pin para ENA como salida
GPIO.setup(o2, GPIO.OUT)  # Configura el pin para ENB como salida
GPIO.setup(trig, GPIO.OUT, initial=0)  # Configura el pin de trig como salida con valor inicial bajo
GPIO.setup(echo, GPIO.IN)  # Configura el pin de echo como entrada

# Configura PWM para controlar la velocidad de los motores
out1 = GPIO.PWM(o1, 100)  # PWM en el pin o1 con frecuencia de 100 Hz
out2 = GPIO.PWM(o2, 100)  # PWM en el pin o2 con frecuencia de 100 Hz
out1.start(0)  # Inicia PWM con ciclo de trabajo de 0% en o1
out2.start(0)  # Inicia PWM con ciclo de trabajo de 0% en o2

# Función para controlar el movimiento del vehículo
def movement(val, d):
    global sense
    global mail
    if val == '0':  # Si el valor es '0', detiene el vehículo
        if d < 5:  # Si la distancia es menor de 5 cm, se envía un correo
            mail = 1
        out1.ChangeDutyCycle(0)  # Detiene el motor conectado a o1
        out2.ChangeDutyCycle(0)  # Detiene el motor conectado a o2
    elif val == '1':  # Movimiento hacia adelante
        sense = 0  # Sentido de giro hacia adelante
        if mail == 1:  # Si se debe enviar correo
            mail = 2  # Cambia el estado del correo a 2 (para funcionamiento del vehículo)
        GPIO.output(en[:2], 1)  # Activa EN1 y EN4 (motor hacia adelante)
        GPIO.output(en[2:], 0)  # Desactiva EN2 y EN3
        out1.ChangeDutyCycle(50)  # Establece la velocidad del motor a 50% en o1
        out2.ChangeDutyCycle(50)  # Establece la velocidad del motor a 50% en o2
    elif val == '2':  # Movimiento hacia atrás
        sense = 1  # Sentido de giro hacia atrás
        GPIO.output(en[:2], 0)  # Desactiva EN1 y EN4
        GPIO.output(en[2:], 1)  # Activa EN2 y EN3 (motor hacia atrás)
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)
    elif val == '3':  # Giro hacia la derecha
        if sense == 1:  # Si el vehículo va hacia atrás
            GPIO.output(en, 0)  # Apaga todos los motores
            GPIO.output(en[3], 1)  # Activa solo EN3
        else:  # Si va hacia adelante
            GPIO.output(en, 0)
            GPIO.output(en[0], 1)  # Activa solo EN1
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)
    elif val == '4':  # Giro hacia la izquierda
        if sense == 1:  # Si va hacia atrás
            GPIO.output(en, 0)
            GPIO.output(en[2], 1)  # Activa solo EN2
        else:
            GPIO.output(en, 0)
            GPIO.output(en[1], 1)  # Activa solo EN4
        out1.ChangeDutyCycle(50)
        out2.ChangeDutyCycle(50)

# Función para medir la distancia usando el sensor ultrasónico
def distance():
    GPIO.output(trig, GPIO.HIGH)  # Enviar pulso de disparo
    time.sleep(0.00001)  # Espera 10 microsegundos
    GPIO.output(trig, GPIO.LOW)  # Finaliza el pulso de disparo
    while True:
        pulso_inicio = time.time()  # Captura el tiempo de inicio
        if GPIO.input(echo) == GPIO.HIGH:  # Espera hasta recibir eco
            break
    while True:
        pulso_fin = time.time()  # Captura el tiempo de fin
        if GPIO.input(echo) == GPIO.LOW:  # Espera hasta que el eco termine
            break
    duracion = pulso_fin - pulso_inicio  # Calcula la duración del pulso
    distancia = (34300 * duracion) / 2  # Calcula la distancia en cm

    return distancia

# Función para enviar correos electrónicos
def emailSent(mess, sub):
    global mail
    global emaildir
    global emailpass
    if mail != 0:
        msg = EmailMessage()  # Crea el mensaje de correo
        msg['From'] = "Raspberry Pi Car"  # Define el remitente
        msg['To'] = "emmanuel.idiaquez@ucb.edu.bo"  # Define el destinatario
        if mail == 1:
            msg['Subject'] = sub[0]  # Asunto del correo cuando el coche se detiene
            msg.set_content(mess[0])  # Contenido del correo
        elif mail == 2:
            msg['Subject'] = sub[1]  # Asunto del correo cuando el coche está en funcionamiento
            msg.set_content(mess[1])

        s = smtplib.SMTP('smtp.gmail.com', 587)  # Conecta al servidor SMTP de Gmail
        s.starttls()  # Inicia la comunicación segura
        s.login(emaildir, emailpass)  # Inicia sesión en el correo
        s.send_message(msg)  # Envía el mensaje
        s.quit()  # Cierra la conexión SMTP
        mail = 0  # Resetea la variable de control de correo
        del msg  # Elimina el mensaje de la memoria

while True:  # Bucle principal del programa
    try:
        file = open("config.txt", 'r')  # Abre el archivo de configuración
        config = file.readlines()  # Lee todas las líneas del archivo
        m = config[0].rstrip()[-1]  # Obtiene el último carácter de la primera línea (modo)
        s = config[1].rstrip()[-1]  # Obtiene el último carácter de la segunda línea (valor SSH)
        
        dist = round(distance(), 2)  # Mide la distancia utilizando el sensor ultrasónico y la redondea a 2 decimales

        if dist < 5:  # Si la distancia es menor de 5 cm
            value = '0'  # Detiene el vehículo (modo parada)
            # emailSent(messages, subjects)  # (comentado) Envía un correo cuando el coche se detiene
            print("Email sent")  # Imprime un mensaje indicando que se enviará un correo
        else:
            if m == '0':  # Si el modo es '0' (control UART)
                if ser.in_waiting > 0:  # Verifica si hay datos en el buffer UART
                    value = ser.readline().decode('utf-8').rstrip()  # Lee los datos del buffer UART y elimina espacios finales
            elif m == '1':  # Si el modo es '1' (control SSH)
                value = s  # Asigna el valor recibido por SSH
            else:
                out1.ChangeDutyCycle(0)  # Detiene el motor conectado a o1
                out2.ChangeDutyCycle(0)  # Detiene el motor conectado a o2
                print('Incorrect mode value')  # Imprime un mensaje si el modo es incorrecto

        # Nueva lógica para girar a la derecha cuando no se detecta un objeto cercano
        if dist >= 5:  # Si no se detecta un objeto (distancia mayor o igual a 5 cm)
            movement('3', dist)  # El vehículo gira a la derecha (valor '3')
        else:
            movement(value, dist)  # Ejecuta el movimiento del vehículo según el valor recibido

        d = str(dist * 100) + '\n'  # Convierte la distancia a centímetros y la formatea como una cadena con salto de línea
        ser.write(d.encode('utf-8'))  # Envía la distancia al puerto serie (UART)
        
        file.close()  # Cierra el archivo de configuración
    except Exception as e:  # Captura cualquier excepción que ocurra durante la ejecución del bloque try
        print(e)  # Imprime el mensaje de error
