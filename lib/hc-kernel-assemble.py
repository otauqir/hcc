#!/usr/bin/python

#hc-kernel-assemble kernel-bitcode kernel-object

import os
from sys import argv, exit
from tempfile import mkdtemp 
from subprocess import Popen, check_call
from shutil import rmtree, copyfile

if __name__ == "__main__":
    bindir = os.path.dirname(argv[0])
    clang = bindir + "/clang"
    llvm_link = bindir + "/llvm-link"
    opt = bindir + "/opt"
    llvm_as = bindir + "/llvm-as"
    llvm_dis = bindir + "/llvm-dis"
    clamp_asm = bindir + "/clamp-assemble"
    libpath = bindir + "/../lib"

    if len(argv) != 3:
        print("Usage: %s kernel-bitcode kernel-object" % argv[0])
        exit(1)

    kernel_input = argv[1]
    command = [clang, "-std=c++amp", "-I" + bindir + "/../../include", "-fPIC", "-O3", "-c", "-o"]

    if not os.path.isfile(kernel_input):
        print("kernel-bitcode %s is not valid" % kernel_input)
        exit(1)

    temp_dir = mkdtemp()
    basename = os.path.basename(argv[2])
    if os.name == "nt":
        temp_name = temp_dir + '\\' + basename
    else:
        temp_name = temp_dir + '/' + basename

    if os.path.isfile(argv[2]):
        copyfile(argv[2], temp_name + ".tmp.o")
        copyfile(argv[2], "C:\\" + basename)
        #os.remove(argv[2])

    check_call([llvm_dis,
        kernel_input,
        "-o",
        temp_name + ".ll"])

    #not sure if this works as inteneded
    f0 = open(temp_name + ".ll", "rb")
    if os.name == "nt":
        f1 = open("nul", "wb")
        ext = ".dll"
    else:
        f1 = open("/dev/null", "wb")
        ext = ".so"
    f2 = open(temp_name + ".kernel_redirect.ll", "wb")
    p = Popen([opt,
        "-load",
        libpath + "/LLVMDirectFuncCall" + ext],
        #"-redirect"],
        stdin = f0,
        stdout = f1,
        stderr = f2)
    p.wait()
    f0.close()
    f1.close()
    f2.close()

    if os.path.isfile(temp_name + ".kernel_redirect.ll") and (os.stat(temp_name + ".kernel_redirect.ll").st_size != 0):
        f0 = open(temp_name + ".ll", "rb")
        if os.name == "nt":
            f1 = open("nul", "ab")
        else:
            f1 = open("/dev/null", "ab")
        f2 = open(temp_name + ".camp.cpp", "wb")
        p = Popen([opt,
            "-load",
            libpath + "/LLVMWrapperGen.so",
            "-gensrc"],
            stdin = f0,
            stdout = f1,
            stderr = f2)
        p.wait()
        f0.close()
        f1.close()
        f2.close()

        check_call([llvm_as,
            temp_name + ".kernel_redirect.ll",
            "-o",
            temp_name + ".kernel_redirect.bc"])
        check_call(command + [temp_name + ".camp.s", "-emit-llvm"])
        check_call(command + [temp_name + ".camp.o"])
        if os.name == "nt":
            check_call(["objcopy",
                "-R",
                ".kernel",
                temp_name + ".camp.o"])
        else:
            check_call(["objcopy",
                "-R",
                ".kernel",
                temp_name + ".camp.o"])
        check_call([llvm_link,
            temp_name + ".kernel_redirect.bc",
            temp_name + ".camp.s",
            "-o",
            temp_name + ".link.bc"])

        check_call([clamp_asm,
            kernel_input + ".bc",
            temp_name + ".camp.o"])
    else:
        os.link(kernel_input, kernel_input + ".bc")
        #copyfile(kernel_input, kernel_input + ".bc")
        if os.name == "nt":
            check_call(["python",
                clamp_asm + ".py",
                kernel_input + ".bc",
                temp_name + ".camp.o"])
        else:
            check_call([clamp_asm,
                kernel_input + ".bc",
                temp_name + ".camp.o"])
        #copyfile(kernel_input + ".bc", kernel_input)
    if os.path.isfile(temp_dir + '/' + basename + ".tmp.o"):
        if os.name == "nt":
            check_call(["LINK",
                "/FORCE:MULTIPLE",
                "/NOENTRY",
                temp_dir + "\\" + basename + ".tmp.o",
                temp_name + ".camp.o",
                "/OUT:" + argv[2]])
        else:
            check_call(["ld",
                "-r",
                "--allow-multiple-definition",
                temp_dir + '/' + basename + ".tmp.o",
                temp_name + ".camp.o",
                "-o",
                argv[2]])
    else:
        copyfile(temp_name + ".camp.o", argv[2])
        os.remove(temp_name + ".camp.o")

    rmtree(temp_dir)
    exit(0)
