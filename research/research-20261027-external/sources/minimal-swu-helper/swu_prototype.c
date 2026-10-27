#include "swu_prototype.h"
#include <string.h>

/* Source prototype only. No main, dlopen, TEEC import, listener or live adapter. */
#define LOCAL_FAILURE UINT32_C(0xffff0006)
#define ORIGIN_UNSET UINT32_MAX
static void wipe(void *p, size_t n) {
    volatile uint8_t *v=p;
    while(n--) *v++=0;
}
static void memref(SwuParam32 *p, uint32_t parent, uint32_t size) {
    p->memory.parent=parent; p->memory.size=size; p->memory.offset=0;
}
void swu_frame0(SwuOperation32 *o, uint32_t input, uint32_t salt) {
    memset(o,0,sizeof(*o)); o->types=SWU_TYPES(13,13,1,1);
    memref(&o->p[0],input,SWU_BLOB); memref(&o->p[1],salt,8);
    o->p[2].value.a=0; o->p[2].value.b=1;
    o->p[3].value.a=1; o->p[3].value.b=0x201;
}
void swu_frame1(SwuOperation32 *o, uint32_t input, uint32_t output) {
    memset(o,0,sizeof(*o)); o->types=SWU_TYPES(13,14,2,0);
    memref(&o->p[0],input,SWU_CIPHER); memref(&o->p[1],output,SWU_CIPHER);
}
void swu_frame2(SwuOperation32 *o, uint32_t output) {
    memset(o,0,sizeof(*o)); o->types=SWU_TYPES(14,2,0,0);
    memref(&o->p[0],output,SWU_SHARED);
}
static int complete_api(const SwuApi *a) {
    return a && a->initialize && a->allocate && a->open && a->invoke &&
        a->close && a->release && a->finalize && a->addr32 && a->map && a->sha256;
}
static int matches(const SwuApi *a, const uint8_t *p, size_t n, const char *hex) {
    uint8_t digest[32]; uint32_t diff=0;
    a->sha256(p,n,digest);
    for(size_t i=0;i<32;i++) {
        unsigned hi=(unsigned)(hex[2*i]<='9'?hex[2*i]-'0':hex[2*i]-'a'+10);
        unsigned lo=(unsigned)(hex[2*i+1]<='9'?hex[2*i+1]-'0':hex[2*i+1]-'a'+10);
        diff |= digest[i] ^ ((hi<<4)|lo);
    }
    wipe(digest,sizeof(digest)); return diff==0;
}
/* Private core permits white-box synthetic tests after hash validation. It is
 * static and has no externally linkable bypass of the fixed input checks. */
static int run_validated(const SwuApi *a, const uint8_t *env, uint8_t *blob, SwuReport *r) {
    SwuContext32 ctx={0}; SwuSession32 session={0}; SwuShared32 sm[3]={{0}};
    SwuOperation32 op={0}; uint8_t *view[3]={0}; uint32_t parent[3]={0};
    uint8_t plaintext[SWU_CIPHER]={0};
    unsigned allocated=0; int initialized=0, opened=0, success=0;
    uint32_t produced=0, total=0;
    const SwuUuid32 uuid={0x22222221,0,0,{0,0,0,0,0,0,0,1}};
    r->stage=SWU_CONTEXT; r->result=a->initialize(NULL,&ctx);
    if(r->result) goto cleanup;
    initialized=1;
    for(unsigned i=0;i<3;i++) {
        r->stage=(enum SwuStage)(SWU_ALLOC0+i); r->origin=ORIGIN_UNSET;
        sm[i].size=SWU_SHARED; sm[i].flags=3;
        r->result=a->allocate(&ctx,&sm[i]);
        if(r->result) goto cleanup;
        allocated++;
        /* Snapshot backing views. An operation's returned memref.size cannot
         * increase these local capacities or cause a different mapping. */
        if(sm[i].size!=SWU_SHARED || !sm[i].buffer ||
           !(view[i]=a->map(&sm[i],SWU_SHARED)) || !(parent[i]=a->addr32(&sm[i]))) {
            r->result=LOCAL_FAILURE; r->local_failure=1; goto cleanup;
        }
        wipe(view[i],SWU_SHARED);
    }
    r->stage=SWU_SESSION; r->origin=ORIGIN_UNSET;
    r->result=a->open(&ctx,&session,&uuid,0,NULL,NULL,&r->origin);
    if(r->result) goto cleanup;
    opened=1;
    /* Match installed Core roles: sm0 input/blob; sm1 output; sm2 salt. */
    memcpy(view[0],blob,SWU_BLOB); memcpy(view[2],env+16,8);
    swu_frame0(&op,parent[0],parent[2]);
    r->stage=SWU_CMD0; r->origin=ORIGIN_UNSET; r->command_calls[0]++;
    r->result=a->invoke(&session,0,&op,&r->origin);
    wipe(view[0],SWU_SHARED); wipe(view[2],SWU_SHARED); wipe(blob,SWU_BLOB);
    if(r->result) goto cleanup;
    memcpy(view[0],env+24,SWU_CIPHER);
    swu_frame1(&op,parent[0],parent[1]);
    r->stage=SWU_CMD1; r->origin=ORIGIN_UNSET; r->command_calls[1]++;
    r->result=a->invoke(&session,1,&op,&r->origin);
    if(r->result) goto cleanup; /* No output inspected after failed TEEC call. */
    produced=op.p[2].value.a;
    r->observed_counts[0]=produced;
    if(produced>SWU_CIPHER || produced>SWU_SHARED || produced>SWU_CIPHER-total) {
        r->result=LOCAL_FAILURE; r->local_failure=1; goto cleanup;
    }
    r->counts[0]=produced; memcpy(plaintext+total,view[1],produced); total+=produced;
    wipe(view[1],SWU_SHARED);
    swu_frame2(&op,parent[1]);
    r->stage=SWU_CMD2; r->origin=ORIGIN_UNSET; r->command_calls[2]++;
    r->result=a->invoke(&session,2,&op,&r->origin);
    if(r->result) goto cleanup;
    produced=op.p[1].value.a;
    r->observed_counts[1]=produced;
    if(produced>SWU_SHARED || produced>SWU_CIPHER-total) {
        r->result=LOCAL_FAILURE; r->local_failure=1; goto cleanup;
    }
    r->counts[1]=produced; memcpy(plaintext+total,view[1],produced); total+=produced;
    /* No guessed padding removal or OUIT parser: decode semantics unqualified.
     * This state means command sequence completed, never metadata validated. */
    r->stage=SWU_QUARANTINED; success=1;
cleanup:
    /* No extra TA final command on failure. Close is not secure-world rollback. */
    if(opened) { a->close(&session); r->session_closed=1; }
    for(unsigned i=allocated;i>0;i--) {
        if(view[i-1]) wipe(view[i-1],SWU_SHARED);
        a->release(&sm[i-1]); r->shared_released++;
    }
    if(initialized) { a->finalize(&ctx); r->context_finalized=1; }
    wipe(blob,SWU_BLOB); wipe(plaintext,sizeof(plaintext)); wipe(&op,sizeof(op));
    wipe(sm,sizeof(sm)); wipe(&session,sizeof(session)); wipe(&ctx,sizeof(ctx));
    return success?0:-1;
}
int swu_metadata_prototype(const SwuApi *a, const uint8_t *env, size_t env_n,
                           uint8_t *blob, size_t blob_n, SwuReport *r) {
    if(!r) { if(blob && blob_n==SWU_BLOB) wipe(blob,blob_n); return -1; }
    memset(r,0,sizeof(*r)); r->stage=SWU_INPUT; r->origin=ORIGIN_UNSET;
    r->result=LOCAL_FAILURE; r->local_failure=1;
    if(!complete_api(a) || !env || !blob || env_n!=SWU_ENVELOPE || blob_n!=SWU_BLOB ||
       memcmp(env+8,"Salted__",8)!=0 ||
       !matches(a,env,env_n,"6da1e2386f0f97a180984f249febaf831febfee1adb35a8cefa96f89ad069e0d") ||
       !matches(a,blob,blob_n,"d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220")) {
        if(blob && blob_n==SWU_BLOB) wipe(blob,blob_n);
        return -1;
    }
    r->result=0; r->local_failure=0;
    return run_validated(a,env,blob,r);
}
