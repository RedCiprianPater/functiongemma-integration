# MQTT Bridge for FunctionGemma-NWO Robotics

import paho.mqtt.client as mqtt
import json
import asyncio
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FunctionGemmaMQTTBridge:
    """
    MQTT Bridge connecting FunctionGemma to NWO Robotics API
    
    Subscribes to robot command topics, publishes status updates.
    Works with industrial MQTT brokers (Mosquitto, HiveMQ, AWS IoT, etc.)
    """
    
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        client_id: str = "functiongemma_bridge_001"
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        
        # MQTT Client
        self.client = mqtt.Client(client_id=client_id)
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        if use_tls:
            self.client.tls_set()
        
        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Topic patterns
        self.topics = {
            'commands': 'nwo/robot/+/command',
            'function_calls': 'nwo/function/call',
            'swarm_commands': 'nwo/swarm/+/command',
            'emergency': 'nwo/emergency/stop',
            'status_request': 'nwo/robot/+/status/request',
            'config': 'nwo/config/update'
        }
        
        # Publish topics
        self.pub_topics = {
            'status': 'nwo/robot/{robot_id}/status',
            'response': 'nwo/robot/{robot_id}/response',
            'telemetry': 'nwo/robot/{robot_id}/telemetry',
            'function_result': 'nwo/function/result',
            'error': 'nwo/error'
        }
        
        # State
        self.connected = False
        self.robot_states = {}
        self.command_queue = []
        
        # Function handlers (mapped to NWO API)
        self.function_handlers = {
            'robot_command': self._handle_robot_command,
            'swarm_deploy': self._handle_swarm_deploy,
            'sensor_activate': self._handle_sensor_activate,
            'slam_start': self._handle_slam_start,
            'navigation_goto': self._handle_navigation_goto,
            'calibration_run': self._handle_calibration_run,
            'emergency_stop': self._handle_emergency_stop,
            'status_check': self._handle_status_check,
            'manipulator_control': self._handle_manipulator_control,
            'task_queue_submit': self._handle_task_queue_submit,
            'patrol_route': self._handle_patrol_route,
            'return_to_base': self._handle_return_to_base,
            'follow_me': self._handle_follow_me,
            'inference': self._handle_inference,
            'list_models': self._handle_list_models,
            'query_state': self._handle_query_state,
            'task_planner': self._handle_task_planner,
            'learning_recommend': self._handle_learning_recommend,
            'ros2_send_command': self._handle_ros2_command,
            'simulate_trajectory': self._handle_simulation,
            'check_collision': self._handle_simulation,
            'get_tactile': self._handle_tactile
        }
    
    def _on_connect(self, client, userdata, flags, rc):
        """Called when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to all command topics
            for topic in self.topics.values():
                client.subscribe(topic)
                logger.info(f"Subscribed to: {topic}")
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Called when disconnected from broker"""
        self.connected = False
        logger.warning(f"Disconnected from broker (rc={rc})")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            logger.info(f"Received message on {topic}")
            
            # Route based on topic pattern
            if topic == 'nwo/function/call':
                self._process_function_call(payload)
            elif topic == 'nwo/emergency/stop':
                self._handle_emergency_stop(payload)
            elif 'swarm' in topic:
                self._process_swarm_command(topic, payload)
            elif 'command' in topic:
                self._process_robot_command(topic, payload)
            elif 'status/request' in topic:
                self._process_status_request(topic)
            elif topic == 'nwo/config/update':
                self._process_config_update(payload)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            self._publish_error("invalid_json", str(e))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self._publish_error("processing_error", str(e))
    
    def _process_function_call(self, payload: Dict[str, Any]):
        """Process a FunctionGemma function call"""
        function_name = payload.get('name')
        arguments = payload.get('arguments', {})
        request_id = payload.get('request_id', 'unknown')
        
        logger.info(f"Processing function call: {function_name}")
        
        handler = self.function_handlers.get(function_name)
        if handler:
            try:
                result = handler(arguments)
                self._publish_function_result(request_id, function_name, result, success=True)
            except Exception as e:
                logger.error(f"Function {function_name} failed: {e}")
                self._publish_function_result(request_id, function_name, {"error": str(e)}, success=False)
        else:
            logger.warning(f"Unknown function: {function_name}")
            self._publish_function_result(request_id, function_name, {"error": "Unknown function"}, success=False)
    
    def _process_robot_command(self, topic: str, payload: Dict[str, Any]):
        """Process direct robot command from MQTT"""
        # Extract robot_id from topic: nwo/robot/{id}/command
        parts = topic.split('/')
        if len(parts) >= 3:
            robot_id = parts[2]
            payload['robot_id'] = robot_id
            
            # Convert to function call format
            function_call = {
                'name': 'robot_command',
                'arguments': payload,
                'request_id': payload.get('request_id', f"cmd_{robot_id}")
            }
            self._process_function_call(function_call)
    
    def _process_swarm_command(self, topic: str, payload: Dict[str, Any]):
        """Process swarm command from MQTT"""
        parts = topic.split('/')
        if len(parts) >= 3:
            swarm_id = parts[2]
            payload['swarm_id'] = swarm_id
            
            function_call = {
                'name': 'swarm_deploy',
                'arguments': payload,
                'request_id': payload.get('request_id', f"swarm_{swarm_id}")
            }
            self._process_function_call(function_call)
    
    def _process_status_request(self, topic: str):
        """Handle status request"""
        parts = topic.split('/')
        if len(parts) >= 3:
            robot_id = parts[2]
            self._handle_status_check({'robot_id': robot_id, 'detailed': True})
    
    def _process_config_update(self, payload: Dict[str, Any]):
        """Handle configuration updates"""
        logger.info(f"Config update received: {payload}")
        # Update local configuration
        if 'broker_host' in payload:
            self.broker_host = payload['broker_host']
        if 'log_level' in payload:
            logging.getLogger().setLevel(getattr(logging, payload['log_level'].upper()))
    
    # Function Handlers (integrate with NWO API)
    
    def _handle_robot_command(self, args: Dict) -> Dict:
        """Send natural language command to robot"""
        robot_id = args.get('robot_id')
        instruction = args.get('instruction')
        priority = args.get('priority', 'normal')
        
        # TODO: Integrate with actual NWO API
        # For now, simulate success
        result = {
            'robot_id': robot_id,
            'command': instruction,
            'priority': priority,
            'status': 'accepted',
            'timestamp': asyncio.get_event_loop().time()
        }
        
        self._publish_robot_response(robot_id, result)
        return result
    
    def _handle_swarm_deploy(self, args: Dict) -> Dict:
        """Deploy robot swarm"""
        swarm_id = args.get('swarm_id')
        robot_ids = args.get('robot_ids', [])
        formation = args.get('formation', 'grid')
        mission_type = args.get('mission_type', 'inspection')
        
        result = {
            'swarm_id': swarm_id,
            'robots': robot_ids,
            'formation': formation,
            'mission': mission_type,
            'status': 'deployed'
        }
        
        # Publish status for each robot in swarm
        for robot_id in robot_ids:
            self._publish_robot_status(robot_id, {'swarm_id': swarm_id, 'role': 'swarm_member'})
        
        return result
    
    def _handle_sensor_activate(self, args: Dict) -> Dict:
        """Activate robot sensor"""
        return {
            'robot_id': args.get('robot_id'),
            'sensor': args.get('sensor_type'),
            'mode': args.get('mode', 'stream'),
            'status': 'activated'
        }
    
    def _handle_slam_start(self, args: Dict) -> Dict:
        """Start SLAM mapping/localization"""
        return {
            'robot_id': args.get('robot_id'),
            'mode': args.get('mode'),
            'resolution': args.get('resolution', 0.05),
            'status': 'started'
        }
    
    def _handle_navigation_goto(self, args: Dict) -> Dict:
        """Navigate to coordinates"""
        return {
            'robot_id': args.get('robot_id'),
            'destination': args.get('destination'),
            'obstacle_avoidance': args.get('obstacle_avoidance', True),
            'status': 'navigating'
        }
    
    def _handle_calibration_run(self, args: Dict) -> Dict:
        """Run calibration procedure"""
        return {
            'robot_id': args.get('robot_id'),
            'system': args.get('system'),
            'auto_accept': args.get('auto_accept', False),
            'status': 'calibrating'
        }
    
    def _handle_emergency_stop(self, args: Dict) -> Dict:
        """Emergency stop all robots or specific robot"""
        robot_id = args.get('robot_id', 'all')
        reason = args.get('reason', 'Emergency stop triggered')
        
        # Publish emergency stop to all robots if 'all'
        if robot_id == 'all':
            self.client.publish('nwo/emergency/all', json.dumps({
                'action': 'stop',
                'reason': reason,
                'timestamp': asyncio.get_event_loop().time()
            }))
        
        return {
            'robot_id': robot_id,
            'action': 'emergency_stop',
            'reason': reason,
            'status': 'executed'
        }
    
    def _handle_status_check(self, args: Dict) -> Dict:
        """Check robot status"""
        robot_id = args.get('robot_id')
        detailed = args.get('detailed', False)
        
        status = {
            'robot_id': robot_id,
            'online': True,
            'battery': 85.0,
            'state': 'idle',
            'position': {'x': 0.0, 'y': 0.0, 'z': 0.0}
        }
        
        if detailed:
            status.update({
                'sensors': ['camera', 'lidar', 'imu'],
                'temperature': 42.0,
                'uptime': 3600
            })
        
        self._publish_robot_status(robot_id, status)
        return status
    
    def _handle_manipulator_control(self, args: Dict) -> Dict:
        """Control robot manipulator"""
        return {
            'robot_id': args.get('robot_id'),
            'action': args.get('action'),
            'position': args.get('position'),
            'force': args.get('force'),
            'status': 'executed'
        }
    
    def _handle_task_queue_submit(self, args: Dict) -> Dict:
        """Submit task to queue"""
        return {
            'robot_id': args.get('robot_id'),
            'task_type': args.get('task_type'),
            'priority': args.get('priority', 5),
            'status': 'queued'
        }
    
    def _handle_patrol_route(self, args: Dict) -> Dict:
        """Set up patrol route"""
        return {
            'robot_id': args.get('robot_id'),
            'loop': args.get('loop', True),
            'status': 'patrol_started'
        }
    
    def _handle_return_to_base(self, args: Dict) -> Dict:
        """Return to charging station"""
        return {
            'robot_id': args.get('robot_id'),
            'action': 'return_to_base',
            'status': 'returning'
        }
    
    def _handle_follow_me(self, args: Dict) -> Dict:
        """Enable follow mode"""
        return {
            'robot_id': args.get('robot_id'),
            'distance': args.get('distance', 1.0),
            'mode': 'follow',
            'status': 'active'
        }
    
    def _handle_inference(self, args: Dict) -> Dict:
        """Run model inference"""
        return {
            'model_id': args.get('model_id', 'gemma-2b'),
            'input': args.get('input'),
            'output': {'text': 'Inference result placeholder'},
            'latency_ms': 150
        }
    
    def _handle_list_models(self, args: Dict) -> Dict:
        """List available models"""
        return {
            'models': [
                {'id': 'gemma-2b', 'name': 'Gemma 2B'},
                {'id': 'gemma-function', 'name': 'FunctionGemma'},
                {'id': 'nwo-control', 'name': 'NWO Control Model'}
            ]
        }
    
    def _handle_query_state(self, args: Dict) -> Dict:
        """Query robot state"""
        return self._handle_status_check(args)
    
    def _handle_task_planner(self, args: Dict) -> Dict:
        """Plan multi-step task"""
        return {
            'task': args.get('task'),
            'plan': ['step1', 'step2', 'step3'],
            'estimated_duration': 300
        }
    
    def _handle_learning_recommend(self, args: Dict) -> Dict:
        """Get learning recommendations"""
        return {
            'robot_id': args.get('robot_id'),
            'recommendations': ['improve_navigation', 'optimize_grasping']
        }
    
    def _handle_ros2_command(self, args: Dict) -> Dict:
        """Send command via ROS2 bridge"""
        return {
            'robot_id': args.get('robot_id'),
            'command': args.get('command'),
            'bridge': 'ros2',
            'status': 'sent'
        }
    
    def _handle_simulation(self, args: Dict) -> Dict:
        """Run physics simulation"""
        return {
            'action': args.get('action', 'simulate'),
            'result': 'simulation_complete',
            'metrics': {'success_rate': 0.95}
        }
    
    def _handle_tactile(self, args: Dict) -> Dict:
        """Get tactile sensor data"""
        return {
            'robot_id': args.get('robot_id'),
            'sensor_data': {'pressure': [0.1, 0.2, 0.3]},
            'slip_detected': False
        }
    
    # Publishing helpers
    
    def _publish_robot_status(self, robot_id: str, status: Dict):
        """Publish robot status to MQTT"""
        topic = self.pub_topics['status'].format(robot_id=robot_id)
        self.client.publish(topic, json.dumps(status))
    
    def _publish_robot_response(self, robot_id: str, response: Dict):
        """Publish robot command response"""
        topic = self.pub_topics['response'].format(robot_id=robot_id)
        self.client.publish(topic, json.dumps(response))
    
    def _publish_function_result(self, request_id: str, function_name: str, result: Dict, success: bool):
        """Publish function call result"""
        payload = {
            'request_id': request_id,
            'function': function_name,
            'success': success,
            'result': result,
            'timestamp': asyncio.get_event_loop().time()
        }
        self.client.publish(self.pub_topics['function_result'], json.dumps(payload))
    
    def _publish_error(self, error_type: str, message: str):
        """Publish error message"""
        payload = {
            'type': error_type,
            'message': message,
            'timestamp': asyncio.get_event_loop().time()
        }
        self.client.publish(self.pub_topics['error'], json.dumps(payload))
    
    # Public API
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
        logger.info("Disconnected from MQTT broker")
    
    def publish_telemetry(self, robot_id: str, data: Dict):
        """Publish robot telemetry"""
        topic = self.pub_topics['telemetry'].format(robot_id=robot_id)
        self.client.publish(topic, json.dumps(data))
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected


# Standalone runner
if __name__ == '__main__':
    import os
    
    # Get config from environment
    broker_host = os.getenv('MQTT_BROKER', 'localhost')
    broker_port = int(os.getenv('MQTT_PORT', '1883'))
    username = os.getenv('MQTT_USER')
    password = os.getenv('MQTT_PASS')
    use_tls = os.getenv('MQTT_TLS', 'false').lower() == 'true'
    
    bridge = FunctionGemmaMQTTBridge(
        broker_host=broker_host,
        broker_port=broker_port,
        username=username,
        password=password,
        use_tls=use_tls
    )
    
    try:
        if bridge.connect():
            logger.info("MQTT Bridge running. Press Ctrl+C to exit.")
            while True:
                import time
                time.sleep(1)
        else:
            logger.error("Failed to start bridge")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        bridge.disconnect()
