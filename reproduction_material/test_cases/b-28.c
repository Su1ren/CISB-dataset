/**
 * UB_local_addr
 * Source: GCC Bugzilla Bug 48623
 * 
 * Test case for undefined behavior when taking the address of a local
 * variable and using it in inline assembly.
 * 
 * Evidence: When compiled with GCC -O2, the whole function is optimized away,
 * leading to incorrect behavior when the inline assembly tries to access the
 * address of the local variable.
 * 
 * Requirement: GCC 4.5.3 and above, -Os/O1 and above.
 * Mitigation: Use a separate pointer variable and inline assembly to confuse the compiler.
*/

#define inline inline __attribute__((always_inline))

#define CONFIG_KERNEL_STACK_ORDER 0
#define PAGE_SIZE 4096
#define THREAD_SIZE ((1 << CONFIG_KERNEL_STACK_ORDER) * PAGE_SIZE)

#define preempt_count() (current_thread_info()->preempt_count)
#define sub_preempt_count(val) do { preempt_count() -= (val); } while (0)

struct thread_info {
	int preempt_count;
};

static inline struct thread_info *current_thread_info(void) {
    struct thread_info *ti;
    unsigned long mask = THREAD_SIZE - 1;

    ti = (struct thread_info *) (((unsigned long) &ti) & ~mask);
    return ti;
    // struct thread_info *ti;
    // unsigned long mask = THREAD_SIZE - 1;
    // void *p;
    // asm volatile ("" : "=r" (p) : "0" (&ti));
    // ti = (struct thread_info *) (((unsigned long) p) & ~mask);
    // return ti;
}

static void __local_bh_enable(unsigned int cnt) {
	sub_preempt_count(cnt);
}

void dummy_usage1(unsigned int cnt) {
  __local_bh_enable(cnt);
}

int main() {
    dummy_usage1(1);
    return 0;
}