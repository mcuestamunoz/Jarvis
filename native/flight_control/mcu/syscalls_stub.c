/* Fase C · C18 — minimal newlib syscall stubs
 * (`B1-fase-c-cpp-mcu-freestanding-elf`).
 *
 * HONESTY: these are OUR generic stubs, not a vendor SDK. They exist only
 * so the linker can resolve symbols newlib/libstdc++ reference (e.g. the
 * C++ exception-handling runtime's allocator, transitively, via `malloc`
 * -> `_sbrk`) when linking a full freestanding executable — not because
 * `stub_main.cpp`'s own code path calls any of them at runtime. No
 * semihosting, no UART, no real I/O of any kind: `_write`/`_read`/etc.
 * are no-op/error stubs, matching IC §0 decision 8's "minimal syscall
 * stubs" choice (a) over disabling C++ exceptions.
 */

#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/stat.h>
#include <sys/types.h>

extern uint32_t end; /* from linker_cortex_m4.ld — first free heap byte */
extern uint32_t _estack;

static uint8_t *heap_end = (uint8_t *)&end;

void *_sbrk(ptrdiff_t incr) {
    uint8_t *prev_heap_end = heap_end;
    if (heap_end + incr > (uint8_t *)&_estack) {
        errno = ENOMEM;
        return (void *)-1;
    }
    heap_end += incr;
    return prev_heap_end;
}

int _write(int fd, const char *buf, int len) {
    (void)fd;
    (void)buf;
    return len; /* pretend it succeeded; no UART/semihosting here */
}

int _read(int fd, char *buf, int len) {
    (void)fd;
    (void)buf;
    (void)len;
    return 0; /* EOF */
}

int _close(int fd) {
    (void)fd;
    return -1;
}

int _lseek(int fd, int offset, int whence) {
    (void)fd;
    (void)offset;
    (void)whence;
    return 0;
}

int _fstat(int fd, struct stat *st) {
    (void)fd;
    st->st_mode = S_IFCHR;
    return 0;
}

int _isatty(int fd) {
    (void)fd;
    return 1;
}

void _exit(int status) {
    (void)status;
    while (1) {
    }
}

int _kill(int pid, int sig) {
    (void)pid;
    (void)sig;
    errno = EINVAL;
    return -1;
}

int _getpid(void) {
    return 1;
}
