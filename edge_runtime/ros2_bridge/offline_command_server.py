#!/usr/bin/env python3
"""
Offline Command Server
Handles robot commands when connectivity is lost
Caches commands and executes safety protocols locally
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Float32
from geometry_msgs.msg import Pose, Twist
from nav_msgs.msg import Odometry
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import sqlite3
import os


class CommandPriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    EMERGENCY = 10


@dataclass
class CachedCommand:
    """Represents a cached command for offline execution"""
    id: str
    timestamp: float
    function_name: str
    arguments: Dict[str, Any]
    priority: int
    executed: bool = False
    result: Optional[str] = None


class OfflineCommandServer(Node):
    """
    Server that maintains command queue and executes safety protocols
    when network connectivity is lost
    """
    
    # Predefined safety protocols
    SAFETY_PROTOCOLS = {
        'emergency_stop': {
            'description': 'Stop all motion immediately',
            'action': 'publish_emergency_stop'
        },
        'return_to_base': {
            'description': 'Navigate to last known safe location',
            'action': 'navigate_to_base'
        },
        'status_broadcast': {
            'description': 'Broadcast status via local radio/bluetooth',
            'action': 'broadcast_status'
        },
        'low_battery_protocol': {
            'description': 'Return to charging station',
            'action': 'return_to_charge',
            'trigger': 'battery < 20%'
        }
    }
    
    # Cached command patterns (most common commands)
    CACHED_PATTERNS = {
        'stop': {'function': 'emergency_stop', 'args': {'robot_id': 'all'}},
        'go home': {'function': 'return_to_base', 'args': {}},
        'status': {'function': 'status_check', 'args': {'detailed': False}},
        'patrol': {'function': 'patrol_route', 'args': {'loop': True}},
        'follow': {'function': 'follow_me', 'args': {'distance': 1.5}},
        'charge': {'function': 'return_to_base', 'args': {}}
    }
    
    def __init__(self):
        super().__init__('offline_command_server')
        
        # Parameters
        self.declare_parameter('db_path', '/tmp/offline_commands.db')
        self.declare_parameter('max_cache_size', 1000)
        self.declare_parameter('sync_interval', 30.0)
        self.declare_parameter('battery_threshold', 20.0)
        
        # Initialize database
        self.db_path = self.get_parameter('db_path').value
        self.init_database()
        
        # Publishers
        self.emergency_pub = self.create_publisher(Bool, '/nwo/emergency_stop', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/nwo/offline_status', 10)
        self.broadcast_pub = self.create_publisher(String, '/nwo/local_broadcast', 10)
        
        # Subscribers
        self.create_subscription(String, '/nwo/function_call', self.on_function_call, 10)
        self.create_subscription(Odometry, '/odom', self.on_odometry, 10)
        self.create_subscription(Float32, '/battery_level', self.on_battery, 10)
        self.create_subscription(Bool, '/nwo/connectivity', self.on_connectivity_change, 10)
        
        # State
        self.is_online = True
        self.command_queue: List[CachedCommand] = []
        self.current_pose = None
        self.battery_level = 100.0
        self.base_position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        self.last_waypoints = []
        
        # Timers
        self.create_timer(self.get_parameter('sync_interval').value, self.attempt_sync)
        self.create_timer(1.0, self.check_safety_conditions)
        
        self.get_logger().info('Offline Command Server initialized')
    
    def init_database(self):
        """Initialize SQLite database for persistent command storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                function_name TEXT,
                arguments TEXT,
                priority INTEGER,
                executed BOOLEAN,
                result TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS waypoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                x REAL,
                y REAL,
                z REAL,
                timestamp REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def on_function_call(self, msg: String):
        """Handle incoming function calls"""
        try:
            call = json.loads(msg.data)
            
            if self.is_online:
                # Forward to cloud/primary API
                self.get_logger().debug('Online mode - forwarding command')
                return
            
            # Offline mode - cache and queue
            self.cache_command(call)
            
        except json.JSONDecodeError:
            self.get_logger().error('Invalid JSON in function call')
    
    def cache_command(self, call: Dict[str, Any]):
        """Cache a command for offline execution"""
        cmd = CachedCommand(
            id=f"cmd_{int(time.time() * 1000)}",
            timestamp=time.time(),
            function_name=call.get('name', 'unknown'),
            arguments=call.get('arguments', {}),
            priority=call.get('priority', CommandPriority.NORMAL.value)
        )
        
        # Add to queue
        self.command_queue.append(cmd)
        self.command_queue.sort(key=lambda x: x.priority, reverse=True)
        
        # Persist to database
        self.persist_command(cmd)
        
        self.get_logger().info(f'Cached command: {cmd.function_name} (priority {cmd.priority})')
        
        # Execute immediately if high priority
        if cmd.priority >= CommandPriority.HIGH.value:
            self.execute_cached_command(cmd)
    
    def persist_command(self, cmd: CachedCommand):
        """Save command to persistent storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO commands 
            (id, timestamp, function_name, arguments, priority, executed, result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            cmd.id,
            cmd.timestamp,
            cmd.function_name,
            json.dumps(cmd.arguments),
            cmd.priority,
            cmd.executed,
            cmd.result
        ))
        
        conn.commit()
        conn.close()
    
    def execute_cached_command(self, cmd: CachedCommand):
        """Execute a cached command locally"""
        self.get_logger().info(f'Executing: {cmd.function_name}')
        
        handler = getattr(self, f'execute_{cmd.function_name}', None)
        
        if handler:
            try:
                result = handler(cmd.arguments)
                cmd.result = json.dumps({'status': 'success', 'result': result})
            except Exception as e:
                cmd.result = json.dumps({'status': 'error', 'message': str(e)})
        else:
            # Try to match cached pattern
            result = self.execute_pattern(cmd.function_name, cmd.arguments)
            cmd.result = json.dumps(result)
        
        cmd.executed = True
        self.persist_command(cmd)
    
    def execute_pattern(self, function_name: str, args: Dict[str, Any]) -> Dict:
        """Execute using cached pattern matching"""
        # Check if we have a similar cached pattern
        for pattern_name, pattern in self.CACHED_PATTERNS.items():
            if pattern['function'] == function_name:
                merged_args = {**pattern['args'], **args}
                handler = getattr(self, f'execute_{function_name}', None)
                if handler:
                    return handler(merged_args)
        
        return {'status': 'unknown_command', 'message': f'No handler for {function_name}'}
    
    # Command Executors
    
    def execute_emergency_stop(self, args: Dict[str, Any]) -> Dict:
        """Execute emergency stop"""
        self.publish_emergency_stop()
        return {'action': 'emergency_stop', 'timestamp': time.time()}
    
    def execute_return_to_base(self, args: Dict[str, Any]) -> Dict:
        """Navigate to base position"""
        if self.current_pose:
            # Simple navigation to base
            twist = self.calculate_velocity_to_target(self.base_position)
            self.cmd_vel_pub.publish(twist)
            return {'action': 'return_to_base', 'target': self.base_position}
        return {'error': 'No current position available'}
    
    def execute_status_check(self, args: Dict[str, Any]) -> Dict:
        """Return current status"""
        status = {
            'battery': self.battery_level,
            'position': self.current_pose,
            'queue_size': len(self.command_queue),
            'online': self.is_online,
            'timestamp': time.time()
        }
        
        # Broadcast locally
        msg = String()
        msg.data = json.dumps(status)
        self.broadcast_pub.publish(msg)
        
        return status
    
    def execute_patrol_route(self, args: Dict[str, Any]) -> Dict:
        """Execute patrol using saved waypoints"""
        waypoints = args.get('waypoints', self.last_waypoints)
        loop = args.get('loop', True)
        
        if not waypoints:
            return {'error': 'No waypoints available'}
        
        # Simple patrol logic - navigate to next waypoint
        if self.current_pose:
            current = waypoints[0]
            twist = self.calculate_velocity_to_target(current)
            self.cmd_vel_pub.publish(twist)
        
        return {'action': 'patrol', 'waypoints': len(waypoints), 'loop': loop}
    
    def execute_follow_me(self, args: Dict[str, Any]) -> Dict:
        """Enable follow mode (requires external tracker)"""
        distance = args.get('distance', 1.5)
        return {'action': 'follow_me', 'distance': distance, 'note': 'Requires person tracking'}
    
    def execute_navigation_goto(self, args: Dict[str, Any]) -> Dict:
        """Navigate to coordinates"""
        destination = args.get('destination', {})
        x = destination.get('x', 0.0)
        y = destination.get('y', 0.0)
        
        twist = self.calculate_velocity_to_target({'x': x, 'y': y, 'z': 0.0})
        self.cmd_vel_pub.publish(twist)
        
        return {'action': 'navigation', 'target': {'x': x, 'y': y}}
    
    def calculate_velocity_to_target(self, target: Dict[str, float]) -> Twist:
        """Calculate velocity command to reach target"""
        twist = Twist()
        
        if not self.current_pose:
            return twist
        
        dx = target['x'] - self.current_pose['x']
        dy = target['y'] - self.current_pose['y']
        
        # Simple proportional control
        distance = (dx**2 + dy**2) ** 0.5
        
        if distance > 0.1:  # 10cm threshold
            max_speed = 0.5
            twist.linear.x = min(max_speed, distance * 0.5)
            twist.angular.z = 0.5 * (dy / distance if distance > 0 else 0)
        
        return twist
    
    def publish_emergency_stop(self):
        """Publish emergency stop message"""
        msg = Bool()
        msg.data = True
        self.emergency_pub.publish(msg)
        
        # Also send zero velocity
        self.cmd_vel_pub.publish(Twist())
    
    # Event Handlers
    
    def on_odometry(self, msg: Odometry):
        """Update current position"""
        self.current_pose = {
            'x': msg.pose.pose.position.x,
            'y': msg.pose.pose.position.y,
            'z': msg.pose.pose.position.z
        }
    
    def on_battery(self, msg: Float32):
        """Monitor battery level"""
        self.battery_level = msg.data
    
    def on_connectivity_change(self, msg: Bool):
        """Handle connectivity status changes"""
        was_online = self.is_online
        self.is_online = msg.data
        
        if was_online and not self.is_online:
            self.get_logger().warn('Connection lost - entering offline mode')
            self.enter_offline_mode()
        elif not was_online and self.is_online:
            self.get_logger().info('Connection restored - syncing queued commands')
            self.exit_offline_mode()
    
    def enter_offline_mode(self):
        """Activate offline mode with safety protocols"""
        status = String()
        status.data = json.dumps({
            'event': 'offline_mode_entered',
            'timestamp': time.time(),
            'queued_commands': len(self.command_queue)
        })
        self.status_pub.publish(status)
        
        # Broadcast status via local radio/bluetooth
        self.broadcast_pub.publish(status)
    
    def exit_offline_mode(self):
        """Restore online mode and sync"""
        self.attempt_sync()
    
    def attempt_sync(self):
        """Attempt to sync queued commands with cloud"""
        if not self.is_online:
            return
        
        pending = [cmd for cmd in self.command_queue if not cmd.executed]
        
        if pending:
            self.get_logger().info(f'Attempting to sync {len(pending)} commands')
            
            # In real implementation, this would send to cloud API
            for cmd in pending:
                cmd.executed = True
                self.persist_command(cmd)
            
            self.command_queue = []
    
    def check_safety_conditions(self):
        """Periodic safety check"""
        # Low battery check
        if self.battery_level < self.get_parameter('battery_threshold').value:
            self.get_logger().warn(f'Low battery: {self.battery_level}%')
            
            if not self.is_online:
                # Trigger return to charge protocol
                self.cache_command({
                    'name': 'return_to_base',
                    'arguments': {},
                    'priority': CommandPriority.HIGH.value
                })


def main(args=None):
    rclpy.init(args=args)
    
    server = OfflineCommandServer()
    
    try:
        rclpy.spin(server)
    except KeyboardInterrupt:
        pass
    finally:
        server.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
