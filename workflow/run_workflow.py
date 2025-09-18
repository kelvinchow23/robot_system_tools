#!/usr/bin/env python3
"""
Simple Workflow Runner
Quick script to run robot workflows
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from .workflow_executor import WorkflowExecutor
except ImportError:
    # For direct execution
    from workflow_executor import WorkflowExecutor

def run_sample_workflow(step_mode=False):
    """Run the sample pick and place workflow"""
    print("🚀 Starting Sample Pick and Place Workflow")
    if step_mode:
        print("🐾 Step-by-step mode enabled")
    print("=" * 50)
    
    # Create executor
    executor = WorkflowExecutor()
    
    # List available positions
    executor.list_available_positions()
    
    # Connect to robot
    print("\n🔌 Connecting to robot...")
    if not executor.connect_robot():
        print("❌ Failed to connect to robot")
        return False
    
    try:
        # Load and execute sample workflow
        workflow_file = Path(__file__).parent / "sample_workflow.yaml"
        
        if not workflow_file.exists():
            print(f"❌ Sample workflow not found: {workflow_file}")
            return False
        
        print(f"\n📄 Loading workflow: {workflow_file}")
        success = executor.execute_workflow(workflow_file, step_mode)
        
        if success:
            print("\n🎉 Workflow completed successfully!")
        else:
            print("\n💥 Workflow failed!")
        
        # Show execution history
        history = executor.get_workflow_history()
        if history:
            last_run = history[-1]
            print(f"\n📊 Execution Summary:")
            print(f"   ⏱️  Duration: {last_run['duration']:.2f} seconds")
            print(f"   ✅ Success Rate: {last_run['steps_successful']}/{last_run['steps_total']}")
        
        return success
        
    finally:
        executor.disconnect_robot()

def run_custom_workflow(workflow_file, step_mode=False):
    """Run a custom workflow file"""
    print(f"🚀 Running Custom Workflow: {workflow_file}")
    if step_mode:
        print("🐾 Step-by-step mode enabled")
    print("=" * 50)
    
    executor = WorkflowExecutor()
    
    if not executor.connect_robot():
        print("❌ Failed to connect to robot")
        return False
    
    try:
        success = executor.execute_workflow(workflow_file, step_mode)
        return success
    finally:
        executor.disconnect_robot()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robot Workflow Runner")
    parser.add_argument("workflow", nargs="?", help="Path to workflow YAML file")
    parser.add_argument("--step", "-s", action="store_true", help="Enable step-by-step mode")
    
    args = parser.parse_args()
    
    if args.workflow:
        # Run custom workflow
        run_custom_workflow(args.workflow, args.step)
    else:
        # Run sample workflow with step mode option
        if args.step:
            print("🐾 Step-by-step mode enabled for sample workflow")
        success = run_sample_workflow(args.step)

if __name__ == "__main__":
    main()