# -*- coding: utf-8 -*-
# usage: python -m unittest egid3test
import unittest
import egid3
import io

class TestEgID3(unittest.TestCase):
    def test_to_synchsafe(self):
        self.assertEqual(egid3.to_synchsafe(0x12ab, 2), b'\x25\x2b')

    def test_from_synchsafe(self):
        self.assertEqual(egid3.from_synchsafe(b'\x01\x01'), 129)

    def test_text_makebin_utf16(self):
        frame = egid3.ID3FrameText()
        frame.encoding = frame.ENCODING_LIST[1]
        frame.info = "TEST"
        frame.makebin()
        if frame.bininfo[1:3] == b'\xfe\xff':
            expectedBin = b'\x01\xfe\xff\x00T\x00E\x00S\x00T'
        else:
            expectedBin = b'\x01\xff\xfeT\x00E\x00S\x00T\x00'
        self.assertEqual(frame.bininfo, expectedBin)

    def test_text_makebin_utf16_array(self):
        frame = egid3.ID3FrameText()
        frame.encoding = frame.ENCODING_LIST[1]
        frame.info = ["A", "B", "C"]
        frame.makebin()
        if frame.bininfo[1:3] == b'\xfe\xff':
            expectedBin = b'\x01\xfe\xff\x00A\x00,\x00 \x00B\x00,\x00 \x00C'
        else:
            expectedBin = b'\x01\xff\xfeA\x00,\x00 \x00B\x00,\x00 \x00C\x00'
        self.assertEqual(frame.bininfo, expectedBin)
        self.assertEqual(frame.size(), 17)

    def test_url_makebin(self):
        frame = egid3.ID3FrameURL()
        frame.info = "http://www.eagan.jp/"
        frame.makebin()
        self.assertEqual(frame.bininfo, b'http://www.eagan.jp/')
        self.assertEqual(frame.size(), 20)

if __name__=='__main__':
    unittest.main()
