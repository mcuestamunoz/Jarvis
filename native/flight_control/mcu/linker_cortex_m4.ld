/* Fase C · C18 — generic Cortex-M4 linker script
 * (`B1-fase-c-cpp-mcu-freestanding-elf`).
 *
 * HONESTY: this is a FICTIONAL, generic memory map, not any named board's
 * silicon. FLASH at 0x00000000 and RAM at 0x20000000 are the ARM-
 * architected default Cortex-M memory regions (Code region and SRAM
 * region per the ARMv7-M architecture reference manual) — deliberately
 * NOT a vendor's remapped boot address (many real boards remap flash to
 * e.g. 0x08000000; this script does not claim to be any of them). Sizes
 * (256 KiB FLASH / 64 KiB RAM) are a round, illustrative "class" size,
 * not sourced from any real part's datasheet. This script produces an
 * inspectable ELF only — it is never flashed, and nothing in this repo
 * claims this image boots on real hardware.
 */

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x00000000, LENGTH = 256K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 64K
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
