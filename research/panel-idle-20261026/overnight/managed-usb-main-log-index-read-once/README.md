# Fixed main-log index and status-flag reader

This helper is a mechanical derivative of the reviewed fixed 64-byte DMA-alias
reader. Its only active request is target `0x101`, address `0x45000e20`, length
64, encoded as `01010000200e004540000000`. It accepts no caller-selected
address or length and sends no write, retry, reset, or control request.

Under the previously qualified core-tag-`0xa` alias, the candidate CPU window
is `0x20000e20..0x20000e5f`. It places the main status byte at snapshot offset
`0x10` and the main event-log write-index DWORD at offset `0x3c`. The retained
logger evidence identifies the index literal at CPU `0x20000e5c` and the log
byte buffer at direct address `0x20205000`.

This read only samples the opaque 64-byte window. Transport acceptance does
not establish that a changing byte has the proposed meaning, prove a fault, or
establish whole running-image identity. Default mode performs no target I/O.
This helper has not been deployed or executed on the TV.
