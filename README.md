# ANIReader
A converter for 3DO Army Men *.ani files to PNG.

Requires python3 and pillow

Usage: unpacker.py [-o outdir] [-v] [-h] filename.ani

* -h	Print this help
* -o	Specify output directory
* -v	Verbose unpacking

Arguments can come in any order, except for the input .ani, which must
come last.

Credit to /u/Robozome for reverse engineering the format and writing the
conversion, and for /u/HMS3 for telling us about the need for it.

This repository is probably going to just act as an archive, not for
active development. I just didn't want it to be lost to the net after we
spent a few days writing the code up.

If you want the nitty gritty of the format without wading through code,
check FORMAT.txt. It has everything I know about it.

--Willrandship
