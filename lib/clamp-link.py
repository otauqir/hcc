#!/usr/bin/python

import os
from sys import argv, exit
from tempfile import mkdtemp
from shutil import rmtree, copyfile
from subprocess import Popen, check_call, check_output, PIPE

if __name__ == "__main__":

    bindir = os.path.dirname(argv[0])
    link = bindir + "/llvm-link"
    opt = bindir + "/opt"
    clamp_device = bindir + "/clamp-device"
    clamp_embed = bindir + "/clamp-embed"
    clang_offload_bundler = bindir + "/clang-offload-bundler"

    verbose = 0
    amdgpu_target_array = []
    link_kernel_args = []
    link_host_args = []
    link_cpu_args = []
    link_other_args = []

    temp_dir = mkdtemp()

    cxxamp_serialize_symbol_file = temp_dir + "/symbol.txt"
    f = open(cxxamp_serialize_symbol_file, "w")
    f.close()

    args = argv[1:]
    static_lib_list = []
    temp_ar_dirs = []

    if "--verbose" in args:
        verbose = 1

    lib_search_paths = []
    for arg in args:
        if arg[:2] == "-L":
            real_path = os.path.realpath(arg[2:])
            if verbose == 2:
                print("add library path: %s, canonical path: %s" % (arg[2:], real_path))
            lib_search_paths.append(real_path)

    for arg in args:
        if arg.find("--amdgpu-target=") == 0:
            amdgpu_target_array.append(arg[16:])

        objs_to_process = []

        if arg[-4:] == ".cpu":
            copyfile(arg, temp_dir + "/kernel_cpu.o")
            link_cpu_args.append(temp_dir + "/kernel_cpu.o")

        elif arg[-2:] == ".o":
            if verbose == 2:
                print("detect object file to process further: %s" % arg)
            objs_to_process.append(arg)

        elif (arg[:2] == "-l") or (arg[-2:] == ".a"):
            detected_static_library = ""

            if arg[:2] == "-l":
                static_lib_name = "lib" + arg[2:] + ".a"

                if verbose == 2:
                    print("looking for static library %s" % static_lib_name)

                for lib_path in lib_search_paths:
                    full_lib_path = os.path.realpath(lib_path + '/' + static_lib_name)
                    if verbose == 2:
                        print("trying to detect %s" % full_lib_path)

                    if os.path.isfile(full_lib_path):
                        if verbose == 2:
                            print("%s detected" % full_lib_path)
                        detected_static_library = full_lib_path
            else:
                if os.path.isfile(arg):
                    full_lib_path = os.path.realpath(arg)
                    if verbose == 2:
                        print("use .a specified at: %s" % full_lib_path)
                    detected_static_library = full_lib_path

            if detected_static_library != "":
                for lib in static_lib_list:
                    if lib == detected_static_library:
                        detected_static_library = ""
                        break

                if detected_static_library != "":
                    static_lib_list.append(detected_static_library)

            kernel_undetected = 1
            if detected_static_library != "":
                if verbose == 2:
                    print("processing static library %s" % detected_static_library)

                if os.name == "nt":
                    #FIX
                    #use DUMPBIN.EXE /SYMBOLS instead of objdump -t
                    #use FINDSTR
                    #kernel_undetected = check_call()
                    p1 = Popen(["objdump",
                        "-t",
                        detected_static_library],
                        stdout=PIPE)
                    p2 = Popen(["grep",
                        "-q",
                        "\.kernel"],
                        stdin=p1.stdout)
                else:
                    p1 = Popen(["objdump",
                        "-t",
                        detected_static_library],
                        stdout=PIPE)
                    p2 = Popen(["grep",
                        "-q",\
                        "\.kernel"],
                        stdin=p1.stdout)
                p1.stdout.close()
                p2.wait()
                kernel_undetected = p2.returncode

                if kernel_undetected == 0:
                    if verbose == 2:
                        print("kernel detected in %s" % detected_static_library)

                    current_dir = os.getcwd()
                    file = os.path.basename(detected_static_library)
                    ar_temp_dir = temp_dir + '/' + file

                    if verbose == 2:
                        print("creating temp dir: %s" % ar_temp_dir)

                    os.mkdir(ar_temp_dir)
                    temp_ar_dirs.append(ar_temp_dir)
                    os.chdir(ar_temp_dir)

                    if os.name == "nt":
                        #FIX
                        pass
                    else:
                        check_call(["ar",
                            "x",
                            detected_static_library])

                    os.chdir(current_dir)

                    for f in os.listdir(ar_temp_dir):
                        if f[-2:] == ".o":
                            objs_to_process.append(ar_temp_dir + '/' + f)

        elif os.path.isfile(arg):
            #object file without .o extension
            #let's hope we don't get here
            pass

        if len(objs_to_process) == 0:
            if verbose == 2:
                print("passing down link args: %s" % arg)
            link_other_args.append(arg)
            continue

        for obj in objs_to_process:
            if verbose == 2:
                print("processing %s" % obj)

            if os.name == "nt":
                #FIX
                #use DUMPBIN.EXE /SYMBOLS instead of objdump -t
                #use FINDSTR
                p1 = Popen(["objdump",
                    "-t",
                    obj],
                    stdout=PIPE)
                p2 = Popen(["grep",
                    "-q",\
                    "\.kernel"],
                    stdin=p1.stdout)
            else:
                p1 = Popen(["objdump",
                    "-t",
                    obj],
                    stdout=PIPE)
                p2 = Popen(["grep",
                    "-q",\
                    "\.kernel"],
                    stdin=p1.stdout)
            p1.stdout.close()
            p2.wait()
            kernel_undetected = p2.returncode

            if kernel_undetected == 0:
                file = os.path.basename(obj)
                filename = os.path.splitext(file)[0]
                kernel_file = temp_dir + '/' + filename + ".kernel.bc"
                host_file = temp_dir + '/' + filename + ".host.o"

                if os.name == "nt":
                    #FIX
                    pass
                else:
                    check_call(["objcopy",
                        "-O",
                        "binary",
                        "-j",
                        ".kernel",
                        obj,
                        kernel_file])

                    check_call(["objcopy",
                        "-R",
                        ".kernel",
                        obj,
                        host_file])

                    err = open("/dev/null", 'ab')
                    check_call(["objcopy",
                        '@' + cxxamp_serialize_symbol_file,
                        host_file,
                        host_file + ".new"],
                        stderr = err)

                    if os.path.isfile(host_file + ".new"):
                        copyfile(host_file + ".new", host_file)
                        os.remove(host_file + ".new")

                    f = open(cxxamp_serialize_symbol_file, 'a')
                    p1 = Popen(["objdump",
                        "-t",
                        host_file,
                        "-j",
                        ".text"],
                        stderr = err,
                        stdout = PIPE)
                    p2 = Popen(["grep",
                        "g.*__cxxamp_serialize"],
                        stdin = p1.stdout,
                        stdout = PIPE)
                    p3 = Popen(["awk",
                        "{print \"-L\"$6}"],
                        stdin = p2.stdout,
                        stdout = f)
                    p3.wait()
                    f.close()

                link_kernel_args.append(kernel_file)
                link_host_args.append(host_file)
            else:
                link_other_args.append(obj)

    if len(amdgpu_target_array) == 0:
        amdgpu_target_array.append("gfx803")

    if verbose != 0:
        print("AMDGPU target array: ", amdgpu_target_array)
        print("new kernel args: ", link_kernel_args)
        print("new host args: ", link_host_args)
        print("new other args: ", link_other_args)

    if len(link_kernel_args) != 0:
        command = [link]
        command += link_kernel_args
        p1 = Popen(command,
            stdout = PIPE)
        p2 = Popen([opt,
            "-always-inline",
            "-",
            "-o",
            temp_dir + "/kernel.bc"],
            stdin = p1.stdout)
        p2.wait()

        if verbose == 1:
            print("Generating AMD GCN kernel")

        f = open(temp_dir + "/__empty.o", "w")
        f.close()

        clang_offload_bundler_input_args = "-inputs=" + temp_dir + "/__empty.o"
        if os.name == "nt":
            #FIX
            clang_offload_bundler_targets_args = "-targets=i686-pc-windows-msvc"
        else:
            clang_offload_bundler_targets_args = "-targets=host-x86_64-unknown-linux"

        for amdgpu_target in amdgpu_target_array:
            check_call([clamp_device,
                temp_dir + "/kernel.bc",
                temp_dir + "/kernel-" + amdgpu_target + ".hsaco",
                "--amdgpu-target=" + amdgpu_target])

            clang_offload_bundler_input_args += "," + temp_dir + "/kernel-" + amdgpu_target + ".hsaco"
            clang_offload_bundler_targets_args += ",hcc-amdgcn--amdhsa-" + amdgpu_target

        check_call([clang_offload_bundler,
            "-type=o",
            clang_offload_bundler_input_args,
            clang_offload_bundler_targets_args,
            "-outputs=" + temp_dir + "/kernel.bundle"])

        current_dir = os.getcwd()
        os.chdir(temp_dir)
        check_call([clamp_embed,
            "kernel.bundle",
            "kernel_hsa.o"])
        os.chdir(current_dir)

        if os.name == "nt":
            #FIX
            pass
        else:
            command = ["ld", "--allow-multiple-definition", temp_dir + "/kernel_hsa.o"]
        command += link_host_args
        command += link_cpu_args
        command += link_other_args
        check_call(command)

        if os.path.isfile(temp_dir + "/kernel_hsa.o"):
            os.remove(temp_dir + "/kernel_hsa.o")
        if os.path.isfile(temp_dir + "/kernel_cpu.o"):
            os.remove(temp_dir + "/kernel_cpu.o")
        if os.path.isfile(temp_dir + "/__empty.o"):
            os.remove(temp_dir + "/__empty.o")
        if os.path.isfile(temp_dir + "/kernel.bundle"):
            os.remove(temp_dir + "/kernel.bundle")
        for f in os.listdir(temp_dir):
            if f[-6] == ".hsaco":
                os.remove(temp_dir + '/' + f)
        if os.path.isfile(temp_dir + "kernel.bc"):
            os.remove(temp_dir + "kernel.bc")
        for arg in link_kernel_args:
            os.remove(arg)
        for arg in link_host_args:
            os.remove(arg)
        if os.path.isfile(cxxamp_serialize_symbol_file):
            os.remove(cxxamp_serialize_symbol_file)
        for td in temp_ar_dirs:
            rmtree(td)
        if os.path.isdir(temp_dir):
            rmtree(temp_dir)

        exit(0)
