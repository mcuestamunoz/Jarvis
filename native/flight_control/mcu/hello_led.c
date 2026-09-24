/* Fase C · C30 — bare-metal PC13 status-LED toggle
 * (`B1-fase-c-mcu-flash-observable`).
 *
 * WHAT THIS IS: the first human-observable signal on this desk's own
 * silicon — a busy-wait blink on the status LED, driven by bare
 * `volatile` MMIO stores. WHAT THIS IS NOT: DShot, a motor pin, USART,
 * an IRQ/DMA driver, a calibrated millisecond clock, ExpressLRS, or a
 * claim that any real vehicle flies. Flashed LED blink != flying !=
 * DShot != USART live != Betaflight HGLRCF405V2.
 *
 * Pin citation (C30 IC §0 decision 4, locked): Betaflight unified
 * target HGLR-HGLRCF405V2.config, line `resource LED 1 C13` —
 * https://raw.githubusercontent.com/betaflight/unified-targets/master/configs/default/HGLR-HGLRCF405V2.config
 * That is the CURRENT (V2) target for this desk's FC (HGLRC F405 8S
 * V1 / MCU STM32F405). PA8 is deliberately NOT used here — on the same
 * V2 target that pin is `resource MOTOR 6 A08`, a motor-timer pin, not
 * the status LED (an older, non-V2 HGLRCF405 target used PA8 for LED;
 * this board's own current target does not). PB1 (`LED_STRIP`) is also
 * deliberately not used — that pin drives addressable wire LEDs, not
 * the onboard status LED.
 *
 * Register map citation (RM0090, STM32F405xx/07xx reference manual —
 * transcribed by hand, no CMSIS device header, no ST HAL, no vendor
 * SDK pulled in to derive these addresses):
 *   RCC base            0x40023800
 *   RCC_AHB1ENR          0x40023830  (RCC base + 0x30) — bit 2 = GPIOCEN
 *   GPIOC base           0x40020800
 *   GPIOC_MODER          0x40020800  (GPIOC base + 0x00) — pin13 = bits[27:26]
 *   GPIOC_BSRR           0x40020818  (GPIOC base + 0x18) — BS13 = bit13, BR13 = bit29
 *
 * After enabling the GPIOC clock, RM0090 documents a delay between the
 * clock-enable write and the peripheral becoming usable; this file
 * follows the common, RM0090-documented workaround of a dummy read-back
 * of RCC_AHB1ENR immediately after the write.
 *
 * Clock: reset-default HSI 16 MHz. No PLL, no HSE, no SystemInit from a
 * vendor pack this Buy (C30 IC §0 decision 7) — the busy-wait period
 * below is a documented, uncalibrated visible flicker, not a timed
 * millisecond value.
 */
#include "hello_led.h"

#include <stdint.h>

#define RCC_AHB1ENR (*(volatile uint32_t *)0x40023830u)
#define GPIOC_MODER (*(volatile uint32_t *)0x40020800u)
#define GPIOC_BSRR  (*(volatile uint32_t *)0x40020818u)

#define RCC_AHB1ENR_GPIOCEN (1u << 2)

#define GPIOC_MODER_PIN13_MASK   (3u << 26)
#define GPIOC_MODER_PIN13_OUTPUT (1u << 26)

#define GPIOC_BSRR_BS13 (1u << 13) /* set PC13 high */
#define GPIOC_BSRR_BR13 (1u << 29) /* set PC13 low  */

/* Uncalibrated: no claim this produces any particular frequency. At
 * reset-default HSI 16 MHz this is chosen only to be visibly slow
 * enough for a human eye to see toggling, not to hit any target Hz. */
#define HELLO_LED_BUSY_WAIT_ITERATIONS 1600000u

void hello_led_init(void) {
    RCC_AHB1ENR |= RCC_AHB1ENR_GPIOCEN;
    (void)RCC_AHB1ENR; /* dummy read-back — RM0090 clock-enable delay */

    uint32_t moder = GPIOC_MODER;
    moder &= ~GPIOC_MODER_PIN13_MASK;
    moder |= GPIOC_MODER_PIN13_OUTPUT;
    GPIOC_MODER = moder;
}

static void hello_led_busy_wait(uint32_t iterations) {
    /* `counter` is itself volatile (not just the parameter) so every
     * decrement is a real memory access the compiler cannot prove has
     * no observable effect and optimize away — a portable busy-wait
     * idiom, no inline asm. */
    volatile uint32_t counter = iterations;
    while (counter != 0u) {
        counter--;
    }
}

void hello_led_spin(void) {
    for (;;) {
        GPIOC_BSRR = GPIOC_BSRR_BS13;
        hello_led_busy_wait(HELLO_LED_BUSY_WAIT_ITERATIONS);
        GPIOC_BSRR = GPIOC_BSRR_BR13;
        hello_led_busy_wait(HELLO_LED_BUSY_WAIT_ITERATIONS);
    }
}
