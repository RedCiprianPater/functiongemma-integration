/**
 * Inference Engine - Runs FunctionGemma inference with function calling
 */

#ifndef INFERENCE_ENGINE_H
#define INFERENCE_ENGINE_H

#include "model_loader.h"
#include "function_parser.h"
#include <string>
#include <vector>
#include <memory>
#include <functional>

namespace nwo {
namespace litert {

// Inference result
struct InferenceResult {
    ParsedResult function_calls;
    float inference_time_ms;
    bool success;
    std::string error_message;
    
    bool IsValid() const { return success && function_calls.success; }
};

// Tokenizer interface (simplified - use actual Gemma tokenizer in production)
class Tokenizer {
public:
    virtual ~Tokenizer() = default;
    virtual std::vector<int> Encode(const std::string& text) = 0;
    virtual std::string Decode(const std::vector<int>& tokens) = 0;
    virtual size_t VocabSize() const = 0;
};

// Simple BPE tokenizer stub
class BPETokenizer : public Tokenizer {
public:
    BPETokenizer(const std::string& vocab_path);
    
    std::vector<int> Encode(const std::string& text) override;
    std::string Decode(const std::vector<int>& tokens) override;
    size_t VocabSize() const override { return vocab_size_; }
    
private:
    size_t vocab_size_ = 32000;  // Gemma vocab size
    // In production, load actual BPE merges and vocab
};

// Inference engine
class InferenceEngine {
public:
    InferenceEngine(std::unique_ptr<FunctionGemmaModel> model,
                    std::unique_ptr<Tokenizer> tokenizer);
    
    // Main inference method
    InferenceResult RunInference(const std::string& prompt,
                                  const FunctionParser& parser,
                                  int max_tokens = 512,
                                  float temperature = 0.7);
    
    // Streaming inference
    void RunInferenceStreaming(
        const std::string& prompt,
        const FunctionParser& parser,
        std::function<void(const std::string&)> token_callback,
        int max_tokens = 512
    );
    
    // Batch inference for multiple prompts
    std::vector<InferenceResult> RunBatchInference(
        const std::vector<std::string>& prompts,
        const FunctionParser& parser,
        int max_tokens = 512
    );
    
    // Voice-to-function pipeline
    InferenceResult ProcessVoiceCommand(
        const std::vector<float>& audio_samples,
        const FunctionParser& parser
    );
    
    // Configuration
    void SetMaxContextLength(int length) { max_context_length_ = length; }
    void SetRepetitionPenalty(float penalty) { repetition_penalty_ = penalty; }
    
    // Status
    bool IsReady() const { return model_ != nullptr && model_->IsLoaded(); }
    
private:
    std::unique_ptr<FunctionGemmaModel> model_;
    std::unique_ptr<Tokenizer> tokenizer_;
    
    // Generation parameters
    int max_context_length_ = 2048;
    float repetition_penalty_ = 1.1f;
    
    // Internal methods
    std::vector<float> PrepareInput(const std::vector<int>& tokens);
    std::vector<int> GenerateTokens(const std::vector<int>& input_tokens,
                                     int max_new_tokens,
                                     float temperature);
    int SampleToken(const std::vector<float>& logits, float temperature);
    void ApplyRepetitionPenalty(std::vector<float>& logits,
                                 const std::vector<int>& generated_tokens);
};

// Factory function
std::unique_ptr<InferenceEngine> CreateInferenceEngine(
    const std::string& model_path,
    const std::string& tokenizer_path,
    bool use_gpu = false,
    int num_threads = 4
);

} // namespace litert
} // namespace nwo

#endif // INFERENCE_ENGINE_H
