#! /usr/local/bin/python
# -*- coding: utf-8 -*-

from io import FileIO
import sys
import codecs
import json

def to_synchsafe(integer, nbyte):
    b = bytearray(nbyte)
    for i in range(nbyte):
        b[i] = (integer >> (nbyte - i - 1) * 7) & 0x7f
    return b

def from_synchsafe(barray):
    j = 0
    for i in range(len(barray)):
        j = (j << 7) | (barray[i] & 0x7f)
    return j

def select_best_encoding(str, encoding_list):
    best_encoding = (None, None)
    for e in encoding_list:
        estr = None
        try:
            estr = str.encode(e[2])
            if best_encoding[1] is None or len(estr) < len(best_encoding[1]):
                best_encoding = (e, estr)
        except UnicodeEncodeError:
            pass
    return best_encoding


class ID3SyntaxError(SyntaxError):
    pass

class ID3NotImplemented(Exception):
    pass

class ID3Frame:
    CODING_ASCII = 'ascii'
    
    def __init__(self):
        self.parent = None
        self.frameid = None
        self.flags = [0, 0]
        self.info = None
        self.bininfo = b''

    def size(self):
        return len(self.bininfo)

    def fullsize(self):
        if self.parent and self.parent.version[0] <= 2:
            fullsize = self.size() + 6
        else:
            fullsize = self.size() + 10
        return fullsize

    def makebin(self):
        self.bininfo = self.info

    @classmethod
    def from_stream(cls, instrm, parent=None):
        if parent and parent.version[0] <= 2:
            frameid_bin = instrm.read(3)
        else:
            frameid_bin = instrm.read(4)
        frameid = frameid_bin.decode(cls.CODING_ASCII)
        if frameid[0] == 'T':
            newframe = ID3FrameText()
        elif frameid[0] == 'W':
            newframe = ID3FrameURL()
        else:
            newframe = ID3Frame()
        newframe.parent = parent
        newframe.frameid = frameid
        
        if parent and parent.version[0] <= 2:
            size_bin = instrm.read(3)
        else:
            size_bin = instrm.read(4)
        size = from_synchsafe(size_bin)
        
        if parent and parent.version[0] <= 2:
            newframe.flags = None
        else:
            flags = instrm.read(2)
            newframe.flags = [flags[0], flags[1]]
        buf = instrm.read(size)
        newframe.set_bininfo(buf)
        return newframe

    def set_bininfo(self, bininfo):
        self.bininfo = bininfo
        self.info = bininfo

    def write(self, outstrm):
        outstrm.write(self.frameid.encode(self.CODING_ASCII))
        
        if self.parent and self.parent.version[0] <= 2:
            sizebin = to_synchsafe(self.size(), 3)
        else:
            sizebin = to_synchsafe(self.size(), 4)
        outstrm.write(sizebin)
        
        if self.parent and self.parent.version[0] >= 3:
            outstrm.write(b'%c%c' % (self.flags[0], self.flags[1]))
        outstrm.write(self.bininfo)

# Text information frames
class ID3FrameText(ID3Frame):
    ENCODING_LIST = ((b'\x00', b'\x00'    , 'iso-8859-1'),
                     (b'\x01', b'\x00\x00', 'utf-16'),
                     (b'\x02', b'\x00\x00', 'utf-16be'),
                     (b'\x03', b'\x00'    , 'utf-8'),
    )

    def __init__(self):
        super().__init__()
        self.encoding = None

    def set_bininfo(self, buf):
        self.bininfo = buf
        for e in self.ENCODING_LIST:
            if buf[0] == e[0][0]:
                self.encoding = e
        s = buf[1:].decode(self.encoding[2])
        if self.parent and self.parent.version[0] >= 4 and '\0' in s:
            self.info = s.split('\0')
        else:
            self.info = s

    def makebin(self):
        if isinstance(self.info, (list)):
            if self.parent.version[0] <= 3:
                separator = ' / '
            else:
                separator = '\x00'
            info = ''
            for i in self.info:
                if len(info) > 0:
                    info += separator
                info += i
        else:
            info = self.info
        if self.parent.version[0] <= 2:
            encoding_list = self.ENCODING_LIST[:2] # ISO-8859-1 or UTF-16
        else:
            encoding_list = self.ENCODING_LIST
        einfo = select_best_encoding(info, encoding_list)
        self.encoding = einfo[0]
        self.bininfo = b'%c%b' % (self.encoding[0], einfo[1])

class ID3FrameURL(ID3Frame):
    def set_bininfo(self, buf):
        self.bininfo = buf
        self.info = buf.decode(self.CODING_ASCII)

    def makebin(self):
        self.bininfo = self.info.encode(self.CODING_ASCII)

class ID3Tag:
    BYTE_ORDER = 'big'
    
    ID_ID3 = b'ID3'
    
    # bit masks for 'flags'
    FLAG_UNSYNC  = 0x80
    FLAG_EXTHEADER = 0x40
    FLAG_EXPERIMENTAL = 0x20
    FLAG_FOOTER  = 0x10
    FLAG_UNUSED  = 0x0f
    
    def __init__(self):
        self.version = b'\x03\x00' # default
        self.flags = 0
        self.frames = []

    def size(self):
        s = 0
        for f in self.frames:
            s += f.fullsize()
        return s

    @classmethod
    def from_stream(cls, instrm):
        newid3 = cls()
        # Header (10 bytes)
        buf = instrm.read(3)
        if buf != newid3.ID_ID3:
            raise ID3SyntaxError()
        newid3.version = instrm.read(2)
        newid3.flags = instrm.read(1)[0]
        size = from_synchsafe(instrm.read(4))
        # Extended header (variable length, OPTIONAL)
        # TODO
        # Frames (variable length)
        while size >=6:
            newframe = ID3Frame.from_stream(instrm, newid3)
            if newframe.frameid[0] != '\x00':
                newid3.frames.append(newframe) # workaround for padding...
            size -= newframe.fullsize()
        if size > 0:
            instrm.read(size) # may be the rest of padding
        return newid3

    @classmethod
    def from_json(cls, jsonobj):
        newid3 = cls()
        newid3.version = b'%c%c' % (tuple(jsonobj["version"]))
        newid3.flags = jsonobj["flags"]
        frames = jsonobj["frames"]
        for fid in frames:
            if fid[0] == 'T':
                newframe = ID3FrameText()
            elif fid[0] == 'W':
                newframe = ID3FrameURL()
            else:
                newframe = ID3Frame()
            newframe.frameid = fid
            newframe.info = frames[fid]
            newframe.parent = newid3
            newid3.frames.append(newframe)
        return newid3
    
    def write(self, outstrm):
        # Header (10 bytes)
        outstrm.write(self.ID_ID3)
        outstrm.write(self.version)
        outstrm.write(self.flags.to_bytes(1, self.BYTE_ORDER))
        outstrm.write(to_synchsafe(self.size(), 4))
        # Extended header (variable length, OPTIONAL)
        if self.flags & self.FLAG_EXTHEADER:
            raise ID3NotImplemented()
        # Frames (variable length)
        for f in self.frames:
            f.write(outstrm)
        # Padding (variable length, OPTIONAL)
        # Footer (10 bytes, OPTIONAL)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write('usage: python egid3.py jsonfile id3file\n')
        sys.exit(1)
    else:
        with FileIO(sys.argv[1], 'r') as r:
            jsonobj = json.load(r)
            tag = ID3Tag.from_json(jsonobj)
            for f in tag.frames:
                f.makebin()
            with FileIO(sys.argv[2], 'wb') as w:
                tag.write(w)
