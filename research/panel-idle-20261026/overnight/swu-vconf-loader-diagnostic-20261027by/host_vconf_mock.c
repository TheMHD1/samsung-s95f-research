#include <stdlib.h>
__attribute__((visibility("default"))) int vconf_get_bool(const char *key,int *value)
{
    (void)key;(void)value;abort(); /* Any accidental call fails the host process. */
}
