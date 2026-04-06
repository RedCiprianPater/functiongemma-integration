#!/usr/bin/env python3
"""
FunctionGemma ROS2 Bridge
Connects on-device FunctionGemma inference to ROS2 robot control
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from sensor_msgs.msg import Image, PointCloud2
import json
import asyncio
from typing import Dict, Any, Optional
import threading


class FunctionGemmaROS2Bridge(Node):
    """ROS2 node that receives function calls from FunctionGemma and executes robot commands"""
    
    def __init__(self):
        super().__init__('functiongemma_ros2_bridge')
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.command_pub = self.create_publisher(String, '/nwo/robot_command', 10)
        self.emergency_pub = self.create_publisher(Bool, '/nwo/emergency_stop', 10)
        
        # Subscribers
        self.create_subscription(
            String,
            '/nwo/function_call',
            self.function_call_callback,
            10
        )
        
        # Action clients
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # State
        self.current_pose = None
        self.is_navigating = False
        self.robot_status = {
            'battery': 100.0,
            'state': 'idle',
            'position': {'x': 0.0, 'y': 0.0, 'z': 0.0}
        }
        
        # Local command cache for offline mode
        self.offline_commands = []
        self.offline_mode = False
        
        self.get_logger().info('FunctionGemma ROS2 Bridge initialized')
    
    def function_call_callback(self, msg: String):
        """Process incoming function calls from FunctionGemma"""
        try:
            call = json.loads(msg.data)
            function_name = call.get('name')
            arguments = call.get('arguments', {})
            
            self.get_logger().info(f'Received function call: {function_name}')
            
            # Route to appropriate handler
            handler = getattr(self, f'handle_{function_name}', None)
            if handler:
                handler(arguments)
            else:
                self.get_logger().warn(f'Unknown function: {function_name}')
                
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Invalid JSON: {e}')
        except Exception as e:
            self.get_logger().error(f'Error processing function call: {e}')
    
    def handle_robot_command(self, args: Dict[str, Any]):
        """Handle natural language robot commands"""
        robot_id = args.get('robot_id', 'default')
        instruction = args.get('instruction', '')
        priority = args.get('priority', 'normal')
        
        self.get_logger().info(f'Robot command [{priority}]: {instruction}')
        
        # Parse instruction and convert to concrete actions
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'natural_language',
            'robot_id': robot_id,
            'instruction': instruction,
            'priority': priority,
            'timestamp': self.get_clock().now().to_msg().sec
        })
        self.command_pub.publish(command_msg)
    
    def handle_swarm_deploy(self, args: Dict[str, Any]):
        """Deploy robots as a coordinated swarm"""
        swarm_id = args.get('swarm_id', 'default_swarm')
        robot_ids = args.get('robot_ids', [])
        formation = args.get('formation', 'grid')
        mission_type = args.get('mission_type', 'patrol')
        
        self.get_logger().info(f'Deploying swarm {swarm_id} with {len(robot_ids)} robots')
        
        # Publish swarm command
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'swarm_deploy',
            'swarm_id': swarm_id,
            'robot_ids': robot_ids,
            'formation': formation,
            'mission_type': mission_type
        })
        self.command_pub.publish(command_msg)
        
        # Set formation-based waypoints
        waypoints = self.calculate_formation_waypoints(formation, len(robot_ids))
        for i, robot_id in enumerate(robot_ids):
            if i < len(waypoints):
                self.send_navigation_goal(robot_id, waypoints[i])
    
    def handle_sensor_activate(self, args: Dict[str, Any]):
        """Activate or configure robot sensors"""
        robot_id = args.get('robot_id', 'default')
        sensor_type = args.get('sensor_type', 'camera')
        mode = args.get('mode', 'stream')
        settings = args.get('settings', {})
        
        self.get_logger().info(f'Activating {sensor_type} on {robot_id} in {mode} mode')
        
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'sensor_control',
            'robot_id': robot_id,
            'sensor': sensor_type,
            'mode': mode,
            'settings': settings
        })
        self.command_pub.publish(command_msg)
    
    def handle_slam_start(self, args: Dict[str, Any]):
        """Start SLAM mapping or localization"""
        robot_id = args.get('robot_id', 'default')
        mode = args.get('mode', 'mapping')
        resolution = args.get('resolution', 0.05)
        area_bounds = args.get('area_bounds', {})
        
        self.get_logger().info(f'Starting SLAM {mode} on {robot_id}')
        
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'slam_control',
            'robot_id': robot_id,
            'mode': mode,
            'resolution': resolution,
            'area_bounds': area_bounds
        })
        self.command_pub.publish(command_msg)
    
    def handle_navigation_goto(self, args: Dict[str, Any]):
        """Navigate robot to specific coordinates"""
        robot_id = args.get('robot_id', 'default')
        destination = args.get('destination', {})
        obstacle_avoidance = args.get('obstacle_avoidance', True)
        speed = args.get('speed', 0.5)
        
        x = destination.get('x', 0.0)
        y = destination.get('y', 0.0)
        z = destination.get('z', 0.0)
        frame = destination.get('frame', 'map')
        
        self.get_logger().info(f'Navigating {robot_id} to ({x}, {y}, {z}) in {frame} frame')
        
        self.send_navigation_goal(robot_id, (x, y, z), speed)
    
    def handle_calibration_run(self, args: Dict[str, Any]):
        """Run calibration procedure"""
        robot_id = args.get('robot_id', 'default')
        system = args.get('system', 'full')
        auto_accept = args.get('auto_accept', False)
        
        self.get_logger().info(f'Running {system} calibration on {robot_id}')
        
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'calibration',
            'robot_id': robot_id,
            'system': system,
            'auto_accept': auto_accept
        })
        self.command_pub.publish(command_msg)
    
    def handle_emergency_stop(self, args: Dict[str, Any]):
        """Emergency stop all robot motion"""
        robot_id = args.get('robot_id', 'all')
        reason = args.get('reason', 'Emergency stop triggered')
        
        self.get_logger().error(f'EMERGENCY STOP: {reason}')
        
        # Publish emergency stop
        emergency_msg = Bool()
        emergency_msg.data = True
        self.emergency_pub.publish(emergency_msg)
        
        # Stop motion immediately
        stop_cmd = Twist()
        self.cmd_vel_pub.publish(stop_cmd)
        
        # Cancel any ongoing navigation
        if self.is_navigating:
            self.nav_client.cancel_all_goals()
            self.is_navigating = False
    
    def handle_status_check(self, args: Dict[str, Any]):
        """Check robot status"""
        robot_id = args.get('robot_id', 'default')
        detailed = args.get('detailed', False)
        
        self.get_logger().info(f'Status check for {robot_id}')
        
        # Return current status
        status_msg = String()
        status_msg.data = json.dumps({
            'type': 'status_response',
            'robot_id': robot_id,
            'status': self.robot_status,
            'detailed': detailed
        })
        self.command_pub.publish(status_msg)
    
    def handle_manipulator_control(self, args: Dict[str, Any]):
        """Control robot manipulator/gripper"""
        robot_id = args.get('robot_id', 'default')
        action = args.get('action', 'open')
        position = args.get('position', {})
        force = args.get('force', 10.0)
        
        self.get_logger().info(f'Manipulator {action} on {robot_id}')
        
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'manipulator',
            'robot_id': robot_id,
            'action': action,
            'position': position,
            'force': force
        })
        self.command_pub.publish(command_msg)
    
    def handle_task_queue_submit(self, args: Dict[str, Any]):
        """Submit task to robot's queue"""
        robot_id = args.get('robot_id', 'default')
        task_type = args.get('task_type', 'navigate')
        parameters = args.get('parameters', {})
        priority = args.get('priority', 5)
        
        self.get_logger().info(f'Queueing {task_type} task for {robot_id} (priority {priority})')
        
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'task_queue',
            'robot_id': robot_id,
            'task_type': task_type,
            'parameters': parameters,
            'priority': priority
        })
        self.command_pub.publish(command_msg)
    
    def handle_patrol_route(self, args: Dict[str, Any]):
        """Start patrol route"""
        robot_id = args.get('robot_id', 'default')
        waypoints = args.get('waypoints', [])
        loop = args.get('loop', True)
        
        self.get_logger().info(f'Starting patrol route with {len(waypoints)} waypoints')
        
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'patrol',
            'robot_id': robot_id,
            'waypoints': waypoints,
            'loop': loop
        })
        self.command_pub.publish(command_msg)
    
    def handle_return_to_base(self, args: Dict[str, Any]):
        """Return robot to base/charging station"""
        robot_id = args.get('robot_id', 'default')
        
        self.get_logger().info(f'Returning {robot_id} to base')
        
        # Navigate to base position (0, 0, 0)
        self.send_navigation_goal(robot_id, (0.0, 0.0, 0.0))
    
    def handle_follow_me(self, args: Dict[str, Any]):
        """Enable follow mode"""
        robot_id = args.get('robot_id', 'default')
        distance = args.get('distance', 1.5)
        
        self.get_logger().info(f'Enabling follow mode on {robot_id}')
        
        command_msg = String()
        command_msg.data = json.dumps({
            'type': 'follow',
            'robot_id': robot_id,
            'distance': distance
        })
        self.command_pub.publish(command_msg)
    
    def send_navigation_goal(self, robot_id: str, position: tuple, speed: float = 0.5):
        """Send navigation goal to Nav2"""
        if not self.nav_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warn('Navigation server not available')
            return
        
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = position[0]
        goal_msg.pose.pose.position.y = position[1]
        goal_msg.pose.pose.position.z = position[2] if len(position) > 2 else 0.0
        goal_msg.pose.pose.orientation.w = 1.0
        
        self.nav_client.send_goal_async(goal_msg)
        self.is_navigating = True
    
    def calculate_formation_waypoints(self, formation: str, count: int) -> list:
        """Calculate waypoints for swarm formation"""
        waypoints = []
        spacing = 2.0  # meters
        
        if formation == 'line':
            for i in range(count):
                waypoints.append((i * spacing, 0.0, 0.0))
        elif formation == 'grid':
            side = int(count ** 0.5)
            for i in range(count):
                x = (i % side) * spacing
                y = (i // side) * spacing
                waypoints.append((x, y, 0.0))
        elif formation == 'circle':
            radius = spacing * count / (2 * 3.14159)
            for i in range(count):
                angle = 2 * 3.14159 * i / count
                x = radius * cos(angle)
                y = radius * sin(angle)
                waypoints.append((x, y, 0.0))
        elif formation == 'v_formation':
            for i in range(count):
                row = i // 2
                side = 1 if i % 2 == 0 else -1
                x = row * spacing
                y = side * row * spacing * 0.5
                waypoints.append((x, y, 0.0))
        
        return waypoints
    
    def set_offline_mode(self, enabled: bool):
        """Enable/disable offline mode"""
        self.offline_mode = enabled
        self.get_logger().info(f'Offline mode: {enabled}')


def main(args=None):
    rclpy.init(args=args)
    
    bridge = FunctionGemmaROS2Bridge()
    
    try:
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    from math import cos, sin
    main()
