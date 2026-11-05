#include <stdio.h>
#include <stdlib.h>
#define PSXBIOS_LOG(...) do { if (getenv("BIOSLOG")) fprintf(stderr, __VA_ARGS__); } while (0)
