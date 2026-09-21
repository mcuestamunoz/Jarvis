/* Fase C · C18 — generic Cortex-M4 minimal startup
 * (`B1-fase-c-cpp-mcu-freestanding-elf`).
 *
 * HONESTY: this vector table + Reset_Handler are OURS — generic, not any
 * vendor's BSP/CMSIS device pack. This file is never flashed to a board
 * in this repo; it exists so `linker_cortex_m4.ld` has a real .isr_vector
 * to place and a real Reset_Handler to set as ENTRY, so the produced .elf
 * is inspectable (objdump/readelf show a genuine ARM entry point and
 * vector table), not a claim that this image has run or would run
 * correctly on real silicon. No GPIO, no peripheral register access, no
 * interrupt handling beyond a do-nothing default loop.
 */

#include <stdint.h>

extern uint32_t _estack;
extern uint32_t _sidata;
extern uint32_t _sdata;
extern uint32_t _edata;
extern uint32_t _sbss;
extern uint32_t _ebss;

extern int main(void);

void Reset_Handler(void);
static void Default_Handler(void);

/* Minimal ARMv7-M system exception set (no vendor external IRQs modeled —
 * this is not any named board's interrupt layout). Every entry but Reset
 * points at Default_Handler, which just loops forever; nothing here ever
 * fires since this image is never flashed/run on real hardware. */
void NMI_Handler(void) __attribute__((weak, alias("Default_Handler")));
void HardFault_Handler(void) __attribute__((weak, alias("Default_Handler")));
void MemManage_Handler(void) __attribute__((weak, alias("Default_Handler")));
void BusFault_Handler(void) __attribute__((weak, alias("Default_Handler")));
void UsageFault_Handler(void) __attribute__((weak, alias("Default_Handler")));
void SVC_Handler(void) __attribute__((weak, alias("Default_Handler")));
void DebugMon_Handler(void) __attribute__((weak, alias("Default_Handler")));
void PendSV_Handler(void) __attribute__((weak, alias("Default_Handler")));
void SysTick_Handler(void) __attribute__((weak, alias("Default_Handler")));

typedef void (*VectorEntry)(void);

__attribute__((section(".isr_vector"), used))
const VectorEntry g_vector_table[16] = {
    (VectorEntry)&_estack,   /* 0:  initial stack pointer */
    Reset_Handler,           /* 1:  Reset */
    NMI_Handler,              /* 2:  NMI */
    HardFault_Handler,        /* 3:  HardFault */
    MemManage_Handler,        /* 4:  MemManage (Cortex-M4 has an MPU fault) */
    BusFault_Handler,         /* 5:  BusFault */
    UsageFault_Handler,       /* 6:  UsageFault */
    0,                        /* 7:  reserved */
    0,                        /* 8:  reserved */
    0,                        /* 9:  reserved */
    0,                        /* 10: reserved */
    SVC_Handler,              /* 11: SVCall */
    DebugMon_Handler,         /* 12: Debug Monitor */
    0,                        /* 13: reserved */
    PendSV_Handler,           /* 14: PendSV */
    SysTick_Handler,          /* 15: SysTick */
};

void Reset_Handler(void) {
    /* Copy .data initializers from FLASH (LMA) to RAM (VMA). */
    uint32_t *src = &_sidata;
    uint32_t *dst = &_sdata;
    while (dst < &_edata) {
        *dst++ = *src++;
    }

    /* Zero .bss. */
    dst = &_sbss;
    while (dst < &_ebss) {
        *dst++ = 0;
    }

    /* No __libc_init_array() call: jarvis_fc has no global C++ objects
     * with non-trivial (runtime) constructors — confirmed in the C18
     * implementation report — so static-init is not needed for
     * stub_main.cpp's own code path. */

    (void)main();

    /* main() is not expected to return on this freestanding target; if it
     * somehow does, idle forever rather than fall off into undefined
     * memory. */
    while (1) {
    }
}

static void Default_Handler(void) {
    while (1) {
    }
}
