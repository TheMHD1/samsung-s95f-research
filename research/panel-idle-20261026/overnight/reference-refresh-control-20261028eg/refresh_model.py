"""Pure integer model of two bounded selected-source blocks, not scheduling."""

def unsigned(value, bits):
    if type(value) is not int or not 0 <= value < (1 << bits):
        raise ValueError('unsigned field width')
    return value

def synchronize(mirror, counter, selector):
    """c27c..c2a2, assuming one stable selector value for these loads."""
    unsigned(mirror, 16)
    unsigned(counter, 16)
    unsigned(selector, 8)
    if mirror == selector:
        return mirror, counter
    return selector, int(selector != 0)

def snapshot(counter, selector, header_flag, row, height):
    """b824..b828 +1c12c. Copy kind only, not bytes, epochs or physical data."""
    unsigned(counter, 16)
    unsigned(selector, 8)
    unsigned(header_flag, 8)
    unsigned(row, 16)
    unsigned(height, 16)
    if header_flag == 0 or counter == 0 or selector == 0:
        return counter, None
    kind = None
    if row == 0:
        kind = 'top'
    elif row == ((height - 1) & 0xffffffff):
        kind = 'bottom'
    if kind is not None:
        counter = (counter + 1) & 0xffff
    if counter > 2:
        counter = 0
    return counter, kind
