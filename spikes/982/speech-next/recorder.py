#!/usr/bin/env python3
"""Bounded synthetic PulseAudio recording; PA_STREAM_DONT_MOVE forbids fallback."""
import ctypes as C
import ctypes.util
import os
import re
import sys
import time


def main():
    if sys.platform != 'linux' or os.getuid() == 0 or len(sys.argv) != 3:
        raise SystemExit('unprivileged guest recorder: explicit server and synthetic source required')
    server, source = sys.argv[1:]
    if server != '/run/user/1000/pulse/native' or not re.fullmatch(r'campus982_synthetic_[0-9a-f]{8}\.monitor', source):
        raise SystemExit('refuse non-spike audio source')
    lib = C.CDLL(ctypes.util.find_library('pulse'))
    def bind(name, result, *args):
        f = getattr(lib, name); f.restype = result; f.argtypes = list(args); return f
    ptr = C.c_void_p; integer = C.c_int; string = C.c_char_p
    cb = C.CFUNCTYPE(None, ptr, ptr); readcb = C.CFUNCTYPE(None, ptr, C.c_size_t, ptr)
    class Spec(C.Structure):
        _fields_ = [('format', integer), ('rate', C.c_uint32), ('channels', C.c_uint8)]
    class Buffer(C.Structure):
        _fields_ = [(name, C.c_uint32) for name in ('maxlength', 'tlength', 'prebuf', 'minreq', 'fragsize')]
    bind('pa_mainloop_new', ptr); bind('pa_mainloop_get_api', ptr, ptr)
    bind('pa_mainloop_iterate', integer, ptr, integer, C.POINTER(integer))
    bind('pa_context_new', ptr, ptr, string); bind('pa_context_set_state_callback', None, ptr, cb, ptr)
    bind('pa_context_connect', integer, ptr, string, integer, ptr); bind('pa_context_get_state', integer, ptr)
    bind('pa_stream_new', ptr, ptr, string, C.POINTER(Spec), ptr)
    bind('pa_stream_set_read_callback', None, ptr, readcb, ptr)
    bind('pa_stream_set_state_callback', None, ptr, cb, ptr)
    bind('pa_stream_connect_record', integer, ptr, string, ptr, integer)
    bind('pa_stream_get_state', integer, ptr); bind('pa_stream_get_device_name', string, ptr)
    bind('pa_stream_peek', integer, ptr, C.POINTER(ptr), C.POINTER(C.c_size_t))
    bind('pa_stream_drop', integer, ptr)
    state = {'exit': None, 'bytes': 0, 'stream': None}
    @readcb
    def read(stream, length, userdata):
        if lib.pa_stream_get_device_name(stream) != source.encode(): state['exit'] = 6; return
        data = ptr(); size = C.c_size_t()
        if lib.pa_stream_peek(stream, C.byref(data), C.byref(size)) < 0: state['exit'] = 7; return
        if state['bytes'] + size.value >= 1024 * 1024: state['exit'] = 8; return
        if size.value:
            payload = C.string_at(data, size.value) if data else bytes(size.value)
            os.write(1, payload); state['bytes'] += size.value
            lib.pa_stream_drop(stream)
    @cb
    def stream_state(stream, userdata):
        s = lib.pa_stream_get_state(stream)
        if s in (3, 4): state['exit'] = 9
        if s == 2:
            if lib.pa_stream_get_device_name(stream) != source.encode(): state['exit'] = 10
            else: print('CONNECTED_SYNTHETIC_SOURCE=' + source, file=sys.stderr, flush=True)
    @cb
    def context_state(context, userdata):
        status = lib.pa_context_get_state(context)
        if status in (5, 6): state['exit'] = 11
        if status == 4:
            spec = Spec(3, 16000, 1)  # PA_SAMPLE_S16LE, mono16kHz
            stream = lib.pa_stream_new(context, b'Campus982SyntheticOnly', C.byref(spec), None)
            if not stream: state['exit'] = 12; return
            state['stream'] = stream
            lib.pa_stream_set_read_callback(stream, read, None)
            lib.pa_stream_set_state_callback(stream, stream_state, None)
            # Public libpulse ABI: PA_STREAM_DONT_MOVE=0x0200. No default device.
            buffer = Buffer(0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 4096)
            if lib.pa_stream_connect_record(stream, source.encode(), C.byref(buffer), 0x0200) < 0: state['exit'] = 13
    loop = lib.pa_mainloop_new(); context = lib.pa_context_new(lib.pa_mainloop_get_api(loop), b'Campus982SyntheticOnly')
    lib.pa_context_set_state_callback(context, context_state, None)
    if lib.pa_context_connect(context, ('unix:' + server).encode(), 1, None) < 0: raise SystemExit(14)
    start = time.monotonic(); result = integer()
    while state['exit'] is None and time.monotonic() - start < 30:
        if lib.pa_mainloop_iterate(loop, 0, C.byref(result)) < 0: state['exit'] = 15
        time.sleep(0.005)
    raise SystemExit(state['exit'] or 16)


if __name__ == '__main__': main()
