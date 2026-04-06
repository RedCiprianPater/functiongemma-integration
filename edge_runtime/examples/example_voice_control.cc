/**
 * Example: Voice command processing
 */

#include <iostream>
#include <memory>
#include <vector>
#include "litert_runtime/inference_engine.h"
#include "litert_runtime/function_parser.h"

using namespace nwo::litert;

// Simulated audio capture (replace with actual audio library)
std::vector<float> CaptureAudio() {
    // In production, use PortAudio, ALSA, or similar
    // This is a placeholder
    return std::vector<float>(16000, 0.0f);  // 1 second of silence
}

int main(int argc, char* argv[]) {
    std::cout << "NWO Robotics Voice Control Example" << std::endl;
    std::cout << "==================================" << std::endl;
    
    // Initialize engine
    auto engine = CreateInferenceEngine(
        "models/functiongemma-nwo.tflite",
        "models/tokenizer.json",
        false,  // CPU mode
        4       // 4 threads
    );
    
    if (!engine) {
        std::cerr << "Failed to initialize engine" << std::endl;
        return 1;
    }
    
    FunctionParser parser;
    parser.LoadSchemasFromJson("../../function_schemas/nwo_robotics_functions.json");
    
    std::cout << "\nVoice control ready. Say a command..." << std::endl;
    std::cout << "Examples:" << std::endl;
    std::cout << "  - 'Move go2_001 forward'" << std::endl;
    std::cout << "  - 'Check battery'" << std::endl;
    std::cout << "  - 'Stop all robots'" << std::endl;
    std::cout << "\nPress Ctrl+C to exit\n" << std::endl;
    
    // Main loop
    while (true) {
        std::cout << "\n[Listening...]" << std::endl;
        
        // Capture audio (simulated)
        auto audio = CaptureAudio();
        
        // Process voice command
        // Note: In production, integrate with Whisper or similar STT
        // This example uses text input for demonstration
        
        std::cout << "Enter command (or 'quit'): ";
        std::string text_input;
        std::getline(std::cin, text_input);
        
        if (text_input == "quit") {
            break;
        }
        
        // Run inference
        auto result = engine->RunInference(text_input, parser);
        
        if (result.success && result.function_calls.success) {
            std::cout << "✓ Command recognized:" << std::endl;
            
            for (const auto& call : result.function_calls.calls) {
                std::cout << "  Function: " << call.name << std::endl;
                
                // Check if confirmation required
                if (parser.RequiresConfirmation(call.name)) {
                    std::cout << "  ⚠ This command requires confirmation!" << std::endl;
                    std::cout << "  Confirm? (yes/no): ";
                    
                    std::string confirm;
                    std::getline(std::cin, confirm);
                    
                    if (confirm != "yes") {
                        std::cout << "  Cancelled." << std::endl;
                        continue;
                    }
                }
                
                // Execute command (in production, call NWO API)
                std::cout << "  → Executing..." << std::endl;
                
                // Simulate execution
                std::cout << "  ✓ Done (" << result.inference_time_ms << "ms)" << std::endl;
            }
        } else {
            std::cout << "✗ Could not understand command" << std::endl;
        }
    }
    
    std::cout << "\nGoodbye!" << std::endl;
    return 0;
}
