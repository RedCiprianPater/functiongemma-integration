import Foundation
import TensorFlowLite
import Accelerate

/// FunctionGemma Manager for NWO Robotics (iOS)
/// Handles on-device inference for voice-to-function calling
class FunctionGemmaManager {
    
    // MARK: - Constants
    private let modelName = "functiongemma_270m.tflite"
    private let maxTokens = 512
    private let confidenceThreshold = 0.85
    
    // MARK: - Properties
    private var interpreter: Interpreter?
    private let functionSchemas: [String: Any]
    private var commandCache: [String: [String: Any]] = [:]
    
    let availableFunctions = [
        "robot_command", "swarm_deploy", "sensor_activate", "slam_start",
        "navigation_goto", "calibration_run", "emergency_stop", "status_check",
        "manipulator_control", "task_queue_submit", "patrol_route",
        "return_to_base", "follow_me", "voice_interaction"
    ]
    
    // MARK: - Initialization
    init() throws {
        self.functionSchemas = try FunctionGemmaManager.loadFunctionSchemas()
        try initializeInterpreter()
    }
    
    deinit {
        interpreter = nil
    }
    
    // MARK: - Model Setup
    private func initializeInterpreter() throws {
        guard let modelPath = Bundle.main.path(forResource: "functiongemma_270m", ofType: "tflite") else {
            throw FunctionGemmaError.modelNotFound
        }
        
        var options = Interpreter.Options()
        options.threadCount = 4
        
        // Configure delegates
        var delegates: [Delegate] = []
        
        // Try Metal delegate for GPU acceleration
        if let metalDelegate = try? MetalDelegate() {
            delegates.append(metalDelegate)
            print("✓ Metal GPU acceleration enabled")
        } else {
            print("⚠ Metal not available, using CPU")
        }
        
        interpreter = try Interpreter(modelPath: modelPath, options: options, delegates: delegates)
        try interpreter?.allocateTensors()
        
        print("✓ FunctionGemma interpreter initialized")
    }
    
    private static func loadFunctionSchemas() throws -> [String: Any] {
        guard let url = Bundle.main.url(forResource: "nwo_robotics_functions", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw FunctionGemmaError.schemaLoadFailed
        }
        return json
    }
    
    // MARK: - Command Processing
    func processCommand(
        _ command: String,
        context: [String: Any] = [:]
    ) -> FunctionCallResult {
        
        // Check cache
        if let cached = commandCache[command] {
            print("📦 Cache hit for: \(command)")
            return .success(cached, cached: true)
        }
        
        do {
            // Build prompt
            let prompt = buildPrompt(command: command, context: context)
            
            // Tokenize and run inference
            let inputIds = tokenize(prompt)
            let outputIds = try runInference(inputIds: inputIds)
            let response = detokenize(outputIds)
            
            // Parse function calls
            guard let functionCalls = parseFunctionCalls(response),
                  !functionCalls.isEmpty else {
                return .error("No valid function calls generated")
            }
            
            // Validate
            let validatedCalls = validateFunctionCalls(functionCalls)
            let result: [String: Any] = [
                "calls": validatedCalls,
                "confidence": calculateConfidence(validatedCalls),
                "original_command": command
            ]
            
            // Cache if confident
            if let confidence = result["confidence"] as? Double,
               confidence > confidenceThreshold {
                commandCache[command] = result
            }
            
            return .success(result, cached: false)
            
        } catch {
            return .error(error.localizedDescription)
        }
    }
    
    // MARK: - Prompt Building
    private func buildPrompt(command: String, context: [String: Any]) -> String {
        let systemPrompt = loadSystemPrompt()
        let schemaSummary = buildSchemaSummary()
        
        return """
        \(systemPrompt)
        
        Available Functions:
        \(schemaSummary)
        
        User Command: "\(command)"
        
        Respond with JSON function calls:
        {"calls": [{"name": "function_name", "arguments": {...}}]}
        """
    }
    
    private func loadSystemPrompt() -> String {
        guard let url = Bundle.main.url(forResource: "system_prompt", withExtension: "txt"),
              let content = try? String(contentsOf: url) else {
            return "You are a robot control assistant. Convert natural language to function calls."
        }
        return content
    }
    
    private func buildSchemaSummary() -> String {
        guard let functions = functionSchemas["functions"] as? [[String: Any]] else {
            return ""
        }
        
        return functions.compactMap { funcDef -> String? in
            guard let name = funcDef["name"] as? String,
                  let desc = funcDef["description"] as? String else { return nil }
            return "- \(name): \(desc)"
        }.joined(separator: "\n")
    }
    
    // MARK: - Tokenization (Placeholder - integrate SentencePiece)
    private func tokenize(_ text: String) -> [Int32] {
        // TODO: Replace with actual SentencePiece tokenizer
        var tokens: [Int32] = [1] // BOS
        for byte in text.utf8 {
            tokens.append(Int32(byte))
        }
        tokens.append(2) // EOS
        return tokens
    }
    
    private func detokenize(_ tokens: [Int32]) -> String {
        // TODO: Replace with actual SentencePiece detokenizer
        let bytes = tokens.filter { $0 > 2 }.map { UInt8($0) }
        return String(bytes: bytes, encoding: .utf8) ?? ""
    }
    
    // MARK: - Inference
    private func runInference(inputIds: [Int32]) throws -> [Int32] {
        guard let interpreter = interpreter else {
            throw FunctionGemmaError.interpreterNotInitialized
        }
        
        // Prepare input tensor
        let inputShape = interpreter.input(at: 0).shape
        let inputData = Data(bytes: inputIds, count: inputIds.count * MemoryLayout<Int32>.size)
        
        try interpreter.copy(inputData, toInputAt: 0)
        try interpreter.invoke()
        
        // Get output
        let outputTensor = try interpreter.output(at: 0)
        let outputData = outputTensor.data
        
        // Convert to Int32 array
        var outputIds = [Int32](repeating: 0, count: outputData.count / MemoryLayout<Int32>.size)
        outputData.copyBytes(to: &outputIds, count: outputData.count)
        
        return Array(outputIds.prefix(maxTokens))
    }
    
    // MARK: - Parsing & Validation
    private func parseFunctionCalls(_ response: String) -> [[String: Any]]? {
        // Try direct JSON parsing
        if let data = response.data(using: .utf8),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let calls = json["calls"] as? [[String: Any]] {
            return calls
        }
        
        // Try extracting from markdown code blocks
        let pattern = "```json\\s*(.*?)\\s*```"
        guard let regex = try? NSRegularExpression(pattern: pattern, options: .dotMatchesLineSeparators),
              let match = regex.firstMatch(in: response, range: NSRange(response.startIndex..., in: response)) else {
            return nil
        }
        
        if let range = Range(match.range(at: 1), in: response) {
            let jsonStr = String(response[range])
            if let data = jsonStr.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let calls = json["calls"] as? [[String: Any]] {
                return calls
            }
        }
        
        return nil
    }
    
    private func validateFunctionCalls(_ calls: [[String: Any]]) -> [[String: Any]] {
        return calls.compactMap { call -> [String: Any]? in
            guard let funcName = call["name"] as? String,
                  availableFunctions.contains(funcName) else {
                print("⚠ Unknown function: \(call["name"] ?? "nil")")
                return nil
            }
            
            // Find schema
            guard let functions = functionSchemas["functions"] as? [[String: Any]],
                  let schema = functions.first(where: { $0["name"] as? String == funcName }),
                  let params = schema["parameters"] as? [String: Any] else {
                return call
            }
            
            // Validate and fill defaults
            var validatedCall = call
            if var arguments = call["arguments"] as? [String: Any] {
                arguments = fillDefaultValues(arguments: arguments, schema: params)
                validatedCall["arguments"] = arguments
            }
            
            return validatedCall
        }
    }
    
    private func fillDefaultValues(arguments: [String: Any], schema: [String: Any]) -> [String: Any] {
        var result = arguments
        
        guard let properties = schema["properties"] as? [String: [String: Any]] else {
            return result
        }
        
        for (key, prop) in properties {
            if result[key] == nil, let defaultValue = prop["default"] {
                result[key] = defaultValue
            }
        }
        
        return result
    }
    
    private func calculateConfidence(_ calls: [[String: Any]]) -> Double {
        var score = 1.0
        
        // Penalty for many calls
        if calls.count > 3 {
            score -= 0.1 * Double(calls.count - 3)
        }
        
        // Boost for safety commands
        for call in calls {
            if call["name"] as? String == "emergency_stop" {
                score += 0.05
            }
        }
        
        return min(max(score, 0.0), 1.0)
    }
    
    // MARK: - Utilities
    func requiresConfirmation(_ functionName: String) -> Bool {
        return ["emergency_stop", "calibration_run", "swarm_deploy"].contains(functionName)
    }
    
    func clearCache() {
        commandCache.removeAll()
        print("🗑 Cache cleared")
    }
    
    // MARK: - Types
    enum FunctionCallResult {
        case success([String: Any], cached: Bool)
        case error(String)
    }
    
    enum FunctionGemmaError: Error {
        case modelNotFound
        case schemaLoadFailed
        case interpreterNotInitialized
        case inferenceFailed
    }
}
