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

#ifdef DEBUG
void __error__(char *pcFilename, uint32_t ui32Line) {
    while(1);
}
#endif

bool state = false;
bool blinky = false;
void printData(void);
void Timer0IntHandler(void);

void uart(void) {
    SysCtlPeripheralEnable(SYSCTL_PERIPH_UART0);
    GPIOPinConfigure(GPIO_PA0_U0RX);
    GPIOPinConfigure(GPIO_PA1_U0TX);
    GPIOPinTypeUART(GPIO_PORTA_BASE, 0x03);
    UARTStdioConfig(0, 9600, 120000000);
}

void checking(void) {
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOA)) {}
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOH)) {}
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOM)) {}
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPION)) {}
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOF)) {}
}

void pinConfiguration(void) {
    GPIOPinTypeGPIOOutput(GPIO_PORTN_BASE, 0x03);
    GPIOPinTypeGPIOOutput(GPIO_PORTF_BASE, 0x11);
    GPIOPinTypeGPIOInput(GPIO_PORTH_BASE, 0x03);
    GPIOPinTypeGPIOInput(GPIO_PORTM_BASE, 0x07);
    GPIOPadConfigSet(GPIO_PORTH_BASE, 0X03, GPIO_STRENGTH_2MA, GPIO_PIN_TYPE_STD_WPU);
    GPIOPadConfigSet(GPIO_PORTM_BASE, 0X07, GPIO_STRENGTH_2MA, GPIO_PIN_TYPE_STD_WPU);
}

void Timer0IntHandler(void) {
    TimerIntClear(TIMER0_BASE, TIMER_TIMA_TIMEOUT);
    if (blinky) {
        if (state) {
            GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x00);
        } else {
            GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x03);
        }
        state = !state;
    }
}

int main(void) {
    SysCtlClockFreqSet((SYSCTL_XTAL_25MHZ|SYSCTL_OSC_MAIN|SYSCTL_USE_PLL|SYSCTL_CFG_VCO_480), 120000000);
    
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOA);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOH);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOM);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPION);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOF);
    
    uart(); 
    checking();
    pinConfiguration();

    SysCtlPeripheralEnable(SYSCTL_PERIPH_TIMER0);
    TimerConfigure(TIMER0_BASE, TIMER_CFG_PERIODIC);
    TimerLoadSet(TIMER0_BASE, TIMER_A, 120000000);
    TimerIntRegister(TIMER0_BASE, TIMER_A, Timer0IntHandler);
    IntEnable(INT_TIMER0A);
    TimerIntEnable(TIMER0_BASE, TIMER_TIMA_TIMEOUT);
    TimerEnable(TIMER0_BASE, TIMER_A);

    while(1) {
        printData();
        if (UARTCharsAvail(UART0_BASE)) {
            UARTgets(data, 50);
            ind = atoi(data);
            if (strcmp(data, "standby") == 0) {
                blinky = !blinky;
                state = false;
                //GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x00);
            }
            GPIOPinWrite(GPIO_PORTN_BASE, 0x03, 0x00);
        }
    }
}

void printData(void) {
    if (GPIOPinRead(GPIO_PORTM_BASE, 0x01) == 0) {
        UARTprintf("0\n");
    } else if (GPIOPinRead(GPIO_PORTM_BASE, 0x02) == 0) {
        UARTprintf("1\n");
    } else if (GPIOPinRead(GPIO_PORTM_BASE, 0x04) == 0) {
        UARTprintf("2\n");
    } else if (GPIOPinRead(GPIO_PORTH_BASE, 0x01) == 0) {
        UARTprintf("3\n");
    } else if (GPIOPinRead(GPIO_PORTH_BASE, 0x02) == 0) {
        UARTprintf("4\n");
    }
    SysCtlDelay(20000000);
}
