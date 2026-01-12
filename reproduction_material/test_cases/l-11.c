/**
 * l-11
 * Source: Kernel Commit 543e8669ed9bfb30545fd52bc0e047ca4df7fb31
 * 
 * Test case that demonstrates a CISB zero-initialization optimization that causes padding uninitialized data leak. Furthermore, the memcpy copies the entire struct including the uninitialized padding bytes to user space, leading to potential data leakage.
 * 
 * Evidence: With O1 and above optimizations, the compiler optimizes the zero-initialization of struct info by merging it with memcpy, only initializing data field, leaving the padding bytes uninitialized. 
 * 
 * Requirement: GCC 4.7.1-4.9.4 -O1 and above.
 * Mitigation: use memset to explicitly zero-initialize the struct instead of relying on aggregate initialization.
 */

#include <stdint.h>
#include <string.h>

/*
 * sizeof(struct info) == 16
 * only 12 bytes are initialized
 */
struct info {
    uint64_t a;   // 8 bytes
    uint32_t b;   // 4 bytes
    /* 4-byte padding here */
};

/*
 * simulate ioctl handler
 */
void leak(uint8_t *user)
{
    struct info dev_info = {};  // expecting zero-initialize entire struct
    // struct info dev_info;
    // memset(&dev_info, 0, sizeof(dev_info)); // fix compiler optimization -O1 bug: memcpy copies uninitialized padding
    /*
     * simulate copy_to_user()
     * in actual kernel code:
     *   copy_to_user(arg, &dev_info, sizeof(dev_info))
     */
    memcpy(user, &dev_info, sizeof(dev_info)); // 16 bytes copied, 4 bytes uninitialized at end
}