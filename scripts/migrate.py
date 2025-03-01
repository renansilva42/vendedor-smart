#!/usr/bin/env python3
"""
Migration script to transition from old to new chatbot architecture.
This script handles file replacements and necessary updates.
"""

import os
import shutil
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages the migration process from old to new architecture."""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.backup_dir = os.path.join(
            project_root,
            'backups',
            f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )
        
        # Files to migrate (old_path -> new_path)
        self.migration_map = {
            'app/chatbot/base.py': 'app/chatbot/base_new.py',
            'app/chatbot/vendas.py': 'app/chatbot/vendas_new.py',
            'app/chatbot/treinamento.py': 'app/chatbot/treinamento_new.py',
            'app/chatbot/whatsapp.py': 'app/chatbot/whatsapp_new.py',
            'app/chatbot/__init__.py': 'app/chatbot/__init__new.py'
        }
        
        # Files to verify exist
        self.required_files = [
            'app/services/interfaces.py',
            'app/services/ai_service.py',
            'app/services/database_service.py',
            'app/services/cache_service.py',
            'app/services/logging_service.py',
            'app/services/container.py',
            'app/chatbot/factory.py',
            'tests/test_new_implementation.py',
            'docs/MIGRATION.md'
        ]
    
    def verify_requirements(self) -> bool:
        """Verify all required files exist."""
        logger.info("Verifying required files...")
        missing_files = []
        
        for file_path in self.required_files:
            full_path = os.path.join(self.project_root, file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)
        
        if missing_files:
            logger.error("Missing required files:")
            for file in missing_files:
                logger.error(f"  - {file}")
            return False
        
        logger.info("All required files present")
        return True
    
    def create_backup(self) -> bool:
        """Create backup of files to be migrated."""
        try:
            logger.info(f"Creating backup directory: {self.backup_dir}")
            os.makedirs(self.backup_dir, exist_ok=True)
            
            for old_path in self.migration_map.keys():
                full_old_path = os.path.join(self.project_root, old_path)
                if os.path.exists(full_old_path):
                    backup_path = os.path.join(self.backup_dir, old_path)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(full_old_path, backup_path)
                    logger.info(f"Backed up: {old_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return False
    
    def perform_migration(self) -> bool:
        """Perform the migration by replacing files."""
        try:
            for old_path, new_path in self.migration_map.items():
                full_old_path = os.path.join(self.project_root, old_path)
                full_new_path = os.path.join(self.project_root, new_path)
                
                if not os.path.exists(full_new_path):
                    logger.error(f"New file not found: {new_path}")
                    return False
                
                # Replace old with new
                shutil.copy2(full_new_path, full_old_path)
                logger.info(f"Replaced: {old_path}")
                
                # Remove the _new file
                os.remove(full_new_path)
                logger.info(f"Removed: {new_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify the migration was successful."""
        try:
            import pytest
            logger.info("Running tests...")
            
            # Run pytest with coverage
            result = pytest.main([
                'tests',
                '--verbose',
                '--cov=app',
                '--cov-report=term-missing'
            ])
            
            if result == 0:
                logger.info("All tests passed!")
                return True
            else:
                logger.error("Some tests failed")
                return False
                
        except Exception as e:
            logger.error(f"Test verification failed: {str(e)}")
            return False
    
    def rollback(self) -> bool:
        """Rollback changes if migration fails."""
        try:
            logger.info("Rolling back changes...")
            
            for old_path in self.migration_map.keys():
                backup_path = os.path.join(self.backup_dir, old_path)
                full_old_path = os.path.join(self.project_root, old_path)
                
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, full_old_path)
                    logger.info(f"Restored: {old_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False

def main():
    """Main migration function."""
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create migration manager
    manager = MigrationManager(project_root)
    
    # Verify requirements
    if not manager.verify_requirements():
        logger.error("Requirements verification failed")
        sys.exit(1)
    
    # Create backup
    if not manager.create_backup():
        logger.error("Backup creation failed")
        sys.exit(1)
    
    # Perform migration
    if not manager.perform_migration():
        logger.error("Migration failed")
        if not manager.rollback():
            logger.error("Rollback failed - manual intervention required")
        sys.exit(1)
    
    # Verify migration
    if not manager.verify_migration():
        logger.error("Migration verification failed")
        if not manager.rollback():
            logger.error("Rollback failed - manual intervention required")
        sys.exit(1)
    
    logger.info("Migration completed successfully!")

if __name__ == '__main__':
    main()
