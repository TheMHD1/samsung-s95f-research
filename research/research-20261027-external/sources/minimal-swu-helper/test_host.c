/* White-box synthetic host tests. No target loader, socket, file or TEEC call. */
#include <stdio.h>
#include <stdlib.h>
#include "swu_prototype.c"
#define CHECK(x) do { if(!(x)) { fprintf(stderr,"check failed line %d: %s\n",__LINE__,#x); exit(1); } } while(0)
typedef struct { uint8_t before[16], data[SWU_SHARED], after[16]; } Guarded;
static Guarded buffers[3];
static SwuShared32 *objects[3];
static unsigned next_alloc, commands, closes, releases, finals, call_step;
static int fail_step, mode;
static uint32_t fail_now(void) { return (int)call_step++==fail_step?0xffff0001:0; }
static void zero_check(const void *p,size_t n) {
    const uint8_t *v=p; for(size_t i=0;i<n;i++) CHECK(v[i]==0);
}
static uint32_t init(const char *name, SwuContext32 *c) {
    CHECK(name==NULL); zero_check(c,sizeof(*c)); c->opaque=1; return fail_now();
}
static uint32_t alloc(SwuContext32 *c,SwuShared32 *m) {
    CHECK(c->opaque==1 && m->size==SWU_SHARED && m->flags==3 && m->buffer==0);
    zero_check(m->backend_reserved,sizeof(m->backend_reserved));
    uint32_t result=fail_now(); if(result) return result;
    CHECK(next_alloc<3); objects[next_alloc]=m; m->buffer=0x1000+next_alloc*0x100;
    m->backend_reserved[0]=next_alloc+1; next_alloc++; return 0;
}
static uint32_t open_session(SwuContext32 *c,SwuSession32 *s,const SwuUuid32 *u,
                            uint32_t login,const void *data,SwuOperation32 *o,uint32_t *origin) {
    CHECK(c->opaque==1 && login==0 && !data && !o && *origin==UINT32_MAX);
    CHECK(u->time_low==0x22222221 && u->time_mid==0 && u->time_hi==0 && u->node[7]==1);
    for(unsigned i=0;i<7;i++) CHECK(u->node[i]==0);
    zero_check(s,sizeof(*s)); s->opaque=2; *origin=3; return fail_now();
}
static uint32_t address(const void *p) {
    for(unsigned i=0;i<3;i++) if(p==objects[i]) return 0x2000+i*36;
    return 0;
}
static uint8_t *map(SwuShared32 *m,uint32_t capacity) {
    CHECK(capacity==SWU_SHARED);
    for(unsigned i=0;i<3;i++) if(m==objects[i]) return buffers[i].data;
    return NULL;
}
static uint32_t invoke(SwuSession32 *s,uint32_t cmd,SwuOperation32 *o,uint32_t *origin) {
    CHECK(s->opaque==2 && cmd==commands && cmd<3 && *origin==UINT32_MAX);
    CHECK(o->started==0 && o->backend_cancellation==0);
    SwuOperation32 expected;
    if(cmd==0) swu_frame0(&expected,0x2000,0x2048);
    else if(cmd==1) swu_frame1(&expected,0x2000,0x2024);
    else swu_frame2(&expected,0x2024);
    CHECK(memcmp(o,&expected,60)==0);
    /* Model installed common's write through operation+56, then cancellation.
     * Every subsequent operation must have this full tail zeroed afresh. */
    *(uint32_t *)((uint8_t *)o+56)=0x12345678;
    o->started=3; commands++; *origin=4;
    uint32_t result=fail_now();
    memset(buffers[1].data,0xa5,SWU_SHARED);
    if(cmd==1) {
        o->p[1].memory.size=mode==1?UINT32_MAX:0; /* never use callee capacity */
        o->p[2].value.a=result?UINT32_MAX:(mode==2?4033:4016);
    }
    if(cmd==2) {
        o->p[0].memory.size=mode==1?UINT32_MAX:0;
        o->p[1].value.a=result?UINT32_MAX:(mode==3?17:mode==4?65537:16);
    }
    return result;
}
static void close_session(SwuSession32 *s) { CHECK(s->opaque==2); closes++; }
static void release_mem(SwuShared32 *m) {
    CHECK(next_alloc>releases && m==objects[next_alloc-releases-1]);
    zero_check(buffers[next_alloc-releases-1].data,SWU_SHARED); releases++;
}
static void finalize(SwuContext32 *c) { CHECK(c->opaque==1); finals++; }
static void reject_digest(const uint8_t *p,size_t n,uint8_t digest[32]) {
    CHECK(p && n>0); memset(digest,0,32);
}
static const SwuApi api={init,alloc,open_session,invoke,close_session,release_mem,
                         finalize,address,map,reject_digest};
static void reset(int failure,int scenario) {
    next_alloc=commands=closes=releases=finals=call_step=0; fail_step=failure; mode=scenario;
    memset(objects,0,sizeof(objects)); memset(buffers,0xcc,sizeof(buffers));
}
static void check_guards(void) {
    for(unsigned i=0;i<3;i++) for(unsigned j=0;j<16;j++)
        CHECK(buffers[i].before[j]==0xcc && buffers[i].after[j]==0xcc);
}
static void test_core(int failure,int scenario) {
    uint8_t env[SWU_ENVELOPE]={0}, blob[SWU_BLOB]; memset(blob,0x42,sizeof(blob));
    SwuReport r={0}; r.origin=UINT32_MAX; reset(failure,scenario);
    int result=run_validated(&api,env,blob,&r);
    int expect_success=failure<0 && scenario<2;
    CHECK((result==0)==expect_success); CHECK(r.metadata_published==0);
    for(unsigned cmd=0;cmd<3;cmd++) CHECK(r.command_calls[cmd]==(commands>cmd?1:0));
    if(expect_success) {
        CHECK(commands==3 && r.stage==SWU_QUARANTINED && r.result==0);
        CHECK(r.counts[0]==4016 && r.counts[1]==16);
    } else {
        CHECK(r.result!=0);
        CHECK(r.local_failure==(scenario>=2?1:0));
        if(failure>=0) CHECK(r.stage==(enum SwuStage)(SWU_CONTEXT+failure));
        if(scenario==2) CHECK(commands==2 && r.counts[0]==0 && r.stage==SWU_CMD1 && r.observed_counts[0]==4033);
        if(scenario==3 || scenario==4) CHECK(commands==3 && r.counts[1]==0 && r.stage==SWU_CMD2);
    }
    if(failure>=0) {
        unsigned expected_commands=failure<5?0:(unsigned)(failure-4);
        CHECK(commands==expected_commands);
        /* Failed calls deliberately report UINT_MAX; no output count copied. */
        if(failure==6) CHECK(r.counts[0]==0 && r.observed_counts[0]==0);
        if(failure==7) CHECK(r.counts[1]==0 && r.observed_counts[1]==0);
    }
    CHECK(closes==(failure>=0 && failure<=4?0:1));
    CHECK(releases==next_alloc && r.shared_released==releases);
    CHECK(finals==(failure==0?0:1) && r.context_finalized==finals);
    CHECK(r.session_closed==closes); zero_check(blob,sizeof(blob)); check_guards();
}
static void golden_frames(void) {
    struct { uint32_t before; SwuOperation32 op; uint32_t after; } g;
    const uint32_t expected[3][15]={
        {0,0x01010d0d,0x11111110,416,0,0x33333330,8,0,0,1,0,1,0x201,0,0},
        {0,0x00020e0d,0x11111110,4032,0,0x22222220,4032,0,0,0,0,0,0,0,0},
        {0,0x0000020e,0x22222220,65536,0,0,0,0,0,0,0,0,0,0,0}};
    for(unsigned cmd=0;cmd<3;cmd++) {
        memset(&g,0xa5,sizeof(g)); g.before=0x11223344; g.after=0x55667788;
        if(cmd==0) swu_frame0(&g.op,0x11111110,0x33333330);
        if(cmd==1) swu_frame1(&g.op,0x11111110,0x22222220);
        if(cmd==2) swu_frame2(&g.op,0x22222220);
        CHECK(memcmp(&g.op,expected[cmd],60)==0);
        CHECK(g.before==0x11223344 && g.after==0x55667788);
        printf("frame%u=",cmd);
        const uint8_t *v=(const uint8_t *)&g.op;
        for(size_t i=0;i<60;i++) printf("%02x",v[i]);
        putchar('\n');
    }
}
int main(void) {
    CHECK(*(const uint8_t *)&(const uint32_t){1}==1); /* host output is LE */
    golden_frames();
    for(int failure=0;failure<8;failure++) test_core(failure,0);
    for(int scenario=0;scenario<5;scenario++) test_core(-1,scenario);
    uint8_t env[SWU_ENVELOPE]={0},blob[SWU_BLOB]; SwuReport r;
    reset(-1,0); memset(blob,0x42,sizeof(blob));
    CHECK(swu_metadata_prototype(&api,env,sizeof(env)-1,blob,sizeof(blob),&r)==-1);
    CHECK(call_step==0 && r.stage==SWU_INPUT); zero_check(blob,sizeof(blob));
    memcpy(env+8,"Salted__",8); memset(blob,0x42,sizeof(blob));
    CHECK(swu_metadata_prototype(&api,env,sizeof(env),blob,sizeof(blob),&r)==-1);
    CHECK(call_step==0 && r.stage==SWU_INPUT); zero_check(blob,sizeof(blob));
    puts("PASS: 3 golden frames; 8 failure stages; 2 size-mutation successes; 3 count overflows; 2 input rejections; canaries and cleanup");
    return 0;
}
