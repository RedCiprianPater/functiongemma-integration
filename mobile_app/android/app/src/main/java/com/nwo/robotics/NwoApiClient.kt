package com.nwo.robotics

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * NWO Robotics API Client
 * Handles communication with NWO Robotics API endpoints
 */
class NwoApiClient(
    private val context: Context,
    private val baseUrl: String = "https://nwo.capital/webapp/api",
    private val ros2BridgeUrl: String = "https://nwo-ros2-bridge.onrender.com/api/v1",
    private val apiKey: String
) {
    companion object {
        private const val TAG = "NwoApiClient"
        private const val CONNECT_TIMEOUT = 10L
        private const val READ_TIMEOUT = 30L
    }

    private val client = OkHttpClient.Builder()
        .connectTimeout(CONNECT_TIMEOUT, TimeUnit.SECONDS)
        .readTimeout(READ_TIMEOUT, TimeUnit.SECONDS)
        .build()

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    // Offline queue for commands when network is unavailable
    private val offlineQueue = mutableListOf<PendingCommand>()
    private var isOffline = false

    data class PendingCommand(
        val endpoint: String,
        val payload: JSONObject,
        val timestamp: Long,
        val method: String,
        val useRos2: Boolean
    )

    sealed class ApiResult {
        data class Success(val data: JSONObject) : ApiResult()
        data class Error(val message: String) : ApiResult()
        data class Queued(val message: String) : ApiResult()
        data class Offline(val message: String) : ApiResult()
    }

    /**
     * Execute a function call via API
     */
    suspend fun executeFunction(
        name: String,
        arguments: Map<String, Any>
    ): ApiResult = withContext(Dispatchers.IO) {
        val (endpoint, method, useRos2) = endpointForFunction(name)
        val payload = buildPayload(name, arguments)
        val base = if (useRos2) ros2BridgeUrl else baseUrl

        if (isOffline && method == "POST") {
            offlineQueue.add(PendingCommand(endpoint, payload, System.currentTimeMillis(), method, useRos2))
            return@withContext ApiResult.Queued("Command queued for offline execution")
        }

        return@withContext executeRequest(endpoint, payload, method, base)
    }

    /**
     * Execute multiple function calls
     */
    suspend fun executeFunctions(
        calls: List<Pair<String, Map<String, Any>>>
    ): List<ApiResult> = withContext(Dispatchers.IO) {
        val results = mutableListOf<ApiResult>()

        for ((name, arguments) in calls) {
            val result = executeFunction(name, arguments)
            results.add(result)

            // Stop on emergency stop error
            if (result is ApiResult.Error && (name == "emergency_stop" || name == "ros2_emergency_stop")) {
                break
            }
        }

        return@withContext results
    }

    /**
     * Get endpoint for function
     */
    private fun endpointForFunction(name: String): Triple<String, String, Boolean> {
        return when (name) {
            // Core Robot Control
            "robot_command" -> Triple("/api-robotics.php?action=execute", "POST", false)
            "swarm_deploy" -> Triple("/api-robotics.php?action=swarm", "POST", false)
            "sensor_activate" -> Triple("/api-robotics.php?action=sensor_fusion", "POST", false)
            "slam_start" -> Triple("/api-robotics-slam.php", "POST", false)
            "navigation_goto" -> Triple("/api-robotics.php?action=navigate", "POST", false)
            "calibration_run" -> Triple("/api-calibration.php?action=run_calibration", "POST", false)
            "emergency_stop" -> Triple("/api-robotics.php?action=emergency", "POST", false)
            "status_check" -> Triple("/api-robotics.php?action=query_state", "GET", false)
            "manipulator_control" -> Triple("/api-robotics.php?action=manipulate", "POST", false)
            "task_queue_submit" -> Triple("/api-robotics.php?action=task_planner", "POST", false)
            "patrol_route" -> Triple("/api-robotics.php?action=patrol", "POST", false)
            "return_to_base" -> Triple("/api-robotics.php?action=return", "POST", false)
            "follow_me" -> Triple("/api-robotics.php?action=follow", "POST", false)
            "voice_interaction" -> Triple("/api-robotics.php?action=voice", "POST", false)
            
            // Inference & Models
            "inference" -> Triple("/api-robotics.php?action=inference", "POST", false)
            "list_models" -> Triple("/api-robotics.php?action=list_models", "GET", false)
            "get_model_info" -> Triple("/api-robotics.php?action=get_model_info", "GET", false)
            "inference_stream" -> Triple("/api-robotics.php?action=inference_stream&format=sse", "GET", false)
            "streaming_config" -> Triple("/api-robotics.php?action=streaming_config", "GET", false)
            
            // Robot State & Query
            "query_state" -> Triple("/api-robotics.php?action=query_state", "GET", false)
            "get_agent_status" -> Triple("/api-robotics.php?action=get_agent_status", "POST", false)
            "robot_query" -> Triple("/api-robotics.php?action=robot_query", "POST", false)
            
            // Task & Learning System
            "task_planner" -> Triple("/api-robotics.php?action=task_planner", "POST", false)
            "execute_subtask" -> Triple("/api-robotics.php?action=execute_subtask", "POST", false)
            "learning_recommend" -> Triple("/api-robotics.php?action=learning&subaction=recommend", "POST", false)
            "learning_log" -> Triple("/api-robotics.php?action=learning&subaction=log", "POST", false)
            
            // Agent Management
            "register_agent" -> Triple("/api-agent-register.php", "POST", false)
            "update_agent" -> Triple("/api-robotics.php?action=update_agent", "PUT", false)
            "get_agent" -> Triple("/api-robotics.php?action=get_agent", "GET", false)
            "check_agent_balance" -> Triple("/api-agent-balance.php", "GET", false)
            "agent_pay" -> Triple("/api-agent-pay.php", "POST", false)
            
            // Agent Discovery
            "agent_discovery_health" -> Triple("/api-agent-discovery.php?action=health", "GET", false)
            "agent_discovery_whoami" -> Triple("/api-agent-discovery.php?action=whoami", "GET", false)
            "agent_discovery_capabilities" -> Triple("/api-agent-discovery.php?action=capabilities", "GET", false)
            "agent_discovery_dry_run" -> Triple("/api-agent-discovery.php?action=dry-run", "POST", false)
            "agent_discovery_plan" -> Triple("/api-agent-discovery.php?action=plan", "POST", false)
            
            // ROS2 Bridge
            "ros2_submit_action" -> Triple("/action", "POST", true)
            "ros2_list_robots" -> Triple("/robots", "GET", true)
            "ros2_get_robot_status" -> Triple("/robots/{id}/status", "GET", true)
            "ros2_send_command" -> Triple("/robots/{id}/command", "POST", true)
            "ros2_emergency_stop" -> Triple("/robots/{id}/emergency_stop", "POST", true)
            
            // Physics & Simulation
            "simulate_trajectory" -> Triple("/api-simulation.php?action=simulate_trajectory", "POST", false)
            "check_collision" -> Triple("/api-simulation.php?action=check_collision", "POST", false)
            "estimate_torques" -> Triple("/api-simulation.php?action=estimate_torques", "POST", false)
            "validate_grasp" -> Triple("/api-simulation.php?action=validate_grasp", "POST", false)
            "plan_motion" -> Triple("/api-simulation.php?action=plan_motion", "POST", false)
            "get_scene_library" -> Triple("/api-simulation.php?action=get_scene_library", "GET", false)
            "generate_scene" -> Triple("/api-cosmos.php?action=generate_scene", "POST", false)
            
            // Embodiment
            "list_embodiments" -> Triple("/api-embodiment.php?action=list", "GET", false)
            "get_embodiment_detail" -> Triple("/api-embodiment.php?action=detail", "GET", false)
            "get_normalization" -> Triple("/api-embodiment.php?action=normalization", "GET", false)
            "get_urdf" -> Triple("/api-embodiment.php?action=urdf", "GET", false)
            "get_test_results" -> Triple("/api-embodiment.php?action=test_results", "GET", false)
            "compare_robots" -> Triple("/api-embodiment.php?action=compare", "POST", false)
            
            // Calibration
            "calibrate_confidence" -> Triple("/api-calibration.php?action=calibrate", "POST", false)
            "run_calibration" -> Triple("/api-calibration.php?action=run_calibration", "POST", false)
            
            // Tactile Sensing (ORCA)
            "get_tactile" -> Triple("/api-orca.php?action=get_tactile", "POST", false)
            "process_tactile" -> Triple("/api-tactile.php?action=process_input", "POST", false)
            "slip_detection" -> Triple("/api-tactile.php?action=slip_detection", "POST", false)
            
            // Online RL
            "start_online_rl" -> Triple("/api-online-rl.php?action=start_online_rl", "POST", false)
            "submit_telemetry" -> Triple("/api-online-rl.php?action=submit_telemetry", "POST", false)
            
            // Fine-tuning
            "create_dataset" -> Triple("/api-fine-tune.php?action=create_dataset", "POST", false)
            "start_fine_tuning" -> Triple("/api-fine-tune.php?action=start_job", "POST", false)
            
            // Datasets
            "list_datasets" -> Triple("/api-unitree-datasets.php?action=list", "GET", false)
            
            else -> Triple("/api-robotics.php", "POST", false)
        }
    }

    /**
     * Build API payload
     */
    private fun buildPayload(function: String, arguments: Map<String, Any>): JSONObject {
        return JSONObject().apply {
            put("function", function)
            put("arguments", JSONObject(arguments))
            put("timestamp", System.currentTimeMillis())
            put("request_id", generateRequestId())
        }
    }

    /**
     * Generate unique request ID
     */
    private fun generateRequestId(): String {
        return "req_${System.currentTimeMillis()}_${(0..9999).random()}"
    }

    /**
     * Execute HTTP request
     */
    private fun executeRequest(endpoint: String, payload: JSONObject, method: String, baseUrl: String): ApiResult {
        // Replace path parameters
        var finalEndpoint = endpoint
        val args = payload.optJSONObject("arguments")
        args?.optString("robot_id")?.let { id ->
            finalEndpoint = endpoint.replace("{id}", id)
        }
        
        val url = "$baseUrl$finalEndpoint"

        val requestBuilder = Request.Builder()
            .url(url)
            .header("X-API-Key", apiKey)
            .header("X-Request-ID", payload.getString("request_id"))

        when (method) {
            "POST", "PUT" -> {
                requestBuilder.post(payload.toString().toRequestBody(jsonMediaType))
            }
            "GET" -> {
                // Add query params for GET requests
                val urlBuilder = okhttp3.HttpUrl.parse(url)?.newBuilder()
                args?.keys()?.forEach { key ->
                    urlBuilder?.addQueryParameter(key, args.getString(key))
                }
                urlBuilder?.let { requestBuilder.url(it.build()) }
            }
        }

        val request = requestBuilder.build()

        return try {
            client.newCall(request).execute().use { response ->
                when (response.code) {
                    200, 201 -> {
                        val body = response.body?.string()
                        if (body != null && body.isNotEmpty()) {
                            ApiResult.Success(JSONObject(body))
                        } else {
                            ApiResult.Success(JSONObject().apply { put("status", "success") })
                        }
                    }
                    else -> {
                        val errorBody = response.body?.string() ?: "HTTP ${response.code}"
                        ApiResult.Error(errorBody)
                    }
                }
            }
        } catch (e: IOException) {
            // Network error - queue for retry
            isOffline = true
            offlineQueue.add(PendingCommand(endpoint, payload, System.currentTimeMillis(), method, baseUrl == ros2BridgeUrl))
            ApiResult.Offline("Network unavailable: ${e.message}")
        }
    }

    /**
     * Sync offline queue when connectivity returns
     */
    suspend fun syncOfflineQueue(): SyncResult = withContext(Dispatchers.IO) {
        if (offlineQueue.isEmpty()) {
            return@withContext SyncResult.Success(0)
        }

        isOffline = false
        val toSync = offlineQueue.toList()
        offlineQueue.clear()

        var successCount = 0
        var failCount = 0

        for (command in toSync) {
            val base = if (command.useRos2) ros2BridgeUrl else baseUrl
            val result = executeRequest(command.endpoint, command.payload, command.method, base)

            when (result) {
                is ApiResult.Success -> successCount++
                else -> {
                    failCount++
                    offlineQueue.add(command)
                }
            }
        }

        return@withContext if (failCount == 0) {
            SyncResult.Success(successCount)
        } else {
            SyncResult.Partial(successCount, failCount)
        }
    }

    /**
     * Get offline queue size
     */
    fun getOfflineQueueSize(): Int = offlineQueue.size

    /**
     * Clear offline queue
     */
    fun clearOfflineQueue() {
        offlineQueue.clear()
    }

    /**
     * Check connectivity
     */
    suspend fun checkConnectivity(): Boolean = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$baseUrl/api-agent-discovery.php?action=health")
            .header("X-API-Key", apiKey)
            .timeout(5, TimeUnit.SECONDS)
            .build()

        return@withContext try {
            client.newCall(request).execute().use { response ->
                val isConnected = response.code == 200
                isOffline = !isConnected
                isConnected
            }
        } catch (e: IOException) {
            isOffline = true
            false
        }
    }

    /**
     * Connect WebSocket for streaming
     */
    fun connectWebSocket(listener: WebSocketListener): WebSocket {
        val request = Request.Builder()
            .url("wss://nwo.capital/ws/stream")
            .header("X-API-Key", apiKey)
            .build()
        return client.newWebSocket(request, listener)
    }

    /**
     * Connect ROS2 WebSocket
     */
    fun connectRos2WebSocket(robotId: String, listener: WebSocketListener): WebSocket {
        val request = Request.Builder()
            .url("wss://nwo-ros2-bridge.onrender.com/ws/robot/$robotId")
            .build()
        return client.newWebSocket(request, listener)
    }

    sealed class SyncResult {
        data class Success(val count: Int) : SyncResult()
        data class Partial(val success: Int, val failed: Int) : SyncResult()
    }
}
