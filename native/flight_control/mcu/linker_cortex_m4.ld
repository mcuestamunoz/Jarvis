/* Fase C · C18 — generic Cortex-M4 linker script
 * (`B1-fase-c-cpp-mcu-freestanding-elf`), memory map re-cited for C29
 * (`B1-fase-c-silicon-cited-flash-map`).
 *
 * Desk identity: HGLRC F460 6S V1 stack / HGLRC F405 8S V1 FC / MCU line
 * STM32F405 (from the HGLRC F460 6S V1 stack manual — that manual names
 * the MCU line; it is not a memory-map source and prints no
 * ORIGIN/LENGTH numbers itself).
 *
 * Cited map: ST RM0090 Table 3 (STM32F405xx/07xx, STM32F415xx/17xx),
 * "Memory map":
 *   FLASH  0x08000000-0x080FFFFF  (1 MiB)
 *   SRAM1  0x20000000-0x2001BFFF  (112 KiB)
 *   SRAM2  0x2001C000-0x2001FFFF  (16 KiB)
 * This script uses FLASH 1024K @ 0x08000000 and RAM 128K @ 0x20000000
 * (SRAM1+SRAM2 taken as one contiguous region). CCM RAM (0x10000000,
 * 64 KiB per RM0090) is deliberately NOT included in this MEMORY block
 * this Buy — CCM is not bus-accessible by DMA/some peripherals on this
 * family and folding it into a flat RAM region would be its own,
 * separate, undisclosed simplification; a later Buy can add a distinct
 * CCM region if ever needed.
 *
 * Residual disclosed (C29 IC §0 decision 7): the HGLRC manual does not
 * print the exact ST order-code suffix (e.g. "RG" vs "VG"); RM0090
 * Table 3's 1 MiB FLASH / 192 KiB total SRAM figures apply to the whole
 * STM32F405xx/07xx line regardless of package/suffix, so this citation
 * holds without that suffix. If a later teardown identifies a different
 * ST part on this specific board, this map should be re-cut from that
 * part's own datasheet — never silently reused for a guessed sibling
 * part (e.g. F411, F722).
 *
 * HONESTY: citing ST's own published memory map for the MCU line named
 * on this desk's own FC is NOT the same claim as flashing anything, NOT
 * a claim this .elf boots on the HGLRC stack, and NOT a claim this
 * project is (or replaces) the stack's own shipped Betaflight target
 * ("HGLRCF405V2"). This script still produces an inspectable ELF only —
 * it is never flashed, no OpenOCD/J-Link path exists anywhere in this
 * repo, and no vendor SDK/BSP (STM32Cube, CMSIS device pack) was pulled
 * in to derive these numbers — they come from RM0090's own published
 * table, transcribed by hand.
 *
 * Cited map != flashed != boots on this stack != Betaflight HGLRCF405V2.
 */

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

/* Top of RAM — initial stack pointer, written into vector table word 0 by
 * startup_cortex_m4.c. Stack grows down from here. */
_estack = ORIGIN(RAM) + LENGTH(RAM);

ENTRY(Reset_Handler)

SECTIONS
{
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))   /* must survive --gc-sections */
        . = ALIGN(4);
    } > FLASH

    .text :
    {
        . = ALIGN(4);
        *(.text)
        *(.text*)
        *(.rodata)
        *(.rodata*)
        . = ALIGN(4);
    } > FLASH

    /* C++ exception-handling unwind tables (used by the rung sources'
     * `throw std::invalid_argument(...)` calls) — kept in FLASH, never
     * copied to RAM. */
    .ARM.extab :
    {
        *(.ARM.extab* .gnu.linkonce.armextab.*)
    } > FLASH

    .ARM.exidx :
    {
        __exidx_start = .;
        *(.ARM.exidx* .gnu.linkonce.armexidx.*)
        __exidx_end = .;
    } > FLASH

    _sidata = LOADADDR(.data);

    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } > RAM AT> FLASH

    .bss :
    {
        . = ALIGN(4);
        _sbss = .;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > RAM

    /* Heap start, for the syscalls_stub.c `_sbrk` implementation — grows
     * up from here toward `_estack`, never actually exercised by
     * stub_main.cpp's own code path (no dynamic allocation on that path),
     * only present so the link succeeds if any pulled-in C++ runtime
     * symbol references it. */
    . = ALIGN(4);
    end = .;
    PROVIDE(_end = end);

    /DISCARD/ :
    {
        *(.comment)
        *(.ARM.attributes)
    }
}
