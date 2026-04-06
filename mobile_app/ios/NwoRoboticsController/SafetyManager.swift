import Foundation
import UIKit

/// Safety Manager for NWO Robotics
/// Handles emergency protocols, confirmation dialogs, and safety checks
class SafetyManager {
    
    // MARK: - Properties
    
    private var emergencyStopActive = false
    private var confirmationCallbacks: [String: () -> Void] = [:]
    
    // Functions requiring confirmation
    let confirmationRequiredFunctions = [
        "emergency_stop",
        "calibration_run",
        "swarm_deploy"
    ]
    
    // High-risk operations
    let highRiskOperations = [
        "manipulator_control",
        "navigation_goto"
    ]
    
    // MARK: - Initialization
    
    init() {
        setupNotifications()
    }
    
    // MARK: - Public Methods
    
    /// Check if a function requires confirmation
    func requiresConfirmation(functionName: String) -> Bool {
        return confirmationRequiredFunctions.contains(functionName)
    }
    
    /// Check if operation is high-risk
    func isHighRisk(functionName: String) -> Bool {
        return highRiskOperations.contains(functionName)
    }
    
    /// Show confirmation dialog
    func showConfirmation(
        for function: String,
        arguments: [String: Any],
        onConfirm: @escaping () -> Void,
        onCancel: (() -> Void)? = nil
    ) {
        let title = "Confirm \(function)"
        let message = buildConfirmationMessage(function: function, arguments: arguments)
        
        let alert = UIAlertController(
            title: title,
            message: message,
            preferredStyle: .alert
        )
        
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in
            onCancel?()
        })
        
        alert.addAction(UIAlertAction(title: "Confirm", style: .destructive) { _ in
            onConfirm()
        })
        
        // Present on top view controller
        if let topVC = getTopViewController() {
            topVC.present(alert, animated: true)
        }
    }
    
    /// Trigger emergency stop
    func triggerEmergencyStop(reason: String) {
        emergencyStopActive = true
        
        // Post notification
        NotificationCenter.default.post(
            name: .emergencyStopTriggered,
            object: nil,
            userInfo: ["reason": reason]
        )
        
        // Log event
        logSafetyEvent(type: "emergency_stop", details: reason)
    }
    
    /// Reset emergency stop
    func resetEmergencyStop() {
        emergencyStopActive = false
        
        NotificationCenter.default.post(
            name: .emergencyStopReset,
            object: nil
        )
    }
    
    /// Check if emergency stop is active
    func isEmergencyStopActive() -> Bool {
        return emergencyStopActive
    }
    
    /// Validate command for safety
    func validateCommand(function: String, arguments: [String: Any]) -> SafetyValidation {
        // Check emergency stop
        if emergencyStopActive && function != "emergency_stop" {
            return .blocked(reason: "Emergency stop is active")
        }
        
        // Check for dangerous parameters
        if let speed = arguments["speed"] as? Double, speed > 5.0 {
            return .warning(message: "High speed detected (\(speed) m/s)")
        }
        
        // Check for invalid coordinates
        if let destination = arguments["destination"] as? [String: Any] {
            if let x = destination["x"] as? Double, abs(x) > 1000 {
                return .blocked(reason: "Coordinates out of safe range")
            }
            if let y = destination["y"] as? Double, abs(y) > 1000 {
                return .blocked(reason: "Coordinates out of safe range")
            }
        }
        
        return .safe
    }
    
    /// Log safety event
    func logSafetyEvent(type: String, details: String) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let logEntry = "[\(timestamp)] \(type.uppercased()): \(details)"
        print(logEntry)
        
        // In production, send to logging service
        // Logger.shared.logSafetyEvent(type: type, details: details)
    }
    
    /// Get safety status report
    func getSafetyStatus() -> [String: Any] {
        return [
            "emergency_stop_active": emergencyStopActive,
            "confirmation_required_functions": confirmationRequiredFunctions,
            "high_risk_operations": highRiskOperations,
            "timestamp": ISO8601DateFormatter().string(from: Date())
        ]
    }
    
    // MARK: - Private Methods
    
    private func setupNotifications() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleBatteryWarning),
            name: .batteryWarning,
            object: nil
        )
    }
    
    @objc private func handleBatteryWarning(_ notification: Notification) {
        guard let level = notification.userInfo?["level"] as? Double else { return }
        
        if level < 10 {
            // Critical battery - suggest return to base
            NotificationCenter.default.post(
                name: .suggestionReturnToBase,
                object: nil,
                userInfo: ["reason": "Critical battery level: \(level)%"]
            )
        }
    }
    
    private func buildConfirmationMessage(function: String, arguments: [String: Any]) -> String {
        var message = "Are you sure you want to execute '\(function)'?"
        
        if let robotId = arguments["robot_id"] as? String {
            message += "\n\nRobot: \(robotId)"
        }
        
        if let instruction = arguments["instruction"] as? String {
            message += "\nInstruction: \(instruction)"
        }
        
        if function == "emergency_stop" {
            message = "⚠️ EMERGENCY STOP\n\nThis will immediately halt all robot motion. Continue?"
        }
        
        return message
    }
    
    private func getTopViewController() -> UIViewController? {
        guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let window = windowScene.windows.first else {
            return nil
        }
        
        var topController = window.rootViewController
        while let presented = topController?.presentedViewController {
            topController = presented
        }
        
        return topController
    }
}

// MARK: - Safety Validation Enum

enum SafetyValidation {
    case safe
    case warning(message: String)
    case blocked(reason: String)
    
    var isSafe: Bool {
        switch self {
        case .safe:
            return true
        case .warning, .blocked:
            return false
        }
    }
    
    var canProceed: Bool {
        switch self {
        case .safe, .warning:
            return true
        case .blocked:
            return false
        }
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let emergencyStopTriggered = Notification.Name("emergencyStopTriggered")
    static let emergencyStopReset = Notification.Name("emergencyStopReset")
    static let batteryWarning = Notification.Name("batteryWarning")
    static let suggestionReturnToBase = Notification.Name("suggestionReturnToBase")
}
