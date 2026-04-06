import Foundation
import Speech
import AVFoundation

/// Voice Command Processor (iOS)
/// Handles voice-to-text, wake word detection, and command execution
class VoiceCommandProcessor: NSObject {
    
    // MARK: - Properties
    private let gemmaManager: FunctionGemmaManager
    private let apiClient: NwoApiClient
    
    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    private var isListening = false
    private var commandBuffer = ""
    
    weak var delegate: VoiceCommandProcessorDelegate?
    
    enum State {
        case idle
        case listening
        case processing
        case executing
        case speaking
    }
    
    private(set) var currentState: State = .idle {
        didSet {
            DispatchQueue.main.async {
                self.delegate?.voiceProcessor(self, didChangeState: self.currentState)
            }
        }
    }
    
    // MARK: - Initialization
    init(gemmaManager: FunctionGemmaManager, apiClient: NwoApiClient) {
        self.gemmaManager = gemmaManager
        self.apiClient = apiClient
        super.init()
        
        setupSpeechRecognizer()
    }
    
    // MARK: - Setup
    private func setupSpeechRecognizer() {
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        speechRecognizer?.delegate = self
    }
    
    // MARK: - Permissions
    func requestPermissions() async -> Bool {
        // Request speech recognition permission
        await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
        
        // Request microphone permission
        await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
        
        return true
    }
    
    // MARK: - Voice Control
    func startListening() {
        guard !isListening else { return }
        
        do {
            try startRecording()
            isListening = true
            currentState = .listening
        } catch {
            delegate?.voiceProcessor(self, didEncounterError: error.localizedDescription)
        }
    }
    
    func stopListening() {
        audioEngine.stop()
        recognitionRequest?.endAudio()
        audioEngine.inputNode.removeTap(onBus: 0)
        
        isListening = false
        currentState = .idle
    }
    
    // MARK: - Recording
    private func startRecording() throws {
        // Cancel any existing task
        recognitionTask?.cancel()
        recognitionTask = nil
        
        // Configure audio session
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        
        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            throw VoiceProcessorError.recognitionRequestFailed
        }
        
        recognitionRequest.shouldReportPartialResults = true
        recognitionRequest.requiresOnDeviceRecognition = true // Keep on-device
        
        // Start recognition
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self = self else { return }
            
            if let result = result {
                let transcript = result.bestTranscription.formattedString
                self.commandBuffer = transcript
                
                // Check for wake word
                if self.currentState == .idle && transcript.lowercased().contains("hey nwo") {
                    self.delegate?.voiceProcessor(self, didDetectWakeWord: transcript)
                    self.currentState = .listening
                }
                
                // Process final result
                if result.isFinal {
                    self.processCommand(transcript)
                }
            }
            
            if error != nil {
                self.stopListening()
            }
        }
        
        // Configure audio engine
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            self.recognitionRequest?.append(buffer)
        }
        
        audioEngine.prepare()
        try audioEngine.start()
    }
    
    // MARK: - Command Processing
    func processTextCommand(_ command: String) {
        currentState = .processing
        
        Task {
            let result = gemmaManager.processCommand(command)
            
            switch result {
            case .success(let data, _):
                await MainActor.run {
                    self.delegate?.voiceProcessor(self, didGenerateFunctionCalls: data)
                }
                await executeFunctionCalls(data)
                
            case .error(let message):
                await MainActor.run {
                    self.delegate?.voiceProcessor(self, didEncounterError: message)
                    self.speak("Sorry, I didn't understand that command")
                    self.currentState = .idle
                }
            }
        }
    }
    
    private func processCommand(_ command: String) {
        // Remove wake word
        var cleanCommand = command.lowercased()
        if let range = cleanCommand.range(of: "hey nwo") {
            cleanCommand.removeSubrange(range)
        }
        cleanCommand = cleanCommand.trimmingCharacters(in: .whitespacesAndNewlines)
        
        guard !cleanCommand.isEmpty else {
            currentState = .idle
            return
        }
        
        processTextCommand(cleanCommand)
    }
    
    // MARK: - Execution
    private func executeFunctionCalls(_ data: [String: Any]) async {
        currentState = .executing
        
        guard let calls = data["calls"] as? [[String: Any]] else {
            speak("No actions to perform")
            currentState = .idle
            return
        }
        
        var apiCalls: [(name: String, arguments: [String: Any])] = []
        
        for call in calls {
            guard let name = call["name"] as? String,
                  let arguments = call["arguments"] as? [String: Any] else {
                continue
            }
            
            // Check for confirmation
            if gemmaManager.requiresConfirmation(name) {
                // TODO: Show confirmation UI
            }
            
            apiCalls.append((name: name, arguments: arguments))
        }
        
        let results = await apiClient.executeFunctions(calls: apiCalls)
        
        await MainActor.run {
            for result in results {
                self.delegate?.voiceProcessor(self, didExecuteCommand: result)
            }
            
            let response = self.generateResponse(from: results)
            self.speak(response)
        }
    }
    
    private func generateResponse(from results: [NwoApiClient.ApiResult]) -> String {
        let successCount = results.filter {
            if case .success = $0 { return true }
            return false
        }.count
        
        let errorCount = results.count - successCount
        
        if errorCount == 0 {
            return "Command executed successfully"
        } else if successCount == 0 {
            return "Command failed. Please try again."
        } else {
            return "Command partially completed with \(errorCount) errors"
        }
    }
    
    // MARK: - Text-to-Speech
    private func speak(_ text: String) {
        currentState = .speaking
        delegate?.voiceProcessor(self, willSpeak: text)
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        
        let synthesizer = AVSpeechSynthesizer()
        synthesizer.speak(utterance)
        
        // Return to idle after speech
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            self.currentState = .idle
        }
    }
    
    enum VoiceProcessorError: Error {
        case recognitionRequestFailed
        case audioEngineFailed
        case notAuthorized
    }
}

// MARK: - Delegate Protocol
protocol VoiceCommandProcessorDelegate: AnyObject {
    func voiceProcessor(_ processor: VoiceCommandProcessor, didChangeState state: VoiceCommandProcessor.State)
    func voiceProcessor(_ processor: VoiceCommandProcessor, didDetectWakeWord transcript: String)
    func voiceProcessor(_ processor: VoiceCommandProcessor, didGenerateFunctionCalls data: [String: Any])
    func voiceProcessor(_ processor: VoiceCommandProcessor, didExecuteCommand result: NwoApiClient.ApiResult)
    func voiceProcessor(_ processor: VoiceCommandProcessor, willSpeak text: String)
    func voiceProcessor(_ processor: VoiceCommandProcessor, didEncounterError error: String)
}

// MARK: - SFSpeechRecognizerDelegate
extension VoiceCommandProcessor: SFSpeechRecognizerDelegate {
    func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        if !available {
            stopListening()
            delegate?.voiceProcessor(self, didEncounterError: "Speech recognition unavailable")
        }
    }
}
