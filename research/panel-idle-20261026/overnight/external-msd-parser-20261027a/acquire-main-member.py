#!/usr/bin/env python3
"""Acquire one existing official ZIP member on the host, never the TV."""
import hashlib
import json
import os
from pathlib import Path
import struct
import time
import urllib.request
import zlib

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
META = json.loads((BASE / 'samsung-official-firmware-archive-metadata.json').read_text())
ENTRY = next(x for x in META['entries'] if x['name'] == 'T-RSMFAKUC-0090/image/upgrade.msd')
START = ENTRY['local_header_offset']
DATA_START = START + 30 + len(ENTRY['name'].encode('ascii'))
END = DATA_START + ENTRY['compressed_size'] - 1
TOTAL = 2439527748
RATE = 16 * 1024 * 1024
PARTIAL = HERE / 'upgrade.msd.partial'
DEST = HERE / 'upgrade.msd'
RESULT = HERE / 'acquisition-result.json'


def need(value, why):
    if not value:
        raise ValueError(why)


def main():
    need(not any(x.exists() for x in (PARTIAL, DEST, RESULT)), 'output already exists; no retry')
    request = urllib.request.Request(META['resolved_url'], headers={
        'User-Agent': 'Samsung-owner-offline-diagnostics',
        'Range': f'bytes={START}-{END}',
        'If-Match': META['headers']['ETag'],
        'Accept-Encoding': 'identity',
    })
    result = {'accepted': False, 'source': META['resolved_url'],
              'requested_range': [START, END], 'tv_operations': 0}
    began = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            result['response_status'] = response.status
            result['response_headers'] = dict(response.headers)
            need(response.status == 206, 'server did not honor range')
            need(response.headers.get('Content-Range') == f'bytes {START}-{END}/{TOTAL}', 'range changed')
            need(int(response.headers.get('Content-Length', '-1')) == END - START + 1, 'length changed')
            need(response.headers.get('ETag') == META['headers']['ETag'], 'etag changed')
            header = response.read(DATA_START - START)
            need(len(header) == DATA_START - START, 'short local header')
            fields = struct.unpack_from('<IHHHHHIIIHH', header)
            need(fields[0] == 0x04034b50 and fields[2] == 0 and fields[3] == 8, 'local ZIP format changed')
            need(fields[6] == int(ENTRY['crc32'], 16), 'local CRC disagrees')
            need(fields[7:9] == (ENTRY['compressed_size'], ENTRY['uncompressed_size']), 'local sizes disagree')
            need(fields[9] == len(ENTRY['name']) and fields[10] == 0, 'local name/extra changed')
            need(header[30:].decode('ascii') == ENTRY['name'], 'local filename changed')
            decoder = zlib.decompressobj(-15)
            compressed_hash = hashlib.sha256()
            plain_hash = hashlib.sha256()
            prefix = bytearray()
            compressed_count = plain_count = crc = 0
            remaining = ENTRY['compressed_size']
            announced = 0
            fd = os.open(PARTIAL, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as output:
                while remaining:
                    block = response.read(min(1024 * 1024, remaining))
                    need(block, 'short compressed stream')
                    compressed_hash.update(block)
                    compressed_count += len(block)
                    remaining -= len(block)
                    decoded = decoder.decompress(block, 2 * 1024 * 1024)
                    need(not decoder.unconsumed_tail, 'unexpected expansion bound')
                    need(plain_count + len(decoded) <= ENTRY['uncompressed_size'], 'member size overflow')
                    output.write(decoded)
                    plain_hash.update(decoded)
                    crc = zlib.crc32(decoded, crc)
                    if len(prefix) < 65494:
                        prefix.extend(decoded[:65494 - len(prefix)])
                    plain_count += len(decoded)
                    if compressed_count // (128 * 1024 * 1024) > announced:
                        announced = compressed_count // (128 * 1024 * 1024)
                        print(json.dumps({'compressed_bytes': compressed_count, 'elapsed_s': round(time.monotonic() - began, 2)}), flush=True)
                    delay = compressed_count / RATE - (time.monotonic() - began)
                    if delay > 0:
                        time.sleep(min(delay, 0.1))
                tail = decoder.flush()
                need(plain_count + len(tail) <= ENTRY['uncompressed_size'], 'tail overflow')
                output.write(tail)
                plain_hash.update(tail)
                crc = zlib.crc32(tail, crc) & 0xffffffff
                plain_count += len(tail)
                output.flush()
                os.fsync(output.fileno())
            need(decoder.eof and not decoder.unused_data, 'incomplete or extra deflate bytes')
            need(compressed_count == ENTRY['compressed_size'] and plain_count == ENTRY['uncompressed_size'], 'count mismatch')
            need(crc == int(ENTRY['crc32'], 16), 'whole member CRC mismatch')
            need(hashlib.sha256(prefix).hexdigest() == '01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d', 'retained prefix mismatch')
            os.rename(PARTIAL, DEST)
            result.update(accepted=True, compressed_bytes=compressed_count,
                          decompressed_bytes=plain_count, compressed_sha256=compressed_hash.hexdigest(),
                          msd_sha256=plain_hash.hexdigest(), member_crc32=f'{crc:08x}',
                          prefix_matches=True, elapsed_s=round(time.monotonic() - began, 2),
                          qualification='Whole ZIP member CRC/size validated; package signature and plaintext sections not validated.')
    except BaseException as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        RESULT.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
