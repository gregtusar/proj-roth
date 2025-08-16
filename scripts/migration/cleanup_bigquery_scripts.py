#!/usr/bin/env python3
"""
Cleanup script to remove BigQuery-specific geocoding scripts and replace with PostgreSQL versions.
This script identifies and removes the complex threading-based BigQuery scripts.
"""

import os
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BigQueryScriptCleanup:
    """Handles cleanup of BigQuery-specific scripts."""
    
    def __init__(self, repo_root: str = "/home/ubuntu/repos/proj-roth"):
        self.repo_root = Path(repo_root)
        self.backup_dir = self.repo_root / "backup_bigquery_scripts"
        
    def create_backup_directory(self):
        """Create backup directory for removed scripts."""
        self.backup_dir.mkdir(exist_ok=True)
        logger.info(f"📁 Created backup directory: {self.backup_dir}")
    
    def backup_and_remove_file(self, file_path: Path, reason: str):
        """Backup a file to backup directory and remove from original location."""
        if not file_path.exists():
            logger.warning(f"⚠️ File not found: {file_path}")
            return
        
        backup_path = self.backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)
        logger.info(f"💾 Backed up {file_path.name} to {backup_path}")
        
        file_path.unlink()
        logger.info(f"🗑️ Removed {file_path.name} - {reason}")
    
    def cleanup_geocoding_scripts(self):
        """Remove BigQuery-specific geocoding scripts."""
        logger.info("🧹 Cleaning up BigQuery geocoding scripts...")
        
        geocoding_dir = self.repo_root / "scripts" / "geocoding"
        
        scripts_to_remove = [
            {
                "file": "bigquery_geocoding_pipeline.py",
                "reason": "BigQuery-specific base class, replaced by PostgreSQL version"
            },
            {
                "file": "ultra_fast_geocoding_pipeline.py", 
                "reason": "Complex threading BigQuery pipeline, replaced by simple PostgreSQL version"
            },
            {
                "file": "ultra_simple_linear_geocoding.py",
                "reason": "BigQuery-dependent linear script, replaced by PostgreSQL version"
            },
            {
                "file": "optimized_geocoding_pipeline.py",
                "reason": "BigQuery optimization script, no longer needed"
            },
            {
                "file": "simple_linear_geocoding.py",
                "reason": "Another BigQuery linear script, consolidated into PostgreSQL version"
            }
        ]
        
        for script_info in scripts_to_remove:
            file_path = geocoding_dir / script_info["file"]
            self.backup_and_remove_file(file_path, script_info["reason"])
    
    def cleanup_visualization_scripts(self):
        """Remove BigQuery-specific visualization scripts."""
        logger.info("🧹 Cleaning up BigQuery visualization scripts...")
        
        viz_dir = self.repo_root / "scripts" / "visualization"
        
        scripts_to_remove = [
            {
                "file": "create_mapping_visualizations.py",
                "reason": "BigQuery-dependent visualization, needs PostgreSQL version"
            },
            {
                "file": "fixed_create_mapping_visualizations.py",
                "reason": "BigQuery-dependent visualization fix, needs PostgreSQL version"
            }
        ]
        
        for script_info in scripts_to_remove:
            file_path = viz_dir / script_info["file"]
            self.backup_and_remove_file(file_path, script_info["reason"])
    
    def cleanup_setup_scripts(self):
        """Remove BigQuery setup scripts."""
        logger.info("🧹 Cleaning up BigQuery setup scripts...")
        
        setup_dir = self.repo_root / "scripts" / "setup"
        
        if setup_dir.exists():
            scripts_to_remove = [
                {
                    "file": "setup_bigquery_environment.py",
                    "reason": "BigQuery environment setup, replaced by PostgreSQL setup"
                }
            ]
            
            for script_info in scripts_to_remove:
                file_path = setup_dir / script_info["file"]
                self.backup_and_remove_file(file_path, script_info["reason"])
    
    def cleanup_diagnostic_scripts(self):
        """Remove BigQuery-specific diagnostic scripts."""
        logger.info("🧹 Cleaning up diagnostic scripts...")
        
        diagnostic_files = [
            {
                "file": "diagnose_geocoding_auth.py",
                "reason": "BigQuery-specific authentication diagnostics"
            },
            {
                "file": "diagnose_threading.py", 
                "reason": "BigQuery threading diagnostics, not needed for simple PostgreSQL version"
            }
        ]
        
        for script_info in diagnostic_files:
            file_path = self.repo_root / script_info["file"]
            self.backup_and_remove_file(file_path, script_info["reason"])
    
    def create_migration_summary(self):
        """Create a summary of the migration changes."""
        summary_path = self.repo_root / "MIGRATION_SUMMARY.md"
        
        summary_content = """# BigQuery to PostgreSQL Migration Summary

This repository has been migrated from BigQuery to PostgreSQL for improved performance and simplified operations.

The following scripts have been backed up to `backup_bigquery_scripts/` and removed:

- `bigquery_geocoding_pipeline.py` - BigQuery base class
- `ultra_fast_geocoding_pipeline.py` - Complex threading pipeline  
- `ultra_simple_linear_geocoding.py` - BigQuery linear script
- `optimized_geocoding_pipeline.py` - BigQuery optimization script
- `simple_linear_geocoding.py` - Additional BigQuery linear script

- `create_mapping_visualizations.py` - BigQuery-dependent visualizations
- `fixed_create_mapping_visualizations.py` - BigQuery visualization fixes

- `setup_bigquery_environment.py` - BigQuery environment setup

- `diagnose_geocoding_auth.py` - BigQuery authentication diagnostics
- `diagnose_threading.py` - BigQuery threading diagnostics


- `scripts/migration/create_postgres_tables.sql` - PostgreSQL table creation
- `scripts/migration/migrate_bigquery_to_postgres.py` - Data migration script

- `scripts/geocoding/postgres_linear_geocoding.py` - Simple PostgreSQL geocoding

- `scripts/migration/cleanup_bigquery_scripts.py` - This cleanup script

1. Run `create_postgres_tables.sql` to create PostgreSQL schema
2. Run `migrate_bigquery_to_postgres.py` to transfer data
3. Use `postgres_linear_geocoding.py` for geocoding operations
4. Update visualization scripts to use PostgreSQL

- ✅ Simplified architecture without complex threading
- ✅ Better performance with PostgreSQL
- ✅ Reduced dependencies and complexity
- ✅ PostGIS spatial capabilities
- ✅ Standard SQL operations
"""
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        logger.info(f"📋 Created migration summary: {summary_path}")
    
    def run_cleanup(self):
        """Execute the complete cleanup process."""
        logger.info("🚀 Starting BigQuery to PostgreSQL cleanup...")
        
        self.create_backup_directory()
        self.cleanup_geocoding_scripts()
        self.cleanup_visualization_scripts() 
        self.cleanup_setup_scripts()
        self.cleanup_diagnostic_scripts()
        self.create_migration_summary()
        
        logger.info("✅ Cleanup completed successfully!")
        logger.info(f"📁 Backup files available in: {self.backup_dir}")
        logger.info("📋 See MIGRATION_SUMMARY.md for details")

def main():
    """Main cleanup execution."""
    cleanup = BigQueryScriptCleanup()
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()
