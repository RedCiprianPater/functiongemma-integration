# Google AI Edge Gallery Integration

## Quick Start for Users

### 1. Install Google AI Edge Gallery

- **Android**: [Google Play Store](https://play.google.com/store/apps/details?id=com.google.android.apps.ai.edge)
- **iOS**: Coming soon

### 2. Import NWO Robotics Schema

1. Open AI Edge Gallery app
2. Tap **"Import Custom Model"**
3. Select **"Import from URL"**
4. Enter: `https://nwo.capital/functiongemma/edge_gallery_schema.json`
5. Or download `edge_gallery_schema.json` and import from file

### 3. Configure API Key

1. Get your API key from [nwo.capital/settings](https://nwo.capital/webapp/settings.php)
2. In the app, go to **Settings → API Configuration**
3. Enter your API key
4. Tap **Test Connection**

### 4. Start Controlling Robots

1. Tap the microphone button
2. Say: *"Check status of go2_001"*
3. The app will:
   - Convert speech to text
   - Run FunctionGemma inference
   - Call the NWO API
   - Show robot status

## Schema Format

The `edge_gallery_schema.json` follows the Google AI Edge Gallery custom function format:

```json
{
  "name": "NWO Robotics Controller",
  "model": {
    "base_model": "google/functiongemma-270m",
    "format": "litert"
  },
  "functions": [...],
  "api": {...},
  "examples": [...]
}
```

## Hosting the Schema

### Option 1: Static File on Your Server

Upload `edge_gallery_schema.json` to:
```
https://nwo.capital/.well-known/ai-edge-gallery/nwo-robotics.json
```

This enables auto-discovery when users search "NWO Robotics" in the Edge Gallery app.

### Option 2: GitHub Pages

1. Fork the schema to a GitHub repo
2. Enable GitHub Pages
3. Users import from: `https://yourusername.github.io/nwo-functiongemma/edge_gallery_schema.json`

## Offline Mode

The schema includes `offline_fallback: true`, which enables:

- **Cached commands**: Last 100 commands work without internet
- **Safety protocols**: Emergency stop always works offline
- **Local queue**: Commands queue and sync when reconnected

## Voice Commands Reference

| Command | Function Called |
|---------|----------------|
| "Move {robot} forward" | `robot_command` |
| "Deploy swarm {name}" | `swarm_deploy` |
| "Stop all robots" | `emergency_stop` |
| "Check {robot} battery" | `status_check` |
| "Start mapping" | `slam_start` |
| "Go to coordinates X, Y" | `navigation_goto` |
| "Open gripper" | `manipulator_control` |
| "Patrol this area" | `patrol_route` |
| "Return to base" | `return_to_base` |
| "Follow me" | `follow_me` |

## Troubleshooting

### "Model not found"
- Ensure FunctionGemma base model is downloaded in Edge Gallery
- Check internet connection for initial model download

### "API connection failed"
- Verify API key in settings
- Check that `nwo.capital` is accessible
- Try with VPN if behind firewall

### "Function not recognized"
- Speak clearly and use robot IDs from your fleet
- Check that robot is registered in NWO system

## Advanced: Custom Voice Triggers

Edit the schema to add custom wake words:

```json
{
  "voice": {
    "wake_words": ["Hey NWO", "Robot command"],
    "language": "en-US",
    "continuous_listening": false
  }
}
```

## For Developers

To extend this schema with new functions:

1. Add function definition to `functions` array
2. Add training example to `examples` array
3. Update API endpoint mapping in `api.endpoints`
4. Test in Edge Gallery app
5. Submit PR to GitHub repo
