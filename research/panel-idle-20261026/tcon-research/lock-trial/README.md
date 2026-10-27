# S95F bounded display-lock trial

This is a host-built .NET 6 helper for the exact `libdeviced.so.1.0.3` collected
from this TV. It does nothing without an explicit operation argument.

Both operations check that they are a 32-bit process, check the SHA-256 of
`/usr/lib/libdeviced.so.1.0.3`, and require effective UID 0 or 901. `query`
performs only a native screen-state read. `trial` requests `lcdon/gotostatenow`
for 180000 ms, waits once without renewal, and always sends the matching
reset-timer unlock in `finally`.

The request is a high-level deviced idle/DPMS policy lock. It does not change
TCON registers or disable ERR_DET, panel protection, compensation, or thermal
handling. A real panel/TCON fault may still blank the picture and recover.
