/**
 * LiteRT Model Loader
 * Loads and initializes TFLite models for FunctionGemma inference
 */

#ifndef MODEL_LOADER_H
#define MODEL_LOADER_H

#include <string>
#include <memory>
#include <vector>

#include "tensorflow/lite/interpreter.h"
#include "tensorflow/lite/kernels/register.h"
#include "tensorflow/lite/model.h"
#include "tensorflow/lite/delegates/gpu/delegate.h"

namespace nwo {
namespace litert {

// Model configuration
struct ModelConfig {
    std::string model_path;
    int num_threads = 4;
    bool use_gpu = true;
    int max_tokens = 512;
    float temperature = 0.1f;
};

// Model handle
class FunctionGemmaModel {
public:
    explicit FunctionGemmaModel(const ModelConfig& config);
    ~FunctionGemmaModel();

    // Disable copy
    FunctionGemmaModel(const FunctionGemmaModel&) = delete;
    FunctionGemmaModel& operator=(const FunctionGemmaModel&) = delete;

    // Enable move
    FunctionGemmaModel(FunctionGemmaModel&&) noexcept;
    FunctionGemmaModel& operator=(FunctionGemmaModel&&) noexcept;

    // Model info
    bool IsLoaded() const { return model_ != nullptr; }
    size_t GetInputSize() const;
    size_t GetOutputSize() const;
    
    // Get interpreter for inference
    tflite::Interpreter* GetInterpreter() { return interpreter_.get(); }

private:
    bool LoadModel(const std::string& path);
    bool BuildInterpreter();
    bool ApplyDelegates();

    ModelConfig config_;
    std::unique_ptr<tflite::FlatBufferModel> model_;
    std::unique_ptr<tflite::Interpreter> interpreter_;
    TfLiteDelegate* gpu_delegate_ = nullptr;
    
    bool initialized_ = false;
};

// Factory function
std::unique_ptr<FunctionGemmaModel> LoadModel(const ModelConfig& config);

} // namespace litert
} // namespace nwo

#endif // MODEL_LOADER_H
