import Foundation

/// NWO Robotics API Client (iOS)
/// Handles communication with NWO Robotics API endpoints
class NwoApiClient {
    
    // MARK: - Properties
    private let baseUrl: String
    private let ros2BridgeUrl: String
    private let apiKey: String
    private let session: URLSession
    
    private var offlineQueue: [PendingCommand] = []
    private var isOffline = false
    
    struct PendingCommand {
        let endpoint: String
        let payload: [String: Any]
        let timestamp: Date
        let method: String
    }
    
    enum ApiResult {
        case success([String: Any])
        case error(String)
        case queued(String)
        case offline(String)
    }
    
    enum SyncResult {
        case success(Int)
        case partial(success: Int, failed: Int)
    }
    
    // MARK: - Initialization
    init(baseUrl: String = "https://nwo.capital/webapp/api",
         ros2BridgeUrl: String = "https://nwo-ros2-bridge.onrender.com/api/v1",
         apiKey: String) {
        self.baseUrl = baseUrl
        self.ros2BridgeUrl = ros2BridgeUrl
        self.apiKey = apiKey
        
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 30
        self.session = URLSession(configuration: config)
    }
    
    // MARK: - API Execution
    func executeFunction(
        name: String,
        arguments: [String: Any]
    ) async -> ApiResult {
        
        let (endpoint, method, useRos2) = endpointForFunction(name)
        let payload = buildPayload(function: name, arguments: arguments)
        let base = useRos2 ? ros2BridgeUrl : baseUrl
        
        if isOffline && method == "POST" {
            offlineQueue.append(PendingCommand(
                endpoint: endpoint,
                payload: payload,
                timestamp: Date(),
                method: method
            ))
            return .queued("Command queued for offline execution")
        }
        
        return await executeRequest(endpoint: endpoint, payload: payload, method: method, baseUrl: base)
    }
    
    func executeFunctions(
        calls: [(name: String, arguments: [String: Any])]
    ) async -> [ApiResult] {
        var results: [ApiResult] = []
        
        for call in calls {
            let result = await executeFunction(name: call.name, arguments: call.arguments)
            results.append(result)
            
            // Stop on emergency stop error
            if case .error = result, call.name == "emergency_stop" || call.name == "ros2_emergency_stop" {
                break
            }
        }
        
        return results
    }
    
    // MARK: - Request Building
    private func endpointForFunction(_ name: String) -> (String, String, Bool) {
        switch name {
        // Core Robot Control
        case "robot_command": return ("/api-robotics.php?action=execute", "POST", false)
        case "swarm_deploy": return ("/api-robotics.php?action=swarm", "POST", false)
        case "sensor_activate": return ("/api-robotics.php?action=sensor_fusion", "POST", false)
        case "slam_start": return ("/api-robotics-slam.php", "POST", false)
        case "navigation_goto": return ("/api-robotics.php?action=navigate", "POST", false)
        case "calibration_run": return ("/api-calibration.php?action=run_calibration", "POST", false)
        case "emergency_stop": return ("/api-robotics.php?action=emergency", "POST", false)
        case "status_check": return ("/api-robotics.php?action=query_state", "GET", false)
        case "manipulator_control": return ("/api-robotics.php?action=manipulate", "POST", false)
        case "task_queue_submit": return ("/api-robotics.php?action=task_planner", "POST", false)
        case "patrol_route": return ("/api-robotics.php?action=patrol", "POST", false)
        case "return_to_base": return ("/api-robotics.php?action=return", "POST", false)
        case "follow_me": return ("/api-robotics.php?action=follow", "POST", false)
        case "voice_interaction": return ("/api-robotics.php?action=voice", "POST", false)
        
        // Inference & Models
        case "inference": return ("/api-robotics.php?action=inference", "POST", false)
        case "list_models": return ("/api-robotics.php?action=list_models", "GET", false)
        case "get_model_info": return ("/api-robotics.php?action=get_model_info", "GET", false)
        case "inference_stream": return ("/api-robotics.php?action=inference_stream&format=sse", "GET", false)
        case "streaming_config": return ("/api-robotics.php?action=streaming_config", "GET", false)
        
        // Robot State & Query
        case "query_state": return ("/api-robotics.php?action=query_state", "GET", false)
        case "get_agent_status": return ("/api-robotics.php?action=get_agent_status", "POST", false)
        case "robot_query": return ("/api-robotics.php?action=robot_query", "POST", false)
        
        // Task & Learning System
        case "task_planner": return ("/api-robotics.php?action=task_planner", "POST", false)
        case "execute_subtask": return ("/api-robotics.php?action=execute_subtask", "POST", false)
        case "learning_recommend": return ("/api-robotics.php?action=learning&subaction=recommend", "POST", false)
        case "learning_log": return ("/api-robotics.php?action=learning&subaction=log", "POST", false)
        
        // Agent Management
        case "register_agent": return ("/api-agent-register.php", "POST", false)
        case "update_agent": return ("/api-robotics.php?action=update_agent", "PUT", false)
        case "get_agent": return ("/api-robotics.php?action=get_agent", "GET", false)
        case "check_agent_balance": return ("/api-agent-balance.php", "GET", false)
        case "agent_pay": return ("/api-agent-pay.php", "POST", false)
        
        // Agent Discovery
        case "agent_discovery_health": return ("/api-agent-discovery.php?action=health", "GET", false)
        case "agent_discovery_whoami": return ("/api-agent-discovery.php?action=whoami", "GET", false)
        case "agent_discovery_capabilities": return ("/api-agent-discovery.php?action=capabilities", "GET", false)
        case "agent_discovery_dry_run": return ("/api-agent-discovery.php?action=dry-run", "POST", false)
        case "agent_discovery_plan": return ("/api-agent-discovery.php?action=plan", "POST", false)
        
        // ROS2 Bridge
        case "ros2_submit_action": return ("/action", "POST", true)
        case "ros2_list_robots": return ("/robots", "GET", true)
        case "ros2_get_robot_status": return ("/robots/{id}/status", "GET", true)
        case "ros2_send_command": return ("/robots/{id}/command", "POST", true)
        case "ros2_emergency_stop": return ("/robots/{id}/emergency_stop", "POST", true)
        
        // Physics & Simulation
        case "simulate_trajectory": return ("/api-simulation.php?action=simulate_trajectory", "POST", false)
        case "check_collision": return ("/api-simulation.php?action=check_collision", "POST", false)
        case "estimate_torques": return ("/api-simulation.php?action=estimate_torques", "POST", false)
        case "validate_grasp": return ("/api-simulation.php?action=validate_grasp", "POST", false)
        case "plan_motion": return ("/api-simulation.php?action=plan_motion", "POST", false)
        case "get_scene_library": return ("/api-simulation.php?action=get_scene_library", "GET", false)
        case "generate_scene": return ("/api-cosmos.php?action=generate_scene", "POST", false)
        
        // Embodiment
        case "list_embodiments": return ("/api-embodiment.php?action=list", "GET", false)
        case "get_embodiment_detail": return ("/api-embodiment.php?action=detail", "GET", false)
        case "get_normalization": return ("/api-embodiment.php?action=normalization", "GET", false)
        case "get_urdf": return ("/api-embodiment.php?action=urdf", "GET", false)
        case "get_test_results": return ("/api-embodiment.php?action=test_results", "GET", false)
        case "compare_robots": return ("/api-embodiment.php?action=compare", "POST", false)
        
        // Calibration
        case "calibrate_confidence": return ("/api-calibration.php?action=calibrate", "POST", false)
        case "run_calibration": return ("/api-calibration.php?action=run_calibration", "POST", false)
        
        // Tactile Sensing (ORCA)
        case "get_tactile": return ("/api-orca.php?action=get_tactile", "POST", false)
        case "process_tactile": return ("/api-tactile.php?action=process_input", "POST", false)
        case "slip_detection": return ("/api-tactile.php?action=slip_detection", "POST", false)
        
        // Online RL
        case "start_online_rl": return ("/api-online-rl.php?action=start_online_rl", "POST", false)
        case "submit_telemetry": return ("/api-online-rl.php?action=submit_telemetry", "POST", false)
        
        // Fine-tuning
        case "create_dataset": return ("/api-fine-tune.php?action=create_dataset", "POST", false)
        case "start_fine_tuning": return ("/api-fine-tune.php?action=start_job", "POST", false)
        
        // Datasets
        case "list_datasets": return ("/api-unitree-datasets.php?action=list", "GET", false)
        
        default: return ("/api-robotics.php", "POST", false)
        }
    }
    
    private func buildPayload(function: String, arguments: [String: Any]) -> [String: Any] {
        return [
            "function": function,
            "arguments": arguments,
            "timestamp": Int(Date().timeIntervalSince1970 * 1000),
            "request_id": generateRequestId()
        ]
    }
    
    private func generateRequestId() -> String {
        return "req_\(Int(Date().timeIntervalSince1970))_\(Int.random(in: 0...9999))"
    }
    
    // MARK: - Network Request
    private func executeRequest(
        endpoint: String,
        payload: [String: Any],
        method: String,
        baseUrl: String
    ) async -> ApiResult {
        
        // Replace path parameters
        var finalEndpoint = endpoint
        if let robotId = payload["arguments"] as? [String: Any],
           let id = robotId["robot_id"] as? String {
            finalEndpoint = endpoint.replacingOccurrences(of: "{id}", with: id)
        }
        
        guard let url = URL(string: baseUrl + finalEndpoint) else {
            return .error("Invalid URL")
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        request.setValue(payload["request_id"] as? String, forHTTPHeaderField: "X-Request-ID")
        
        do {
            if method == "POST" || method == "PUT" {
                request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            }
        } catch {
            return .error("Failed to encode payload: \(error.localizedDescription)")
        }
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                return .error("Invalid response")
            }
            
            if httpResponse.statusCode == 200 || httpResponse.statusCode == 201 {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    return .success(json)
                } else {
                    // For empty responses
                    return .success(["status": "success"])
                }
            } else {
                let message = String(data: data, encoding: .utf8) ?? "HTTP \(httpResponse.statusCode)"
                return .error(message)
            }
            
        } catch {
            // Network error - queue for retry
            if isNetworkError(error) {
                isOffline = true
                offlineQueue.append(PendingCommand(
                    endpoint: endpoint,
                    payload: payload,
                    timestamp: Date(),
                    method: method
                ))
                return .offline("Network unavailable, command queued")
            }
            
            return .error(error.localizedDescription)
        }
    }
    
    private func isNetworkError(_ error: Error) -> Bool {
        let nsError = error as NSError
        return nsError.domain == NSURLErrorDomain &&
               [NSURLErrorNotConnectedToInternet,
                NSURLErrorTimedOut,
                NSURLErrorCannotConnectToHost].contains(nsError.code)
    }
    
    // MARK: - Offline Queue
    func syncOfflineQueue() async -> SyncResult {
        guard !offlineQueue.isEmpty else {
            return .success(0)
        }
        
        isOffline = false
        let toSync = offlineQueue
        offlineQueue.removeAll()
        
        var successCount = 0
        var failCount = 0
        
        for command in toSync {
            let base = command.endpoint.contains("/robots") ? ros2BridgeUrl : baseUrl
            let result = await executeRequest(endpoint: command.endpoint, payload: command.payload, method: command.method, baseUrl: base)
            
            switch result {
            case .success:
                successCount += 1
            default:
                failCount += 1
                offlineQueue.append(command)
            }
        }
        
        return failCount == 0 ? .success(successCount) : .partial(success: successCount, failed: failCount)
    }
    
    func getOfflineQueueSize() -> Int {
        return offlineQueue.count
    }
    
    func clearOfflineQueue() {
        offlineQueue.removeAll()
    }
    
    // MARK: - Connectivity
    func checkConnectivity() async -> Bool {
        guard let url = URL(string: baseUrl + "/api-agent-discovery.php?action=health") else {
            return false
        }
        
        var request = URLRequest(url: url)
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        request.timeoutInterval = 5
        
        do {
            let (_, response) = try await session.data(for: request)
            let httpResponse = response as? HTTPURLResponse
            let isConnected = httpResponse?.statusCode == 200
            isOffline = !isConnected
            return isConnected
        } catch {
            isOffline = true
            return false
        }
    }
    
    // MARK: - WebSocket
    func connectWebSocket(robotId: String) -> URLSessionWebSocketTask? {
        let wsUrl = "wss://nwo.capital/ws/stream"
        guard let url = URL(string: wsUrl) else { return nil }
        
        var request = URLRequest(url: url)
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        
        let task = session.webSocketTask(with: request)
        task.resume()
        return task
    }
    
    func connectRos2WebSocket(robotId: String) -> URLSessionWebSocketTask? {
        let wsUrl = "wss://nwo-ros2-bridge.onrender.com/ws/robot/\(robotId)"
        guard let url = URL(string: wsUrl) else { return nil }
        
        let task = session.webSocketTask(with: url)
        task.resume()
        return task
    }
}
