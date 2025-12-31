/**
 * tail_call_opti
 * Source: Linux Commit a9a3ed1eff3601b63aea4fb462d8b3b92c7c1e7e
 * 
 * Test case that demonstrates how tail-call optimization can lead to
 * stack canary checks semantics disruption.
 * 
 * Evidence: When compiled with optimizations, the compiler may tail-call
 * optimize the call to a noreturn function into a jump, skipping the stack canary
 * check that would normally occur on function exit, leading to software defense vulnerabilities.
 * 
 * Requirement: GCC 10, -O1 or higher. Clang 14 -O1 and above. -fstack-protector -fno-omit-frame-pointer enabled.
 * Mitigation: Mark the tail call function as noinline to prevent tail-call optimization.
 */

#include <stdint.h>

/* pretend kernel stack-guard object (normally provided by crt / kernel) */
volatile uintptr_t __stack_chk_guard;

/* function that initializes the global canary (in kernel: boot_init_stack_canary) */
void boot_init_stack_canary(void) {
    /* write to the global guard (simulate kernel init) */
    __stack_chk_guard = 0xdeadbeefcafebabeUL;
}

/* a never-returning "entry" function (in kernel: cpu_startup_entry) */
__attribute__((noreturn))
// __attribute__((noinline))
void cpu_startup_entry(void) {
    /* infinite loop to model 'does not return' behaviour */
    for (;;);
}

/* the function that triggers the problem: it (1) initializes canary, then
 * (2) calls another function as its last action.
 * gcc-10 may tail-call optimize the cpu_startup_entry call into a jmp.
 */
__attribute__((noinline))
void start_secondary(void) {
    /* stack-protector will make compiler load __stack_chk_guard into stack here */
    boot_init_stack_canary();

    /* last call -- candidate for tail-call optimization */
    cpu_startup_entry();

    /* never reached */
}