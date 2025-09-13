#!/usr/bin/env python3
"""
Media Pipeline Orchestrator
Coordinates the execution of all pipeline stages in the correct sequence
"""

import os
import sys
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from common import config_manager, db_manager, setup_module_logger, auth_manager
from telegram_notifier import send_pipeline_start, send_pipeline_complete, send_pipeline_error, send_stage_complete

# Setup module-specific logger
logger = setup_module_logger(__name__)

class PipelineOrchestrator:
    """Orchestrates the execution of the media pipeline stages"""
    
    def __init__(self):
        self.config = config_manager
        self.db = db_manager
        self.stages = [
            'icloud_sync',
            'pixel_sync', 
            'nas_sync',
            'compression',
            'cleanup',
            'deletion'
        ]
        self.stage_modules = {
            'icloud_sync': 'sync_icloud',
            'pixel_sync': 'bulk_pixel_sync',
            'nas_sync': 'bulk_nas_sync',
            'compression': 'compress_media',
            'cleanup': 'cleanup_icloud',
            'deletion': 'delete_icloud'
        }
        self.stage_descriptions = {
            'icloud_sync': 'Download media from iCloud',
            'pixel_sync': 'Sync media to Pixel/Google Photos',
            'nas_sync': 'Sync media to NAS for local backup',
            'compression': 'Compress media files based on age',
            'cleanup': 'Move files to delete pending album',
            'deletion': 'Delete files from iCloud and local storage'
        }
    
    def validate_environment(self) -> bool:
        """Validate the environment and dependencies"""
        logger.info("Validating environment...")
        
        # Validate configuration
        if not self.config.validate_config():
            logger.error("Configuration validation failed")
            return False
        
        # Validate database
        try:
            self.db.init_database()
            logger.info("✅ Database validation successful")
        except Exception as e:
            logger.error(f"❌ Database validation failed: {e}")
            return False
        
        # Validate external connections
        connections = auth_manager.validate_all_connections()
        for service, status in connections.items():
            if status:
                logger.info(f"✅ {service.title()} connection validated")
            else:
                logger.warning(f"⚠️ {service.title()} connection validation failed")
        
        return True
    
    def run_stage(self, stage_name: str, dry_run: bool = False) -> Dict[str, Any]:
        """Run a specific pipeline stage"""
        if stage_name not in self.stage_modules:
            raise ValueError(f"Unknown stage: {stage_name}")
        
        logger.info(f"🚀 Starting stage: {stage_name} - {self.stage_descriptions[stage_name]}")
        
        if dry_run:
            logger.info(f"🔍 DRY RUN: Would execute {stage_name}")
            return {
                'stage': stage_name,
                'success': True,
                'dry_run': True,
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': 0
            }
        
        # Start pipeline stage tracking
        stage_id = self.db.start_pipeline_stage(stage_name)
        
        start_time = datetime.now()
        success = False
        error_message = None
        files_processed = 0
        files_failed = 0
        
        try:
            # Import and run the stage module
            module_name = self.stage_modules[stage_name]
            module = __import__(module_name)
            
            # Call the main function
            result = module.main()
            success = result if isinstance(result, bool) else True
            files_processed = 1  # Simplified for now
            
        except ImportError as e:
            error_message = f"Failed to import module {module_name}: {e}"
            logger.error(error_message)
        except Exception as e:
            error_message = f"Stage {stage_name} failed: {e}"
            logger.error(error_message)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Complete pipeline stage tracking
        self.db.complete_pipeline_stage(
            stage_id, 
            files_processed, 
            files_failed, 
            error_message
        )
        
        result = {
            'stage': stage_name,
            'success': success,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'files_processed': files_processed,
            'files_failed': files_failed,
            'error_message': error_message
        }
        
        if success:
            logger.info(f"✅ Stage {stage_name} completed successfully in {duration:.1f}s")
        else:
            logger.error(f"❌ Stage {stage_name} failed: {error_message}")
        
        return result
    
    def run_pipeline(self, stages: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Run the complete pipeline or specified stages"""
        if stages is None:
            stages = self.stages
        
        logger.info(f"🎬 Starting media pipeline with stages: {stages}")
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No actual operations will be performed")
        
        # Send Telegram notification for pipeline start
        try:
            send_pipeline_start(stages)
        except Exception as e:
            logger.warning(f"Failed to send Telegram start notification: {e}")
        
        pipeline_start = datetime.now()
        results = {
            'pipeline_start': pipeline_start.isoformat(),
            'stages': [],
            'overall_success': True,
            'total_duration': 0
        }
        
        for stage in stages:
            if stage not in self.stages:
                logger.warning(f"⚠️ Skipping unknown stage: {stage}")
                continue
            
            try:
                stage_result = self.run_stage(stage, dry_run)
                results['stages'].append(stage_result)
                
                # Send Telegram notification for stage completion
                try:
                    send_stage_complete(
                        stage,
                        stage_result['success'],
                        stage_result.get('duration_seconds', 0),
                        stage_result.get('files_processed', 0),
                        stage_result.get('files_failed', 0)
                    )
                except Exception as e:
                    logger.warning(f"Failed to send Telegram stage notification: {e}")
                
                if not stage_result['success']:
                    results['overall_success'] = False
                    logger.error(f"❌ Pipeline failed at stage: {stage}")
                    
                    # Send Telegram error notification
                    try:
                        send_pipeline_error(stage_result.get('error_message', 'Unknown error'), stage)
                    except Exception as e:
                        logger.warning(f"Failed to send Telegram error notification: {e}")
                    
                    # Optionally continue with remaining stages
                    # For now, we'll stop on first failure
                    break
                
            except Exception as e:
                logger.error(f"❌ Unexpected error in stage {stage}: {e}")
                results['stages'].append({
                    'stage': stage,
                    'success': False,
                    'error_message': str(e),
                    'start_time': datetime.now().isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_seconds': 0
                })
                results['overall_success'] = False
                break
        
        pipeline_end = datetime.now()
        results['pipeline_end'] = pipeline_end.isoformat()
        results['total_duration'] = (pipeline_end - pipeline_start).total_seconds()
        
        # Log summary
        self._log_pipeline_summary(results)
        
        # Send Telegram notification for pipeline completion
        try:
            send_pipeline_complete(results)
        except Exception as e:
            logger.warning(f"Failed to send Telegram completion notification: {e}")
        
        return results
    
    def _log_pipeline_summary(self, results: Dict[str, Any]):
        """Log pipeline execution summary"""
        logger.info("📊 Pipeline Execution Summary:")
        logger.info(f"  Overall Success: {'✅' if results['overall_success'] else '❌'}")
        logger.info(f"  Total Duration: {results['total_duration']:.1f}s")
        logger.info(f"  Stages Executed: {len(results['stages'])}")
        
        for stage_result in results['stages']:
            status = "✅" if stage_result['success'] else "❌"
            duration = stage_result.get('duration_seconds', 0)
            logger.info(f"    {status} {stage_result['stage']}: {duration:.1f}s")
            
            if not stage_result['success'] and stage_result.get('error_message'):
                logger.info(f"      Error: {stage_result['error_message']}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and statistics"""
        try:
            stats = self.db.get_pipeline_stats()
            return {
                'database_stats': stats,
                'available_stages': self.stages,
                'stage_descriptions': self.stage_descriptions,
                'configuration_valid': self.config.validate_config()
            }
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {}
    
    def list_stages(self):
        """List available pipeline stages"""
        logger.info("Available pipeline stages:")
        for i, stage in enumerate(self.stages, 1):
            logger.info(f"  {i}. {stage}: {self.stage_descriptions[stage]}")

def main():
    """Main pipeline orchestrator entry point"""
    parser = argparse.ArgumentParser(description="Media Pipeline Orchestrator")
    parser.add_argument('--stages', nargs='+', choices=[
        'icloud_sync', 'pixel_sync', 'nas_sync', 'compression', 'cleanup', 'deletion'
    ], help='Specific stages to run (default: all stages)')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without executing operations')
    parser.add_argument('--list-stages', action='store_true', help='List available stages and exit')
    parser.add_argument('--status', action='store_true', help='Show pipeline status and exit')
    parser.add_argument('--validate', action='store_true', help='Validate environment and exit')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = PipelineOrchestrator()
    
    # Handle special commands
    if args.list_stages:
        orchestrator.list_stages()
        return 0
    
    if args.status:
        status = orchestrator.get_pipeline_status()
        logger.info(f"Pipeline Status: {status}")
        return 0
    
    if args.validate:
        success = orchestrator.validate_environment()
        return 0 if success else 1
    
    # Validate environment before running pipeline
    if not orchestrator.validate_environment():
        logger.error("Environment validation failed")
        return 1
    
    # Run pipeline
    try:
        results = orchestrator.run_pipeline(args.stages, args.dry_run)
        
        if results['overall_success']:
            logger.info("🎉 Pipeline completed successfully!")
            return 0
        else:
            logger.error("💥 Pipeline completed with failures")
            return 1
            
    except KeyboardInterrupt:
        logger.info("⏹️ Pipeline interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"💥 Pipeline failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
