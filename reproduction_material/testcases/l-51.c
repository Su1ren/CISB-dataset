/**
 * DB_type_demotion
 * Source: Linux Commit 3751c3d34cd5a750c86d1c8eaf217d8faf7f9325
 * 
 * Test case for type demotion issues in database code leading to
 * incorrect calculations due to signed to unsigned conversions.
 * 
 * Evidence: When compiled on a 32-bit system, the calculation in function
 * will demote s64 to s32, then promote to u32 when added to u64.
 * The execution result is NOT reproduced, but the demotion was reported
 * to introduce a bug in Linux kernel code, observed in this test case as well.
 * 
 * Requirement: GCC/Clang -O1 and above on a 32-bit architecture, 64-bit sometimes fails.
 * Mitigation: Do the multiplication before the division.
 */
#include <stdint.h>

int64_t test(int clk_rate) {
    int64_t adj = 0;
    uint64_t ns  = 1000000000000LL;

    adj += -(2 * (1000000000 / clk_rate));
    // adj += -((2 * 1000000000LL) / clk_rate);

    ns += adj;

    return ns;
}
