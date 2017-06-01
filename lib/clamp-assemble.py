#!/usr/bin/python
#clamp-assemble kernel-bitcode kernel-object

from sys import argv, exit
import os
from shutil import copyfile
from subprocess import check_call

if __name__ == "__main__":

    bindir = os.path.dirname(argv[0])
    if os.name == "nt":
        embed = bindir + "/clamp-embed.py"
    else:
        embed = bindir + "/clamp-embed"

    if len(argv) != 3:
        print("Usage: %s kernel-bitcode object" % argv[0])
        exit(1)

    if not os.path.isfile(argv[1]):
        print("kernel-bitcode %s is not valid" % argv[1])
        exit(1)
    
    if os.path.isfile(argv[2]):
        copyfile(argv[2], argv[2] + ".host.o")
        os.remove(argv[2])
        check_call(["python",
            embed,
            argv[1],
            argv[2] + ".kernel.o"])

        if os.name == "nt": #Windows
            check_call(["LINK",
                "/NODEFAULTLIB:msvcrt.lib",
                #"/FORCE:MULTIPLE",
                "/INCREMENTAL",
                "/SUBSYSTEM:CONSOLE",
                "/IGNORE:4006",
                "/LIBPATH:C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\lib\amd64",
                "libcmt.lib",
                "vcruntime.lib",
                "/VERBOSE:Lib",
                "/MACHINE:X86",
                argv[2] + ".kernel.o",
                argv[2] + ".host.o",
                "/OUT:" + argv[2]])
        else: #Linux
            check_call(["ld",
                "-r",
                argv[2] + ".kernel.o",
                argv[2] + ".host.o",
                "-o",
                argv[2]])

        os.remove(argv[2] + ".kernel.o")
        os.remove(argv[2] + ".host.o")
    else:
        check_call(["python",
            embed,
            argv[1],
            argv[2]])

    exit(0)


