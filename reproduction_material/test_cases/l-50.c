/**
 * bool_promotion
 * Source: Linux Commit 63d78b7e8ca2d0eb8c687a355fa19d01b6fcc723
 * 
 * Test case that demonstrates how compilers may optimize boolean
 * expressions by promoting them to integer comparisons, which can
 * expand register range to unspecified values, defeating BPF verifier
 * checks.
 * 
 * Evidence: When compiled with optimizations, the compiler transforms
 * triple-valued boolean logic into only return do_bind(); which promotes
 * the boolean to an integer, expanding its range.
 * 
 * Requirenment: LLVM/Clang 17, BPF target, -O1 and above.
 * Mitigation: specify the do_bind functions as weak symbols to prevent
 * the compiler from optimizing the boolean logic.
 */

#include <stdint.h>

__attribute__((noinline))
// __attribute__((weak))
int do_bind(void *ctx) {
    if ((uintptr_t)ctx & 1)
        return 0;
    return 1;
}

int connect_v4_prog(void *ctx) {
    
    return do_bind(ctx) ? 1 : 0;
}
