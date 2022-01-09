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
    
    def test_select_best_encoding_iso8859(self):
        ENCODING_LIST = ((b'\x00', b'\x00'    , 'iso-8859-1'),
                         (b'\x01', b'\x00\x00', 'utf-16'),
                         (b'\x02', b'\x00\x00', 'utf-16be'),
                         (b'\x03', b'\x00'    , 'utf-8'),
        )
        e = egid3.select_best_encoding('¡ASCII STRING!', ENCODING_LIST)
        self.assertEqual(e[0][0], b'\x00')
        self.assertEqual(e[1], b'\xa1ASCII STRING!')

    def test_select_best_encoding_utf16be(self):
        ENCODING_LIST = ((b'\x00', b'\x00'    , 'iso-8859-1'),
                         (b'\x01', b'\x00\x00', 'utf-16'),
                         (b'\x02', b'\x00\x00', 'utf-16be'),
                         (b'\x03', b'\x00'    , 'utf-8'),
        )
        e = egid3.select_best_encoding('漢字', ENCODING_LIST)
        self.assertEqual(e[0][0], b'\x02')
        self.assertEqual(e[1], b'\x6f\x22\x5b\x57')

    def test_select_best_encoding_utf16(self):
        ENCODING_LIST = ((b'\x00', b'\x00'    , 'iso-8859-1'),
                         (b'\x01', b'\x00\x00', 'utf-16'),
        )
        e = egid3.select_best_encoding('漢字', ENCODING_LIST)
        self.assertEqual(e[0][0], b'\x01')
        if e[1][0] == 0xfe:
            # Big Endian
            self.assertEqual(e[1], b'\xfe\xff\x6f\x22\x5b\x57')
        else:
            # Little Endian
            self.assertEqual(e[1], b'\xff\xfe\x22\x6f\x57\x5b')

    def test_select_best_encoding_utf8(self):
        ENCODING_LIST = ((b'\x00', b'\x00'    , 'iso-8859-1'),
                         (b'\x01', b'\x00\x00', 'utf-16'),
                         (b'\x02', b'\x00\x00', 'utf-16be'),
                         (b'\x03', b'\x00'    , 'utf-8'),
        )
        e = egid3.select_best_encoding('ASCII STRING 漢字', ENCODING_LIST)
        self.assertEqual(e[0][0], b'\x03')
        self.assertEqual(e[1], b'ASCII STRING \xe6\xbc\xa2\xe5\xad\x97')

    def test_text_makebin_iso8859(self):
        frame = egid3.ID3FrameText()
        frame.parent = egid3.ID3Tag()
        frame.parent.version = b'\x03\x00' # id3v2.3.0
        frame.encoding = frame.ENCODING_LIST[1]
        frame.info = "¡TEST!"
        frame.makebin()
        expectedBin = b'\x00\xa1TEST!'
        self.assertEqual(frame.bininfo, expectedBin)

    def test_text_makebin_utf16be(self):
        frame = egid3.ID3FrameText()
        frame.parent = egid3.ID3Tag()
        frame.parent.version = b'\x03\x00' # id3v2.3.0
        frame.info = "漢字"
        frame.makebin()
        expectedBin = b'\x02\x6f\x22\x5b\x57'
        self.assertEqual(frame.bininfo, expectedBin)
    
    def test_text_makebin_utf16(self):
        frame = egid3.ID3FrameText()
        frame.parent = egid3.ID3Tag()
        frame.parent.version = b'\x02\x00' # id3v2.2.0
        frame.info = "漢字"
        frame.makebin()
        if frame.bininfo[1:3] == b'\xfe\xff':
            # Big Endian
            expectedBin = b'\x01\xfe\xff\x6f\x22\x5b\x57'
        else:
            # Little Endian
            expectedBin = b'\x01\xff\xfe\x22\x6f\x57\x5b'
        self.assertEqual(frame.bininfo, expectedBin)

    def test_text_makebin_iso8859_array_v230(self):
        frame = egid3.ID3FrameText()
        frame.parent = egid3.ID3Tag()
        frame.parent.version = b'\x03\x00' # id3v2.3.0
        frame.info = ["1", "2", "3"]
        frame.makebin()
        expectedBin = b'\x001 / 2 / 3'
        self.assertEqual(frame.bininfo, expectedBin)

    def test_text_makebin_iso8859_array_v240(self):
        frame = egid3.ID3FrameText()
        frame.parent = egid3.ID3Tag()
        frame.parent.version = b'\x04\x00' # id3v2.4.0
        frame.info = ["1", "2", "3"]
        frame.makebin()
        expectedBin = b'\x001\x002\x003'
        self.assertEqual(frame.bininfo, expectedBin)

    def test_url_makebin(self):
        frame = egid3.ID3FrameURL()
        frame.info = "http://www.eagan.jp/"
        frame.makebin()
        self.assertEqual(frame.bininfo, b'http://www.eagan.jp/')
        self.assertEqual(frame.size(), 20)

if __name__=='__main__':
    unittest.main()
