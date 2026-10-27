#define main supplied_host_tests_main
#include "${S95F_EVIDENCE_ROOT}/research-20261027-external/sources/minimal-swu-helper/test_host.c"
#undef main
static unsigned invalid_index, validation_kind;
static uint32_t altered_allocate(SwuContext32 *c,SwuShared32 *m) {
    uint32_t result=alloc(c,m);
    if(!result && next_alloc-1==invalid_index) {
        if(validation_kind==0) m->size=SWU_SHARED+1;
        if(validation_kind==1) m->buffer=0;
    }
    return result;
}
static uint8_t *altered_map(SwuShared32 *m,uint32_t n) {
    if(validation_kind==2 && m==objects[invalid_index]) return NULL;
    return map(m,n);
}
static uint32_t altered_address(const void *p) {
    if(validation_kind==3 && p==objects[invalid_index]) return 0;
    return address(p);
}
static void validation_release(SwuShared32 *m) {
    CHECK(next_alloc>releases && m==objects[next_alloc-releases-1]);
    /* Invalid allocations fail before any blob/ciphertext copy. A mapping that
     * failed cannot be dereferenced for wiping; all earlier maps must be wiped. */
    if(next_alloc-releases-1!=invalid_index || validation_kind==3)
        zero_check(buffers[next_alloc-releases-1].data,SWU_SHARED);
    releases++;
}
int main(void) {
    CHECK(supplied_host_tests_main()==0);
    SwuApi faulty=api; faulty.allocate=altered_allocate; faulty.map=altered_map;
    faulty.addr32=altered_address; faulty.release=validation_release;
    for(validation_kind=0;validation_kind<4;validation_kind++) {
        for(invalid_index=0;invalid_index<3;invalid_index++) {
            uint8_t env[SWU_ENVELOPE]={0},blob[SWU_BLOB]; SwuReport r={0};
            memset(blob,0x42,sizeof(blob));r.origin=UINT32_MAX;reset(-1,0);
            CHECK(run_validated(&faulty,env,blob,&r)==-1);
            CHECK(r.local_failure==1 && r.result==LOCAL_FAILURE);
            CHECK(r.stage==(enum SwuStage)(SWU_ALLOC0+invalid_index));
            CHECK(commands==0 && closes==0 && releases==invalid_index+1 && finals==1);
            CHECK(r.shared_released==releases && r.context_finalized==1);
            CHECK(r.observed_counts[0]==0 && r.observed_counts[1]==0);
            CHECK(r.metadata_published==0);zero_check(blob,sizeof(blob));check_guards();
        }
    }
    puts("INDEPENDENT PASS: 12 allocation-size/null-buffer/map/address fault cases; no commands; exact reverse release; blob wiped");
    return 0;
}
