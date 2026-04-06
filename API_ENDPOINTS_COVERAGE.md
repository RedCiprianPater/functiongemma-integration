# NWO Robotics API Endpoints Coverage

This document shows all NWO Robotics API endpoints that are now integrated into the FunctionGemma system.

## ✅ Fully Integrated Endpoints

### Authentication
- Headers: `X-API-Key: sk_live_abc123xyz789` ✓ (Supported in all API clients)

### Inference & Models
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `inference` | `/api-robotics.php?action=inference` | POST | ✅ |
| `list_models` | `/api-robotics.php?action=list_models` | GET | ✅ |
| `get_model_info` | `/api-robotics.php?action=get_model_info` | GET | ✅ |
| Edge API | `https://nwo-robotics-api-edge.ciprianpater.workers.dev/api/inference` | POST | ✅ (via use_edge param) |
| `inference_stream` | `/api-robotics.php?action=inference_stream&format=sse` | GET | ✅ |
| `streaming_config` | `/api-robotics.php?action=streaming_config` | GET | ✅ |

### Robot Control
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `query_state` | `/api-robotics.php?action=query_state` | GET | ✅ |
| `robot_command` | `/api-robotics.php?action=execute` | POST | ✅ |
| `sensor_activate` | `/api-robotics.php?action=sensor_fusion` | POST | ✅ |
| `robot_query` | `/api-robotics.php?action=robot_query` | POST | ✅ |
| `get_agent_status` | `/api-robotics.php?action=get_agent_status` | POST | ✅ |

### Task & Learning System
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `task_planner` | `/api-robotics.php?action=task_planner` | POST | ✅ |
| `execute_subtask` | `/api-robotics.php?action=execute_subtask` | POST | ✅ |
| `learning_recommend` | `/api-robotics.php?action=learning&subaction=recommend` | POST | ✅ |
| `learning_log` | `/api-robotics.php?action=learning&subaction=log` | POST | ✅ |

### Agent Management
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `register_agent` | `/api-agent-register.php` | POST | ✅ |
| `agent_pay` | `/api-agent-pay.php` | POST | ✅ |
| `check_agent_balance` | `/api-agent-balance.php` | GET | ✅ |
| `register_agent` | `/api-robotics.php?action=register_agent` | POST | ✅ |
| `update_agent` | `/api-robotics.php?action=update_agent` | PUT | ✅ |
| `get_agent` | `/api-robotics.php?action=get_agent` | GET | ✅ |

### Agent Discovery API
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `agent_discovery_health` | `/api-agent-discovery.php?action=health` | GET | ✅ |
| `agent_discovery_whoami` | `/api-agent-discovery.php?action=whoami` | GET | ✅ |
| `agent_discovery_capabilities` | `/api-agent-discovery.php?action=capabilities` | GET | ✅ |
| `agent_discovery_dry_run` | `/api-agent-discovery.php?action=dry-run` | POST | ✅ |
| `agent_discovery_plan` | `/api-agent-discovery.php?action=plan` | POST | ✅ |

### ROS2 Bridge
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `ros2_submit_action` | `https://nwo-ros2-bridge.onrender.com/api/v1/action` | POST | ✅ |
| `ros2_list_robots` | `https://nwo-ros2-bridge.onrender.com/api/v1/robots` | GET | ✅ |
| `ros2_get_robot_status` | `https://nwo-ros2-bridge.onrender.com/api/v1/robots/{id}/status` | GET | ✅ |
| `ros2_send_command` | `https://nwo-ros2-bridge.onrender.com/api/v1/robots/{id}/command` | POST | ✅ |
| `ros2_emergency_stop` | `https://nwo-ros2-bridge.onrender.com/api/v1/robots/{id}/emergency_stop` | POST | ✅ |

### WebSocket & Streaming
| Function | Endpoint | Status |
|----------|----------|--------|
| WebSocket | `wss://nwo.capital/ws/stream` | ✅ |
| ROS2 WebSocket | `wss://nwo-ros2-bridge.onrender.com/ws/robot/{robot_id}` | ✅ |

### Physics & Simulation
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `simulate_trajectory` | `/api-simulation.php?action=simulate_trajectory` | POST | ✅ |
| `check_collision` | `/api-simulation.php?action=check_collision` | POST | ✅ |
| `estimate_torques` | `/api-simulation.php?action=estimate_torques` | POST | ✅ |
| `validate_grasp` | `/api-simulation.php?action=validate_grasp` | POST | ✅ |
| `plan_motion` | `/api-simulation.php?action=plan_motion` | POST | ✅ |
| `get_scene_library` | `/api-simulation.php?action=get_scene_library` | GET | ✅ |
| `generate_scene` | `/api-cosmos.php?action=generate_scene` | POST | ✅ |

### Embodiment & Calibration
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `list_embodiments` | `/api-embodiment.php?action=list` | GET | ✅ |
| `get_embodiment_detail` | `/api-embodiment.php?action=detail` | GET | ✅ |
| `get_normalization` | `/api-embodiment.php?action=normalization` | GET | ✅ |
| `get_urdf` | `/api-embodiment.php?action=urdf` | GET | ✅ |
| `get_test_results` | `/api-embodiment.php?action=test_results` | GET | ✅ |
| `compare_robots` | `/api-embodiment.php?action=compare` | POST | ✅ |
| `calibrate_confidence` | `/api-calibration.php?action=calibrate` | POST | ✅ |
| `run_calibration` | `/api-calibration.php?action=run_calibration` | POST | ✅ |

### Online RL & Fine-tuning
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `start_online_rl` | `/api-online-rl.php?action=start_online_rl` | POST | ✅ |
| `submit_telemetry` | `/api-online-rl.php?action=submit_telemetry` | POST | ✅ |
| `create_dataset` | `/api-fine-tune.php?action=create_dataset` | POST | ✅ |
| `start_fine_tuning` | `/api-fine-tune.php?action=start_job` | POST | ✅ |

### Tactile Sensing (ORCA Hand)
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `get_tactile` | `/api-orca.php?action=get_tactile` | POST | ✅ |
| `process_tactile` | `/api-tactile.php?action=process_input` | POST | ✅ |
| `slip_detection` | `/api-tactile.php?action=slip_detection` | POST | ✅ |

### Dataset Hub
| Function | Endpoint | Method | Status |
|----------|----------|--------|--------|
| `list_datasets` | `/api-unitree-datasets.php?action=list` | GET | ✅ |

### Additional Core Functions
| Function | Description | Status |
|----------|-------------|--------|
| `swarm_deploy` | Deploy robot swarms | ✅ |
| `slam_start` | Start SLAM mapping/localization | ✅ |
| `navigation_goto` | Navigate to coordinates | ✅ |
| `calibration_run` | Run calibration procedures | ✅ |
| `emergency_stop` | Emergency stop | ✅ |
| `status_check` | Check robot status | ✅ |
| `manipulator_control` | Control manipulator/gripper | ✅ |
| `task_queue_submit` | Submit tasks to queue | ✅ |
| `patrol_route` | Set up patrol routes | ✅ |
| `return_to_base` | Return to charging station | ✅ |
| `follow_me` | Enable follow mode | ✅ |
| `voice_interaction` | Voice command mode | ✅ |

## Files Updated

1. **`function_schemas/nwo_robotics_functions.json`** - Complete function schemas for all 45+ endpoints
2. **`mobile_app/ios/NwoRoboticsController/NwoApiClient.swift`** - iOS API client with all endpoints
3. **`mobile_app/android/app/src/main/java/com/nwo/robotics/NwoApiClient.kt`** - Android API client with all endpoints

## Usage Example

```swift
// iOS
let client = NwoApiClient(apiKey: "sk_live_abc123xyz789")

// Run inference
let result = await client.executeFunction(
    name: "inference",
    arguments: ["model_id": "gemma-2b", "input": ["text": "Hello"]]
)

// Control robot
let result = await client.executeFunction(
    name: "robot_command",
    arguments: ["robot_id": "go2_001", "instruction": "move forward"]
)

// ROS2 bridge
let result = await client.executeFunction(
    name: "ros2_send_command",
    arguments: ["robot_id": "spot_001", "command": "stand"]
)
```

```kotlin
// Android
val client = NwoApiClient(context, apiKey = "sk_live_abc123xyz789")

// Run inference
val result = client.executeFunction(
    "inference",
    mapOf("model_id" to "gemma-2b", "input" to mapOf("text" to "Hello"))
)

// Control robot
val result = client.executeFunction(
    "robot_command",
    mapOf("robot_id" to "go2_001", "instruction" to "move forward")
)
```

## Summary

✅ **All 45+ NWO Robotics API endpoints are now integrated into the FunctionGemma system**

The integration includes:
- Complete function schemas in JSON format
- iOS API client with all endpoints mapped
- Android API client with all endpoints mapped
- WebSocket support for streaming
- ROS2 bridge integration
- Offline queue support for critical commands
- Proper error handling and retry logic
