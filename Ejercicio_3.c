
//*****************************************************************************
//
// blinky.c - Simple example to blink the on-board LED.
//
// Copyright (c) 2013-2020 Texas Instruments Incorporated.  All rights reserved.
// Software License Agreement
// 
// Texas Instruments (TI) is supplying this software for use solely and
// exclusively on TI's microcontroller products. The software is owned by
// TI and/or its suppliers, and is protected under applicable copyright
// laws. You may not combine this software with "viral" open-source
// software in order to form a larger program.
// 
// THIS SOFTWARE IS PROVIDED "AS IS" AND WITH ALL FAULTS.
// NO WARRANTIES, WHETHER EXPRESS, IMPLIED OR STATUTORY, INCLUDING, BUT
// NOT LIMITED TO, IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE APPLY TO THIS SOFTWARE. TI SHALL NOT, UNDER ANY
// CIRCUMSTANCES, BE LIABLE FOR SPECIAL, INCIDENTAL, OR CONSEQUENTIAL
// DAMAGES, FOR ANY REASON WHATSOEVER.
// 
// This is part of revision 2.2.0.295 of the EK-TM4C1294XL Firmware Package.
//
//*****************************************************************************

#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>  
#include "inc/hw_memmap.h"
#include "inc/hw_ints.h"
#include "driverlib/debug.h"
#include "driverlib/gpio.h"
#include "driverlib/sysctl.h"
#include "driverlib/timer.h"
#include "driverlib/interrupt.h"
#include "driverlib/uart.h"
#include "driverlib/pin_map.h"
#include "utils/uartstdio.c"

//*****************************************************************************
//
//! \addtogroup example_list
//! <h1>Blinky (blinky)</h1>
//!
//! A very simple example that blinks the on-board LED using direct register
//! access.
//
//*****************************************************************************

//*****************************************************************************
//
// The error routine that is called if the driver library encounters an error.
//
//*****************************************************************************
#ifdef DEBUG
void
__error__(char *pcFilename, uint32_t ui32Line)
{
    while(1);
}
#endif

//*****************************************************************************
//
// Blink the on-board LED.
//
//*****************************************************************************
// Variables globales
bool state = false; // estado del led
void printData(void); // declaración de función para imprimir datos por UART
uint32_t ind = 0; // índice para recibir datos por UART
char data[50]; // buffer de datos recibido por UART
bool clawActivated = false; // indica si la garra está activada

// Configuración del UART
void uart(void) {
    SysCtlPeripheralEnable(SYSCTL_PERIPH_UART0);
    GPIOPinConfigure(GPIO_PA0_U0RX);
    GPIOPinConfigure(GPIO_PA1_U0TX);
    GPIOPinTypeUART(GPIO_PORTA_BASE, 0x03); // Define los pines PA0 y PA1 como UART
    UARTStdioConfig(0, 9600, 120000000); // Configura el UART con 9600 bps y frecuencia de 120 MHz
}

// Configuración de los timers para el parpadeo de los LEDs en el estado de standby
void Timer0IntHandler(void) {
    TimerIntClear(TIMER0_BASE, TIMER_TIMA_TIMEOUT); // Limpia la interrupción
    state = !state; // Cambia el estado de los LEDs
    if (state) {
        GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x01); // LED 0 encendido
        GPIOPinWrite(GPIO_PORTF_BASE, 0x11, 0x01); // LED 3 encendido
    } else {
        GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x00); // LED 0 apagado
        GPIOPinWrite(GPIO_PORTF_BASE, 0x11, 0x00); // LED 3 apagado
    }
}

// Configuración de los timers para la activación del motor de la garra
void Timer1IntHandler(void) {
    TimerIntClear(TIMER1_BASE, TIMER_TIMA_TIMEOUT); // Limpia la interrupción
    if (clawActivated) {
        GPIOPinWrite(GPIO_PORTF_BASE, 0x10, 0x00); // Apaga el motor de la garra
        clawActivated = false;
        TimerDisable(TIMER1_BASE, TIMER_A); // Desactiva el timer 1
    } else {
        GPIOPinWrite(GPIO_PORTF_BASE, 0x10, 0x10); // Activa el motor de la garra
        clawActivated = true;
    }
}

// Check if the peripheral access is enabled.
void checking(void) {
    while (!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOA)) {}
    while (!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOH)) {}
    while (!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOM)) {}
    while (!SysCtlPeripheralReady(SYSCTL_PERIPH_GPION)) {}
    while (!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOF)) {}
}

// Configuración de los pines
void pinConfiguration(void) {
    GPIOPinTypeGPIOOutput(GPIO_PORTN_BASE, 0x03); // Configura PN0 y PN1 como salida
    GPIOPinTypeGPIOOutput(GPIO_PORTF_BASE, 0x11); // Configura PF0 y PF4 como salida
    GPIOPinTypeGPIOInput(GPIO_PORTH_BASE, 0x03); // Configura PH0 y PH1 como entrada
    GPIOPinTypeGPIOInput(GPIO_PORTM_BASE, 0x07); // Configura PM0, PM1 y PM2 como entrada
    GPIOPadConfigSet(GPIO_PORTH_BASE, 0X03, GPIO_STRENGTH_2MA, GPIO_PIN_TYPE_STD_WPU);
    GPIOPadConfigSet(GPIO_PORTM_BASE, 0X07, GPIO_STRENGTH_2MA, GPIO_PIN_TYPE_STD_WPU);
}

// Configuración de los timers
void timerConfiguration(void) {
    SysCtlPeripheralEnable(SYSCTL_PERIPH_TIMER0);
    TimerConfigure(TIMER0_BASE, TIMER_CFG_PERIODIC);
    TimerLoadSet(TIMER0_BASE, TIMER_A, SysCtlClockGet()); // Configuración para 1 segundo
    IntEnable(INT_TIMER0A);
    TimerIntEnable(TIMER0_BASE, TIMER_TIMA_TIMEOUT);
    TimerEnable(TIMER0_BASE, TIMER_A);

    SysCtlPeripheralEnable(SYSCTL_PERIPH_TIMER1);
    TimerConfigure(TIMER1_BASE, TIMER_CFG_ONE_SHOT);
    TimerLoadSet(TIMER1_BASE, TIMER_A, SysCtlClockGet()); // Configuración para 1 segundo
    IntEnable(INT_TIMER1A);
    TimerIntEnable(TIMER1_BASE, TIMER_TIMA_TIMEOUT);
}

// Función principal
int main(void) {
    SysCtlClockFreqSet((SYSCTL_XTAL_25MHZ | SYSCTL_OSC_MAIN | SYSCTL_USE_PLL | SYSCTL_CFG_VCO_480), 120000000); // Configura el reloj del sistema

    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOA);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOH);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOM);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPION);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOF);
    
    uart(); 
    checking();
    pinConfiguration();
    timerConfiguration();

    while (1) {
        printData(); // Imprime los datos de los botones por UART
        if (UARTCharsAvail(UART0_BASE)) { // Si hay datos disponibles por UART
            UARTgets(data, 50); // Lee los datos recibidos
            ind = atoi(data); // Convierte los datos a un número entero
            
            if (ind > 2000) {
                GPIOPinWrite(GPIO_PORTF_BASE, 0x11, 0x0); // Apaga los LEDs PF0 y PF4
                if (!state) {
                    GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x0); // Apaga los LEDs PN0 y PN1
                } else {
                    GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x03); // Enciende los LEDs PN0 y PN1
                }
            } else if (ind < 2000 && ind > 1500) {
                GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x0); // Apaga los LEDs PN0 y PN1
                GPIOPinWrite(GPIO_PORTF_BASE, 0x11, 0x10); // Enciende el LED PF4
            } else if (ind < 1000) {
                GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x03); // Enciende los LEDs PN0 y PN1
                GPIOPinWrite(GPIO_PORTF_BASE, 0x11, 0x11); // Enciende los LEDs PF0 y PF4
            }

            // Si la distancia es menor a 5 cm, activa el motor de la garra
            if (ind < 5) {
                TimerEnable(TIMER1_BASE, TIMER_A); // Activa el temporizador para la interrupción del motor de la garra
            }

            state = !state; // Cambia el estado del LED
        }
    }
}

// Función para imprimir el estado de los botones por UART
void printData(void) {
    if (GPIOPinRead(GPIO_PORTM_BASE, 0x01) == 0) {
        UARTprintf("0\n");
    } else if (GPIOPinRead(GPIO_PORTM_BASE, 0x02) == 0) {
        UARTprintf("1\n");
    } else if (GPIOPinRead(GPIO_PORTM_BASE, 0x04) == 0) {
        UARTprintf("2\n");
    } else {
        UARTprintf("NA\n");
    }
}
