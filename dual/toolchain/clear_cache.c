#include <stdint.h>
#include <stddef.h>
void __clear_cache(void *start, void *end) {
  uint64_t ctr; __asm__ volatile("mrs %0, ctr_el0" : "=r"(ctr));
  uintptr_t dline = 4u << ((ctr >> 16) & 15), iline = 4u << (ctr & 15);
  uintptr_t s = (uintptr_t)start, e = (uintptr_t)end, a;
  if (!(ctr & (1u << 28)))
    for (a = s & ~(dline - 1); a < e; a += dline) __asm__ volatile("dc cvau, %0" :: "r"(a) : "memory");
  __asm__ volatile("dsb ish" ::: "memory");
  if (!(ctr & (1u << 29)))
    for (a = s & ~(iline - 1); a < e; a += iline) __asm__ volatile("ic ivau, %0" :: "r"(a) : "memory");
  __asm__ volatile("dsb ish\n\tisb" ::: "memory");
}
