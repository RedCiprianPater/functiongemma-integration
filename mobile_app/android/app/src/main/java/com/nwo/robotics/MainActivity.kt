package com.nwo.robotics

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import org.json.JSONObject

/**
 * Main Activity for NWO Robotics Controller
 */
class MainActivity : AppCompatActivity() {
    
    companion object {
        private const val PERMISSION_REQUEST_CODE = 100
    }
    
    private lateinit var statusText: TextView
    private lateinit var commandInput: EditText
    private lateinit var sendButton: Button
    private lateinit var voiceButton: Button
    
    private var gemmaManager: FunctionGemmaManager? = null
    private var apiClient: NwoApiClient? = null
    private var voiceProcessor: VoiceCommandProcessor? = null
    private var safetyManager: SafetyManager? = null
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        initializeViews()
        checkPermissions()
        initializeComponents()
        setupListeners()
    }
    
    private fun initializeViews() {
        statusText = findViewById(R.id.statusText)
        commandInput = findViewById(R.id.commandInput)
        sendButton = findViewById(R.id.sendButton)
        voiceButton = findViewById(R.id.voiceButton)
    }
    
    private fun checkPermissions() {
        val permissions = arrayOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.INTERNET
        )
        
        val missingPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        
        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                missingPermissions.toTypedArray(),
                PERMISSION_REQUEST_CODE
            )
        }
    }
    
    private fun initializeComponents() {
        try {
            gemmaManager = FunctionGemmaManager(this)
        } catch (e: Exception) {
            updateStatus("Failed to initialize FunctionGemma: ${e.message}")
        }
        
        apiClient = NwoApiClient(
            context = this,
            apiKey = loadApiKey()
        )
        
        safetyManager = SafetyManager(this)
        
        gemmaManager?.let { gemma ->
            apiClient?.let { api ->
                safetyManager?.let { safety ->
                    voiceProcessor = VoiceCommandProcessor(
                        context = this,
                        gemmaManager = gemma,
                        apiClient = api,
                        safetyManager = safety
                    ).apply {
                        onStateChange = { state ->
                            runOnUiThread {
                                updateStatus("State: ${state.name}")
                            }
                        }
                        
                        onWakeWordDetected = { transcript ->
                            runOnUiThread {
                                updateStatus("Wake word detected: $transcript")
                            }
                        }
                        
                        onFunctionCallsGenerated = { data ->
                            runOnUiThread {
                                updateStatus("Generated calls: ${data.toString().take(100)}...")
                            }
                        }
                        
                        onCommandExecuted = { result ->
                            runOnUiThread {
                                when (result) {
                                    is NwoApiClient.ApiResult.Success -> {
                                        updateStatus("Command executed successfully")
                                    }
                                    is NwoApiClient.ApiResult.Error -> {
                                        updateStatus("Error: ${result.message}")
                                    }
                                    else -> {}
                                }
                            }
                        }
                        
                        onError = { error ->
                            runOnUiThread {
                                updateStatus("Error: $error")
                            }
                        }
                        
                        onSpeak = { text ->
                            runOnUiThread {
                                updateStatus("Speaking: $text")
                            }
                        }
                    }
                }
            }
        }
    }
    
    private fun setupListeners() {
        sendButton.setOnClickListener {
            val command = commandInput.text.toString().trim()
            if (command.isNotEmpty()) {
                voiceProcessor?.processTextCommand(command)
                commandInput.text.clear()
            }
        }
        
        voiceButton.setOnClickListener {
            when (voiceProcessor?.getCurrentState()) {
                VoiceCommandProcessor.State.LISTENING -> {
                    voiceProcessor?.stopListening()
                    voiceButton.text = "🎤"
                }
                else -> {
                    voiceProcessor?.startListening()
                    voiceButton.text = "🔴"
                }
            }
        }
    }
    
    private fun updateStatus(message: String) {
        statusText.text = message
    }
    
    private fun loadApiKey(): String {
        // Load from secure storage in production
        // For demo, return placeholder
        return "your_api_key_here"
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        
        if (requestCode == PERMISSION_REQUEST_CODE) {
            val allGranted = grantResults.all { it == PackageManager.PERMISSION_GRANTED }
            if (!allGranted) {
                updateStatus("Some permissions denied. Voice features may not work.")
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        voiceProcessor?.release()
        gemmaManager?.release()
    }
}
