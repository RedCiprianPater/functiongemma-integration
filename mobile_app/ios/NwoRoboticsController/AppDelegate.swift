import UIKit

@main
class AppDelegate: UIResponder, UIApplicationDelegate {

    var window: UIWindow?
    var gemmaManager: FunctionGemmaManager?
    var apiClient: NwoApiClient?
    var voiceProcessor: VoiceCommandProcessor?
    var safetyManager: SafetyManager?

    func application(_ application: UIApplication, 
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Initialize core components
        do {
            gemmaManager = try FunctionGemmaManager()
        } catch {
            print("Failed to initialize FunctionGemma: \(error)")
        }
        
        // Initialize API client
        apiClient = NwoApiClient(
            baseUrl: "https://nwo.capital/webapp/api",
            apiKey: loadApiKey()
        )
        
        // Initialize safety manager
        safetyManager = SafetyManager()
        
        // Initialize voice processor
        if let gemma = gemmaManager, let api = apiClient {
            voiceProcessor = VoiceCommandProcessor(
                gemmaManager: gemma,
                apiClient: api
            )
            voiceProcessor?.delegate = self
        }
        
        // Setup window
        window = UIWindow(frame: UIScreen.main.bounds)
        let viewController = ViewController()
        window?.rootViewController = UINavigationController(rootViewController: viewController)
        window?.makeKeyAndVisible()
        
        return true
    }

    func applicationWillResignActive(_ application: UIApplication) {
        // Pause ongoing operations
        voiceProcessor?.stopListening()
    }

    func applicationDidEnterBackground(_ application: UIApplication) {
        // Save state if needed
    }

    func applicationWillEnterForeground(_ application: UIApplication) {
        // Resume operations
    }

    func applicationDidBecomeActive(_ application: UIApplication) {
        // Check connectivity
        Task {
            await apiClient?.checkConnectivity()
        }
    }

    func applicationWillTerminate(_ application: UIApplication) {
        // Cleanup
        voiceProcessor = nil
        gemmaManager = nil
    }
    
    // MARK: - Private
    
    private func loadApiKey() -> String {
        // Load from secure storage (Keychain)
        // For demo, return placeholder
        return "your_api_key_here"
    }
}

// MARK: - VoiceCommandProcessorDelegate
extension AppDelegate: VoiceCommandProcessorDelegate {
    func voiceProcessor(_ processor: VoiceCommandProcessor, didChangeState state: VoiceCommandProcessor.State) {
        // Handle state changes
    }
    
    func voiceProcessor(_ processor: VoiceCommandProcessor, didDetectWakeWord transcript: String) {
        print("Wake word detected: \(transcript)")
    }
    
    func voiceProcessor(_ processor: VoiceCommandProcessor, didGenerateFunctionCalls data: [String: Any]) {
        print("Generated function calls: \(data)")
    }
    
    func voiceProcessor(_ processor: VoiceCommandProcessor, didExecuteCommand result: NwoApiClient.ApiResult) {
        print("Command executed: \(result)")
    }
    
    func voiceProcessor(_ processor: VoiceCommandProcessor, willSpeak text: String) {
        print("Speaking: \(text)")
    }
    
    func voiceProcessor(_ processor: VoiceCommandProcessor, didEncounterError error: String) {
        print("Voice processor error: \(error)")
    }
}

// MARK: - ViewController
class ViewController: UIViewController {
    
    private let statusLabel = UILabel()
    private let commandTextField = UITextField()
    private let sendButton = UIButton()
    private let voiceButton = UIButton()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
    }
    
    private func setupUI() {
        view.backgroundColor = .systemBackground
        title = "NWO Robotics"
        
        // Status label
        statusLabel.text = "Ready"
        statusLabel.textAlignment = .center
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusLabel)
        
        // Command text field
        commandTextField.placeholder = "Enter command..."
        commandTextField.borderStyle = .roundedRect
        commandTextField.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(commandTextField)
        
        // Send button
        sendButton.setTitle("Send", for: .normal)
        sendButton.backgroundColor = .systemBlue
        sendButton.layer.cornerRadius = 8
        sendButton.translatesAutoresizingMaskIntoConstraints = false
        sendButton.addTarget(self, action: #selector(sendTapped), for: .touchUpInside)
        view.addSubview(sendButton)
        
        // Voice button
        voiceButton.setTitle("🎤", for: .normal)
        voiceButton.titleLabel?.font = .systemFont(ofSize: 32)
        voiceButton.translatesAutoresizingMaskIntoConstraints = false
        voiceButton.addTarget(self, action: #selector(voiceTapped), for: .touchUpInside)
        view.addSubview(voiceButton)
        
        // Layout
        NSLayoutConstraint.activate([
            statusLabel.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 20),
            statusLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            statusLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
            
            commandTextField.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 40),
            commandTextField.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            commandTextField.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
            commandTextField.heightAnchor.constraint(equalToConstant: 44),
            
            sendButton.topAnchor.constraint(equalTo: commandTextField.bottomAnchor, constant: 20),
            sendButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            sendButton.widthAnchor.constraint(equalToConstant: 120),
            sendButton.heightAnchor.constraint(equalToConstant: 44),
            
            voiceButton.topAnchor.constraint(equalTo: sendButton.bottomAnchor, constant: 40),
            voiceButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            voiceButton.widthAnchor.constraint(equalToConstant: 80),
            voiceButton.heightAnchor.constraint(equalToConstant: 80)
        ])
    }
    
    @objc private func sendTapped() {
        guard let command = commandTextField.text, !command.isEmpty else { return }
        
        let appDelegate = UIApplication.shared.delegate as? AppDelegate
        appDelegate?.voiceProcessor?.processTextCommand(command)
        
        commandTextField.text = ""
    }
    
    @objc private func voiceTapped() {
        let appDelegate = UIApplication.shared.delegate as? AppDelegate
        
        if appDelegate?.voiceProcessor?.currentState == .listening {
            appDelegate?.voiceProcessor?.stopListening()
            voiceButton.setTitle("🎤", for: .normal)
        } else {
            appDelegate?.voiceProcessor?.startListening()
            voiceButton.setTitle("🔴", for: .normal)
        }
    }
}
