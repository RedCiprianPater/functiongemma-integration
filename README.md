# FunctionGemma Integration for NWO Robotics

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![C++17](https://img.shields.io/badge/C++-17-blue.svg)](https://isocpp.org/)

On-device function calling for NWO Robotics using Google's FunctionGemma (270M parameters). Control robots with natural language voice commands — no cloud required.

## 🚀 Quick Start

### Option 1: Google AI Edge Gallery (Easiest)

1. Install [Google AI Edge Gallery](https://play.google.com/store/apps/details?id=com.google.android.apps.ai.edge) on Android
2. Import our schema: `edge_gallery_schema.json`
3. Enter your NWO API key
4. Start controlling robots with voice commands

See [EDGE_GALLERY_GUIDE.md](EDGE_GALLERY_GUIDE.md) for details.

### Option 2: Build Your Own App

```bash
# Clone repository
git clone https://github.com/nwo-robotics/functiongemma-integration.git
cd functiongemma-integration

# Install Python dependencies
pip install -r edge_runtime/mqtt_bridge/requirements.txt

# Run MQTT bridge
python edge_runtime/mqtt_bridge/functiongemma_mqtt_bridge.py
```

### Option 3: C++ Edge Runtime (Jetson/Embedded)

```bash
cd edge_runtime
mkdir build && cd build
cmake .. -DUSE_GPU=ON
make -j4
./examples/example_inference models/functiongemma-nwo.tflite models/tokenizer.json
```

## 📁 Repository Structure

```
functiongemma-integration/
├── README.md                          # This file
├── API_ENDPOINTS_COVERAGE.md          # Complete API documentation
├── EDGE_GALLERY_GUIDE.md              # Edge Gallery integration guide
├── edge_gallery_schema.json           # Importable schema for Edge Gallery
│
├── function_schemas/                  # Function definitions
│   ├── nwo_robotics_functions.json    # 45+ endpoint schemas
│   ├── gemma_config.yaml              # Model configuration
│   └── system_prompt.txt              # System prompt for Gemma
│
├── mobile_app/                        # Mobile applications
│   ├── android/                       # Kotlin Android app
│   └── ios/                           # Swift iOS app
│
├── edge_runtime/                      # Edge deployment
│   ├── litert_runtime/                # C++ LiteRT runtime
│   │   ├── model_loader.h/cc          # Model loading
│   │   ├── inference_engine.h/cc      # Inference engine
│   │   ├── function_parser.h/cc       # Function parsing
│   │   └── CMakeLists.txt             # Build configuration
│   ├── ros2_bridge/                   # ROS2 integration
│   │   ├── functiongemma_ros2_bridge.py
│   │   └── offline_command_server.py
│   └── mqtt_bridge/                   # MQTT integration (NEW)
│       ├── functiongemma_mqtt_bridge.py
│       ├── requirements.txt
│       └── README.md
│
├── training/                          # Fine-tuning
│   ├── fine_tuning/
│   │   ├── prepare_nwo_dataset.py
│   │   ├── train_functiongemma.py
│   │   └── convert_to_litert.py
│   └── datasets/
│       ├── nwo_commands_train.jsonl   # 2,600+ examples
│       └── nwo_commands_val.jsonl
│
└── examples/                          # Usage examples
    ├── voice_command_demo.py
    ├── swarm_control_demo.py
    └── offline_mode_demo.py
```

## ✨ Features

- ✅ **45+ API Endpoints** - Complete NWO Robotics API coverage
- ✅ **On-Device Inference** - No internet required for command parsing
- ✅ **Voice Control** - Natural language to robot commands
- ✅ **Multi-Platform** - Android, iOS, Linux, Jetson
- ✅ **MQTT Bridge** - Industrial IoT integration
- ✅ **ROS2 Bridge** - Robot operating system integration
- ✅ **Offline Mode** - Cached commands work without connectivity
- ✅ **Safety First** - Confirmation dialogs for critical operations

## 🔌 Integration Options

### MQTT Bridge (Industrial IoT)

Connect to industrial MQTT brokers (Mosquitto, HiveMQ, AWS IoT):

```python
from functiongemma_mqtt_bridge import FunctionGemmaMQTTBridge

bridge = FunctionGemmaMQTTBridge(
    broker_host="broker.hivemq.com",
    broker_port=1883
)
bridge.connect()

# Now robots can be controlled via MQTT topics:
# Publish to: nwo/function/call
# {"name": "robot_command", "arguments": {"robot_id": "go2_001", "instruction": "move forward"}}
```

See [edge_runtime/mqtt_bridge/README.md](edge_runtime/mqtt_bridge/README.md)

### ROS2 Bridge

Integrate with ROS2 for direct robot control:

```bash
# Terminal 1: Start ROS2 bridge
ros2 run functiongemma_ros2 functiongemma_ros2_bridge

# Terminal 2: Publish function call
ros2 topic pub /nwo/function_call std_msgs/String '{data: "{\"name\": \"robot_command\", \"arguments\": {...}}"}'
```

### C++ Edge Runtime

For embedded deployments (Jetson Nano, Raspberry Pi, etc.):

```cpp
#include "inference_engine.h"

auto engine = nwo::litert::CreateInferenceEngine(
    "model.tflite", "tokenizer.json", true, 4
);

auto result = engine->RunInference(
    "Move go2_001 forward",
    parser,
    256,    // max tokens
    0.7f    // temperature
);
```

## 🎯 Example Commands

| Voice Input | Function Called |
|-------------|-----------------|
| "Move go2_001 forward 2 meters" | `robot_command` |
| "Deploy swarm alpha for patrol" | `swarm_deploy` |
| "Check battery on spot_001" | `status_check` |
| "Emergency stop all robots" | `emergency_stop` |
| "Start mapping with 5cm resolution" | `slam_start` |
| "Navigate to coordinates 10, 20" | `navigation_goto` |
| "Calibrate the IMU" | `calibration_run` |
| "Open gripper" | `manipulator_control` |

## 📊 Performance Benchmarks

| Device | CPU Prefill | CPU Decode | GPU Prefill | GPU Decode |
|--------|-------------|------------|-------------|------------|
| Pixel 7 Pro | 1916 tok/s | 142 tok/s | 2847 tok/s | 198 tok/s |
| iPhone 15 Pro | 2100 tok/s | 165 tok/s | 3200 tok/s | 245 tok/s |
| Jetson Orin Nano | 850 tok/s | 68 tok/s | 1450 tok/s | 112 tok/s |
| Raspberry Pi 5 | 320 tok/s | 28 tok/s | N/A | N/A |

## 🔧 Configuration

### API Key

Get your API key from [nwo.capital/settings](https://nwo.capital/webapp/settings.php)

### Environment Variables

```bash
export NWO_API_KEY="your-api-key"
export MQTT_BROKER="localhost"
export MQTT_PORT="1883"
export USE_GPU="true"
```

## 🛡️ Safety

- **Emergency stop** requires confirmation
- **Swarm deploy** requires confirmation  
- **Calibration** requires confirmation
- All commands logged for audit
- Offline mode caches last 100 commands
- API keys never leave the device

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for contribution:
- Additional robot platforms
- More voice languages
- Improved training data
- Edge case handling
- Documentation

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🔗 Links

- [NWO Robotics](https://nwo.capital)
- [FunctionGemma Paper](https://arxiv.org/abs/240x.xxxxx)
- [Google AI Edge Gallery](https://play.google.com/store/apps/details?id=com.google.android.apps.ai.edge)
- [Issues](https://github.com/nwo-robotics/functiongemma-integration/issues)

## 📞 Support

- Discord: [NWO Robotics Community](https://discord.gg/nwo)
- Email: support@nwo.capital
- Telegram: [@PaterPontifex](https://t.me/PaterPontifex)

---

**Built with ❤️ by NWO Robotics** | Powering the future of autonomous systems
