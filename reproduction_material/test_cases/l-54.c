/**
 * env_memset_in_stream_mode
 * Source: Linux Commit d6da04b6fbabf4b464bfe29e34ff10c62024d1e4
 * 
 * Test case that demonstrates how compilers may optimize memset calls
 * into vectorized stores or library calls that use FP/SIMD instructions,
 * which may not be allowed in certain CPU modes (e.g. ARM stream mode).
 * 
 * Evidence: When compiled with high optimizations, the compiler replaces
 * memset calls with vectorized stores or calls to memcpy/memset that
 * use FP/SIMD instructions.
 * 
 * Requirement: AARCH64 GCC from 11.1.0 -O2 and above. Clang from 9.0.0 -O1 and above.
 * Mitigation: Use manual byte-wise clearing with compiler barriers to
 * prevent such optimizations.
 */

#include <string.h>
#include <stddef.h>
#include <stdio.h>

void *memset_wrapper(void *p, int c, size_t n) {
    // VERSION A: use standard memset (the compiler may replace with
    // vectorized stores / library calls that use FP/SIMD instructions)
    return memset(p, c, n);
}

void manual_clear_volatile(char *p, size_t n) {
    // VERSION B: explicitly zero with byte stores + asm barrier to prevent
    // the compiler recognising/optimizing this into vectorized sequence.
    size_t i;
    for (i = 0; i < n; ++i) {
        p[i] = 0;
        /* prevent compiler turning this into a memset/memcpy/vector store */
        __asm__ ("" : "+m" (p[i]) : : "memory");
    }
}

int main(void) {
    /* allocate a reasonably large buffer so compilers try to vectorize */
    enum { SZ = 256 };
    static char buf1[SZ];
    static char buf2[SZ];

    /* Call the two variants so they both appear in the assembly */
    memset_wrapper(buf1, 0, SZ);
    manual_clear_volatile(buf2, SZ);

    /* touch so optimizer keeps buffers alive */
    printf("%d %d\n", buf1[0], buf2[0]);
    return 0;
}
