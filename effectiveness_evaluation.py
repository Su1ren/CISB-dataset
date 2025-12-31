#!/usr/bin/python3
"""
This script evaluates the effectiveness of different compiler strategies (options)
in preventing bugs in the CISB dataset. It reads compiler options and test configurations,
runs the tests, and reports statistics on bug prevention and undefined behavior (UB) detection.
Some special cases are handled for specific test files.
"""

import argparse
import yaml
import os
from reproduction_material.reproduction_tester import bug_not_trigger
from reproduction_material.reproduction_tester import ubsan_testing
from reproduction_material.reproduction_tester import warning_testing
from reproduction_material.reproduction_tester import arm_file_list

config_file_path = 'reproduction_material/config.yml'
reproduce_set_path = 'reproduction_material/test_cases/'

class EvaluationStats:
    """Holds statistics for the evaluation process."""
    def __init__(self):
        self.num_bug = 0
        self.num_nobug = 0
        self.num_bug_clang = 0
        self.num_nobug_clang = 0
        self.num_bug_gcc = 0
        self.num_nobug_gcc = 0
        self.num_UB_gcc = 0
        self.num_UB_clang = 0
        self.num_UBno_clang = 0
        self.num_UBno_gcc = 0

    def to_list(self):
        """Returns the stats as a list for compatibility."""
        return [
            self.num_UB_gcc, self.num_UBno_gcc, 
            self.num_bug_gcc, self.num_nobug_gcc, 
            self.num_UB_clang, self.num_UBno_clang, 
            self.num_bug_clang, self.num_nobug_clang
        ]

def _handle_special_cases(config_name, file_name, option_file_name, output, stats, clang_only, gcc_only, ubsan_flag, warning_flag):
    """
    Handles special cases for specific files (ARM cases).
    @return: True if a special case was handled, False otherwise.
    """
    if config_name == arm_file_list[0]: # l_23.c
        if ubsan_flag or warning_flag:
            # not UB
            return True
        if 'All-cisb' in option_file_name:
            if output == 'verbose':
                print('no bug file:  ', file_name)
            stats.num_nobug += 1
            if not clang_only:
                stats.num_nobug_gcc += 1
            if not gcc_only:
                stats.num_nobug_clang += 1
        else:
            if output == 'verbose':
                print('bug file:  ', file_name)
            stats.num_bug += 1
            if not clang_only:
                stats.num_bug_gcc += 1
            if not gcc_only:
                stats.num_bug_clang += 1
        return True
    
    if config_name == arm_file_list[1]: # b_26.c
        stats.num_bug += 1
        if output == 'verbose':
            print('bug file:  ', file_name)
        stats.num_bug += 1 # Kept from original logic
        if not clang_only:
            stats.num_bug_gcc += 1
            stats.num_UB_gcc += 1
        if not gcc_only:
            stats.num_bug_clang += 1
            stats.num_UB_clang += 1
        return True

    return False

def _run_ubsan_test(cc, args, file_name, input_str, UB_flag, output, stats, reproduce_set_path):
    """Runs UBSan testing."""
    if not UB_flag:
        if output == 'verbose':
            print(file_name + ' do not support this test')
        return

    try:
        res = ubsan_testing(cc, args, reproduce_set_path, file_name, input_str, output=output)
        if res:
            if 'gcc' in cc: stats.num_UBno_gcc += 1
            if 'clang' in cc: stats.num_UBno_clang += 1
        else:
            if 'gcc' in cc: stats.num_UB_gcc += 1
            if 'clang' in cc: stats.num_UB_clang += 1
    except Exception:
        # time out or gcc4 do not support ubsan
        if 'gcc' in cc: stats.num_UB_gcc += 1
        if 'clang' in cc: stats.num_UB_clang += 1

def _run_warning_test(cc, args, file_name, UB_flag, cc_type, output, stats, reproduce_set_path):
    """Runs warning testing."""
    if not UB_flag:
        if output == 'verbose':
            print(file_name + ' do not support this test')
        return

    Wall_num = warning_testing(cc, args, reproduce_set_path, file_name)
    if Wall_num:
        stats.num_nobug += 1
        if cc_type == 'clang':
            stats.num_nobug_clang += 1
            if UB_flag: stats.num_UBno_clang += 1
        elif cc_type == 'gcc':
            stats.num_nobug_gcc += 1
            stats.num_UBno_gcc += 1
        if output == 'verbose':
            print("-Wall protect file: ", file_name + ' in ' + cc_type)
    else:
        stats.num_bug += 1
        if cc_type == 'clang':
            stats.num_bug_clang += 1
            if UB_flag: stats.num_UB_clang += 1
        elif cc_type == 'gcc':
            stats.num_bug_gcc += 1
            stats.num_UB_gcc += 1
        if output == 'verbose':
            print("-Wall fail to protect file: ", file_name + ' in ' + cc_type)

def _run_standard_test(cc, args, file_name, input_str, check_type, test_str, section_start, section_end, UB_flag, cc_type, output, stats, reproduce_set_path):
    """Runs standard bug trigger testing."""
    # Compile
    compile_cmd = f"{cc} {args} {reproduce_set_path}{file_name}"
    if check_type in [5, 6, 7]:
        section_end = ':'
        args += ' -S -o temp.s '
        compile_cmd = f"{cc} {args} {reproduce_set_path}{file_name}"
    
    if output == 'verbose':
        print(compile_cmd)
    
    ret_code = os.system(compile_cmd)
    if ret_code != 0:
        # Original code asserted.
        raise RuntimeError(f"Compilation failed: {compile_cmd}")

    # Check
    is_protected = bug_not_trigger(check_type, input_str, test_str, section_start, section_end) or \
                   warning_testing(cc, args, reproduce_set_path, file_name)
    
    if is_protected:
        stats.num_nobug += 1
        if cc_type == 'clang':
            stats.num_nobug_clang += 1
            if UB_flag: stats.num_UBno_clang += 1
        elif cc_type == 'gcc':
            stats.num_nobug_gcc += 1
            if UB_flag: stats.num_UBno_gcc += 1
        if output == 'verbose':
            print("protect file: ", file_name + '_' + cc_type)
    else:
        stats.num_bug += 1
        if cc_type == 'clang':
            stats.num_bug_clang += 1
            if UB_flag: stats.num_UB_clang += 1
        elif cc_type == 'gcc':
            stats.num_bug_gcc += 1
            if UB_flag: stats.num_UB_gcc += 1
        if output == 'verbose':
            print("cisb in file: ", file_name + '_' + cc_type)

def _print_summary(output, warning_flag, ubsan_flag, clang_only, gcc_only, stats):
    """Prints the summary of the evaluation."""
    if output != 'verbose':
        return

    if warning_flag:
        total_gcc = stats.num_UB_gcc + stats.num_UBno_gcc
        if total_gcc > 0:
            print('gcc Wall protect UB: ', stats.num_UBno_gcc, 'total: ', total_gcc, stats.num_UBno_gcc/total_gcc)
        
        total_clang = stats.num_UB_clang + stats.num_UBno_clang
        if total_clang > 0:
            print('clang Wall protect UB: ', stats.num_UBno_clang, 'total: ', total_clang, stats.num_UBno_clang/total_clang)
            
    elif ubsan_flag:
        total_gcc = stats.num_UB_gcc + stats.num_UBno_gcc
        if total_gcc > 0:
            print('gcc ubsan protect UB: ', stats.num_UBno_gcc, 'total: ', total_gcc, stats.num_UBno_gcc/total_gcc)
        
        total_clang = stats.num_UB_clang + stats.num_UBno_clang
        if total_clang > 0:
            print('clang ubsan protect UB: ', stats.num_UBno_clang, 'total: ', total_clang, stats.num_UBno_clang/total_clang)
    
    else:
        if not clang_only:
            total_gcc = stats.num_bug_gcc + stats.num_nobug_gcc
            if total_gcc > 0:
                print('Prevent ' + str(stats.num_nobug_gcc) + ' gcc bugs in all ' + str(total_gcc) + ' bugs', stats.num_nobug_gcc / total_gcc)
            
            total_ub_gcc = stats.num_UB_gcc + stats.num_UBno_gcc
            if total_ub_gcc > 0:
                print('prevent UB: ', stats.num_UBno_gcc, 'total: ', total_ub_gcc, stats.num_UB_gcc/total_ub_gcc)
        
        if not gcc_only:
            total_clang = stats.num_bug_clang + stats.num_nobug_clang
            if total_clang > 0:
                print('Prevent ' + str(stats.num_nobug_clang) + ' clang bugs in all ' + str(total_clang) + ' bugs', stats.num_nobug_clang / total_clang)
            
            total_ub_clang = stats.num_UB_clang + stats.num_UBno_clang
            if total_ub_clang > 0:
                print('prevent UB: ', stats.num_UBno_clang, 'total: ', total_ub_clang, stats.num_UB_clang/total_ub_clang)

def get_dataset_value(option_file_name, output='verbose'):
    """
    Evaluates the dataset against the provided compiler options.

    Args:
        option_file_name (str): Path to the file containing compiler options.
        output (str, optional): Output mode. Defaults to 'verbose'.

    Returns:
        list: A list of statistics.
    """
    stats = EvaluationStats()
    clang_only = 'clang' in option_file_name
    gcc_only = 'gcc' in option_file_name
    ubsan_flag = 'ubsan' in option_file_name
    warning_flag = 'wall' in option_file_name and not ubsan_flag

    with open(option_file_name, 'r') as f:
        args_origin = f.read().strip()

    opti_level = args_origin.split(' ')[0]

    with open(config_file_path, 'r') as f:
        configs = yaml.safe_load(f.read())

    for config_name, config in configs.items():
        file_name = config['file_name']
        
        if _handle_special_cases(config_name, file_name, option_file_name, output, stats, clang_only, gcc_only, ubsan_flag, warning_flag):
            continue

        cc = config['cc']
        if opti_level != '-' + config_name.split('-')[-1]:
            continue
        
        cc_type = ''
        if 'gcc' in cc:
            if clang_only: continue
            cc_type = 'gcc'
        elif 'clang' in cc:
            if gcc_only: continue
            cc_type = 'clang'
        
        # Prepare arguments
        args = args_origin
        input_str = str(config.get('input', ''))
        if input_str == 'None': input_str = ''
        
        check_type = config['check_type']
        test_str = config['test_str']
        section_name = config['section_name']
        special_cause = config.get('special_cause')
        UB_flag = (special_cause == 'UB')

        # Parse section name
        section_end = '>:'
        if section_name and str(section_name).startswith('between'):
            parts = section_name.split(' ')
            section_start = parts[1]
            section_end = parts[2]
        else:
            section_start = section_name

        if 'default_option' in config:
            args += ' ' + config['default_option']

        # GCC version specific adjustments
        if cc == 'gcc-4.4':
            args = args.replace('-fno-aggressive-loop-optimizations', '')\
                       .replace('-fno-optimize-strlen', '')\
                       .replace('-fno-tree-forwprop', '')
        if cc == 'gcc-4.1':
            args = args.replace('-fno-aggressive-loop-optimizations', '')\
                       .replace('-fno-optimize-strlen', '')\
                       .replace('-fno-tree-forwprop', '')\
                       .replace('-fno-strict-overflow', '')\
                       .replace('-fno-dce', '')

        # Run Tests
        if ubsan_flag:
            _run_ubsan_test(cc, args, file_name, input_str, UB_flag, output, stats, reproduce_set_path)
        elif warning_flag:
            _run_warning_test(cc, args, file_name, UB_flag, cc_type, output, stats, reproduce_set_path)
        else:
            _run_standard_test(cc, args, file_name, input_str, check_type, test_str, section_start, section_end, UB_flag, cc_type, output, stats, reproduce_set_path)

    _print_summary(output, warning_flag, ubsan_flag, clang_only, gcc_only, stats)
    return stats.to_list()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-opt', type=argparse.FileType('r'), help='Choose one option file in \'compiler_strategies\' directory')
    input_args = parser.parse_args()
    if input_args.opt:
        evaluate_options = input_args.opt
        get_dataset_value(evaluate_options.name)
    else:
        parser.print_help()
