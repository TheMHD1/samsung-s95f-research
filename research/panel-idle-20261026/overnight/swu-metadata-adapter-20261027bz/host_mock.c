/* HOST-ONLY dynamic-binding fixture. No device, socket, TEE or file calls. */
#include <stdint.h>
#include <stddef.h>
uint32_t TEEC_InitializeContext(const char *name,uint32_t *context) {
    if(name || *context) return 1;
    *context=0x11223344; return 0;
}
uint32_t TEEC_AllocateSharedMemory(uint32_t *context,uint32_t *shared) {
    if(*context!=0x11223344 || shared[1]!=65536 || shared[2]!=3) return 2;
    shared[0]=0x1000; return 0;
}
uint32_t TEEC_OpenSession(uint32_t *context,uint32_t *session,const uint8_t *uuid,
                         uint32_t login,const void *data,void *operation,uint32_t *origin) {
    *origin=3;
    if(*context!=0x11223344 || login || data || operation || uuid[0]!=0x21 || uuid[15]!=1) return 3;
    *session=0x55667788; return 0;
}
uint32_t TEEC_InvokeCommand(uint32_t *session,uint32_t command,uint32_t *operation,uint32_t *origin) {
    const uint32_t types[3]={0x01010d0d,0x00020e0d,0x0000020e};
    *origin=4;
    if(*session!=0x55667788 || command>2 || operation[0] || operation[1]!=types[command] || operation[14]) return 4;
    operation[14]=0x12345678; /* exact backend tail write at offset56 */
    if(command==1)operation[8]=4016;
    if(command==2)operation[5]=16;
    return 0;
}
void TEEC_CloseSession(uint32_t *session) { *session=0; }
void TEEC_ReleaseSharedMemory(uint32_t *shared) { shared[0]=0; }
void TEEC_FinalizeContext(uint32_t *context) { *context=0; }
