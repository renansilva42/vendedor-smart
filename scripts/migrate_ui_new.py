#!/usr/bin/env python3
"""
Enhanced UI Migration script to transition to the new sophisticated frontend implementation.
This script handles template and static file updates with proper backups and verification.
"""

import os
import shutil
from datetime import datetime
import logging
import json
import subprocess
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedUIMigrationManager:
    """Manages the UI migration process with enhanced error handling and verification."""
    
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
        
        self.static_migrations = {
            'app/static/css/style.css': 'app/static/css/style_new.css',
            'app/static/js/theme.js': 'app/static/js/theme_new.js',
            'app/static/js/chat.js': 'app/static/js/chat_new.js'
        }
        
        self.new_files = {
            'app/templates/errors/404.html': 'Error page (404)',
            'app/templates/errors/500.html': 'Error page (500)',
            'app/static/images/theme-toggle.svg': 'Theme toggle icon',
            'app/routes_new.py': 'Enhanced routes'
        }
        
        # Required directories
        self.required_dirs = [
            'app/templates/errors',
            'app/static/images',
            'backups/templates',
            'backups/static',
            'backups/routes'
        ]
    
    def verify_environment(self) -> bool:
        """Verify the development environment is ready for migration."""
        try:
            logger.info("Verifying development environment...")
            
            # Check Python version
            python_version = subprocess.check_output(['python3', '--version']).decode().strip()
            logger.info(f"Python version: {python_version}")
            
            # Check required packages
            requirements_path = os.path.join(self.project_root, 'requirements.txt')
            if os.path.exists(requirements_path):
                subprocess.check_call(['pip', 'install', '-r', requirements_path])
                logger.info("Required packages verified")
            
            return True
        except Exception as e:
            logger.error(f"Environment verification failed: {str(e)}")
            return False
    
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
        """Create comprehensive backup of files to be migrated."""
        try:
            logger.info("Creating file backups...")
            
            # Backup templates
            for old_path in self.template_migrations.keys():
                self._backup_file(old_path)
            
            # Backup static files
            for old_path in self.static_migrations.keys():
                self._backup_file(old_path)
            
            # Backup routes
            self._backup_file('app/routes.py')
            
            # Create backup manifest
            manifest = {
                'timestamp': datetime.now().isoformat(),
                'templates': list(self.template_migrations.keys()),
                'static_files': list(self.static_migrations.keys()),
                'routes': ['app/routes.py']
            }
            
            manifest_path = os.path.join(self.backup_dir, 'manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Backup created at: {self.backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Error creating backups: {str(e)}")
            return False
    
    def _backup_file(self, file_path: str) -> None:
        """Backup a single file with metadata."""
        full_path = os.path.join(self.project_root, file_path)
        if os.path.exists(full_path):
            backup_path = os.path.join(self.backup_dir, file_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(full_path, backup_path)
            logger.info(f"Backed up: {file_path}")
    
    def migrate_files(self) -> bool:
        """Migrate files to new implementation."""
        try:
            logger.info("Migrating files...")
            
            # Migrate templates
            for old_path, new_path in self.template_migrations.items():
                self._migrate_file(old_path, new_path, "template")
            
            # Migrate static files
            for old_path, new_path in self.static_migrations.items():
                self._migrate_file(old_path, new_path, "static")
            
            # Migrate routes
            self._migrate_file('app/routes.py', 'app/routes_new.py', "route")
            
            # Copy new files
            for file_path, description in self.new_files.items():
                self._copy_new_file(file_path, description)
            
            return True
        except Exception as e:
            logger.error(f"Error migrating files: {str(e)}")
            return False
    
    def _migrate_file(self, old_path: str, new_path: str, file_type: str) -> None:
        """Migrate a single file with verification."""
        full_old_path = os.path.join(self.project_root, old_path)
        full_new_path = os.path.join(self.project_root, new_path)
        
        if not os.path.exists(full_new_path):
            raise FileNotFoundError(f"New {file_type} file not found: {new_path}")
        
        shutil.copy2(full_new_path, full_old_path)
        logger.info(f"Migrated {file_type}: {old_path}")
        
        # Remove the _new file
        os.remove(full_new_path)
        logger.info(f"Removed temporary file: {new_path}")
    
    def _copy_new_file(self, file_path: str, description: str) -> None:
        """Copy a new file to its destination."""
        full_path = os.path.join(self.project_root, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"New file not found: {file_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Copy file
        shutil.copy2(full_path, full_path.replace('_new', ''))
        logger.info(f"Added new {description}: {file_path}")
    
    def verify_migration(self) -> bool:
        """Verify the migration was successful."""
        try:
            logger.info("Verifying migration...")
            
            # Check all required files exist
            for old_path in self.template_migrations.keys():
                if not os.path.exists(os.path.join(self.project_root, old_path)):
                    raise FileNotFoundError(f"Missing template: {old_path}")
            
            for old_path in self.static_migrations.keys():
                if not os.path.exists(os.path.join(self.project_root, old_path)):
                    raise FileNotFoundError(f"Missing static file: {old_path}")
            
            # Verify routes
            if not os.path.exists(os.path.join(self.project_root, 'app/routes.py')):
                raise FileNotFoundError("Missing routes.py")
            
            # Verify new files
            for file_path in self.new_files.keys():
                if not os.path.exists(os.path.join(self.project_root, file_path)):
                    raise FileNotFoundError(f"Missing new file: {file_path}")
            
            logger.info("Migration verification successful!")
            return True
        except Exception as e:
            logger.error(f"Migration verification failed: {str(e)}")
            return False
    
    def rollback(self) -> bool:
        """Rollback changes if migration fails."""
        try:
            logger.info("Rolling back changes...")
            
            # Read backup manifest
            manifest_path = os.path.join(self.backup_dir, 'manifest.json')
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Restore files from manifest
            for file_path in manifest['templates'] + manifest['static_files'] + manifest['routes']:
                backup_path = os.path.join(self.backup_dir, file_path)
                full_path = os.path.join(self.project_root, file_path)
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, full_path)
                    logger.info(f"Restored: {file_path}")
            
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False

def main():
    """Main migration function."""
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create migration manager
    manager = EnhancedUIMigrationManager(project_root)
    
    # Verify environment
    if not manager.verify_environment():
        logger.error("Environment verification failed")
        return
    
    # Create required directories
    if not manager.create_directories():
        logger.error("Failed to create directories")
        return
    
    # Create backup
    if not manager.backup_files():
        logger.error("Backup creation failed")
        return
    
    # Migrate files
    if not manager.migrate_files():
        logger.error("Migration failed")
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
    logger.info("\nNext steps:")
    logger.info("1. Review the migrated files")
    logger.info("2. Test the application thoroughly")
    logger.info("3. Check browser compatibility")
    logger.info("4. Verify responsive design")
    logger.info("5. Test theme switching")
    logger.info("\nBackup location: " + manager.backup_dir)

if __name__ == '__main__':
    main()
