/**
 * UB_four_byte-wise_unaligned
 * Source: GCC Bugzilla Bug 43774
 * 
 * Test case for unaligned access when a structure with a flexible array member
 * is placed at an unaligned address, leading to potential undefined behavior
 * when accessing the flexible array member.
 * 
 * Evidence: When compiled with GCC -O2, the strlen function is optimized to use 4-byte reads,
 * which can lead to unaligned memory access if the structure is not properly aligned.
 * 
 * Requirement: GCC 4.1.2-4.4 -O2 and above. Valgrind can be used to detect the out-of-bounds access.
 * Mitigation: comment out the offset member in struct X to avoid unaligned access.
 */

#include <string.h>
#include <sys/mman.h>

typedef struct {
    int offset; // bug disappears if offset removed
    char data[];
} X;

int main() {
    char *p = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

    char *end = p + 4096 - 5;
    strcpy(end, "1234");

    X *x = (X *)end;
    return strlen(x->data);   // <-- GCC -O2 replaces by builtin strlen (word read!)
}
