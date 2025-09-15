#!/usr/bin/env python3
"""
Headless runner for Alpine Linux
"""

import os
import sys
import time
import signal
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from config_loader import Config
from logger import setup_logger
from workflow_orchestrator import WorkflowOrchestrator
from health_check import HealthChecker


class HeadlessRunner:
    """Headless runner for Alpine Linux"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.config = Config('config.headless.json')
        self.orchestrator = WorkflowOrchestrator()
        self.health_checker = HealthChecker(self.config, self.logger)
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def check_system_health(self):
        """Check system health before running"""
        self.logger.info("Checking system health...")
        
        if not self.health_checker.print_health_report():
            self.logger.error("System health check failed")
            return False
        
        return True
    
    def run_workflow_loop(self, interval_hours=24):
        """Run workflow in a loop"""
        self.logger.info(f"Starting headless workflow loop (interval: {interval_hours}h)")
        
        while self.running:
            try:
                # Check system health
                if not self.check_system_health():
                    self.logger.error("System health check failed, skipping workflow")
                    time.sleep(300)  # Wait 5 minutes before retry
                    continue
                
                # Run workflow
                self.logger.info("Starting workflow execution...")
                success = self.orchestrator.run_workflow(
                    start_step=1,
                    end_step=8,
                    dry_run=False,
                    real_time_monitoring=False  # Disable for headless
                )
                
                if success:
                    self.logger.info("✅ Workflow completed successfully")
                else:
                    self.logger.error("❌ Workflow failed")
                
                # Wait for next execution
                if self.running:
                    wait_seconds = interval_hours * 3600
                    self.logger.info(f"Waiting {interval_hours} hours until next execution...")
                    
                    # Sleep in smaller chunks to allow for graceful shutdown
                    for _ in range(wait_seconds // 60):
                        if not self.running:
                            break
                        time.sleep(60)
                
            except KeyboardInterrupt:
                self.logger.info("Workflow loop interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in workflow loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
        
        self.logger.info("Headless runner stopped")
    
    def run_once(self):
        """Run workflow once"""
        self.logger.info("Running workflow once...")
        
        if not self.check_system_health():
            return False
        
        return self.orchestrator.run_workflow(
            start_step=1,
            end_step=8,
            dry_run=False,
            real_time_monitoring=False
        )
    
    def run_specific_step(self, step_number):
        """Run a specific step"""
        self.logger.info(f"Running step {step_number}...")
        
        if not self.check_system_health():
            return False
        
        return self.orchestrator.run_step(step_number, dry_run=False)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Headless Media Sync Runner')
    parser.add_argument('--once', action='store_true', 
                       help='Run workflow once and exit')
    parser.add_argument('--step', type=int, 
                       help='Run specific step number')
    parser.add_argument('--interval', type=int, default=24,
                       help='Workflow interval in hours (default: 24)')
    parser.add_argument('--health-check', action='store_true',
                       help='Run health check only')
    
    args = parser.parse_args()
    
    runner = HeadlessRunner()
    
    try:
        if args.health_check:
            runner.check_system_health()
        elif args.step:
            success = runner.run_specific_step(args.step)
            sys.exit(0 if success else 1)
        elif args.once:
            success = runner.run_once()
            sys.exit(0 if success else 1)
        else:
            runner.run_workflow_loop(args.interval)
    
    except Exception as e:
        runner.logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
