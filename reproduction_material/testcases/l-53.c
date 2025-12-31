/**
 * reorder_evaluation
 * Source: Linux Commit 3066820034b5dd4e89bd74a7739c51c2d6f5e554
 * 
 * Test case for compiler reordering evaluations in one condition statement
 * leading to lockdep RCU checking bug.
 * 
 * Evidence: When compiled with optimizations, the compiler may merge debug_lockdep_rcu_enabled_old() evaluation
 * and the condition c in RCU_LOCKDEP_WARN_OLD macro in a way that leads to incorrect behavior.
 * 
 * Requirement: GCC/Clang, -O1 and above.
 * Mitigation: Change the macro to evaluate the condition first and use READ_ONCE for volatile access.
 */

#include <stdio.h>

/* simulate globals used in kernel */
int rcu_scheduler_active = 1;
int debug_locks = 0;          /* NON-VOLATILE version (old) */
int current_lockdep_recursion = 0;

/* READ_ONCE implementation via volatile cast */
#define READ_ONCE(x) (*(volatile typeof(x) *)&(x))

/* simulate lock_is_held() which returns 1 if lockdep disabled (safe) */
int lock_is_held_sim(void) {
    /* if debug_locks==0 pretend lock_is_held plays it safe and returns 1 */
    if (debug_locks == 0)
        return 1;
    return 0; /* simplified */
}

/* old debug_lockdep_rcu_enabled: uses plain debug_locks (non-volatile) */
static int debug_lockdep_rcu_enabled_old(void) {
    return rcu_scheduler_active != 0 && debug_locks && current_lockdep_recursion == 0;
}

/* debug_lockdep_rcu_enabled using READ_ONCE(debug_locks) */
static int debug_lockdep_rcu_enabled_readonce(void) {

    return rcu_scheduler_active != 0 && READ_ONCE(debug_locks) && current_lockdep_recursion == 0;
}

/* OLD macro ordering: check enabled() first, then expression c */
#define RCU_LOCKDEP_WARN_OLD(c, s)          \
    do {                                    \
        if (debug_lockdep_rcu_enabled_old() && (c)) { \
            /* warn */                      \
        }                                   \
    } while (0)

/* FIXED macro ordering + READ_ONCE: evaluate c first, then check enabled */
#define RCU_LOCKDEP_WARN_FIXED(c, s)        \
    do {                                    \
        if ((c) && debug_lockdep_rcu_enabled_readonce()) { \
            /* warn */                      \
        }                                   \
    } while (0)

/* callers */
void caller_old(int c) {
    RCU_LOCKDEP_WARN_OLD(c, "old");
}

void caller_fixed(int c) {
    RCU_LOCKDEP_WARN_FIXED(c, "fixed");
}

/* Small main to avoid optimizer removing functions when LTO not used */
int main(void) {

    caller_old(0);
    caller_old(1);
    caller_fixed(0);
    caller_fixed(1);
    printf("done\n");
    return 0;
}
