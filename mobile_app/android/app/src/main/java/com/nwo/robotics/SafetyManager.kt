package com.nwo.robotics

import android.app.AlertDialog
import android.content.Context
import androidx.core.content.ContextCompat
import org.json.JSONObject

/**
 * Safety Manager for NWO Robotics
 * Handles emergency protocols, confirmation dialogs, and safety checks
 */
class SafetyManager(private val context: Context) {

    companion object {
        private const val TAG = "SafetyManager"
        
        // Functions requiring confirmation
        val CONFIRMATION_REQUIRED_FUNCTIONS = listOf(
            "emergency_stop",
            "calibration_run",
            "swarm_deploy"
        )
        
        // High-risk operations
        val HIGH_RISK_OPERATIONS = listOf(
            "manipulator_control",
            "navigation_goto"
        )
    }

    private var emergencyStopActive = false
    private val safetyEventListeners = mutableListOf<SafetyEventListener>()

    interface SafetyEventListener {
        fun onEmergencyStopTriggered(reason: String)
        fun onEmergencyStopReset()
        fun onBatteryWarning(level: Double)
        fun onSuggestionReturnToBase(reason: String)
    }

    /**
     * Check if function requires confirmation
     */
    fun requiresConfirmation(functionName: String): Boolean {
        return CONFIRMATION_REQUIRED_FUNCTIONS.contains(functionName)
    }

    /**
     * Check if operation is high-risk
     */
    fun isHighRisk(functionName: String): Boolean {
        return HIGH_RISK_OPERATIONS.contains(functionName)
    }

    /**
     * Show confirmation dialog
     */
    fun showConfirmation(
        function: String,
        arguments: Map<String, Any>,
        onConfirm: () -> Unit,
        onCancel: (() -> Unit)? = null
    ) {
        val title = "Confirm ${function.replace("_", " ").capitalize()}"
        val message = buildConfirmationMessage(function, arguments)

        AlertDialog.Builder(context)
            .setTitle(title)
            .setMessage(message)
            .setNegativeButton("Cancel") { _, _ -> onCancel?.invoke() }
            .setPositiveButton("Confirm") { _, _ -> onConfirm() }
            .setCancelable(false)
            .show()
    }

    /**
     * Trigger emergency stop
     */
    fun triggerEmergencyStop(reason: String) {
        emergencyStopActive = true
        safetyEventListeners.forEach { it.onEmergencyStopTriggered(reason) }
        logSafetyEvent("emergency_stop", reason)
    }

    /**
     * Reset emergency stop
     */
    fun resetEmergencyStop() {
        emergencyStopActive = false
        safetyEventListeners.forEach { it.onEmergencyStopReset() }
    }

    /**
     * Check if emergency stop is active
     */
    fun isEmergencyStopActive(): Boolean = emergencyStopActive

    /**
     * Validate command for safety
     */
    fun validateCommand(function: String, arguments: Map<String, Any>): SafetyValidation {
        // Check emergency stop
        if (emergencyStopActive && function != "emergency_stop") {
            return SafetyValidation.Blocked("Emergency stop is active")
        }

        // Check for dangerous parameters
        val speed = arguments["speed"] as? Double
        if (speed != null && speed > 5.0) {
            return SafetyValidation.Warning("High speed detected (${speed} m/s)")
        }

        // Check for invalid coordinates
        val destination = arguments["destination"] as? Map<*, *>
        if (destination != null) {
            val x = destination["x"] as? Double
            val y = destination["y"] as? Double
            
            if (x != null && kotlin.math.abs(x) > 1000) {
                return SafetyValidation.Blocked("Coordinates out of safe range")
            }
            if (y != null && kotlin.math.abs(y) > 1000) {
                return SafetyValidation.Blocked("Coordinates out of safe range")
            }
        }

        return SafetyValidation.Safe
    }

    /**
     * Add safety event listener
     */
    fun addSafetyEventListener(listener: SafetyEventListener) {
        safetyEventListeners.add(listener)
    }

    /**
     * Remove safety event listener
     */
    fun removeSafetyEventListener(listener: SafetyEventListener) {
        safetyEventListeners.remove(listener)
    }

    /**
     * Handle battery warning
     */
    fun handleBatteryWarning(level: Double) {
        safetyEventListeners.forEach { it.onBatteryWarning(level) }
        
        if (level < 10) {
            safetyEventListeners.forEach { 
                it.onSuggestionReturnToBase("Critical battery level: ${level.toInt()}%") 
            }
        }
    }

    /**
     * Log safety event
     */
    fun logSafetyEvent(type: String, details: String) {
        val timestamp = java.text.SimpleDateFormat(
            "yyyy-MM-dd'T'HH:mm:ss'Z'",
            java.util.Locale.getDefault()
        ).format(java.util.Date())
        
        android.util.Log.i(TAG, "[$timestamp] ${type.uppercase()}: $details")
        
        // In production, send to logging service
    }

    /**
     * Get safety status
     */
    fun getSafetyStatus(): Map<String, Any> {
        return mapOf(
            "emergency_stop_active" to emergencyStopActive,
            "confirmation_required_functions" to CONFIRMATION_REQUIRED_FUNCTIONS,
            "high_risk_operations" to HIGH_RISK_OPERATIONS,
            "timestamp" to System.currentTimeMillis()
        )
    }

    /**
     * Build confirmation message
     */
    private fun buildConfirmationMessage(function: String, arguments: Map<String, Any>): String {
        val builder = StringBuilder()
        builder.append("Are you sure you want to execute '${function.replace("_", " ")}'?\n\n")

        arguments["robot_id"]?.let {
            builder.append("Robot: $it\n")
        }

        arguments["instruction"]?.let {
            builder.append("Instruction: $it\n")
        }

        if (function == "emergency_stop") {
            return "⚠️ EMERGENCY STOP\n\nThis will immediately halt all robot motion. Continue?"
        }

        return builder.toString()
    }
}

/**
 * Safety validation result
 */
sealed class SafetyValidation {
    object Safe : SafetyValidation()
    data class Warning(val message: String) : SafetyValidation()
    data class Blocked(val reason: String) : SafetyValidation()

    val isSafe: Boolean
        get() = this is Safe

    val canProceed: Boolean
        get() = this is Safe || this is Warning
}
