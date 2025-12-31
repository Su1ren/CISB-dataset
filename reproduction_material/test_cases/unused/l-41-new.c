/**
 * l-41-new.c
 * Source: Linux Commmit eab6870fee877258122a042bfd99ee7908c40280
 * 
 * Test case for common subexpression elimination (CSE) of
 * array_index_mask_nospec function calls leading to potential
 * speculative execution vulnerabilities.
 * 
 * Evidence: When compiled with GCC -O1 and above (low version, -O2 for higher), the two calls to
 * array_index_mask_nospec in function f may be optimized to a single call.
 * 
 * Requirement: On lower GCC versions -O1 (higher -O2), the CSE optimization occurs.
 * Mitigation: Use volatile asm to prevent CSE.
 */

#include <stdio.h>
#include <stdint.h>

/* test.c - non-volatile version */
static inline unsigned long array_index_mask_nospec(unsigned long index,
                                     unsigned long size) {
    unsigned long mask;
    /* 非 volatile asm，编译器可能认为可重复利用结果 */
    asm volatile ("cmp %1,%2; sbb %0,%0;"
        : "=r" (mask)
        : "g" (size), "r" (index)
        : "cc");
    return mask;
}

/* 函数演示：在两个分支中分别调用 array_index_mask_nospec */
int f(unsigned long idx, unsigned long size) {
    unsigned long idx1, idx2;

    if (idx < size) {
        idx1 = idx & array_index_mask_nospec(idx, size);
        if (idx1 == 0)
            return 1;
    }

    /* 加入一段不会被编译器理解为修改 idx/size 的代码
       （例如对外部 volatile 读取）会减少被优化的几率。
       这里故意放空，以便观察编译器是否合并 */
    (void)0;

    if (idx < size) {
        idx2 = idx & array_index_mask_nospec(idx, size);
        if (idx2 == 0)
            return 2;
    }

    return 0;
}