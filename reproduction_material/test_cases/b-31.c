/**
 * time_inst_reorder
 * Source: GCC Bugzilla Bug 50314
 * 
 * Test case that demonstrates how compilers may reorder instructions
 * involving time-critical operations, such as reading timer registers
 * and performing divisions, which can lead to incorrect timing measurements.
 * 
 * Evidence: When compiled with optimizations, the compiler may split 
 * the result_u2 computation into two steps, moving the time-consuming division 
 * after the second timer read, leading to incorrect timing results.
 * 
 * Requirement: AVR GCC/GCC --target=avr 4.3.3 - 4.6.4, plain GCC 4.1.2-4.4.7 -O1 and above.
 * Mitigation: Mark result_u2 as volatile to prevent evaluation splitting/reordering.
 */

#include <stdint.h>

volatile uint16_t TCNT1;  // Timer register (volatile to prevent optimization of reads)

uint32_t MulU2U2(uint16_t a, uint16_t b) {
  return (uint32_t)a * b;
}

int main(void) {

    uint16_t time;
    uint16_t result_u2;
    uint16_t ZERO_DEGC_IN_DEGK = 273;
    uint16_t manPres_u2 = 4505;
    uint16_t airTemp_u2 = 4897;

    asm volatile("cli" ::: "memory");

    time = TCNT1;  // First timer read

    result_u2 = MulU2U2(ZERO_DEGC_IN_DEGK, manPres_u2) / (airTemp_u2 + ZERO_DEGC_IN_DEGK);

    time = TCNT1 - time;  // Second timer read and subtract

    asm volatile("sei" ::: "memory");

    // To trigger delaying the div (due to use site), simulate intervening code or use
    // (in practice, add prints or calls here; compiler may delay div to here in ASM)

    return result_u2;  // Use result to prevent elimination
}
