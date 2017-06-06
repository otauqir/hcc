#!/usr/bin/python

from sys import argv, exit
import os
from subprocess import check_call

if __name__ == "__main__":

    if len(argv) != 3:
        print("Usage: %s input_onject output_kernel" % argv[0])
        exit(1)

    if not os.path.isfile(argv[1]):
        print("input object %s is not valid" % argv[1])
        exit(1)

    bindir = os.path.dirname(argv[0])
    opt = bindir + "/opt"
    llc = bindir + "/llc"
    lib = bindir + "../lib"

    file = os.path.basename(argv[1])
    if file[-3:] == "cpu":
        filename = file[:-3]
    else:
        filename = file

    if file != filename:
        check_call(["OPT",
            "-load",
            lib + "/LLVMCpuRename.so",
            "-cpu-rename",
            argv[1],
            "-S",
            "-o",
            argv[1] + ".S"])
        check_call(["-O=2",
            argv[1] + ".S",
            "-relocation-model=pic",
            "-filetype=obj",
            "-o",
            argv[2]])
        os.remove(argv[1] + ".S")
    else:
        if os.name == "nt":
            check_call(["objcopy",
                "-B",
                "i386:x86-64",
                "-I",
                "binary",
                "-O",
                "pe-i386",
                "--rename-section",
                ".data=.kernel",
                argv[1],
                argv[2]])
        else:
            check_call(["objcopy",
                "-B",
                "i386:x86-64",
                "-I",
                "binary",
                "-O",
                "elf64-x86-64",
                "--rename-section",
                ".data=.kernel",
                argv[1],
                argv[2]])
    exit(0)

        
