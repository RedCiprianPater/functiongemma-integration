package com.nwo.robotics

import android.content.Context
import android.util.Log
import com.google.ai.edge.litert.Interpreter
import com.google.ai.edge.litert.GpuDelegate
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import java.io.FileInputStream

/**
 * FunctionGemma Manager for NWO Robotics
 * Handles on-device inference for voice-to-function calling
 */
class FunctionGemmaManager(private val context: Context) {
    
    companion object {
        private const val TAG = "FunctionGemmaManager"
        private const val MODEL_PATH = "functiongemma_270m.tflite"
        private const val MAX_TOKENS = 512
        private const val CONFIDENCE_THRESHOLD = 0.85
    }
    
    private var interpreter: Interpreter? = null
    private var gpuDelegate: GpuDelegate? = null
    private val functionSchemas: JSONObject
    private val commandCache = mutableMapOf<String, JSONObject>()
    
    // Function registry
    private val availableFunctions = listOf(
        "robot_command",
        "swarm_deploy", 
        "sensor_activate",
        "slam_start",
        "navigation_goto",
        "calibration_run",
        "emergency_stop",
        "status_check",
        "manipulator_control",
        "task_queue_submit",
        "patrol_route",
        "return_to_base",
        "follow_me",
        "voice_interaction"
    )
    
    init {
        functionSchemas = loadFunctionSchemas()
        initializeInterpreter()
    }
    
    /**
     * Initialize LiteRT interpreter with GPU acceleration
     */
    private fun initializeInterpreter() {
        try {
            val modelBuffer = loadModelFile()
            
            val options = Interpreter.Options().apply {
                // Try GPU first, fallback to CPU
                try {
                    gpuDelegate = GpuDelegate()
                    addDelegate(gpuDelegate)
                    Log.i(TAG, "GPU acceleration enabled")
                } catch (e: Exception) {
                    Log.w(TAG, "GPU not available, using CPU", e)
                    setNumThreads(4)
                }
                setUseXNNPACK(true)
            }
            
            interpreter = Interpreter(modelBuffer, options)
            Log.i(TAG, "FunctionGemma interpreter initialized")
            
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize interpreter", e)
            throw RuntimeException("Model initialization failed", e)
        }
    }
    
    /**
     * Load TFLite model from assets
     */
    private fun loadModelFile(): MappedByteBuffer {
        val fileDescriptor = context.assets.openFd(MODEL_PATH)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        val startOffset = fileDescriptor.startOffset
        val declaredLength = fileDescriptor.declaredLength
        return fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
    }
    
    /**
     * Load function schemas from JSON
     */
    private fun loadFunctionSchemas(): JSONObject {
        val jsonString = context.assets.open("nwo_robotics_functions.json")
            .bufferedReader()
            .use { it.readText() }
        return JSONObject(jsonString)
    }
    
    /**
     * Process voice/text command and return function calls
     */
    fun processCommand(
        command: String,
        contextData: Map<String, Any> = emptyMap()
    ): FunctionCallResult {
        
        // Check cache first
        commandCache[command]?.let {
            Log.d(TAG, "Cache hit for command: $command")
            return FunctionCallResult.Success(it, cached = true)
        }
        
        try {
            // Build prompt with system instructions and function schemas
            val prompt = buildPrompt(command, contextData)
            
            // Run inference
            val inputIds = tokenize(prompt)
            val outputIds = runInference(inputIds)
            val response = detokenize(outputIds)
            
            // Parse function calls from response
            val functionCalls = parseFunctionCalls(response)
            
            if (functionCalls.isEmpty()) {
                return FunctionCallResult.Error("No valid function calls generated")
            }
            
            // Validate and cache
            val validatedCalls = validateFunctionCalls(functionCalls)
            val result = JSONObject().apply {
                put("calls", validatedCalls)
                put("confidence", calculateConfidence(validatedCalls))
                put("original_command", command)
            }
            
            // Cache successful results
            if (result.getDouble("confidence") > CONFIDENCE_THRESHOLD) {
                commandCache[command] = result
            }
            
            return FunctionCallResult.Success(result, cached = false)
            
        } catch (e: Exception) {
            Log.e(TAG, "Command processing failed", e)
            return FunctionCallResult.Error(e.message ?: "Unknown error")
        }
    }
    
    /**
     * Build prompt with system instructions and schemas
     */
    private fun buildPrompt(command: String, context: Map<String, Any>): String {
        val systemPrompt = context.assets.open("system_prompt.txt")
            .bufferedReader()
            .use { it.readText() }
        
        val schemaSummary = buildSchemaSummary()
        
        return """
            $systemPrompt
            
            Available Functions:
            $schemaSummary
            
            User Command: "$command"
            
            Respond with JSON function calls:
            {"calls": [{"name": "function_name", "arguments": {...}}]}
        """.trimIndent()
    }
    
    /**
     * Build compact schema summary for prompt
     */
    private fun buildSchemaSummary(): String {
        val functions = functionSchemas.getJSONArray("functions")
        val summary = StringBuilder()
        
        for (i in 0 until functions.length()) {
            val func = functions.getJSONObject(i)
            summary.append("- ${func.getString("name")}: ${func.getString("description")}\n")
        }
        
        return summary.toString()
    }
    
    /**
     * Simple tokenization (replace with proper tokenizer)
     */
    private fun tokenize(text: String): IntArray {
        // TODO: Integrate SentencePiece tokenizer
        // Placeholder: convert to byte array and pad
        val tokens = mutableListOf<Int>()
        tokens.add(1) // BOS token
        text.toByteArray().forEach { byte ->
            tokens.add(byte.toInt() and 0xFF)
        }
        tokens.add(2) // EOS token
        return tokens.toIntArray()
    }
    
    /**
     * Run model inference
     */
    private fun runInference(inputIds: IntArray): IntArray {
        val interpreter = this.interpreter ?: throw IllegalStateException("Interpreter not initialized")
        
        // Prepare input/output buffers
        val inputBuffer = Array(1) { inputIds }
        val outputBuffer = Array(1) { IntArray(MAX_TOKENS) }
        
        // Run inference
        interpreter.run(inputBuffer, outputBuffer)
        
        return outputBuffer[0]
    }
    
    /**
     * Simple detokenization (replace with proper tokenizer)
     */
    private fun detokenize(tokenIds: IntArray): String {
        // TODO: Integrate SentencePiece detokenizer
        val bytes = tokenIds.filter { it > 2 }.map { it.toByte() }.toByteArray()
        return String(bytes)
    }
    
    /**
     * Parse JSON function calls from model output
     */
    private fun parseFunctionCalls(response: String): JSONArray {
        return try {
            val json = JSONObject(response)
            json.getJSONArray("calls")
        } catch (e: Exception) {
            // Try to extract JSON from markdown code blocks
            val jsonRegex = "```json\\s*(.*?)\\s*```".toRegex(RegexOption.DOT_MATCHES_ALL)
            val match = jsonRegex.find(response)
            if (match != null) {
                JSONObject(match.groupValues[1]).getJSONArray("calls")
            } else {
                JSONArray()
            }
        }
    }
    
    /**
     * Validate function calls against schemas
     */
    private fun validateFunctionCalls(calls: JSONArray): JSONArray {
        val validated = JSONArray()
        
        for (i in 0 until calls.length()) {
            val call = calls.getJSONObject(i)
            val funcName = call.getString("name")
            
            if (funcName !in availableFunctions) {
                Log.w(TAG, "Unknown function: $funcName")
                continue
            }
            
            // Get schema for this function
            val schema = findFunctionSchema(funcName)
            if (schema == null) {
                Log.w(TAG, "Schema not found for: $funcName")
                continue
            }
            
            // Validate required parameters
            val params = call.getJSONObject("arguments")
            val required = schema.getJSONObject("parameters")
                .optJSONArray("required") ?: JSONArray()
            
            val missing = mutableListOf<String>()
            for (j in 0 until required.length()) {
                val req = required.getString(j)
                if (!params.has(req)) {
                    missing.add(req)
                }
            }
            
            if (missing.isNotEmpty()) {
                Log.w(TAG, "Missing required params for $funcName: $missing")
                // Fill defaults if available
                fillDefaultValues(params, schema.getJSONObject("parameters"))
            }
            
            validated.put(call)
        }
        
        return validated
    }
    
    /**
     * Find function schema by name
     */
    private fun findFunctionSchema(name: String): JSONObject? {
        val functions = functionSchemas.getJSONArray("functions")
        for (i in 0 until functions.length()) {
            val func = functions.getJSONObject(i)
            if (func.getString("name") == name) {
                return func
            }
        }
        return null
    }
    
    /**
     * Fill default values for missing parameters
     */
    private fun fillDefaultValues(params: JSONObject, schema: JSONObject) {
        val properties = schema.optJSONObject("properties") ?: return
        
        properties.keys().forEach { key ->
            if (!params.has(key)) {
                val prop = properties.getJSONObject(key)
                val default = prop.opt("default")
                if (default != null) {
                    params.put(key, default)
                }
            }
        }
    }
    
    /**
     * Calculate confidence score for function calls
     */
    private fun calculateConfidence(calls: JSONArray): Double {
        // Simple heuristic: more calls = lower confidence, validate params
        var score = 1.0
        
        if (calls.length() > 3) {
            score -= 0.1 * (calls.length() - 3)
        }
        
        for (i in 0 until calls.length()) {
            val call = calls.getJSONObject(i)
            if (call.getString("name") == "emergency_stop") {
                score += 0.05 // Boost for safety commands
            }
        }
        
        return score.coerceIn(0.0, 1.0)
    }
    
    /**
     * Check if command requires confirmation
     */
    fun requiresConfirmation(functionName: String): Boolean {
        return functionName in listOf("emergency_stop", "calibration_run", "swarm_deploy")
    }
    
    /**
     * Clear command cache
     */
    fun clearCache() {
        commandCache.clear()
        Log.i(TAG, "Command cache cleared")
    }
    
    /**
     * Release resources
     */
    fun release() {
        interpreter?.close()
        gpuDelegate?.close()
        interpreter = null
        gpuDelegate = null
        Log.i(TAG, "Resources released")
    }
    
    sealed class FunctionCallResult {
        data class Success(val data: JSONObject, val cached: Boolean) : FunctionCallResult()
        data class Error(val message: String) : FunctionCallResult()
    }
}
