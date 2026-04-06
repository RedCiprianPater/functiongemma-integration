#!/usr/bin/env python3
"""
Prepare NWO Robotics Training Dataset for FunctionGemma Fine-tuning
Generates synthetic training examples from voice commands to function calls
"""

import json
import random
from typing import List, Dict, Any
from dataclasses import dataclass
import argparse


@dataclass
class TrainingExample:
    """Single training example for function calling"""
    instruction: str
    input_text: str
    output_json: Dict[str, Any]
    function_name: str


class NWOCommandGenerator:
    """Generates diverse natural language commands for NWO Robotics"""
    
    # Robot IDs
    ROBOT_IDS = [
        'go2_001', 'go2_002', 'go2_003', 'go2_alpha', 'go2_beta',
        'drone_001', 'drone_alpha', 'drone_beta', 'drone_recon',
        'arm_001', 'arm_assembly', 'arm_packing',
        'unitree_01', 'unitree_02', 'spot_001', 'spot_security'
    ]
    
    # Templates for each function
    TEMPLATES = {
        'robot_command': [
            "Tell {robot_id} to {instruction}",
            "Make {robot_id} {instruction}",
            "Have {robot_id} {instruction}",
            "Command {robot_id}: {instruction}",
            "{robot_id}, please {instruction}",
            "Ask {robot_id} to {instruction}",
            "Get {robot_id} to {instruction}",
            "I need {robot_id} to {instruction}",
            "Can you make {robot_id} {instruction}?",
            "{instruction} with {robot_id}",
        ],
        'swarm_deploy': [
            "Deploy swarm {swarm_id} for {mission_type}",
            "Send robots {robot_list} as {swarm_id} to {mission_type}",
            "Launch swarm {swarm_id} with {robot_list} for {mission_type}",
            "Form a {formation} formation with {robot_list} for {mission_type}",
            "Deploy {robot_list} as {swarm_id} in {formation} formation",
            "Coordinate {robot_list} as swarm {swarm_id} for {mission_type}",
            "Send out swarm {swarm_id} ({robot_list}) to {mission_type}",
            "Assemble {robot_list} into {swarm_id} for {mission_type} mission",
        ],
        'sensor_activate': [
            "Turn on the {sensor_type} on {robot_id}",
            "Activate {robot_id}'s {sensor_type}",
            "Start {sensor_type} on {robot_id}",
            "Enable {sensor_type} sensor on {robot_id}",
            "{robot_id}, activate your {sensor_type}",
            "Switch on {sensor_type} for {robot_id}",
            "Begin {sensor_type} streaming from {robot_id}",
            "Power up {robot_id}'s {sensor_type} sensor",
            "{sensor_type} on {robot_id}, {mode} mode",
        ],
        'slam_start': [
            "Start mapping with {robot_id}",
            "Begin SLAM on {robot_id}",
            "Map the area with {robot_id}",
            "Start {mode} with {robot_id}",
            "{robot_id}, begin {mode} at {resolution} resolution",
            "Initialize SLAM on {robot_id} for {mode}",
            "Begin mapping with {resolution} precision using {robot_id}",
            "Start localization mode on {robot_id}",
        ],
        'navigation_goto': [
            "Go to coordinates {x}, {y}",
            "Navigate to position {x}, {y}",
            "Move {robot_id} to {x}, {y}",
            "Send {robot_id} to location {x}, {y}",
            "{robot_id}, go to {x}, {y}",
            "Navigate {robot_id} to coordinates {x}, {y}",
            "Head to position {x}, {y} with {robot_id}",
            "Move to waypoint {x}, {y}",
        ],
        'calibration_run': [
            "Calibrate {robot_id}'s {system}",
            "Run {system} calibration on {robot_id}",
            "{robot_id}, calibrate your {system}",
            "Start {system} calibration for {robot_id}",
            "Perform {system} calibration on {robot_id}",
            "Initialize {system} calibration for {robot_id}",
            "Auto-calibrate {robot_id}'s {system}",
        ],
        'emergency_stop': [
            "Stop all robots immediately",
            "Emergency stop",
            "Stop everything now",
            "Halt all motion",
            "Emergency halt",
            "Stop {robot_id} immediately",
            "Kill all motors",
            "Full stop",
            "Abort mission",
        ],
        'status_check': [
            "Check status of {robot_id}",
            "What's the status of {robot_id}?",
            "{robot_id} status report",
            "Get diagnostics for {robot_id}",
            "How is {robot_id} doing?",
            "Check {robot_id}'s battery",
            "Status check on {robot_id}",
            "{robot_id} health check",
        ],
        'manipulator_control': [
            "Open {robot_id}'s gripper",
            "Close gripper on {robot_id}",
            "{robot_id}, grasp the object",
            "Release gripper on {robot_id}",
            "{robot_id}, pick up the box",
            "Put down the object with {robot_id}",
            "Move {robot_id}'s arm to position",
            "Rotate {robot_id}'s wrist",
        ],
        'task_queue_submit': [
            "Queue a {task_type} task for {robot_id}",
            "Add {task_type} to {robot_id}'s queue",
            "Schedule {task_type} on {robot_id}",
            "{robot_id}, queue up {task_type}",
            "Submit {task_type} task to {robot_id}",
            "Priority {priority} {task_type} for {robot_id}",
        ],
        'patrol_route': [
            "Start patrol with {robot_id}",
            "Begin patrol route on {robot_id}",
            "{robot_id}, start patrolling",
            "Patrol the area with {robot_id}",
            "Continuous patrol for {robot_id}",
            "Loop patrol with {robot_id}",
        ],
        'return_to_base': [
            "Return to base",
            "Go home",
            "Return {robot_id} to charging station",
            "{robot_id}, return to dock",
            "Head back to base",
            "Go back to starting position",
            "Return to home position",
        ],
        'follow_me': [
            "Follow me",
            "{robot_id}, follow me",
            "Enable follow mode on {robot_id}",
            "Stay behind me {robot_id}",
            "{robot_id}, trail me at {distance} meters",
            "Follow mode on",
        ],
    }
    
    # Parameter variations
    SENSORS = ['camera', 'lidar', 'thermal', 'imu', 'gps', 'ultrasonic', 'microphone']
    SENSOR_MODES = ['stream', 'capture', 'calibrate', 'standby']
    MISSION_TYPES = ['patrol', 'search', 'mapping', 'delivery', 'inspection']
    FORMATIONS = ['line', 'grid', 'circle', 'v_formation', 'custom']
    SLAM_MODES = ['mapping', 'localization', 'navigation']
    CALIBRATION_SYSTEMS = ['imu', 'cameras', 'gripper', 'joints', 'lidar', 'full']
    TASK_TYPES = ['navigate', 'manipulate', 'inspect', 'wait', 'charge']
    PRIORITIES = ['low', 'normal', 'high', 'emergency']
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
    
    def generate_robot_command_examples(self, count: int = 500) -> List[TrainingExample]:
        """Generate robot_command training examples"""
        examples = []
        instructions = [
            "pick up the red box", "deliver package to zone A", "scan the area",
            "inspect the equipment", "move the pallet", "open the door",
            "check temperature", "take a photo", "measure distance",
            "find the object", "avoid obstacles", "maintain position",
            "rotate 90 degrees", "move forward 2 meters", "backup slowly",
            "climb the stairs", "cross the gap", "push the button",
        ]
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['robot_command'])
            robot_id = random.choice(self.ROBOT_IDS)
            instruction = random.choice(instructions)
            priority = random.choice(self.PRIORITIES)
            
            text = template.format(robot_id=robot_id, instruction=instruction)
            
            output = {
                "calls": [{
                    "name": "robot_command",
                    "arguments": {
                        "robot_id": robot_id,
                        "instruction": instruction,
                        "priority": priority
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="robot_command"
            ))
        
        return examples
    
    def generate_swarm_examples(self, count: int = 300) -> List[TrainingExample]:
        """Generate swarm_deploy training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['swarm_deploy'])
            swarm_id = f"swarm_{random.randint(1, 100)}"
            num_robots = random.randint(2, 8)
            robot_ids = random.sample(self.ROBOT_IDS, num_robots)
            mission = random.choice(self.MISSION_TYPES)
            formation = random.choice(self.FORMATIONS)
            
            text = template.format(
                swarm_id=swarm_id,
                robot_list=', '.join(robot_ids),
                mission_type=mission,
                formation=formation
            )
            
            output = {
                "calls": [{
                    "name": "swarm_deploy",
                    "arguments": {
                        "swarm_id": swarm_id,
                        "robot_ids": robot_ids,
                        "mission_type": mission,
                        "formation": formation
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="swarm_deploy"
            ))
        
        return examples
    
    def generate_sensor_examples(self, count: int = 300) -> List[TrainingExample]:
        """Generate sensor_activate training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['sensor_activate'])
            robot_id = random.choice(self.ROBOT_IDS)
            sensor = random.choice(self.SENSORS)
            mode = random.choice(self.SENSOR_MODES)
            
            text = template.format(robot_id=robot_id, sensor_type=sensor, mode=mode)
            
            output = {
                "calls": [{
                    "name": "sensor_activate",
                    "arguments": {
                        "robot_id": robot_id,
                        "sensor_type": sensor,
                        "mode": mode
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="sensor_activate"
            ))
        
        return examples
    
    def generate_slam_examples(self, count: int = 200) -> List[TrainingExample]:
        """Generate slam_start training examples"""
        examples = []
        resolutions = [0.01, 0.02, 0.05, 0.1, 0.2]
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['slam_start'])
            robot_id = random.choice(self.ROBOT_IDS)
            mode = random.choice(self.SLAM_MODES)
            resolution = random.choice(resolutions)
            
            text = template.format(robot_id=robot_id, mode=mode, resolution=resolution)
            
            output = {
                "calls": [{
                    "name": "slam_start",
                    "arguments": {
                        "robot_id": robot_id,
                        "mode": mode,
                        "resolution": resolution
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="slam_start"
            ))
        
        return examples
    
    def generate_navigation_examples(self, count: int = 400) -> List[TrainingExample]:
        """Generate navigation_goto training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['navigation_goto'])
            robot_id = random.choice(self.ROBOT_IDS)
            x = round(random.uniform(-50, 50), 2)
            y = round(random.uniform(-50, 50), 2)
            
            text = template.format(robot_id=robot_id, x=x, y=y)
            
            output = {
                "calls": [{
                    "name": "navigation_goto",
                    "arguments": {
                        "robot_id": robot_id,
                        "destination": {
                            "x": x,
                            "y": y,
                            "z": 0.0,
                            "frame": "map"
                        },
                        "obstacle_avoidance": True,
                        "speed": 0.5
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="navigation_goto"
            ))
        
        return examples
    
    def generate_calibration_examples(self, count: int = 150) -> List[TrainingExample]:
        """Generate calibration_run training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['calibration_run'])
            robot_id = random.choice(self.ROBOT_IDS)
            system = random.choice(self.CALIBRATION_SYSTEMS)
            
            text = template.format(robot_id=robot_id, system=system)
            
            output = {
                "calls": [{
                    "name": "calibration_run",
                    "arguments": {
                        "robot_id": robot_id,
                        "system": system,
                        "auto_accept": False
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="calibration_run"
            ))
        
        return examples
    
    def generate_emergency_examples(self, count: int = 100) -> List[TrainingExample]:
        """Generate emergency_stop training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['emergency_stop'])
            robot_id = random.choice(['all'] + self.ROBOT_IDS)
            
            text = template.format(robot_id=robot_id)
            
            output = {
                "calls": [{
                    "name": "emergency_stop",
                    "arguments": {
                        "robot_id": robot_id,
                        "reason": "Emergency stop triggered by voice command"
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="emergency_stop"
            ))
        
        return examples
    
    def generate_status_examples(self, count: int = 150) -> List[TrainingExample]:
        """Generate status_check training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['status_check'])
            robot_id = random.choice(self.ROBOT_IDS)
            detailed = random.choice([True, False])
            
            text = template.format(robot_id=robot_id)
            
            output = {
                "calls": [{
                    "name": "status_check",
                    "arguments": {
                        "robot_id": robot_id,
                        "detailed": detailed
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="status_check"
            ))
        
        return examples
    
    def generate_manipulator_examples(self, count: int = 200) -> List[TrainingExample]:
        """Generate manipulator_control training examples"""
        examples = []
        actions = ['open', 'close', 'grasp', 'release', 'move_to', 'rotate']
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['manipulator_control'])
            robot_id = random.choice(self.ROBOT_IDS)
            action = random.choice(actions)
            force = round(random.uniform(5, 50), 1)
            
            text = template.format(robot_id=robot_id)
            
            args = {"robot_id": robot_id, "action": action}
            if action in ['grasp', 'close']:
                args["force"] = force
            
            output = {
                "calls": [{
                    "name": "manipulator_control",
                    "arguments": args
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="manipulator_control"
            ))
        
        return examples
    
    def generate_task_queue_examples(self, count: int = 150) -> List[TrainingExample]:
        """Generate task_queue_submit training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['task_queue_submit'])
            robot_id = random.choice(self.ROBOT_IDS)
            task_type = random.choice(self.TASK_TYPES)
            priority = random.randint(1, 10)
            
            text = template.format(robot_id=robot_id, task_type=task_type, priority=priority)
            
            output = {
                "calls": [{
                    "name": "task_queue_submit",
                    "arguments": {
                        "robot_id": robot_id,
                        "task_type": task_type,
                        "priority": priority
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="task_queue_submit"
            ))
        
        return examples
    
    def generate_patrol_examples(self, count: int = 100) -> List[TrainingExample]:
        """Generate patrol_route training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['patrol_route'])
            robot_id = random.choice(self.ROBOT_IDS)
            
            text = template.format(robot_id=robot_id)
            
            output = {
                "calls": [{
                    "name": "patrol_route",
                    "arguments": {
                        "robot_id": robot_id,
                        "loop": True
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="patrol_route"
            ))
        
        return examples
    
    def generate_return_examples(self, count: int = 100) -> List[TrainingExample]:
        """Generate return_to_base training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['return_to_base'])
            robot_id = random.choice(self.ROBOT_IDS)
            
            text = template.format(robot_id=robot_id)
            
            output = {
                "calls": [{
                    "name": "return_to_base",
                    "arguments": {
                        "robot_id": robot_id
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="return_to_base"
            ))
        
        return examples
    
    def generate_follow_examples(self, count: int = 100) -> List[TrainingExample]:
        """Generate follow_me training examples"""
        examples = []
        
        for _ in range(count):
            template = random.choice(self.TEMPLATES['follow_me'])
            robot_id = random.choice(self.ROBOT_IDS)
            distance = round(random.uniform(1.0, 3.0), 1)
            
            text = template.format(robot_id=robot_id, distance=distance)
            
            output = {
                "calls": [{
                    "name": "follow_me",
                    "arguments": {
                        "robot_id": robot_id,
                        "distance": distance
                    }
                }]
            }
            
            examples.append(TrainingExample(
                instruction=text,
                input_text=text,
                output_json=output,
                function_name="follow_me"
            ))
        
        return examples
    
    def generate_multi_function_examples(self, count: int = 200) -> List[TrainingExample]:
        """Generate examples with multiple function calls"""
        examples = []
        
        for _ in range(count):
            # Complex commands that require multiple actions
            robot_id = random.choice(self.ROBOT_IDS)
            
            scenarios = [
                {
                    "text": f"Deploy {robot_id} to sector 7 and scan for heat",
                    "calls": [
                        {"name": "navigation_goto", "args": {"robot_id": robot_id, "destination": {"x": 70, "y": 0, "z": 0, "frame": "map"}}},
                        {"name": "sensor_activate", "args": {"robot_id": robot_id, "sensor_type": "thermal", "mode": "stream"}}
                    ]
                },
                {
                    "text": f"Map the warehouse with {robot_id} then return to base",
                    "calls": [
                        {"name": "slam_start", "args": {"robot_id": robot_id, "mode": "mapping", "resolution": 0.05}},
                        {"name": "return_to_base", "args": {"robot_id": robot_id}}
                    ]
                },
                {
                    "text": f"Check {robot_id}'s status and calibrate if needed",
                    "calls": [
                        {"name": "status_check", "args": {"robot_id": robot_id, "detailed": True}},
                        {"name": "calibration_run", "args": {"robot_id": robot_id, "system": "imu"}}
                    ]
                },
            ]
            
            scenario = random.choice(scenarios)
            
            output = {"calls": scenario["calls"]}
            
            examples.append(TrainingExample(
                instruction=scenario["text"],
                input_text=scenario["text"],
                output_json=output,
                function_name="multi"
            ))
        
        return examples


def format_for_gemma(examples: List[TrainingExample]) -> List[Dict]:
    """Format examples for Gemma fine-tuning"""
    formatted = []
    
    for ex in examples:
        # Build conversation format
        conversation = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a robot control assistant. Convert natural language commands to function calls. Respond with JSON: {\"calls\": [{\"name\": \"function_name\", \"arguments\": {...}}]}"
                },
                {
                    "role": "user",
                    "content": ex.input_text
                },
                {
                    "role": "assistant",
                    "content": json.dumps(ex.output_json)
                }
            ]
        }
        formatted.append(conversation)
    
    return formatted


def main():
    parser = argparse.ArgumentParser(description='Generate NWO Robotics training dataset')
    parser.add_argument('--output', '-o', default='nwo_commands_train.jsonl', help='Output file')
    parser.add_argument('--val-split', type=float, default=0.1, help='Validation split ratio')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()
    
    generator = NWOCommandGenerator(seed=args.seed)
    
    print("Generating training examples...")
    
    # Generate all examples
    all_examples = []
    all_examples.extend(generator.generate_robot_command_examples(500))
    all_examples.extend(generator.generate_swarm_examples(300))
    all_examples.extend(generator.generate_sensor_examples(300))
    all_examples.extend(generator.generate_slam_examples(200))
    all_examples.extend(generator.generate_navigation_examples(400))
    all_examples.extend(generator.generate_calibration_examples(150))
    all_examples.extend(generator.generate_emergency_examples(100))
    all_examples.extend(generator.generate_status_examples(150))
    all_examples.extend(generator.generate_manipulator_examples(200))
    all_examples.extend(generator.generate_task_queue_examples(150))
    all_examples.extend(generator.generate_patrol_examples(100))
    all_examples.extend(generator.generate_return_examples(100))
    all_examples.extend(generator.generate_follow_examples(100))
    all_examples.extend(generator.generate_multi_function_examples(200))
    
    # Shuffle
    random.shuffle(all_examples)
    
    # Split train/val
    split_idx = int(len(all_examples) * (1 - args.val_split))
    train_examples = all_examples[:split_idx]
    val_examples = all_examples[split_idx:]
    
    # Format for Gemma
    train_formatted = format_for_gemma(train_examples)
    val_formatted = format_for_gemma(val_examples)
    
    # Write training set
    train_file = args.output
    with open(train_file, 'w') as f:
        for ex in train_formatted:
            f.write(json.dumps(ex) + '\n')
    
    # Write validation set - use same directory as train file
    import os
    train_dir = os.path.dirname(args.output)
    val_file = os.path.join(train_dir, 'nwo_commands_val.jsonl')
    with open(val_file, 'w') as f:
        for ex in val_formatted:
            f.write(json.dumps(ex) + '\n')
    
    print(f"Generated {len(train_examples)} training examples -> {train_file}")
    print(f"Generated {len(val_examples)} validation examples -> {val_file}")
    
    # Print sample
    print("\nSample training example:")
    print(json.dumps(train_formatted[0], indent=2))


if __name__ == '__main__':
    main()
