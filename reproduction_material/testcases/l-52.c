/**
 * inline_to_caller
 * Source: Linux Commit 50f9a76ef127367847cf62999c79304e48018cfa
 * 
 * Test case that demonstrates how inlining a function into its caller
 * can expand the pair <user_access_begin, user_access_end> window, breaking uaccess control ranges
 * and potentially leading to security vulnerabilities.
 * 
 * Evidence: When compiled with optimizations, the compiler may inline
 * user_access_begin into its caller function `wrapper', expanding the window
 * during which user memory access is allowed, potentially allowing
 * unintended user memory access.
 * 
 * Requirement: GCC -O1 and above. Clang 14.0 -O1 and above (12.0 -O2 and above).
 * Mitigation: Mark the function calling user_access_begin as noinline to prevent inlining.
 */

#include <stdio.h>

__attribute__((noinline))
void user_access_begin(void) {
    asm volatile("" ::: "memory");
}

// __attribute__((noinline))
static int copy_compat_iovec_from_user(int *p) {
    user_access_begin(); // GCC will hoist this into caller if not noinline
    *p = 123;
    return 0;
}

int wrapper(int *p) {
    return copy_compat_iovec_from_user(p);
}

int main() {
    int x = 0;
    wrapper(&x);
    printf("x=%d\n", x);
}
