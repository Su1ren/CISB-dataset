/**
 * UB_merge_causing_unaligned_store
 * Source: GCC Bugzilla Bug 106635
 * 
 * Test case that demonstrates a CISB merging optimization that causes an unaligned store.
 * 
 * Evidence: When compiled with optimizations, the compiler merges two stores into one unaligned store, generating
 * stur x4, [x0, #4] writing 64 bits into dst， causing a runtime crash due to unaligned access.
 * 
 * Requirement: AARCH64 architecture, GCC 8.1.0-12.0.1
 *              CFLAGS = -fpic -Wall -ansi -std=c99 -Wno-variadic-macros -g -Werror -fPIC -shared -Wall -O2 -ggdb3
 * minimal options: -shared and -O2 and above
 * Mitigation: use volatile temporary variables to prevent optimization.
 */

typedef unsigned long long u64;
typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned long addr_t;
#define OPCODE_RREG 0x1

void CWLCollectReadRegData(u32* dst,u16 reg_start, u32 reg_length,u32* total_length, addr_t status_data_base_addr) {
  u32 data_length=0;
  {
    //opcode
    *dst++ = (OPCODE_RREG<<27)|(reg_length<<16)|(reg_start*4);
    data_length++;
 
    //data
    u32 temp_32 = (u32)status_data_base_addr; // fix compiler optimization -O2 bug:  stur  x4, [x0, #4]
    // volatile u32 temp_32 = (u32)status_data_base_addr;
    *dst++ = temp_32;
    data_length++;
 
    if(sizeof(addr_t) == 8) {
      *dst++ = (u32)(((u64)status_data_base_addr)>>32);
      data_length++;
    } else {
      *dst++ = 0;
      data_length++;
    }
    //alignment
    *dst = 0;
    data_length++;
 
    *total_length = data_length;
  }
}

int main() {
    u32 buffer[10];
    u32 total_length = 0;
    addr_t status_data_base_addr = 0x123456789ABCDEF0;

    CWLCollectReadRegData(buffer, 0, 4, &total_length, status_data_base_addr);

    return 0;
}