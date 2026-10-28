/* HOST ONLY: symbol resolution must never invoke these aborting exports. */
#include <stdlib.h>
#define ABORTING(name) void name(void) { abort(); }
ABORTING(vconf_get_bool)
ABORTING(TEEC_InitializeContext)
ABORTING(TEEC_AllocateSharedMemory)
ABORTING(TEEC_OpenSession)
ABORTING(TEEC_InvokeCommand)
ABORTING(TEEC_CloseSession)
ABORTING(TEEC_ReleaseSharedMemory)
ABORTING(TEEC_FinalizeContext)
