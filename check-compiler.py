import subprocess

# required compilers
compiler_list = ['clang-11', 'clang-12', 'clang-14', 'clang-17', 'gcc-4.1', 'gcc-4.4', 'gcc-4.9', 'gcc-7', 'gcc-12']

if __name__ == '__main__':
    for compiler in compiler_list:
        result = subprocess.Popen(compiler + ' --version', shell=True, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        err = err.decode()
        if err:
            print('Compiler ' + compiler + ' do not exits, run script/auto_get_compiler.sh or maybe you should install it manually!')
        else:
            print('Compiler ' + compiler + ' is installed successfully')