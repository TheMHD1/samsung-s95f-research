#ifndef SWU_PROTOTYPE_H
#define SWU_PROTOTYPE_H
#include <stddef.h>
#include <stdint.h>

/* Exact ARM32 public storage. Address words are target addresses, never host
 * pointers. Opaque areas deliberately do not borrow older vendor field names. */
typedef struct { uint32_t opaque; } SwuContext32;
typedef struct { uint32_t opaque; } SwuSession32;
typedef struct {
    uint32_t buffer, size, flags, backend_reserved[6];
} SwuShared32;
typedef union {
    struct { uint32_t parent, size, offset; } memory;
    struct { uint32_t a, b, reserved; } value;
    uint32_t words[3];
} SwuParam32;
typedef struct {
    uint32_t started, types;
    SwuParam32 p[4];
    uint32_t backend_cancellation;
} SwuOperation32;
typedef struct {
    uint32_t time_low;
    uint16_t time_mid, time_hi;
    uint8_t node[8];
} SwuUuid32;

#define SWU_TYPES(a,b,c,d) ((uint32_t)(a) | ((uint32_t)(b)<<8) | \
                           ((uint32_t)(c)<<16) | ((uint32_t)(d)<<24))
_Static_assert(sizeof(SwuContext32)==4 && sizeof(SwuSession32)==4, "handles");
_Static_assert(_Alignof(SwuContext32)==4 && _Alignof(SwuSession32)==4, "handle alignment");
_Static_assert(sizeof(SwuShared32)==36 && _Alignof(SwuShared32)==4, "shared");
_Static_assert(offsetof(SwuShared32,size)==4 && offsetof(SwuShared32,flags)==8, "shared public");
_Static_assert(offsetof(SwuShared32,backend_reserved)==12, "shared backend token");
_Static_assert(sizeof(SwuParam32)==12 && _Alignof(SwuParam32)==4, "parameter");
_Static_assert(offsetof(SwuParam32,memory.size)==4 && offsetof(SwuParam32,memory.offset)==8, "memref");
_Static_assert(sizeof(SwuOperation32)==60 && _Alignof(SwuOperation32)==4, "operation full storage");
_Static_assert(offsetof(SwuOperation32,types)==4 && offsetof(SwuOperation32,p)==8, "operation public prefix");
_Static_assert(offsetof(SwuOperation32,p[1])==20 && offsetof(SwuOperation32,p[2])==32 && offsetof(SwuOperation32,p[3])==44, "parameter stride");
_Static_assert(offsetof(SwuOperation32,backend_cancellation)==56, "backend cancellation tail");
_Static_assert(sizeof(SwuUuid32)==16 && _Alignof(SwuUuid32)==4, "uuid");
_Static_assert(offsetof(SwuUuid32,time_mid)==4 && offsetof(SwuUuid32,time_hi)==6 && offsetof(SwuUuid32,node)==8, "uuid fields");
_Static_assert(SWU_TYPES(13,13,1,1)==0x01010d0d, "init byte slots");
_Static_assert(SWU_TYPES(13,14,2,0)==0x00020e0d, "update byte slots");
_Static_assert(SWU_TYPES(14,2,0,0)==0x0000020e, "final byte slots");

enum { SWU_ENVELOPE=4056, SWU_BLOB=416, SWU_CIPHER=4032, SWU_SHARED=65536 };
enum SwuStage { SWU_INPUT, SWU_CONTEXT, SWU_ALLOC0, SWU_ALLOC1, SWU_ALLOC2,
                SWU_SESSION, SWU_CMD0, SWU_CMD1, SWU_CMD2, SWU_QUARANTINED };
typedef struct {
    enum SwuStage stage;
    uint32_t result, origin, counts[2], command_calls[3];
    uint32_t observed_counts[2], local_failure;
    uint32_t context_finalized, shared_released, session_closed;
    uint32_t metadata_published; /* Always zero: plaintext schema still unqualified. */
} SwuReport;

/* Injection boundary only: NO installed-library adapter or loader is supplied.
 * A future reviewed ARM32 adapter would forward the seven named TEEC methods.
 * addr32 must reject an unrepresentable address; map must validate allocation
 * ownership and return a process-local view of the full requested allocation.
 * sha256 must compute SHA-256, not accept a supplied digest. */
typedef struct {
    uint32_t (*initialize)(const char *, SwuContext32 *);
    uint32_t (*allocate)(SwuContext32 *, SwuShared32 *);
    uint32_t (*open)(SwuContext32 *, SwuSession32 *, const SwuUuid32 *,
                     uint32_t, const void *, SwuOperation32 *, uint32_t *);
    uint32_t (*invoke)(SwuSession32 *, uint32_t, SwuOperation32 *, uint32_t *);
    void (*close)(SwuSession32 *);
    void (*release)(SwuShared32 *);
    void (*finalize)(SwuContext32 *);
    uint32_t (*addr32)(const void *);
    uint8_t *(*map)(SwuShared32 *, uint32_t);
    void (*sha256)(const uint8_t *, size_t, uint8_t[32]);
} SwuApi;

/* No file or network IO; envelope must be exact [234,4290) from the fixed
 * manifest. Caller owns complete regular-file/EOF checks for the selected blob.
 * The borrowed mutable blob is wiped on every path when its size is 416.
 * Produces diagnostic metadata only; never returns plaintext/key/blob bytes. */
int swu_metadata_prototype(const SwuApi *, const uint8_t *, size_t,
                           uint8_t *, size_t, SwuReport *);
void swu_frame0(SwuOperation32 *, uint32_t, uint32_t);
void swu_frame1(SwuOperation32 *, uint32_t, uint32_t);
void swu_frame2(SwuOperation32 *, uint32_t);
#endif
