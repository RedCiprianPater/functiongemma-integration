#!/usr/bin/env python3
"""
Swarm Control Demo for FunctionGemma + NWO Robotics
Demonstrates coordinated multi-robot control via voice
"""

import json
import time
import random


class SwarmController:
    """Simulated swarm controller"""
    
    def __init__(self):
        self.robots = {
            'drone_001': {'type': 'drone', 'battery': 85, 'status': 'idle'},
            'drone_002': {'type': 'drone', 'battery': 92, 'status': 'idle'},
            'drone_003': {'type': 'drone', 'battery': 78, 'status': 'idle'},
            'go2_001': {'type': 'ground', 'battery': 65, 'status': 'idle'},
            'go2_002': {'type': 'ground', 'battery': 88, 'status': 'idle'},
        }
        self.active_swarm = None
    
    def deploy_swarm(self, swarm_id: str, robot_ids: list, mission: str, formation: str):
        """Deploy a robot swarm"""
        print(f"\n🚀 DEPLOYING SWARM: {swarm_id}")
        print(f"   Mission: {mission}")
        print(f"   Formation: {formation}")
        print(f"   Robots: {', '.join(robot_ids)}")
        
        self.active_swarm = {
            'id': swarm_id,
            'robots': robot_ids,
            'mission': mission,
            'formation': formation,
            'status': 'deploying'
        }
        
        # Simulate deployment
        for robot_id in robot_ids:
            if robot_id in self.robots:
                self.robots[robot_id]['status'] = f'deployed_{mission}'
                print(f"   ✓ {robot_id} deployed")
                time.sleep(0.2)
        
        self.active_swarm['status'] = 'active'
        print(f"   ✓ Swarm {swarm_id} is ACTIVE")
        
        return self.active_swarm
    
    def get_formation_positions(self, formation: str, count: int):
        """Calculate formation positions"""
        positions = []
        spacing = 5.0
        
        if formation == 'line':
            for i in range(count):
                positions.append({'x': i * spacing, 'y': 0, 'z': 10})
        elif formation == 'grid':
            side = int(count ** 0.5)
            for i in range(count):
                x = (i % side) * spacing
                y = (i // side) * spacing
                positions.append({'x': x, 'y': y, 'z': 10})
        elif formation == 'v_formation':
            for i in range(count):
                row = i // 2
                side = 1 if i % 2 == 0 else -1
                positions.append({'x': row * spacing, 'y': side * row * spacing * 0.5, 'z': 10})
        
        return positions
    
    def status_report(self):
        """Print swarm status"""
        print(f"\n📊 SWARM STATUS")
        print(f"   Active Swarm: {self.active_swarm['id'] if self.active_swarm else 'None'}")
        print(f"   Robot Status:")
        for rid, info in self.robots.items():
            status_emoji = '🟢' if 'deployed' in info['status'] else '⚪'
            print(f"     {status_emoji} {rid}: {info['status']} (battery: {info['battery']}%)")


def demo_swarm_deployment():
    """Demo: Deploy search swarm"""
    controller = SwarmController()
    
    print("\n" + "="*60)
    print("VOICE COMMAND: \"Deploy search swarm with 3 drones in V formation\"")
    print("="*60)
    
    # FunctionGemma parses this to:
    function_call = {
        "calls": [{
            "name": "swarm_deploy",
            "arguments": {
                "swarm_id": "search_alpha",
                "robot_ids": ["drone_001", "drone_002", "drone_003"],
                "mission_type": "search",
                "formation": "v_formation"
            }
        }]
    }
    
    print("\n🤖 FunctionGemma Output:")
    print(json.dumps(function_call, indent=2))
    
    # Execute
    call = function_call['calls'][0]
    controller.deploy_swarm(
        call['arguments']['swarm_id'],
        call['arguments']['robot_ids'],
        call['arguments']['mission_type'],
        call['arguments']['formation']
    )
    
    controller.status_report()


def demo_coordinated_mission():
    """Demo: Coordinated warehouse inspection"""
    controller = SwarmController()
    
    print("\n" + "="*60)
    print("VOICE COMMAND: \"Inspect warehouse sector A with all available robots\"")
    print("="*60)
    
    # Multi-function call
    function_call = {
        "calls": [
            {
                "name": "swarm_deploy",
                "arguments": {
                    "swarm_id": "inspection_team",
                    "robot_ids": ["drone_001", "drone_002", "go2_001", "go2_002"],
                    "mission_type": "inspection",
                    "formation": "grid"
                }
            },
            {
                "name": "sensor_activate",
                "arguments": {
                    "robot_id": "drone_001",
                    "sensor_type": "camera",
                    "mode": "stream"
                }
            },
            {
                "name": "sensor_activate",
                "arguments": {
                    "robot_id": "go2_001",
                    "sensor_type": "lidar",
                    "mode": "stream"
                }
            }
        ]
    }
    
    print("\n🤖 FunctionGemma Output:")
    print(json.dumps(function_call, indent=2))
    
    # Execute swarm deploy
    swarm_call = function_call['calls'][0]
    controller.deploy_swarm(
        swarm_call['arguments']['swarm_id'],
        swarm_call['arguments']['robot_ids'],
        swarm_call['arguments']['mission_type'],
        swarm_call['arguments']['formation']
    )
    
    # Activate sensors
    for call in function_call['calls'][1:]:
        print(f"\n📡 Activating {call['arguments']['sensor_type']} on {call['arguments']['robot_id']}")
    
    controller.status_report()


def demo_emergency_recall():
    """Demo: Emergency recall"""
    controller = SwarmController()
    
    # First deploy a swarm
    controller.deploy_swarm(
        "patrol_alpha",
        ["drone_001", "drone_002", "go2_001"],
        "patrol",
        "line"
    )
    
    print("\n" + "="*60)
    print("VOICE COMMAND: \"Emergency recall all robots to base\"")
    print("="*60)
    
    function_call = {
        "calls": [
            {
                "name": "emergency_stop",
                "arguments": {
                    "robot_id": "all",
                    "reason": "Emergency recall"
                }
            },
            {
                "name": "return_to_base",
                "arguments": {"robot_id": "drone_001"}
            },
            {
                "name": "return_to_base",
                "arguments": {"robot_id": "drone_002"}
            },
            {
                "name": "return_to_base",
                "arguments": {"robot_id": "go2_001"}
            }
        ]
    }
    
    print("\n🤖 FunctionGemma Output:")
    print(json.dumps(function_call, indent=2))
    
    print("\n🚨 Executing emergency recall...")
    for call in function_call['calls']:
        if call['name'] == 'emergency_stop':
            print(f"   ⛔ Emergency stop: {call['arguments']['reason']}")
        elif call['name'] == 'return_to_base':
            print(f"   🏠 {call['arguments']['robot_id']} returning to base")
            controller.robots[call['arguments']['robot_id']]['status'] = 'returning'
    
    controller.status_report()


def main():
    print("="*60)
    print("NWO Robotics Swarm Control Demo")
    print("FunctionGemma Multi-Robot Coordination")
    print("="*60)
    
    demos = [
        ("Swarm Deployment", demo_swarm_deployment),
        ("Coordinated Mission", demo_coordinated_mission),
        ("Emergency Recall", demo_emergency_recall),
    ]
    
    print("\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    
    for name, demo_func in demos:
        print(f"\n{'='*60}")
        input(f"Press Enter to run: {name}...")
        demo_func()
    
    print("\n" + "="*60)
    print("Swarm Demo Complete!")
    print("="*60)


if __name__ == '__main__':
    main()
