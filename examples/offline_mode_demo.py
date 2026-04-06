#!/usr/bin/env python3
"""
Offline Mode Demo for FunctionGemma + NWO Robotics
Demonstrates operation without network connectivity
"""

import json
import time
from datetime import datetime


class OfflineModeDemo:
    """Simulate offline robot operation"""
    
    def __init__(self):
        self.online = True
        self.command_queue = []
        self.executed_commands = []
        self.cached_patterns = {
            'stop': {'function': 'emergency_stop', 'args': {'robot_id': 'all'}},
            'go home': {'function': 'return_to_base', 'args': {}},
            'status': {'function': 'status_check', 'args': {'detailed': False}},
            'patrol': {'function': 'patrol_route', 'args': {'loop': True}},
        }
    
    def set_connectivity(self, online: bool):
        """Toggle connectivity state"""
        if self.online and not online:
            print("\n⚠️  CONNECTION LOST - Entering offline mode")
            print("   ✓ Local command cache activated")
            print("   ✓ Safety protocols armed")
            print("   ✓ Cached patterns loaded")
        elif not self.online and online:
            print("\n🌐 CONNECTION RESTORED - Syncing queued commands")
            self.sync_offline_queue()
        
        self.online = online
    
    def process_command(self, voice_command: str):
        """Process a voice command"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] 🎤 \"{voice_command}\"")
        
        # Simulate FunctionGemma inference
        function_call = self.infer_function(voice_command)
        
        if self.online:
            print(f"   🌐 Online - Executing immediately")
            self.execute_command(function_call)
        else:
            print(f"   📴 Offline - Caching command")
            self.cache_command(function_call)
    
    def infer_function(self, command: str):
        """Simulate on-device inference"""
        # Simplified pattern matching
        if 'stop' in command.lower():
            return {'name': 'emergency_stop', 'args': {'robot_id': 'all'}, 'priority': 10}
        elif 'home' in command.lower() or 'base' in command.lower():
            return {'name': 'return_to_base', 'args': {'robot_id': 'go2_001'}, 'priority': 8}
        elif 'status' in command.lower():
            return {'name': 'status_check', 'args': {'robot_id': 'go2_001'}, 'priority': 5}
        elif 'patrol' in command.lower():
            return {'name': 'patrol_route', 'args': {'robot_id': 'go2_001', 'loop': True}, 'priority': 5}
        else:
            return {'name': 'robot_command', 'args': {'robot_id': 'go2_001', 'instruction': command}, 'priority': 3}
    
    def cache_command(self, function_call: dict):
        """Cache command for later execution"""
        self.command_queue.append({
            'timestamp': time.time(),
            'function': function_call['name'],
            'args': function_call['args'],
            'priority': function_call.get('priority', 5)
        })
        
        # Sort by priority
        self.command_queue.sort(key=lambda x: x['priority'], reverse=True)
        
        # Execute high-priority commands immediately
        if function_call.get('priority', 0) >= 8:
            print(f"   ⚡ High priority - executing locally")
            self.execute_local(function_call)
        else:
            print(f"   💾 Queued ({len(self.command_queue)} commands in queue)")
    
    def execute_local(self, function_call: dict):
        """Execute command using local safety protocols"""
        print(f"   ✅ Local execution: {function_call['name']}")
        self.executed_commands.append(function_call)
    
    def execute_command(self, function_call: dict):
        """Execute command via API"""
        print(f"   ✅ API call: POST /api/{function_call['name']}")
        self.executed_commands.append(function_call)
    
    def sync_offline_queue(self):
        """Sync queued commands when back online"""
        if not self.command_queue:
            print("   No queued commands to sync")
            return
        
        print(f"   Syncing {len(self.command_queue)} commands...")
        
        for cmd in self.command_queue:
            print(f"   → {cmd['function']}")
        
        self.command_queue = []
        print("   ✓ Sync complete")
    
    def print_status(self):
        """Print current status"""
        status = "🌐 ONLINE" if self.online else "📴 OFFLINE"
        print(f"\n{'='*60}")
        print(f"Status: {status}")
        print(f"Queue size: {len(self.command_queue)}")
        print(f"Executed: {len(self.executed_commands)}")
        print(f"{'='*60}")


def demo_offline_scenario():
    """Demo: Warehouse loses WiFi during operation"""
    demo = OfflineModeDemo()
    
    print("="*60)
    print("Offline Mode Demo: Warehouse WiFi Outage")
    print("="*60)
    
    # Start online
    demo.print_status()
    
    # Normal operation
    print("\n--- Normal Operation (Online) ---")
    demo.process_command("Check status of robot 1")
    demo.process_command("Start patrol route")
    
    # Connection lost
    demo.set_connectivity(False)
    
    # Continue operating offline
    print("\n--- Operating Offline ---")
    demo.process_command("Check status")  # Low priority - queued
    demo.process_command("Go back to base")  # Medium priority - queued
    demo.process_command("Stop all robots immediately")  # High priority - executes locally
    demo.process_command("Continue patrol")  # Low priority - queued
    
    demo.print_status()
    
    # Connection restored
    demo.set_connectivity(True)
    
    demo.print_status()


def demo_mining_operation():
    """Demo: Underground mining with no connectivity"""
    demo = OfflineModeDemo()
    
    print("\n" + "="*60)
    print("Offline Mode Demo: Underground Mining")
    print("="*60)
    
    # Never had connectivity
    demo.online = False
    print("\n📴 Operating in dead zone - no connectivity available")
    print("   ✓ Safety protocols active")
    print("   ✓ Cached commands ready")
    
    commands = [
        "Deploy to sector 3",
        "Scan for hazards",
        "Check air quality",
        "Return to base",
        "Emergency stop",
    ]
    
    for cmd in commands:
        demo.process_command(cmd)
        time.sleep(0.5)
    
    demo.print_status()
    
    print("\n📡 Moving to surface - attempting sync...")
    demo.set_connectivity(True)


def main():
    print("="*60)
    print("NWO Robotics Offline Mode Demo")
    print("FunctionGemma Edge Deployment")
    print("="*60)
    
    demo_offline_scenario()
    
    input("\nPress Enter for next demo...")
    
    demo_mining_operation()
    
    print("\n" + "="*60)
    print("Offline Demo Complete!")
    print("="*60)
    print("\nKey Benefits:")
    print("  • Sub-100ms response times (no network latency)")
    print("  • Works in dead zones, underground, remote areas")
    print("  • Safety protocols execute even without connectivity")
    print("  • Automatic sync when connection restored")


if __name__ == '__main__':
    main()
