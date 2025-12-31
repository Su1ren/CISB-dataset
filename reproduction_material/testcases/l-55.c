/**
 * DSE-memcpy
 * Source: Linux Commit 49705c4ab324654a7038fc843255140730477e04
 * 
 * Test case for potential issues of eliminating memcpy on const volatile globals.
 * The case is specific to BPF context, where globals will be rewritten by the verifier at load time.
 * 
 * Evidence: When compiled with optimizations, the compiler may optimize away the memcpy,
 * leading to incorrect behavior when the global is expected to be read at runtime.
 * 
 * Requirement: LLVM/Clang 14.0.0, -O1 and above, -target bpf.
 * Mitigation: Use a temporary pointer variable and a barrier to prevent optimization.
 */

#include <stdlib.h>
#define ETH_ALEN 1024

const volatile char tx_mac_addr[ETH_ALEN];

typedef struct eth {
    char h_source[ETH_ALEN];
}eth;

int xdp_redirect_map_egress(int *ctx) {
    eth *X = (eth*)malloc(sizeof(eth));
	__builtin_memcpy(X->h_source, (const char *)tx_mac_addr, ETH_ALEN);
    // char* mac_addr = (char*)tx_mac_addr;
    // barrier_var(mac_addr);
	// __builtin_memcpy(X->h_source, mac_addr, ETH_ALEN);

	return 0;
}

int main() {
    int x = 5;
    return xdp_redirect_map_egress(&x);
}