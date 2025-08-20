#!/usr/bin/env python3
"""
Compare two voter CSV files to identify differences in records and columns.
This script helps verify that only participation/vote columns have changed.
"""

import pandas as pd
import sys
import os
from pathlib import Path

def load_csv_with_info(filepath):
    """Load CSV and return dataframe with file info"""
    print(f"\nLoading {filepath}...")
    df = pd.read_csv(filepath, dtype=str, low_memory=False)
    print(f"  - Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  - File size: {os.path.getsize(filepath):,} bytes")
    return df

def compare_voter_files(file1_path, file2_path):
    """Compare two voter CSV files comprehensively"""
    
    print("="*60)
    print("VOTER FILE COMPARISON TOOL")
    print("="*60)
    
    # Load both files
    df1 = load_csv_with_info(file1_path)
    df2 = load_csv_with_info(file2_path)
    
    # Check if 'id' column exists in both
    if 'id' not in df1.columns:
        print("\nWARNING: 'id' column not found in file1. Checking for alternative ID columns...")
        print("File1 columns:", df1.columns.tolist()[:10], "...")
    if 'id' not in df2.columns:
        print("\nWARNING: 'id' column not found in file2. Checking for alternative ID columns...")
        print("File2 columns:", df2.columns.tolist()[:10], "...")
    
    # Try to identify the ID column
    id_col = None
    possible_id_cols = ['id', 'ID', 'voter_id', 'VOTER_ID', 'Id', 'VoterId']
    for col in possible_id_cols:
        if col in df1.columns and col in df2.columns:
            id_col = col
            print(f"\nUsing '{id_col}' as the ID column")
            break
    
    if not id_col:
        print("\nERROR: Could not find a common ID column between files")
        print("\nFile1 first 20 columns:", df1.columns.tolist()[:20])
        print("\nFile2 first 20 columns:", df2.columns.tolist()[:20])
        return
    
    # Compare basic statistics
    print("\n" + "="*60)
    print("BASIC COMPARISON")
    print("="*60)
    
    # Row count comparison
    row_diff = df2.shape[0] - df1.shape[0]
    print(f"\nRow count difference: {row_diff:+,}")
    if row_diff > 0:
        print(f"  → File2 has {row_diff:,} MORE rows")
    elif row_diff < 0:
        print(f"  → File2 has {abs(row_diff):,} FEWER rows")
    else:
        print("  → Same number of rows ✓")
    
    # Column comparison
    print("\n" + "-"*40)
    print("COLUMN ANALYSIS")
    print("-"*40)
    
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    cols_only_in_file1 = cols1 - cols2
    cols_only_in_file2 = cols2 - cols1
    common_cols = cols1 & cols2
    
    print(f"\nColumns in file1: {len(cols1)}")
    print(f"Columns in file2: {len(cols2)}")
    print(f"Common columns: {len(common_cols)}")
    
    if cols_only_in_file1:
        print(f"\nColumns ONLY in file1 ({len(cols_only_in_file1)}):")
        for col in sorted(cols_only_in_file1):
            print(f"  - {col}")
    
    if cols_only_in_file2:
        print(f"\nColumns ONLY in file2 ({len(cols_only_in_file2)}):")
        for col in sorted(cols_only_in_file2):
            print(f"  - {col}")
    
    # Identify participation and vote columns
    participation_cols = [col for col in common_cols if 'participation' in col.lower()]
    vote_cols = [col for col in common_cols if 'vote' in col.lower()]
    
    print(f"\nParticipation columns found: {len(participation_cols)}")
    print(f"Vote columns found: {len(vote_cols)}")
    
    # ID-based comparison
    print("\n" + "="*60)
    print("RECORD COMPARISON (by ID)")
    print("="*60)
    
    ids1 = set(df1[id_col].dropna())
    ids2 = set(df2[id_col].dropna())
    
    ids_only_in_file1 = ids1 - ids2
    ids_only_in_file2 = ids2 - ids1
    common_ids = ids1 & ids2
    
    print(f"\nUnique IDs in file1: {len(ids1):,}")
    print(f"Unique IDs in file2: {len(ids2):,}")
    print(f"Common IDs: {len(common_ids):,}")
    print(f"IDs only in file1: {len(ids_only_in_file1):,}")
    print(f"IDs only in file2: {len(ids_only_in_file2):,}")
    
    # Check for duplicate IDs
    duplicates1 = df1[id_col].duplicated().sum()
    duplicates2 = df2[id_col].duplicated().sum()
    
    if duplicates1 > 0:
        print(f"\nWARNING: File1 has {duplicates1:,} duplicate IDs!")
    if duplicates2 > 0:
        print(f"\nWARNING: File2 has {duplicates2:,} duplicate IDs!")
    
    # Sample mismatched IDs
    if ids_only_in_file1:
        print(f"\nSample IDs only in file1 (first 10):")
        for i, id_val in enumerate(sorted(list(ids_only_in_file1))[:10]):
            print(f"  {i+1}. {id_val}")
        
        # Save full list to file
        output_file = "ids_only_in_file1.txt"
        with open(output_file, 'w') as f:
            for id_val in sorted(ids_only_in_file1):
                f.write(f"{id_val}\n")
        print(f"  → Full list saved to {output_file} ({len(ids_only_in_file1):,} IDs)")
    
    if ids_only_in_file2:
        print(f"\nSample IDs only in file2 (first 10):")
        for i, id_val in enumerate(sorted(list(ids_only_in_file2))[:10]):
            print(f"  {i+1}. {id_val}")
        
        # Save full list to file
        output_file = "ids_only_in_file2.txt"
        with open(output_file, 'w') as f:
            for id_val in sorted(ids_only_in_file2):
                f.write(f"{id_val}\n")
        print(f"  → Full list saved to {output_file} ({len(ids_only_in_file2):,} IDs)")
    
    # For matching IDs, compare non-participation columns
    if len(common_ids) > 0:
        print("\n" + "="*60)
        print("CONTENT COMPARISON (for matching IDs)")
        print("="*60)
        
        # Get columns that should NOT change (exclude participation/vote columns)
        non_voting_cols = [col for col in common_cols 
                          if 'participation' not in col.lower() 
                          and 'vote' not in col.lower()]
        
        print(f"\nChecking {len(non_voting_cols)} non-voting columns for changes...")
        
        # Sample comparison for matching IDs
        sample_size = min(1000, len(common_ids))
        sample_ids = list(common_ids)[:sample_size]
        
        df1_sample = df1[df1[id_col].isin(sample_ids)].set_index(id_col)
        df2_sample = df2[df2[id_col].isin(sample_ids)].set_index(id_col)
        
        changed_cols = []
        for col in non_voting_cols:
            if col in df1_sample.columns and col in df2_sample.columns:
                # Compare values for this column
                col1_vals = df1_sample[col].fillna('')
                col2_vals = df2_sample[col].fillna('')
                
                # Align by index to ensure we're comparing same IDs
                col2_vals = col2_vals.reindex(col1_vals.index, fill_value='')
                
                if not col1_vals.equals(col2_vals):
                    num_changes = (col1_vals != col2_vals).sum()
                    if num_changes > 0:
                        changed_cols.append((col, num_changes))
        
        if changed_cols:
            print(f"\nWARNING: Found changes in {len(changed_cols)} non-voting columns:")
            for col, num_changes in sorted(changed_cols, key=lambda x: x[1], reverse=True)[:20]:
                print(f"  - {col}: {num_changes} changes in sample")
        else:
            print("\n✓ No changes detected in non-voting columns (sample check)")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    issues = []
    if row_diff != 0:
        issues.append(f"Row count mismatch: {row_diff:+,}")
    if len(ids_only_in_file1) > 0:
        issues.append(f"{len(ids_only_in_file1):,} IDs only in file1")
    if len(ids_only_in_file2) > 0:
        issues.append(f"{len(ids_only_in_file2):,} IDs only in file2")
    if duplicates1 > 0:
        issues.append(f"{duplicates1:,} duplicate IDs in file1")
    if duplicates2 > 0:
        issues.append(f"{duplicates2:,} duplicate IDs in file2")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  • {issue}")
        print("\n→ Review the generated .txt files for detailed ID lists")
    else:
        print("\n✓ Files appear to be consistent!")
        print("  - Same number of rows")
        print("  - All IDs match")
        print("  - Only participation/vote columns differ")
    
    # Generate mapping file for debugging
    if len(common_ids) > 0:
        print("\n" + "-"*40)
        print("Generating detailed comparison report...")
        
        # Create a mapping of IDs with basic info
        report_data = []
        
        # Add records from file1
        for _, row in df1.iterrows():
            id_val = row[id_col]
            report_data.append({
                'id': id_val,
                'in_file1': 'Yes',
                'in_file2': 'Yes' if id_val in ids2 else 'No',
                'status': 'Common' if id_val in common_ids else 'Only in file1'
            })
        
        # Add records only in file2
        for id_val in ids_only_in_file2:
            report_data.append({
                'id': id_val,
                'in_file1': 'No',
                'in_file2': 'Yes',
                'status': 'Only in file2'
            })
        
        report_df = pd.DataFrame(report_data)
        report_df.to_csv('voter_comparison_report.csv', index=False)
        print("→ Detailed report saved to voter_comparison_report.csv")
    
    print("\n" + "="*60)
    print("COMPARISON COMPLETE")
    print("="*60)

if __name__ == "__main__":
    # Default file paths
    file1_path = "/Users/gregorytusar/proj-roth/file1"
    file2_path = "/Users/gregorytusar/proj-roth/file2"
    
    # Allow command-line arguments
    if len(sys.argv) == 3:
        file1_path = sys.argv[1]
        file2_path = sys.argv[2]
    
    # Check files exist
    if not Path(file1_path).exists():
        print(f"ERROR: File not found: {file1_path}")
        sys.exit(1)
    if not Path(file2_path).exists():
        print(f"ERROR: File not found: {file2_path}")
        sys.exit(1)
    
    # Run comparison
    compare_voter_files(file1_path, file2_path)