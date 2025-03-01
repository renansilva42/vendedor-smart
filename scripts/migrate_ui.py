#!/usr/bin/env python3
"""
UI Migration script to transition to the new frontend implementation.
This script handles template and static file updates.
"""

import os
import shutil
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UIMigrationManager:
    """Manages the UI migration process."""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.backup_dir = os.path.join(
            project_root,
            'backups',
            f'ui_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )
        
        # Files to migrate (old_path -> new_path)
        self.template_migrations = {
            'app/templates/index.html': 'app/templates/index_new.html',
            'app/templates/chat.html': 'app/templates/chat_new.html',
            'app/templates/select_chatbot.html': 'app/templates/select_chatbot_new.html'
        }
        
        self.js_migrations = {
            'app/static/js/chat.js': 'app/static/js/chat_new.js'
        }
        
        # New files to copy
        self.new_files = [
            'app/templates/errors/404.html',
            'app/templates/errors/500.html',
            'app/routes_new.py'
        ]
        
        # Directories to create
        self.required_dirs = [
            'app/templates/errors',
            'backups/templates',
            'backups/static'
        ]
    
    def create_directories(self) -> bool:
        """Create required directories."""
        try:
            logger.info("Creating required directories...")
            for dir_path in self.required_dirs:
                full_path = os.path.join(self.project_root, dir_path)
                os.makedirs(full_path, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating directories: {str(e)}")
            return False
    
    def backup_files(self) -> bool:
        """Create backup of files to be migrated."""
        try:
            logger.info("Creating file backups...")
            
            # Backup templates
            for old_path in self.template_migrations.keys():
                full_old_path = os.path.join(self.project_root, old_path)
                if os.path.exists(full_old_path):
                    backup_path = os.path.join(self.backup_dir, old_path)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(full_old_path, backup_path)
                    logger.info(f"Backed up: {old_path}")
            
            # Backup JS files
            for old_path in self.js_migrations.keys():
                full_old_path = os.path.join(self.project_root, old_path)
                if os.path.exists(full_old_path):
                    backup_path = os.path.join(self.backup_dir, old_path)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(full_old_path, backup_path)
                    logger.info(f"Backed up: {old_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating backups: {str(e)}")
            return False
    
    def migrate_templates(self) -> bool:
        """Migrate template files."""
        try:
            logger.info("Migrating templates...")
            for old_path, new_path in self.template_migrations.items():
                full_old_path = os.path.join(self.project_root, old_path)
                full_new_path = os.path.join(self.project_root, new_path)
                
                if not os.path.exists(full_new_path):
                    logger.error(f"New template not found: {new_path}")
                    return False
                
                # Replace old with new
                shutil.copy2(full_new_path, full_old_path)
                logger.info(f"Migrated template: {old_path}")
                
                # Remove the _new file
                os.remove(full_new_path)
                logger.info(f"Removed: {new_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error migrating templates: {str(e)}")
            return False
    
    def migrate_js_files(self) -> bool:
        """Migrate JavaScript files."""
        try:
            logger.info("Migrating JavaScript files...")
            for old_path, new_path in self.js_migrations.items():
                full_old_path = os.path.join(self.project_root, old_path)
                full_new_path = os.path.join(self.project_root, new_path)
                
                if not os.path.exists(full_new_path):
                    logger.error(f"New JS file not found: {new_path}")
                    return False
                
                # Replace old with new
                shutil.copy2(full_new_path, full_old_path)
                logger.info(f"Migrated JS file: {old_path}")
                
                # Remove the _new file
                os.remove(full_new_path)
                logger.info(f"Removed: {new_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error migrating JavaScript files: {str(e)}")
            return False
    
    def copy_new_files(self) -> bool:
        """Copy new files to their locations."""
        try:
            logger.info("Copying new files...")
            for file_path in self.new_files:
                full_path = os.path.join(self.project_root, file_path)
                if not os.path.exists(full_path):
                    logger.error(f"New file not found: {file_path}")
                    return False
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # If it's routes_new.py, handle it specially
                if file_path.endswith('routes_new.py'):
                    target_path = os.path.join(self.project_root, 'app/routes.py')
                    shutil.copy2(full_path, target_path)
                    os.remove(full_path)
                    logger.info(f"Updated routes.py")
                else:
                    # Copy file to its location
                    shutil.copy2(full_path, full_path.replace('_new', ''))
                    logger.info(f"Copied: {file_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error copying new files: {str(e)}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify all files are in place."""
        try:
            logger.info("Verifying migration...")
            
            # Check templates
            for old_path in self.template_migrations.keys():
                if not os.path.exists(os.path.join(self.project_root, old_path)):
                    logger.error(f"Missing template: {old_path}")
                    return False
            
            # Check JS files
            for old_path in self.js_migrations.keys():
                if not os.path.exists(os.path.join(self.project_root, old_path)):
                    logger.error(f"Missing JS file: {old_path}")
                    return False
            
            # Check new files
            for file_path in self.new_files:
                if not os.path.exists(os.path.join(self.project_root, file_path.replace('_new', ''))):
                    logger.error(f"Missing new file: {file_path}")
                    return False
            
            logger.info("Migration verification successful!")
            return True
        except Exception as e:
            logger.error(f"Error verifying migration: {str(e)}")
            return False
    
    def rollback(self) -> bool:
        """Rollback changes if migration fails."""
        try:
            logger.info("Rolling back changes...")
            
            # Restore templates
            for old_path in self.template_migrations.keys():
                backup_path = os.path.join(self.backup_dir, old_path)
                full_old_path = os.path.join(self.project_root, old_path)
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, full_old_path)
                    logger.info(f"Restored: {old_path}")
            
            # Restore JS files
            for old_path in self.js_migrations.keys():
                backup_path = os.path.join(self.backup_dir, old_path)
                full_old_path = os.path.join(self.project_root, old_path)
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, full_old_path)
                    logger.info(f"Restored: {old_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error rolling back changes: {str(e)}")
            return False

def main():
    """Main migration function."""
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create migration manager
    manager = UIMigrationManager(project_root)
    
    # Create required directories
    if not manager.create_directories():
        logger.error("Failed to create directories")
        return
    
    # Create backup
    if not manager.backup_files():
        logger.error("Backup creation failed")
        return
    
    # Migrate templates
    if not manager.migrate_templates():
        logger.error("Template migration failed")
        if not manager.rollback():
            logger.error("Rollback failed - manual intervention required")
        return
    
    # Migrate JS files
    if not manager.migrate_js_files():
        logger.error("JavaScript migration failed")
        if not manager.rollback():
            logger.error("Rollback failed - manual intervention required")
        return
    
    # Copy new files
    if not manager.copy_new_files():
        logger.error("Failed to copy new files")
        if not manager.rollback():
            logger.error("Rollback failed - manual intervention required")
        return
    
    # Verify migration
    if not manager.verify_migration():
        logger.error("Migration verification failed")
        if not manager.rollback():
            logger.error("Rollback failed - manual intervention required")
        return
    
    logger.info("UI Migration completed successfully!")

if __name__ == '__main__':
    main()
