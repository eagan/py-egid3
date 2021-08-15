#! /usr/local/bin/python
# -*- coding: utf-8 -*-

from io import FileIO
import sys

from egid3 import ID3Tag, ID3FrameText

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write('usage: python fixsjis.py origfile fixedfile\n')
        sys.exit(1)
    else:
        with FileIO(sys.argv[1], 'rb') as r:
            tag = ID3Tag.from_stream(r)
            for f in tag.frames:
                if isinstance(f, ID3FrameText):
                    if f.bininfo[-1] == 0x00:
                        # strip the trailing 0x00
                        bininfo = f.bininfo[1:-1]
                    else:
                        bininfo = f.bininfo[1:]
                    if f.encoding == f.ENCODING_LIST[0]: # iso-8859-1
                        hasmsb = False
                        for b in f.bininfo[1:]:
                            if b >= 0x80:
                                hasmsb = True
                        if hasmsb:
                            f.encoding = f.ENCODING_LIST[1] # utf-16
                            f.info = bininfo.decode('Shift_JIS')
                        else:
                            f.info = bininfo.decode('iso-8859-1')
                f.makebin()
            with FileIO(sys.argv[2], 'wb') as w:
                tag.write(w)
                buf = r.read()
                w.write(buf)
