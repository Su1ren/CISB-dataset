/**
 * speculative_code_motion
 * Source: Linux Commit 03d4d13fab3fa75fbcf09bced5e3c8acf1622969
 * 
 * Test case that demonstrates how speculative code motion can lead to
 * temporarily out-of-bounds memory access, violating eBPF verifier safety guarantees.
 * Furthermore, this can lead to potential Spectre-like transient execution attacks.
 * 
 * Evidence: When compile with optimization and BPF target, the compiler may speculatively
 * execute the addition of filepart_length to payload before confirming that filepart_length
 * is within bounds, leading to temporarily out-of-bounds access.
 * The program insert a revert path with speculation on branches.
 * 
 * Requirement: LLVM/Clang 11 or lower with -O1 or higher --target=bpf. libbpf is needed.
 * Mitigation: Use barrier_var on filepart_length to prevent speculative code motion.
 */

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

#define MAX_PATH 256

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key, __u32);
    __type(value, __u8 [1024]);
    __uint(max_entries, 1);
} test_map SEC(".maps");

SEC("prog")
int bpf_test(void *ctx) {
    __u32 key = 0;
    __u8 *payload = bpf_map_lookup_elem(&test_map, &key);
    if (!payload) return 0;

    int filepart_length = bpf_probe_read_str(payload + MAX_PATH, MAX_PATH + 1, payload);

    if (filepart_length <= MAX_PATH) {
        // barrier_var(filepart_length);
        payload += filepart_length;
    }
    // prevent DCE of payload usage
    __u8 val = payload[0];
    bpf_printk("val: %u", val);

    return 0;
}