# FunctionGemma MQTT Bridge

## Overview

The MQTT Bridge connects FunctionGemma to industrial MQTT brokers, enabling:
- **Cloud connectivity** for remote robot monitoring
- **Industrial integration** with SCADA/MES systems  
- **Fleet management** across multiple sites
- **AWS IoT / Azure IoT Hub** compatibility

## Quick Start

### 1. Install Dependencies

```bash
cd edge_runtime/mqtt_bridge
pip install -r requirements.txt
```

### 2. Run with Local Mosquitto

```bash
# Start Mosquitto broker
sudo apt install mosquitto
sudo systemctl start mosquitto

# Run bridge
python functiongemma_mqtt_bridge.py
```

### 3. Run with AWS IoT Core

```bash
export MQTT_BROKER=your-endpoint.iot.region.amazonaws.com
export MQTT_PORT=8883
export MQTT_USER=your-client-id
export MQTT_PASS=your-certificate
export MQTT_TLS=true

python functiongemma_mqtt_bridge.py
```

## MQTT Topics

### Subscribe (Incoming Commands)

| Topic | Description |
|-------|-------------|
| `nwo/function/call` | FunctionGemma function calls (JSON) |
| `nwo/robot/+/command` | Direct robot commands |
| `nwo/swarm/+/command` | Swarm deployment commands |
| `nwo/emergency/stop` | Emergency stop all robots |
| `nwo/robot/+/status/request` | Request robot status |
| `nwo/config/update` | Update bridge configuration |

### Publish (Outgoing Data)

| Topic | Description |
|-------|-------------|
| `nwo/robot/{id}/status` | Robot status updates |
| `nwo/robot/{id}/response` | Command responses |
| `nwo/robot/{id}/telemetry` | Continuous telemetry |
| `nwo/function/result` | Function call results |
| `nwo/error` | Error messages |

## Example Messages

### Function Call

```json
{
  "name": "robot_command",
  "arguments": {
    "robot_id": "go2_001",
    "instruction": "move forward 2 meters",
    "priority": "normal"
  },
  "request_id": "req_12345"
}
```

### Swarm Deploy

```json
{
  "name": "swarm_deploy",
  "arguments": {
    "swarm_id": "inspection_team",
    "robot_ids": ["go2_001", "go2_002", "drone_001"],
    "formation": "v_formation",
    "mission_type": "inspection"
  }
}
```

### Emergency Stop

```json
{
  "robot_id": "all",
  "reason": "Human entered work area"
}
```

## Integration with NWO Robotics Cloud

To connect to your actual NWO API, modify the handler methods in `functiongemma_mqtt_bridge.py`:

```python
def _handle_robot_command(self, args: Dict) -> Dict:
    import requests
    
    response = requests.post(
        'https://nwo.capital/api-robotics.php?action=execute',
        headers={'X-API-Key': 'your-api-key'},
        json=args
    )
    
    return response.json()
```

## Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY functiongemma_mqtt_bridge.py .
CMD ["python", "functiongemma_mqtt_bridge.py"]
```

```bash
docker build -t functiongemma-mqtt .
docker run -e MQTT_BROKER=broker.hivemq.com functiongemma-mqtt
```
