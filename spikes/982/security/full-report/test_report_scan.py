import base64
import gzip
import io
import unittest
from report_scan import scan

class ScannerTests(unittest.TestCase):
    def report(self, data):
        compressed=gzip.compress(data)
        # Match Apport's independently base64-encoded compressed chunks.
        return b'ExecutablePath: /usr/bin/sleep\nCoreDump: base64\n'+b''.join(
            b' '+base64.b64encode(compressed[i:i+17])+b'\n' for i in range(0,len(compressed),17))
    def test_marker_crosses_output_chunks(self):
        marker=b'public-synthetic-marker'
        data=b'x'*65530+marker+b'y'*70000+marker
        x=scan(io.BytesIO(self.report(data)),marker)
        self.assertEqual(x['marker_offsets'],[65530,65530+len(marker)+70000])
        self.assertEqual(x['decoded_bytes'],len(data))
    def test_inflate_cap(self):
        with self.assertRaisesRegex(ValueError,'decoded core cap'):
            scan(io.BytesIO(self.report(b'x'*10000)),b'marker',core_cap=100)
    def test_truncated_and_corrupt_gzip(self):
        for data in [gzip.compress(b'hello')[:-3],gzip.compress(b'hello')[:-8]+b'\0'*8]:
            with self.assertRaises((ValueError,Exception)):
                scan(io.BytesIO(b'CoreDump: base64\n '+base64.b64encode(data)+b'\n'),b'hello')
    def test_input_cap(self):
        with self.assertRaisesRegex(ValueError,'input/line cap'):
            scan(io.BytesIO(self.report(b'hello')),b'hello',input_cap=20)

if __name__=='__main__':unittest.main()
