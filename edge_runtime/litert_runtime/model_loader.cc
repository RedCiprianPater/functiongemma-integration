/**
 * LiteRT Model Loader Implementation
 */

#include "model_loader.h"
#include <fstream>
#include <iostream>

namespace nwo {
namespace litert {

FunctionGemmaModel::FunctionGemmaModel(const ModelConfig& config) 
    : config_(config) {
    if (!LoadModel(config.model_path)) {
        std::cerr << "Failed to load model from: " << config.model_path << std::endl;
        return;
    }
    
    if (!BuildInterpreter()) {
        std::cerr << "Failed to build interpreter" << std::endl;
        return;
    }
    
    if (config.use_gpu && !ApplyDelegates()) {
        std::cerr << "Warning: GPU delegate failed, using CPU" << std::endl;
    }
    
    initialized_ = true;
}

FunctionGemmaModel::~FunctionGemmaModel() {
    if (gpu_delegate_) {
        TfLiteGpuDelegateV2Delete(gpu_delegate_);
    }
}

FunctionGemmaModel::FunctionGemmaModel(FunctionGemmaModel&& other) noexcept
    : config_(std::move(other.config_)),
      model_(std::move(other.model_)),
      interpreter_(std::move(other.interpreter_)),
      gpu_delegate_(other.gpu_delegate_),
      initialized_(other.initialized_) {
    other.gpu_delegate_ = nullptr;
    other.initialized_ = false;
}

FunctionGemmaModel& FunctionGemmaModel::operator=(FunctionGemmaModel&& other) noexcept {
    if (this != &other) {
        config_ = std::move(other.config_);
        model_ = std::move(other.model_);
        interpreter_ = std::move(other.interpreter_);
        gpu_delegate_ = other.gpu_delegate_;
        initialized_ = other.initialized_;
        other.gpu_delegate_ = nullptr;
        other.initialized_ = false;
    }
    return *this;
}

bool FunctionGemmaModel::LoadModel(const std::string& path) {
    // Check if file exists
    std::ifstream file(path, std::ios::binary);
    if (!file.good()) {
        std::cerr << "Model file not found: " << path << std::endl;
        return false;
    }
    file.close();
    
    // Load model
    model_ = tflite::FlatBufferModel::BuildFromFile(path.c_str());
    if (!model_) {
        std::cerr << "Failed to build model from file" << std::endl;
        return false;
    }
    
    return true;
}

bool FunctionGemmaModel::BuildInterpreter() {
    tflite::ops::builtin::BuiltinOpResolver resolver;
    
    tflite::InterpreterBuilder builder(*model_, resolver);
    builder.SetNumThreads(config_.num_threads);
    
    if (builder(&interpreter_) != kTfLiteOk) {
        std::cerr << "Failed to build interpreter" << std::endl;
        return false;
    }
    
    // Allocate tensors
    if (interpreter_->AllocateTensors() != kTfLiteOk) {
        std::cerr << "Failed to allocate tensors" << std::endl;
        return false;
    }
    
    return true;
}

bool FunctionGemmaModel::ApplyDelegates() {
    // Configure GPU delegate options
    TfLiteGpuDelegateOptionsV2 gpu_opts = TfLiteGpuDelegateOptionsV2Default();
    gpu_opts.inference_priority1 = TFLITE_GPU_INFERENCE_PRIORITY_MIN_LATENCY;
    gpu_opts.inference_preference = TFLITE_GPU_INFERENCE_PREFERENCE_FAST_SINGLE_ANSWER;
    
    gpu_delegate_ = TfLiteGpuDelegateV2Create(&gpu_opts);
    if (!gpu_delegate_) {
        std::cerr << "Failed to create GPU delegate" << std::endl;
        return false;
    }
    
    if (interpreter_->ModifyGraphWithDelegate(gpu_delegate_) != kTfLiteOk) {
        std::cerr << "Failed to apply GPU delegate" << std::endl;
        TfLiteGpuDelegateV2Delete(gpu_delegate_);
        gpu_delegate_ = nullptr;
        return false;
    }
    
    std::cout << "GPU delegate applied successfully" << std::endl;
    return true;
}

size_t FunctionGemmaModel::GetInputSize() const {
    if (!interpreter_ || interpreter_->inputs().empty()) {
        return 0;
    }
    
    TfLiteTensor* input = interpreter_->input_tensor(0);
    if (!input) return 0;
    
    size_t size = 1;
    for (int i = 0; i < input->dims->size; i++) {
        size *= input->dims->data[i];
    }
    return size;
}

size_t FunctionGemmaModel::GetOutputSize() const {
    if (!interpreter_ || interpreter_->outputs().empty()) {
        return 0;
    }
    
    TfLiteTensor* output = interpreter_->output_tensor(0);
    if (!output) return 0;
    
    size_t size = 1;
    for (int i = 0; i < output->dims->size; i++) {
        size *= output->dims->data[i];
    }
    return size;
}

std::unique_ptr<FunctionGemmaModel> LoadModel(const ModelConfig& config) {
    auto model = std::make_unique<FunctionGemmaModel>(config);
    if (!model->IsLoaded()) {
        return nullptr;
    }
    return model;
}

} // namespace litert
} // namespace nwo
