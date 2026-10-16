"""Stream one attributable Apport report; never write a decoded core/copy."""
import base64
import hashlib
import zlib


def scan(stream, marker, core_cap=9*1024**2, input_cap=32*1024**2):
    total = decoded = metadata = 0
    digest = hashlib.sha256()
    raw_digest = hashlib.sha256()
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
    tail = b''
    offsets = []
    fields = {}
    key = None
    seen_core = False

    def core(data):
        nonlocal decoded, tail
        while data:
            block = decoder.decompress(data, min(65536, core_cap-decoded+1))
            data = decoder.unconsumed_tail
            if decoder.unused_data:
                raise ValueError('trailing gzip data')
            if decoded + len(block) > core_cap:
                raise ValueError('decoded core cap')
            joined = tail + block
            start = 0
            while True:
                found = joined.find(marker, start)
                if found < 0:
                    break
                offsets.append(decoded-len(tail)+found)
                if len(offsets)>100:
                    raise ValueError('marker occurrence cap')
                start = found + 1
            tail = joined[-(len(marker)-1):] if len(marker)>1 else b''
            digest.update(block)
            decoded += len(block)

    while True:
        line = stream.readline(1024**2 + 1)
        if not line:
            break
        total += len(line)
        raw_digest.update(line)
        if len(line)>1024**2 or total>input_cap:
            raise ValueError('report input/line cap')
        if line.startswith(b' '):
            value = line[1:].rstrip(b'\n')
            if key == 'CoreDump':
                core(base64.b64decode(value, validate=True))
                continue
            if key is None:
                raise ValueError('orphan continuation')
            fields[key] += b'\n' + value
        else:
            name, sep, value = line.rstrip(b'\n').partition(b':')
            if not sep:
                raise ValueError('malformed field')
            key = name.decode('ascii')
            if key in fields:
                raise ValueError('duplicate field')
            fields[key] = value.lstrip(b' ')
            if key == 'CoreDump':
                if fields[key] != b'base64':
                    raise ValueError('unexpected core encoding')
                seen_core = True
                continue
        metadata += len(line)
        if metadata > 1024**2:
            raise ValueError('metadata cap')
    if not seen_core or not decoder.eof:
        raise ValueError('missing/incomplete gzip core')
    return dict(input_bytes=total, input_sha256=raw_digest.hexdigest(), decoded_bytes=decoded,
                decoded_sha256=digest.hexdigest(), marker_count=len(offsets), marker_offsets=offsets,
                field_bytes={k:len(v) for k,v in fields.items()},
                binding={k:fields.get(k,b'').decode('utf8') for k in
                         ('ExecutablePath','ProcCmdline','ProcStatus','Signal','_HooksRun')})
