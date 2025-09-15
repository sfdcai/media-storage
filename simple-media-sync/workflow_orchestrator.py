#!/usr/bin/env python3
"""
Workflow Orchestrator
Runs individual steps or complete workflow with real-time monitoring
"""

import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

from config import Config
from logger import setup_logger
from workflow_tracker import WorkflowTracker


class WorkflowOrchestrator:
    """Orchestrates the complete media sync workflow"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger()
        self.tracker = WorkflowTracker(self.config, self.logger)
        self.steps_dir = Path(__file__).parent / 'steps'
        
        # Define workflow steps
        self.workflow_steps = {
            1: 'step1_icloud_download.py',
            2: 'step2_pixel_sync.py',
            3: 'step3_pixel_verification.py',
            4: 'step4_nas_archive.py',
            5: 'step5_processing.py',
            6: 'step6_compression.py',
            7: 'step7_icloud_delete.py',
            8: 'step8_cleanup.py'
        }
    
    def run_step(self, step_number: int, dry_run: bool = False) -> bool:
        """Run a specific workflow step"""
        if step_number not in self.workflow_steps:
            self.logger.error(f"Invalid step number: {step_number}")
            return False
        
        step_file = self.steps_dir / self.workflow_steps[step_number]
        
        if not step_file.exists():
            self.logger.error(f"Step file not found: {step_file}")
            return False
        
        self.logger.info(f"🚀 Running Step {step_number}: {step_file.name}")
        
        try:
            # Run the step script
            result = subprocess.run([sys.executable, str(step_file)], 
                                  capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                self.logger.info(f"✅ Step {step_number} completed successfully")
                if result.stdout:
                    self.logger.info(f"Output: {result.stdout}")
                return True
            else:
                self.logger.error(f"❌ Step {step_number} failed with return code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Error: {result.stderr}")
                if result.stdout:
                    self.logger.error(f"Output: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"❌ Step {step_number} timed out after 1 hour")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error running Step {step_number}: {e}")
            return False
    
    def run_workflow(self, start_step: int = 1, end_step: int = 8, 
                    dry_run: bool = False, real_time_monitoring: bool = True) -> bool:
        """Run the complete workflow or a range of steps"""
        self.logger.info(f"🚀 Starting workflow from Step {start_step} to Step {end_step}")
        
        # Start workflow tracking
        self.tracker.start_workflow()
        
        # Start real-time monitoring if requested
        monitor_thread = None
        if real_time_monitoring:
            monitor_thread = self.tracker.start_real_time_monitoring(interval=30)
        
        try:
            # Run each step in sequence
            for step_number in range(start_step, end_step + 1):
                if step_number not in self.workflow_steps:
                    self.logger.warning(f"Skipping invalid step: {step_number}")
                    continue
                
                # Run the step
                success = self.run_step(step_number, dry_run)
                
                if not success:
                    self.logger.error(f"❌ Workflow failed at Step {step_number}")
                    self.tracker.complete_workflow(success=False, summary={
                        'failed_at_step': step_number,
                        'error': f'Step {step_number} failed'
                    })
                    return False
            
            # Complete workflow
            self.tracker.complete_workflow(success=True, summary={
                'steps_completed': end_step - start_step + 1,
                'start_step': start_step,
                'end_step': end_step
            })
            
            self.logger.info("🎉 Workflow completed successfully!")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("⏹️ Workflow interrupted by user")
            self.tracker.complete_workflow(success=False, summary={'interrupted': True})
            return False
        except Exception as e:
            self.logger.error(f"❌ Workflow failed with error: {e}")
            self.tracker.complete_workflow(success=False, summary={'error': str(e)})
            return False
    
    def get_workflow_status(self) -> dict:
        """Get current workflow status"""
        return self.tracker.get_status()
    
    def print_workflow_status(self):
        """Print current workflow status"""
        self.tracker.print_status()
    
    def list_available_steps(self):
        """List all available workflow steps"""
        print("\nAvailable Workflow Steps:")
        print("=" * 50)
        for step_num, step_file in self.workflow_steps.items():
            step_path = self.steps_dir / step_file
            status = "✅" if step_path.exists() else "❌"
            print(f"{status} Step {step_num}: {step_file}")
        print("=" * 50)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Media Sync Workflow Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow
  python workflow_orchestrator.py --workflow
  
  # Run specific step
  python workflow_orchestrator.py --step 1
  
  # Run steps 1-4
  python workflow_orchestrator.py --workflow --start 1 --end 4
  
  # Run with dry-run mode
  python workflow_orchestrator.py --workflow --dry-run
  
  # List available steps
  python workflow_orchestrator.py --list-steps
  
  # Show workflow status
  python workflow_orchestrator.py --status
        """
    )
    
    # Main action arguments
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--workflow', action='store_true', 
                            help='Run the complete workflow')
    action_group.add_argument('--step', type=int, metavar='N',
                            help='Run a specific step (1-8)')
    action_group.add_argument('--list-steps', action='store_true',
                            help='List all available workflow steps')
    action_group.add_argument('--status', action='store_true',
                            help='Show current workflow status')
    
    # Workflow options
    parser.add_argument('--start', type=int, default=1, metavar='N',
                       help='Start step for workflow (default: 1)')
    parser.add_argument('--end', type=int, default=8, metavar='N',
                       help='End step for workflow (default: 8)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--no-monitoring', action='store_true',
                       help='Disable real-time monitoring')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = WorkflowOrchestrator()
    
    try:
        if args.list_steps:
            orchestrator.list_available_steps()
            return 0
        
        elif args.status:
            orchestrator.print_workflow_status()
            return 0
        
        elif args.step:
            if not (1 <= args.step <= 8):
                print("Error: Step number must be between 1 and 8")
                return 1
            
            success = orchestrator.run_step(args.step, args.dry_run)
            return 0 if success else 1
        
        elif args.workflow:
            if not (1 <= args.start <= 8) or not (1 <= args.end <= 8):
                print("Error: Start and end steps must be between 1 and 8")
                return 1
            
            if args.start > args.end:
                print("Error: Start step cannot be greater than end step")
                return 1
            
            real_time_monitoring = not args.no_monitoring
            success = orchestrator.run_workflow(
                start_step=args.start,
                end_step=args.end,
                dry_run=args.dry_run,
                real_time_monitoring=real_time_monitoring
            )
            return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Operation interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
