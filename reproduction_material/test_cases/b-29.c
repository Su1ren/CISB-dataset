/* UB_ptr_before_obj
 *
 * Source: LLVM Issue #61112
 * Test case for undefined behavior when taking the address of a
 * function parameter and stepping back in memory to read a value
 * that precedes it on the stack.
 * 
 * Evidence: When compiled with optimizations, the compiler may
 * optimize away or misinterpret the memory access, leading to
 * incorrect behavior.
 * 
 * Requirement: GCC 4.8.1+, LLVM/Clang 3.2-12.0.8, -O1 and above, -fno-builtin -DUSE_MEMMGR -I . -m32 -fno-stack-protector
 * Mitigation: Avoid relying on stack layout and use proper parameter passing.
 */

#include <stdio.h>

int get_arg_via_stack(char *p) {
    /* UB: take address of parameter p, step back one `int` slot
       and interpret that memory as the caller's argc. */
    int val = *(int *)(&p - 1);
    return val;
}

int main(int argc, char **argv) {

    /* Pass something as `p` (value not important). We expect get_arg_via_stack
       to read `argc` from the caller's stack. */
    int v = get_arg_via_stack((char *)&argv);
    printf("read value: %d (real argc=%d)\n", v, argc);
    return 0;
}
