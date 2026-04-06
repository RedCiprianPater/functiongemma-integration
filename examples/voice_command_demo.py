#!/usr/bin/env python3
"""
Voice Command Demo for FunctionGemma + NWO Robotics
Demonstrates offline voice-to-function calling
"""

import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def simulate_voice_command(command: str):
    """Simulate processing a voice command"""
    
    print(f"\n{'='*60}")
    print(f"VOICE INPUT: \"{command}\"")
    print(f"{'='*60}")
    
    # Simulated FunctionGemma output
    # In real implementation, this would call the actual model
    
    examples = {
        "Deploy drone alpha to sector 7 and scan for heat": {
            "calls": [
                {
                    "name": "navigation_goto",
                    "arguments": {
                        "robot_id": "drone_alpha",
                        "destination": {"x": 70, "y": 0, "z": 10, "frame": "map"},
                        "speed": 5.0
                    }
                },
                {
                    "name": "sensor_activate",
                    "arguments": {
                        "robot_id": "drone_alpha",
                        "sensor_type": "thermal",
                        "mode": "stream"
                    }
                }
            ]
        },
        "Calibrate the Unitree's IMU": {
            "calls": [
                {
                    "name": "calibration_run",
                    "arguments": {
                        "robot_id": "go2_001",
                        "system": "imu",
                        "auto_accept": False
                    }
                }
            ]
        },
        "Stop all robots immediately": {
            "calls": [
                {
                    "name": "emergency_stop",
                    "arguments": {
                        "robot_id": "all",
                        "reason": "Emergency stop triggered by voice command"
                    }
                }
            ]
        },
        "Start mapping with 5cm resolution": {
            "calls": [
                {
                    "name": "slam_start",
                    "arguments": {
                        "robot_id": "go2_001",
                        "mode": "mapping",
                        "resolution": 0.05
                    }
                }
            ]
        },
        "Check battery on robot 3": {
            "calls": [
                {
                    "name": "status_check",
                    "arguments": {
                        "robot_id": "go2_003",
                        "detailed": False
                    }
                }
            ]
        },
        "Go to coordinates 10, 20": {
            "calls": [
                {
                    "name": "navigation_goto",
                    "arguments": {
                        "robot_id": "go2_001",
                        "destination": {"x": 10, "y": 20, "z": 0, "frame": "map"},
                        "speed": 0.5
                    }
                }
            ]
        },
        "Pick up the red box carefully": {
            "calls": [
                {
                    "name": "robot_command",
                    "arguments": {
                        "robot_id": "go2_001",
                        "instruction": "pick up the red box",
                        "priority": "high"
                    }
                }
            ]
        },
    }
    
    # Find matching example or use default
    result = examples.get(command, {
        "calls": [
            {
                "name": "robot_command",
                "arguments": {
                    "robot_id": "go2_001",
                    "instruction": command,
                    "priority": "normal"
                }
            }
        ]
    })
    
    print("\nFUNCTION CALL OUTPUT:")
    print(json.dumps(result, indent=2))
    
    print("\nAPI CALLS THAT WOULD BE EXECUTED:")
    for call in result["calls"]:
        print(f"  → POST /api/robotics/{call['name']}")
        print(f"    Payload: {json.dumps(call['arguments'])}")
    
    print(f"\nLatency: ~85ms (on-device inference)")
    print(f"Network: {'Offline mode - queued for sync' if False else 'Online - executing now'}")
    
    return result


def main():
    print("="*60)
    print("NWO Robotics Voice Command Demo")
    print("FunctionGemma On-Device Function Calling")
    print("="*60)
    
    demo_commands = [
        "Deploy drone alpha to sector 7 and scan for heat",
        "Calibrate the Unitree's IMU",
        "Stop all robots immediately",
        "Start mapping with 5cm resolution",
        "Check battery on robot 3",
        "Go to coordinates 10, 20",
        "Pick up the red box carefully",
    ]
    
    print("\nDemo Commands:")
    for i, cmd in enumerate(demo_commands, 1):
        print(f"  {i}. {cmd}")
    
    print("\n" + "="*60)
    print("Processing all demo commands...")
    print("="*60)
    
    for cmd in demo_commands:
        simulate_voice_command(cmd)
        input("\nPress Enter for next command...")
    
    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60)


if __name__ == '__main__':
    main()
