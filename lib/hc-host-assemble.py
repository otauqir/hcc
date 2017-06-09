#!/usr/bin/python

#hc-host-assemble host-bitcode host-object (options)

from sys import argv, exit
import os
from subprocess import Popen, check_call
from tempfile import mkdtemp 
from shutil import rmtree

if __name__ == "__main__":

    bindir = os.path.dirname(argv[0])
    clang = bindir + "/clang"
    opt = bindir + "/opt"
    llvm_as = bindir + "/llvm-as"
    llvm_dis = bindir + "/llvm-dis"
    libpath = bindir + "/../lib"

    if len(argv) < 3:
        print("Usage: %s host-bitcode host-object (options)" % argv[0])
        exit(1)

    if not os.path.isfile(argv[1]):
        print("host-bitcode %s is not valid" % argv[1])
        exit(1)

    command = [clang]
    if len(argv) >= 3:
        num = 3
        while num < len(argv):
            command.append(argv[num])
            num += 1
    
    temp_dir = mkdtemp()
    basename = os.path.basename(argv[2])
    temp_name = temp_dir + '/' + basename

    check_call([llvm_dis,
        argv[1],
        "-o",
        temp_name + ".ll"])
    
    #not sure if this works as inteneded
    f0 = open(temp_name + ".ll", "rb")
    if os.name == "nt":
        f1 = open("nul", "ab")
        ext = ".dll"
    else:
        f1 = open("/dev/null", "ab")
        ext = ".so"
    f2 = open(temp_name + ".host_redirect.ll", "wb")
    check_call([opt,
        "-load",
        libpath + "/LLVMDirectFuncCall" + ext],
        #"-redirect",
        #"-host"],
        stdin = f0,
        stdout = f1)
    f0.close()
    f1.close()
    f2.close()
    
    command += ["-c", "-o", argv[2]]

    if os.path.isfile(temp_name + ".host_redirect.ll") and (os.stat(temp_name + ".host_redirect.ll").st_size != 0):
        check_call([llvm_as,
            temp_name + ".host_redirect.ll",
            "-o",
            temp_name + ".host_redirect.bc"])
        command.append(temp_name + ".host_redirect.bc")
        check_call(command)
    else:
        os.link(argv[1], argv[1] + ".bc")
        command.append(argv[1] + ".bc")
        check_call(command)
    
    rmtree(temp_dir)
    exit(0)