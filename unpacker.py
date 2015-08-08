from PIL import Image
import struct
import os

class ANIReader:
    def __init__(self, filename):
        self.dat = open(filename,"rb").read()

        self.pal = {}
        for i in range(256):
            self.pal[i] = tuple(self.dat[i * 4: i*4 + 3])
    
    #A generator that yields animation frames in tuples (image, shadow)
    #Shadows are often None
    def seek(self, start, verbose=False):
        
        # 0x410 - on fire
        # 0x8ba - on fire 2
        count = struct.unpack("<L", self.dat[0x400:0x400+4])[0]
        p = 0x404
        
        if start > 0:
            if verbose: print("Skipping to index")
            for i in range(start):
                p += self.read_pair(p,verbose=verbose)[2]
        
        for i in range(count):
            if verbose: print(i)
            img, i_s, s1 = self.read_pair(p,verbose=verbose)
            yield (img, i_s, i)
            p += s1
    
    def read_pair(self, offset,verbose=False):
        w1, h1, a, b, s1, s2 = struct.unpack('<HHHHhh', self.dat[offset:offset+0xC])
        if verbose: print("PAIR@%04x: %02x %02x %d %d %d %d" %(offset, w1, h1, a, b, s1, s2))
        img, size = self.read_subframe(offset + 0xC, verbose=verbose)
        img_shadow, size2 = self.read_subframe(offset + 0xC + size,
                                               verbose=verbose,is_shadow = True)
        return img, img_shadow, size + size2 + 0xC

    def read_subframe(self, offset, is_shadow=False, verbose=False):
        frame_size, width, height = struct.unpack("<LHH", self.dat[offset:offset+8])

        # no-shadow
        if frame_size == 0:
            return None, 4

        s_lo = 2 * height
        if verbose: print("@%04x: %04x %04x (%02x %02x)" % (offset, offset + 8 + s_lo,
                                                offset + 4 + frame_size, width,
             height))

        rowptrs = []
        for i in range(0, height*2,2):
            rowptrs.append(struct.unpack("<H", self.dat[offset+8+i:offset+8+i+2])[0])
        #print("\n".join("%02x" % dd for dd in rowptrs))

        img = Image.new('RGB', (width, height), "black")
        pixels = img.load() # create the pixel map

        for y,r in enumerate(rowptrs):
            self.decode_prle(self.dat[offset + 4 + r:offset + 4 +
                                        frame_size],
                               pixels, y,
                              width, is_shadow=is_shadow, verbose=verbose)
        return img, frame_size + 4

    def decode_prle(self, data, pixels, y, width, verbose=False, is_shadow=False):
        def set_range(xs, d):
            for x, d in enumerate(d):
                pixels[xs + x, y] = self.pal[d]

        def set_range_v(xs, c):
            for x in range(c):
                pixels[xs + x, y] = self.pal[0]


        x = 0
        show_hd = True
        i=0
        while x < width - 2:
            if show_hd and verbose:
                print("%04x: " % i, end='')
                show_hd = False

            opcode = data[i]
            if 0x00 <= opcode <= width:
                size = data[i+1]

                if not is_shadow:
                    v = data[i+2:i+2+size]
                    i += size + 2

                    sstr = "[%s]" % " ".join("%02x" % j for j in v)
                    if verbose:
                        print("0x%02x %02x %s, " % (
                            opcode, size, sstr), end='')
                    set_range(x + opcode, v)
                else:
                    i += 2
                    if verbose:
                        print("0x%02x %02x shd, " % (
                            opcode, size), end='')
                    set_range_v(x + opcode, size)

                x += opcode + size



                assert x <= width
                if size == 0 or (x == width-1 or x == width):
                    if verbose:
                        print("EOLN x=%02x, y=%02x i=%04x" % (x,y,i))
                    show_hd = True
            else:
                raise NotImplementedError("Opcode %02x at %04x" % (opcode, i))
                break


if __name__ == "__main__":
    import sys
    
    #Get the input file, or print usage.
    if (len(sys.argv) > 1) and not('-h' in sys.argv):
        if sys.argv[-1][-3:] != 'ani': print("Warning: ani files are currently the only type supported.")
        reader = ANIReader(sys.argv[-1])
    else:
        print("ANI animation unpacker by Robozome")
        print("Usage: "+sys.argv[0]+" [-o outdir] [-v] [-h] filename.ani")
        print(" -h	Print this help")
        print(" -o	Specify output directory")
        print(" -v	Verbose unpacking")
        sys.exit()
    
    #check for verbosity
    verbose = False
    if '-v' in sys.argv: verbose = True
    
    #Get and create the output directory, if specified.
    path = "."
    if '-o' in sys.argv:
        path = sys.argv[ sys.argv.index('-o')+1 ]
        
        if not os.path.exists(path):
            os.makedirs(path)
    
    
    #get a generator that yields all the images, in img-shadow-index tuples.
    #You can treat this like a list, with a few exceptions.
    img_gen = reader.seek(0,verbose)
    
    for img_pair in img_gen:
        img_pair[0].save(path+"/img_%d.png" % img_pair[2], "png")
        if img_pair[1] is not None:
                img_pair[1].save(path+"/img_%d_shadow.png" % img_pair[2], "png")
