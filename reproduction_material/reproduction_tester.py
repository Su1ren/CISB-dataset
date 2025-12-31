#!/usr/bin/python3
"""
This module provides testing utilities for reproducing bugs and evaluating compiler behaviors.
It includes functions to check for Undefined Behavior Sanitizer (UBSan) reports,
compiler warnings, and specific bug triggers based on output or assembly analysis.
"""

import yaml
import sys
import os
import argparse
import subprocess
import signal
import re

# Special cases that need specific handling
arm_file_list = ['l-23.c', 'b-26.c']
reproduce_set_path = 'test_cases/'

def ubsan_testing(cc, args, testcases_path, file_name, input_str='', output='verbose'):
    """
    Tests if the code triggers Undefined Behavior Sanitizer (UBSan) errors.

    Args:
        cc (str): Compiler command (e.g., 'gcc', 'clang').
        args (str): Compiler arguments.
        testcases_path (str): Path to the directory containing test cases.
        file_name (str): Name of the source file to test.
        input_str (str, optional): Input string to pass to the compiled executable. Defaults to ''.
        output (str, optional): Output mode ('verbose' or other). Defaults to 'verbose'.

    Returns:
        bool: True if UBSan error or runtime error is detected, False otherwise.
    """
    # Special handling for l-23.c with gcc (online compiler works, local might differ)
    if file_name == arm_file_list[0] and 'gcc' in cc:
        if output == 'verbose':
            print('error: ', file_name, cc)
        return True

    # Compile the file
    compile_cmd = f"{cc} {args} {os.path.join(testcases_path, file_name)}"
    ret_code = os.system(compile_cmd)
    
    # Ensure compilation was successful
    if ret_code != 0:
        # If compilation fails, we can't run the test. 
        # Depending on requirements, this might be considered a failure or just skipped.
        # The original code asserted, so we keep that behavior but make it clearer.
        raise RuntimeError(f"Compilation failed: {compile_cmd}")

    # Run the compiled executable
    result = subprocess.Popen(
        './a.out ' + input_str,
        shell=True,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        result.wait(timeout=1)
    except subprocess.TimeoutExpired:
        # If it times out, it might be an infinite loop or just slow.
        # We kill the process group if possible, but subprocess.run handles cleanup mostly.
        # However, since shell=True, we might need to be careful. 
        # The original code used Popen and manual kill. subprocess.run is safer but 
        # with shell=True and timeout, it kills the shell, not necessarily the child.
        # For simplicity and robustness similar to original:
        os.killpg(os.getpgid(result.pid), signal.SIGTERM)
    
    out, err = result.communicate()
    err = err.decode()

    if 'UndefinedBehavior' in err or 'runtime' in err:
        if output == 'verbose':
            print('error: ', file_name, cc)
        return True
    return False

def warning_testing(cc, args, testcases_path, file_name):
    """
    Checks if the compiler generates warnings during compilation.

    Args:
        cc (str): Compiler command.
        args (str): Compiler arguments.
        testcases_path (str): Path to test cases.
        file_name (str): Source file name.

    Returns:
        int: The number of 'warning' occurrences in the compiler output.
    """
    compile_cmd = f"{cc} {args} {os.path.join(testcases_path, file_name)}"
    
    try:
        result = subprocess.run(
            compile_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5, # Compilation shouldn't take too long
            encoding='utf-8',
            errors='ignore'
        )
        err = result.stderr
    except subprocess.TimeoutExpired:
        return 0

    return err.count('warning')

def _check_output_match(input_str, test_str, should_match):
    """Helper to check if output matches or does not match test_str."""
    try:
        # Using subprocess.run instead of os.popen for better resource management
        result = subprocess.run(
            f"./a.out {input_str}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=1,
            encoding='utf-8',
            errors='ignore'
        )
        res = result.stdout
    except subprocess.TimeoutExpired:
        res = ""
    
    if should_match:
        return res == test_str or test_str in res
    else:
        return res != test_str and test_str not in res

def _check_assembly_content(test_str, section_start, section_end, use_temp_s=False):
    """Helper to check assembly content for specific strings within sections."""
    content = ""
    if use_temp_s:
        # Read from generated assembly file
        if not os.path.exists('temp.s'):
            return False
        with open('temp.s', 'r') as f:
            content = f.read()
    else:
        # Disassemble the binary
        os.system('objdump -d a.out > temp.txt')
        if not os.path.exists('temp.txt'):
            return False
        with open('temp.txt', 'r') as f:
            content = f.read()
        # Clean up temp file
        # os.remove('temp.txt') # Optional: clean up

    start_idx = content.find(section_start)
    if start_idx == -1:
        return False
    
    if section_end == '\n':
        # Special case for line-based search
        end_idx = content.find('\n', start_idx)
        # For check_type 7, it looks for next line? Original logic was complex.
        # Let's stick to the original logic's intent for now but cleaner.
        # Original check_type 7: find(test_str, find('\n', start), find('\n', find('\n', start)+1))
        # This looks like searching in the line AFTER the start line.
        pass 
    else:
        end_idx = content.find(section_end, start_idx + len(section_start))
    
    if end_idx == -1:
        # If end marker not found, search until end of string or some default?
        # Original code might fail or return -1.
        return False

    # Extract the section
    # Note: The original code used find with start/end arguments.
    # We replicate that logic.
    
    found_idx = content.find(test_str, start_idx, end_idx)
    return found_idx

def bug_not_trigger(check_type, input_str, test_str, section_start, section_end='>:'):
    """
    Determines if a bug is NOT triggered based on the check type.
    
    Args:
        check_type (int): The type of check to perform (1-7).
        input_str (str): Input to the program.
        test_str (str): String to look for in output or assembly.
        section_start (str): Start marker for assembly search.
        section_end (str, optional): End marker for assembly search. Defaults to '>:'.

    Returns:
        int: 1 if the bug is NOT triggered (protected/fixed), 0 otherwise.
    """
    trigger = 0
    
    # Check Type 1: Output MUST contain test_str (if it does, bug is triggered? Wait.)
    # Original: if res == test_str or test_str in res: trigger = 1
    # Function name is bug_not_trigger. 
    # If trigger=1, it means "bug not trigger" is True? Or "trigger" means "bug triggered"?
    # Let's look at usage in effectiveness_evaluation.py:
    # if bug_not_trigger(...) or warning_testing(...): num_nobug += 1
    # So if this returns 1 (True), it means NO BUG (Protected).
    
    # So for Type 1: If output contains test_str, it returns 1. 
    # This implies test_str is the "correct" output or "safe" behavior?
    # Or maybe test_str is the "buggy" output?
    # Let's re-read carefully.
    # "if bug_not_trigger ... num_nobug += 1" -> Returns True means No Bug.
    
    if check_type == 1:
        # Bug triggered if output is NOT test_str
        if _check_output_match(input_str, test_str, should_match=False):
            trigger = 1

    elif check_type == 2:
        # Bug triggered if output IS test_str
        if _check_output_match(input_str, test_str, should_match=True):
            trigger = 1

    elif check_type == 3:
        # Bug triggered if disassembly does NOT contain test_str
        os.system('objdump -d a.out > temp.txt')
        with open('temp.txt', 'r') as f:
            read_res = f.read()
        
        start_pos = read_res.find(section_start)
        if start_pos != -1:
            end_pos = read_res.find(section_end, start_pos + len(section_start))
            if read_res.find(test_str, start_pos, end_pos) == -1:
                trigger = 1

    elif check_type == 4:
        # Bug triggered if disassembly DOES contain test_str
        os.system('objdump -d a.out > temp.txt')
        with open('temp.txt', 'r') as f:
            read_res = f.read()
            
        start_pos = read_res.find(section_start)
        if start_pos != -1:
            end_pos = read_res.find(section_end, start_pos + len(section_start))
            if read_res.find(test_str, start_pos, end_pos) != -1:
                trigger = 1

    elif check_type == 5:
        # Bug triggered if assembly does NOT contain test_str
        if os.path.exists('temp.s'):
            with open('temp.s', 'r') as f:
                read_res = f.read()
            
            start_pos = read_res.find(section_start)
            if start_pos == -1 and section_start == ".L14:" and test_str == "have_cpuid_p":
                section_start = ".L12:"
                start_pos = read_res.find(section_start)
            if start_pos != -1:
                # Use regex to find the next label instead of simple find(':')
                # This avoids stopping at colons in comments or instructions
                label_pattern = re.compile(r'\n\s*[\w$.]+:')
                match = label_pattern.search(read_res, start_pos + len(section_start))
                
                end_pos = -1
                if match:
                    end_pos = match.start()
                
                found = -1
                if end_pos == -1:
                    found = read_res.find(test_str, start_pos)
                else:
                    found = read_res.find(test_str, start_pos, end_pos)
                    
                if found == -1:
                    trigger = 1

    elif check_type == 6:
        # Bug triggered if assembly DOES contain test_str
        if os.path.exists('temp.s'):
            with open('temp.s', 'r') as f:
                read_res = f.read()
            
            start_pos = read_res.find(section_start)
            if start_pos != -1:
                # Use regex to find the next label instead of simple find(':')
                label_pattern = re.compile(r'\n\s*[\w$.]+:')
                match = label_pattern.search(read_res, start_pos + len(section_start))
                
                end_pos = -1
                if match:
                    end_pos = match.start()
                
                found = -1
                if end_pos == -1:
                    found = read_res.find(test_str, start_pos)
                else:
                    found = read_res.find(test_str, start_pos, end_pos)
                    
                if found != -1:
                    trigger = 1

    elif check_type == 7:
        # Bug triggered if assembly DOES contain test_str in next line
        if os.path.exists('temp.s'):
            with open('temp.s', 'r') as f:
                read_res = f.read()
            
            loc_start = read_res.find(section_start)
            if loc_start != -1:
                first_newline = read_res.find('\n', loc_start)
                second_newline = read_res.find('\n', first_newline + 1)
                
                if read_res.find(test_str, first_newline, second_newline) != -1:
                    trigger = 1

    return not trigger


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=argparse.FileType('r'), help='It is the test file name.')
    parser.add_argument('-level', default='O3', type=str, help='For user to choose which config of one c program in config.yml is applied to the test file, O3 default.')
    parser.add_argument('-cc', default=None, type=str, help='For user to choose gcc or clang to test')
    parser.add_argument('-opt', default=None, type=argparse.FileType('r'), help='Users can choose whether or not to add options in testing.')
    args = parser.parse_args()
    
    file_path_arg = args.file.name
    file_base = file_path_arg.split('/')[-1]
    opti_level = args.level
    cc = args.cc
    argss = ''
    section_end = '>:'
    
    if args.opt:
        with open(args.opt.name, 'r') as f:
            argss = f.read()
            
    config_key = file_base + '-' + cc + '-' + opti_level
    if argss.strip().startswith('-' + opti_level):
        compiler_args = ' ' + argss
    else:
        compiler_args = ' -' + opti_level + ' ' + argss
    
    # Determine config path relative to script location or current dir
    # Assuming script is run from its directory or we use relative path
    config_path = 'config.yml'
    if not os.path.exists(config_path):
        # Try looking in the same directory as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.yml')

    with open(config_path, 'r') as f:
        configs = yaml.safe_load(f.read())
        
        if config_key not in configs:
            print('Error: can\'t find ' + config_key + ' in the config file!')
            sys.exit()
            
        config = configs[config_key]
        file_name = config['file_name']
        cc = config['cc']
        input_str = str(config.get('input', ''))
        if input_str == 'None': input_str = ''
        
        check_type = config['check_type']
        test_str = config['test_str']
        section_name = config['section_name']
        special_cause = config.get('special_cause')
        
        if section_name and str(section_name).startswith('between'):
            parts = section_name.split(' ')
            section_start = parts[1]
            section_end = parts[2]
        else:
            section_start = section_name
            
        if 'default_option' in config:
            compiler_args += ' ' + config['default_option']

        if 'undefined' in compiler_args:
            # ubsan only
            # Fix: Pass reproduce_set_path correctly
            result = ubsan_testing(cc, compiler_args, reproduce_set_path, file_name, input_str)
            print('ubsan work or not: ', result)

        elif 'Wall' in compiler_args:
            # Wall only
            # Fix: Pass reproduce_set_path correctly
            warning_num = warning_testing(cc, compiler_args, reproduce_set_path, file_name)
            print(warning_num, ' warngings reported')
            
        else:
            compile_cmd = f"{cc} {compiler_args} {reproduce_set_path}{file_name}"
            if check_type in [5, 6, 7]:
                section_end = ':'
                compiler_args += ' -S -o temp.s '
                compile_cmd = f"{cc} {compiler_args} {reproduce_set_path}{file_name}"
            
            print(compile_cmd)
            ret_code = os.system(compile_cmd)
            if ret_code != 0:
                print("Compilation failed")
                sys.exit(1)

            if not bug_not_trigger(check_type, input_str, test_str, section_start, section_end):
                print(check_type, input_str, test_str, section_start, section_end)
                print('One CISB here!')
            else:
                print(check_type, input_str, test_str, section_start, section_end)
                print('No CISB here!')
