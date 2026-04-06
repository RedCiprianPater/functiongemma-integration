package com.nwo.robotics

import android.content.Context
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.util.Locale

/**
 * Voice Command Processor for Android
 * Handles voice-to-text, wake word detection, and command execution
 */
class VoiceCommandProcessor(
    private val context: Context,
    private val gemmaManager: FunctionGemmaManager,
    private val apiClient: NwoApiClient,
    private val safetyManager: SafetyManager
) {
    companion object {
        private const val TAG = "VoiceCommandProcessor"
        private const val WAKE_WORD = "hey nwo"
        private const val SAMPLE_RATE = 16000
    }

    // Speech recognition
    private var speechRecognizer: SpeechRecognizer? = null
    private var textToSpeech: TextToSpeech? = null
    private var isListening = false
    private var commandBuffer = StringBuilder()

    // State
    private var currentState: State = State.IDLE
    private val mainHandler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(Dispatchers.Main)

    // Callbacks
    var onStateChange: ((State) -> Unit)? = null
    var onWakeWordDetected: ((String) -> Unit)? = null
    var onFunctionCallsGenerated: ((JSONObject) -> Unit)? = null
    var onCommandExecuted: ((NwoApiClient.ApiResult) -> Unit)? = null
    var onError: ((String) -> Unit)? = null
    var onSpeak: ((String) -> Unit)? = null

    enum class State {
        IDLE,
        LISTENING,
        PROCESSING,
        EXECUTING,
        SPEAKING
    }

    init {
        initializeSpeechRecognizer()
        initializeTextToSpeech()
    }

    /**
     * Initialize speech recognizer
     */
    private fun initializeSpeechRecognizer() {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            Log.e(TAG, "Speech recognition not available")
            return
        }

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context).apply {
            setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: android.os.Bundle?) {
                    Log.d(TAG, "Ready for speech")
                }

                override fun onBeginningOfSpeech() {
                    Log.d(TAG, "Beginning of speech")
                }

                override fun onRmsChanged(rmsdB: Float) {
                    // Audio level changed
                }

                override fun onBufferReceived(buffer: ByteArray?) {
                    // Audio buffer received
                }

                override fun onEndOfSpeech() {
                    Log.d(TAG, "End of speech")
                }

                override fun onError(error: Int) {
                    val errorMsg = when (error) {
                        SpeechRecognizer.ERROR_AUDIO -> "Audio error"
                        SpeechRecognizer.ERROR_CLIENT -> "Client error"
                        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Permissions denied"
                        SpeechRecognizer.ERROR_NETWORK -> "Network error"
                        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
                        SpeechRecognizer.ERROR_NO_MATCH -> "No speech match"
                        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognizer busy"
                        SpeechRecognizer.ERROR_SERVER -> "Server error"
                        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Speech timeout"
                        else -> "Unknown error: $error"
                    }
                    Log.e(TAG, "Speech recognition error: $errorMsg")
                    onError?.invoke(errorMsg)
                    setState(State.IDLE)
                }

                override fun onResults(results: android.os.Bundle?) {
                    val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if (!matches.isNullOrEmpty()) {
                        val transcript = matches[0]
                        processCommand(transcript)
                    }
                }

                override fun onPartialResults(partialResults: android.os.Bundle?) {
                    val partial = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if (!partial.isNullOrEmpty()) {
                        val transcript = partial[0]
                        
                        // Check for wake word
                        if (currentState == State.IDLE && 
                            transcript.lowercase().contains(WAKE_WORD)) {
                            onWakeWordDetected?.invoke(transcript)
                            setState(State.LISTENING)
                        }
                    }
                }

                override fun onEvent(eventType: Int, params: android.os.Bundle?) {
                    // Event received
                }
            })
        }
    }

    /**
     * Initialize text-to-speech
     */
    private fun initializeTextToSpeech() {
        textToSpeech = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                textToSpeech?.language = Locale.US
                Log.i(TAG, "Text-to-speech initialized")
            } else {
                Log.e(TAG, "Failed to initialize text-to-speech")
            }
        }
    }

    /**
     * Start listening for voice commands
     */
    fun startListening() {
        if (isListening) return

        val intent = android.speech.RecognizerIntent().apply {
            action = android.speech.RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE_MODEL, 
                     android.speech.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
            putExtra(android.speech.RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(android.speech.RecognizerIntent.EXTRA_MAX_RESULTS, 3)
        }

        speechRecognizer?.startListening(intent)
        isListening = true
        setState(State.LISTENING)
    }

    /**
     * Stop listening
     */
    fun stopListening() {
        speechRecognizer?.stopListening()
        isListening = false
        setState(State.IDLE)
    }

    /**
     * Process text command
     */
    fun processTextCommand(command: String) {
        setState(State.PROCESSING)

        scope.launch {
            // Process with FunctionGemma
            val result = gemmaManager.processCommand(command)

            when (result) {
                is FunctionGemmaManager.FunctionCallResult.Success -> {
                    onFunctionCallsGenerated?.invoke(result.data)
                    executeFunctionCalls(result.data)
                }
                is FunctionGemmaManager.FunctionCallResult.Error -> {
                    onError?.invoke(result.message)
                    speak("Sorry, I didn't understand that command")
                    setState(State.IDLE)
                }
            }
        }
    }

    /**
     * Process voice command (with wake word removal)
     */
    private fun processCommand(command: String) {
        // Remove wake word
        var cleanCommand = command.lowercase()
        val wakeIndex = cleanCommand.indexOf(WAKE_WORD)
        if (wakeIndex != -1) {
            cleanCommand = cleanCommand.removeRange(wakeIndex, wakeIndex + WAKE_WORD.length)
        }
        cleanCommand = cleanCommand.trim()

        if (cleanCommand.isEmpty()) {
            setState(State.IDLE)
            return
        }

        processTextCommand(cleanCommand)
    }

    /**
     * Execute function calls
     */
    private suspend fun executeFunctionCalls(data: JSONObject) {
        setState(State.EXECUTING)

        val callsArray = data.optJSONArray("calls") ?: run {
            speak("No actions to perform")
            setState(State.IDLE)
            return
        }

        val apiCalls = mutableListOf<Pair<String, Map<String, Any>>>()

        for (i in 0 until callsArray.length()) {
            val call = callsArray.getJSONObject(i)
            val name = call.optString("name")
            val arguments = call.optJSONObject("arguments")

            if (name.isNotEmpty() && arguments != null) {
                // Check for confirmation
                if (gemmaManager.requiresConfirmation(name)) {
                    // In production, show confirmation dialog
                    // For now, proceed with caution
                    Log.w(TAG, "Function requires confirmation: $name")
                }

                val argsMap = mutableMapOf<String, Any>()
                arguments.keys().forEach { key ->
                    argsMap[key] = arguments.get(key)
                }

                apiCalls.add(name to argsMap)
            }
        }

        // Execute API calls
        val results = apiClient.executeFunctions(apiCalls)

        results.forEach { result ->
            onCommandExecuted?.invoke(result)
        }

        // Generate response
        val response = generateResponse(results)
        speak(response)
    }

    /**
     * Generate response from results
     */
    private fun generateResponse(results: List<NwoApiClient.ApiResult>): String {
        val successCount = results.count { it is NwoApiClient.ApiResult.Success }
        val errorCount = results.size - successCount

        return when {
            errorCount == 0 -> "Command executed successfully"
            successCount == 0 -> "Command failed. Please try again."
            else -> "Command partially completed with $errorCount errors"
        }
    }

    /**
     * Speak text
     */
    private fun speak(text: String) {
        setState(State.SPEAKING)
        onSpeak?.invoke(text)

        textToSpeech?.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)

        // Return to idle after speech
        mainHandler.postDelayed({
            setState(State.IDLE)
        }, 2000)
    }

    /**
     * Set state and notify
     */
    private fun setState(state: State) {
        currentState = state
        mainHandler.post {
            onStateChange?.invoke(state)
        }
    }

    /**
     * Get current state
     */
    fun getCurrentState(): State = currentState

    /**
     * Release resources
     */
    fun release() {
        stopListening()
        speechRecognizer?.destroy()
        speechRecognizer = null

        textToSpeech?.stop()
        textToSpeech?.shutdown()
        textToSpeech = null
    }
}
