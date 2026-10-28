#!/usr/bin/env python3
"""Manual source transcription for one qualified branch; no target/backend access."""
def chip14_nonmonitor_mode(raw_rate, low_input_lag):
    """Requested QDF mode only, conditional on chip14, monitor0 and nonnegative input.

    Do not infer this branch's live configuration or accepted controller value.
    Numeric rates are in hundredths of Hz. This is not a hardware emulator.
    """
    if type(raw_rate) is not int or type(low_input_lag) is not int:
        raise ValueError('exact integer fields required')
    if not 0 <= raw_rate <= 0x7fffffff or not -0x80000000 <= low_input_lag <= 0x7fffffff:
        raise ValueError('outside reviewed nonnegative-rate/int32 branch')
    if low_input_lag == 1:
        return 2
    return int(raw_rate in (14400, 16500))
