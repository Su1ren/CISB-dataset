#!/usr/bin/env python3
"""
Bug Reproduction Analysis Script

This script analyzes the CISB dataset to provide statistics on bug distributions
across GCC and Clang compilers, including version usage and exclusivity analysis.
"""

import pandas as pd
import re
from collections import defaultdict, Counter
import sys

def parse_compiler_versions(version_str):
    """
    Parse compiler version string and extract version ranges and flags.
    
    Args:
        version_str: String like "4.8.0-7 -O2; 8-11 -O1; 12 -O0"
    
    Returns:
        List of tuples: [(version_range, flags), ...]
    """
    if pd.isna(version_str) or not version_str.strip():
        return []
    
    entries = []
    # Split by semicolon to handle multiple version entries
    parts = [p.strip() for p in version_str.split(';')]
    
    for part in parts:
        if not part:
            continue
        
        # Match patterns like "4.8.0-7 -O2", "arm 5.4 -O2", "arm64 11.1.0-12.2 -O2"
        # Also handle cases without flags like "4.1.2-10.1"
        # Updated regex to correctly handle 'arm' (without 64), 'arm64', and 'x86'
        match = re.match(r'^((?:arm(?:64)?|x86)?(?:\s+)?)([\d\.]+-?[\d\.]*)\s*(.*)$', part)
        
        if match:
            arch_prefix = match.group(1).strip()
            version_range = match.group(2).strip()
            flags = match.group(3).strip()
            
            full_version = f"{arch_prefix} {version_range}".strip() if arch_prefix else version_range
            entries.append((full_version, flags if flags else ""))
    
    return entries

def classify_bug_exclusivity(gcc_versions, llvm_versions):
    """
    Classify bug as GCC-Exclusive, Clang-Exclusive, or Shared.
    
    Args:
        gcc_versions: List of GCC version entries
        llvm_versions: List of LLVM version entries
    
    Returns:
        String: "GCC-Exclusive", "Clang-Exclusive", or "Shared"
    """
    has_gcc = len(gcc_versions) > 0
    has_llvm = len(llvm_versions) > 0
    
    if has_gcc and has_llvm:
        return "Shared"
    elif has_gcc:
        return "GCC-Exclusive"
    elif has_llvm:
        return "Clang-Exclusive"
    else:
        return "Unknown"

def extract_bug_source(bug_id):
    """
    Extract bug source from unique bug ID.
    
    Args:
        bug_id: String like "b-1", "l-2", "b-8/l-24"
    
    Returns:
        String: "Bugzilla" for b-*, "Linux Kernel" for l-*, "Cross-referenced" for both
    """
    bug_id = str(bug_id).strip()
    
    # b- prefix indicates Bugzilla
    # l- prefix indicates Linux Kernel
    has_b = 'b-' in bug_id
    has_l = 'l-' in bug_id
    
    if has_b and has_l:
        return "Cross-referenced"
    elif has_b:
        return "Bugzilla"
    elif has_l:
        return "Linux Kernel"
    else:
        return "Unknown"

def analyze_bug_reproduction_data(csv_file_path="./dataset/CISB-dataset-reproduce.csv"):
    """
    Main analysis function that processes the CSV and generates statistics.
    """
    print("Loading and analyzing bug reproduction data...")
    print("=" * 60)
    
    # Load the CSV file
    try:
        # Try different encodings in case of encoding issues
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file_path, encoding=encoding)
                print(f"Loaded {len(df)} records from {csv_file_path} (encoding: {encoding})")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Could not read CSV with any encoding")
            
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return
    
    # Filter for successful reproductions only
    successful_df = df[df['Result'] == 'successful'].copy()
    print(f"Found {len(successful_df)} successful reproductions")
    
    # Parse compiler versions
    print("\nParsing compiler version data...")
    successful_df['gcc_parsed'] = successful_df['Compiler version:gcc'].apply(parse_compiler_versions)
    successful_df['llvm_parsed'] = successful_df['Compiler version:llvm'].apply(parse_compiler_versions)
    
    # Classify bug exclusivity
    successful_df['exclusivity'] = successful_df.apply(
        lambda row: classify_bug_exclusivity(row['gcc_parsed'], row['llvm_parsed']), 
        axis=1
    )
    
    # Extract bug source from ID
    successful_df['bug_source'] = successful_df['Unique bug id'].apply(extract_bug_source)
    
    # Statistical Analysis
    print("\n" + "=" * 60)
    print("BUG REPRODUCTION ANALYSIS RESULTS")
    print("=" * 60)
    
    # 1. Bug Source Distribution
    print("\n1. BUG SOURCE DISTRIBUTION")
    print("-" * 30)
    bug_source_counts = successful_df['bug_source'].value_counts()
    total_bugs = len(successful_df)
    
    for source, count in bug_source_counts.items():
        percentage = (count / total_bugs) * 100
        print(f"{source:15} {count:3d} ({percentage:5.1f}%)")
    
    # 2. Exclusivity Analysis
    print("\n2. EXCLUSIVITY ANALYSIS")
    print("-" * 30)
    exclusivity_counts = successful_df['exclusivity'].value_counts()
    
    for exclusivity, count in exclusivity_counts.items():
        percentage = (count / total_bugs) * 100
        print(f"{exclusivity:15} {count:3d} ({percentage:5.1f}%)")
        
        # Print valid IDs for verification
        ids = sorted(successful_df[successful_df['exclusivity'] == exclusivity]['Unique bug id'].tolist())
        print(f"   IDs: {', '.join(ids)}")
    
    # Calculate exclusivity rates
    gcc_exclusive = exclusivity_counts.get('GCC-Exclusive', 0)
    clang_exclusive = exclusivity_counts.get('Clang-Exclusive', 0)
    shared = exclusivity_counts.get('Shared', 0)
    
    if gcc_exclusive + shared > 0:
        gcc_exclusivity_rate = (gcc_exclusive / (gcc_exclusive + shared)) * 100
        print(f"\nGCC Exclusivity Rate: {gcc_exclusivity_rate:.1f}% ({gcc_exclusive}/{gcc_exclusive + shared})")
    
    if clang_exclusive + shared > 0:
        clang_exclusivity_rate = (clang_exclusive / (clang_exclusive + shared)) * 100
        print(f"Clang Exclusivity Rate: {clang_exclusivity_rate:.1f}% ({clang_exclusive}/{clang_exclusive + shared})")
    
    # 3. Version Range Analysis
    print("\n3. MOST FREQUENTLY AFFECTED VERSION RANGES")
    print("-" * 50)
    
    # Collect all GCC version ranges
    gcc_versions = []
    for versions_list in successful_df['gcc_parsed']:
        gcc_versions.extend([v[0] for v in versions_list])
    
    # Collect all LLVM version ranges  
    llvm_versions = []
    for versions_list in successful_df['llvm_parsed']:
        llvm_versions.extend([v[0] for v in versions_list])
    
    print("\nTop GCC Version Ranges:")
    gcc_counter = Counter(gcc_versions)
    for version, count in gcc_counter.most_common(10):
        print(f"  {version:25} {count:3d} bugs")
    
    print("\nTop Clang/LLVM Version Ranges:")
    llvm_counter = Counter(llvm_versions)
    for version, count in llvm_counter.most_common(10):
        print(f"  {version:25} {count:3d} bugs")
    
    # 4. Cross-tabulation: Bug Source vs Exclusivity
    print("\n4. BUG SOURCE vs EXCLUSIVITY CROSS-TABULATION")
    print("-" * 50)
    crosstab = pd.crosstab(successful_df['bug_source'], successful_df['exclusivity'])
    print(crosstab)
    
    # 5. Summary Statistics
    print("\n5. SUMMARY STATISTICS")
    print("-" * 25)
    print(f"Total successful reproductions: {total_bugs}")
    print(f"Bugs affecting GCC: {len(successful_df[successful_df['gcc_parsed'].apply(len) > 0])}")
    print(f"Bugs affecting Clang: {len(successful_df[successful_df['llvm_parsed'].apply(len) > 0])}")
    print(f"Unique GCC version ranges: {len(set(gcc_versions))}")
    print(f"Unique Clang version ranges: {len(set(llvm_versions))}")
    
    # Save detailed results to file
    output_file = csv_file_path.replace('.csv', '_analysis_results.txt').replace('dataset/', '')
    try:
        with open(output_file, 'w') as f:
            # Redirect stdout to file temporarily to capture all prints
            original_stdout = sys.stdout
            sys.stdout = f
            
            # Re-run key analysis sections for file output
            print("BUG REPRODUCTION ANALYSIS RESULTS")
            print("=" * 60)
            print(f"Analysis performed on: {csv_file_path}")
            print(f"Total records: {len(df)}")
            print(f"Successful reproductions: {total_bugs}")
            
            print("\nBUG SOURCE DISTRIBUTION:")
            for source, count in bug_source_counts.items():
                percentage = (count / total_bugs) * 100
                print(f"{source:15} {count:3d} ({percentage:5.1f}%)")
            
            print("\nEXCLUSIVITY ANALYSIS:")
            for exclusivity, count in exclusivity_counts.items():
                percentage = (count / total_bugs) * 100
                print(f"{exclusivity:15} {count:3d} ({percentage:5.1f}%)")
                
                # Print valid IDs for verification
                ids = sorted(successful_df[successful_df['exclusivity'] == exclusivity]['Unique bug id'].tolist())
                print(f"   IDs: {', '.join(ids)}")
            
            print("\nCROSS-TABULATION:")
            print(crosstab)
            
            sys.stdout = original_stdout
            
        print(f"\nDetailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"Warning: Could not save results to file: {e}")
    
    # print("\nAnalysis completed successfully!")

if __name__ == "__main__":
    analyze_bug_reproduction_data()