#include <stdint.h>  // Incluye definiciones estándar de tipos enteros de tamaño fijo
#include <stdbool.h>  // Incluye soporte para el tipo de dato booleano (true/false)
#include <string.h>  // Incluye funciones de manejo de cadenas como strcmp
#include <stdlib.h>  // Incluye funciones generales como atoi para convertir strings a enteros
#include "inc/hw_memmap.h"  // Incluye el mapeo de la memoria del hardware (ubicaciones de periféricos)
#include "inc/hw_ints.h"  // Incluye definiciones de las interrupciones de hardware
#include "driverlib/debug.h"  // Permite el uso de funciones de depuración
#include "driverlib/gpio.h"  // Controla los pines GPIO
#include "driverlib/sysctl.h"  // Permite el uso de funciones de control del sistema
#include "driverlib/timer.h"  // Controla los temporizadores del microcontrolador
#include "driverlib/interrupt.h"  // Manejo de interrupciones
#include "driverlib/uart.h"  // Controla la UART
#include "driverlib/pin_map.h"  // Mapea los pines del microcontrolador para diferentes funciones
#include "utils/uartstdio.c"  // Biblioteca que proporciona funciones UART estándar

#ifdef DEBUG
// Función para capturar errores en modo de depuración
void __error__(char *pcFilename, uint32_t ui32Line) {
    while(1);  // Si hay un error, el sistema entra en un bucle infinito
}
#endif

// Variables globales para el estado del sistema
bool state = false;  // Estado para controlar el parpadeo del LED
bool blinky = false;  // Estado que controla si el LED debe parpadear

// Declaración de funciones
void printData(void);  // Función que imprime datos a través de UART
void Timer0IntHandler(void);  // Manejador de interrupciones del temporizador

// Función de inicialización de la UART
void uart(void) {
    SysCtlPeripheralEnable(SYSCTL_PERIPH_UART0);  // Habilita el periférico UART0
    GPIOPinConfigure(GPIO_PA0_U0RX);  // Configura el pin PA0 como RX para UART0
    GPIOPinConfigure(GPIO_PA1_U0TX);  // Configura el pin PA1 como TX para UART0
    GPIOPinTypeUART(GPIO_PORTA_BASE, 0x03);  // Configura los pines de UART
    UARTStdioConfig(0, 9600, 120000000);  // Configura la UART a 9600 baudios con una frecuencia de sistema de 120MHz
}

// Función que verifica si los periféricos están listos
void checking(void) {
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOA)) {}  // Espera a que el periférico GPIOA esté listo
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOH)) {}  // Espera a que el periférico GPIOH esté listo
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOM)) {}  // Espera a que el periférico GPIOM esté listo
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPION)) {}  // Espera a que el periférico GPION esté listo
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOF)) {}  // Espera a que el periférico GPIOF esté listo
}

// Configuración de los pines GPIO
void pinConfiguration(void) {
    GPIOPinTypeGPIOOutput(GPIO_PORTN_BASE, 0x03);  // Configura los pines de salida en PORTN
    GPIOPinTypeGPIOOutput(GPIO_PORTF_BASE, 0x11);  // Configura los pines de salida en PORTF
    GPIOPinTypeGPIOInput(GPIO_PORTH_BASE, 0x03);  // Configura los pines de entrada en PORTH
    GPIOPinTypeGPIOInput(GPIO_PORTM_BASE, 0x07);  // Configura los pines de entrada en PORTM
    // Configura los pads de los pines en PORTH y PORTM con resistencia pull-up y corriente de 2 mA
    GPIOPadConfigSet(GPIO_PORTH_BASE, 0X03, GPIO_STRENGTH_2MA, GPIO_PIN_TYPE_STD_WPU);
    GPIOPadConfigSet(GPIO_PORTM_BASE, 0X07, GPIO_STRENGTH_2MA, GPIO_PIN_TYPE_STD_WPU);
}

// Manejador de interrupciones del temporizador 0
void Timer0IntHandler(void) {
    TimerIntClear(TIMER0_BASE, TIMER_TIMA_TIMEOUT);  // Limpia la interrupción del temporizador
    if (blinky) {  // Si el parpadeo está habilitado
        if (state) {  // Si el estado es verdadero (LED encendido)
            GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x00);  // Apaga el LED en PORTN
        } else {  // Si el estado es falso (LED apagado)
            GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x03);  // Enciende el LED en PORTN
        }
        state = !state;  // Cambia el estado del LED para el próximo ciclo
    }
}

// Función principal del programa
int main(void) {
    // Configura la frecuencia del reloj del sistema a 120MHz usando el PLL
    SysCtlClockFreqSet((SYSCTL_XTAL_25MHZ|SYSCTL_OSC_MAIN|SYSCTL_USE_PLL|SYSCTL_CFG_VCO_480), 120000000);

    // Habilita los periféricos necesarios para GPIO
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOA);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOH);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOM);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPION);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOF);

    uart();  // Inicializa la UART
    checking();  // Verifica si los periféricos están listos
    pinConfiguration();  // Configura los pines GPIO

    // Configura el temporizador 0 para generar interrupciones periódicas
    SysCtlPeripheralEnable(SYSCTL_PERIPH_TIMER0);  // Habilita el periférico del temporizador
    TimerConfigure(TIMER0_BASE, TIMER_CFG_PERIODIC);  // Configura el temporizador en modo periódico
    TimerLoadSet(TIMER0_BASE, TIMER_A, 120000000);  // Establece el periodo del temporizador
    TimerIntRegister(TIMER0_BASE, TIMER_A, Timer0IntHandler);  // Registra la función de interrupción del temporizador
    IntEnable(INT_TIMER0A);  // Habilita las interrupciones del temporizador 0A
    TimerIntEnable(TIMER0_BASE, TIMER_TIMA_TIMEOUT);  // Habilita la interrupción por tiempo de espera del temporizador
    TimerEnable(TIMER0_BASE, TIMER_A);  // Habilita el temporizador

    // Bucle infinito
    while(1) {
        printData();  // Llama a la función que imprime datos
        if (UARTCharsAvail(UART0_BASE)) {  // Si hay datos disponibles en la UART
            UARTgets(data, 50);  // Lee los datos recibidos en un buffer
            ind = atoi(data);  // Convierte el string recibido a un número entero
            if (strcmp(data, "standby") == 0) {  // Si el comando recibido es "standby"
                blinky = !blinky;  // Cambia el estado del parpadeo
                state = false;  // Reinicia el estado
                //GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x00);  // Apaga el LED (comentado)
            }
            GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x00);  // Apaga el LED
        }
    }
}

// Función que imprime los datos de los pines GPIO a través de la UART
void printData(void) {
    if (GPIOPinRead(GPIO_PORTM_BASE, 0x01) == 0) {  // Si el pin 0x01 en PORTM está en bajo
        UARTprintf("0\n");  // Imprime "0" en la UART
    } else if (GPIOPinRead(GPIO_PORTM_BASE, 0x02) == 0) {  // Si el pin 0x02 en PORTM está en bajo
        UARTprintf("1\n");  // Imprime "1" en la UART
    } else if (GPIOPinRead(GPIO_PORTM_BASE, 0x04) == 0) {  // Si el pin 0x04 en PORTM está en bajo
        UARTprintf("2\n");  // Imprime "2" en la UART
    } else if (GPIOPinRead(GPIO_PORTH_BASE, 0x01) == 0) {  // Si el pin 0x01 en PORTH está en bajo
        UARTprintf("3\n");  // Imprime "3" en la UART
    } else if (GPIOPinRead(GPIO_PORTH_BASE, 0x02) == 0) {  // Si el pin 0x02 en PORTH está en bajo
        UARTprintf("4\n");
    }
    SysCtlDelay(20000000);
}
