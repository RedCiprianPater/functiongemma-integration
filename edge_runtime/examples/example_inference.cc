/**
 * Example: Basic inference with FunctionGemma
 */

#include <iostream>
#include <memory>
#include "litert_runtime/inference_engine.h"
#include "litert_runtime/function_parser.h"

using namespace nwo::litert;

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <model_path> <tokenizer_path>" << std::endl;
        return 1;
    }
    
    std::string model_path = argv[1];
    std::string tokenizer_path = argv[2];
    
    std::cout << "Loading FunctionGemma model..." << std::endl;
    
    // Create inference engine
    auto engine = CreateInferenceEngine(model_path, tokenizer_path, false, 4);
    
    if (!engine || !engine->IsReady()) {
        std::cerr << "Failed to load model" << std::endl;
        return 1;
    }
    
    std::cout << "Model loaded successfully!" << std::endl;
    
    // Load function schemas
    FunctionParser parser;
    parser.LoadSchemasFromJson("../../function_schemas/nwo_robotics_functions.json");
    
    // Example prompts
    std::vector<std::string> prompts = {
        "Move go2_001 forward 2 meters",
        "Check battery on spot_001",
        "Deploy swarm alpha for patrol",
        "Emergency stop all robots"
    };
    
    std::cout << "\nRunning inference examples:\n" << std::endl;
    
    for (const auto& prompt : prompts) {
        std::cout << "Prompt: \"" << prompt << "\"" << std::endl;
        
        // Run inference
        auto result = engine->RunInference(prompt, parser, 256, 0.7f);
        
        if (result.success && result.function_calls.success) {
            std::cout << "  ✓ Function calls detected:" << std::endl;
            for (const auto& call : result.function_calls.calls) {
                std::cout << "    - " << call.name << "(";
                bool first = true;
                for (const auto& [key, value] : call.arguments) {
                    if (!first) std::cout << ", ";
                    std::cout << key << "=" << value;
                    first = false;
                }
                std::cout << ")" << std::endl;
            }
            std::cout << "  Time: " << result.inference_time_ms << "ms" << std::endl;
        } else {
            std::cout << "  ✗ Failed: " << result.error_message << std::endl;
        }
        
        std::cout << std::endl;
    }
    
    return 0;
}
