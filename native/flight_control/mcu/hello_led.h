/* Fase C · C30 — bare-metal PC13 status-LED toggle
 * (`B1-fase-c-mcu-flash-observable`).
 *
 * See hello_led.c for the full register-map citation and honesty
 * statement. No CMSIS, no HAL, no USART, no motor pins — this header
 * declares exactly two functions.
 */
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Enables the GPIOC peripheral clock (RCC_AHB1ENR bit 2) and configures
 * PC13 as a general-purpose push-pull output (GPIOC_MODER pin13 = 01).
 * Call once before hello_led_spin(). */
void hello_led_init(void);

/* Toggles PC13 forever via GPIOC_BSRR, separated by an uncalibrated
 * busy-wait delay — a visible flicker at reset-default HSI 16 MHz, not
 * a timed/calibrated period. Never returns. */
void hello_led_spin(void) __attribute__((noreturn));

#ifdef __cplusplus
}
#endif
