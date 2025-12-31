/* register_spill
 * Source: Linux Commit 2c88c742d011707b55da7b54b06a030c6f57233f
 * 
 * Test case that demonstrates how register spilling can lead to potential
 * information leakage or further vulnerabilities in the presence of
 * speculative execution attacks. If an attacker can exploit speculative execution,
 * they may be able to read or overwrite these spilled values,
 * leading to information leakage or control flow hijacking.
 * 
 * Evidence: When compiled under register pressure, the compiler may spill
 * sensitive values to the stack across function calls. 
 * 
 * Requirement: GCC 9 lower, -O0 for this test case. -marm -mcpu=cortex-a8 -fno-omit-frame-pointer
 * Mitigation: Use spill disabled register (such as r9 in ARM) to load sensitive values.
 */

typedef void (*fn_t)(void);

int victim(fn_t f) {
    /* "secret" is used before and after the call -> compiler must keep its value alive
       across the call. With register pressure the compiler may spill it to the stack. */
    int secret = 0x12345678;

    /* create register pressure / stack usage to encourage spilling */
    int buf[32];
    for (int i = 0; i < 32; ++i) buf[i] = i;

    /* call an external function - value must survive across this call */
    f();

    /* use secret after the call -> requires it to be restored if spilled */
    return secret + buf[0];
}
