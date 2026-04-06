/**
 * Function Parser Implementation
 */

#include "function_parser.h"
#include <fstream>
#include <sstream>
#include <regex>

namespace nwo {
namespace litert {

FunctionParser::FunctionParser() {}

FunctionParser::FunctionParser(const std::vector<FunctionSchema>& schemas)
    : schemas_(schemas) {}

ParsedResult FunctionParser::Parse(const std::string& model_output) {
    ParsedResult result;
    result.success = false;
    
    // Try to extract JSON from markdown code blocks
    std::string json_str = ExtractJsonFromMarkdown(model_output);
    
    if (json_str.empty()) {
        // Try parsing the whole output as JSON
        json_str = model_output;
    }
    
    return ParseJson(json_str);
}

ParsedResult FunctionParser::ParseJson(const std::string& json_str) {
    ParsedResult result;
    result.success = false;
    
    try {
        // Simple JSON parsing (in production, use nlohmann/json or similar)
        // This is a simplified implementation
        
        // Check for "calls" array format
        size_t calls_pos = json_str.find("\"calls\"");
        if (calls_pos != std::string::npos) {
            // Extract array content
            size_t array_start = json_str.find('[', calls_pos);
            size_t array_end = json_str.find_last_of(']');
            
            if (array_start != std::string::npos && array_end != std::string::npos) {
                std::string array_content = json_str.substr(
                    array_start + 1, array_end - array_start - 1);
                
                result.calls = ParseMultipleCalls(array_content);
            }
        } else {
            // Single function call format
            FunctionCall call = ParseSingleCallFromJson(json_str);
            if (call.IsValid()) {
                result.calls.push_back(call);
            }
        }
        
        result.success = !result.calls.empty();
        if (!result.success) {
            result.error_message = "No valid function calls found";
        }
        
    } catch (const std::exception& e) {
        result.error_message = std::string("Parse error: ") + e.what();
    }
    
    return result;
}

void FunctionParser::AddSchema(const FunctionSchema& schema) {
    schemas_.push_back(schema);
}

void FunctionParser::LoadSchemasFromJson(const std::string& json_path) {
    std::ifstream file(json_path);
    if (!file.is_open()) {
        return;
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string content = buffer.str();
    
    // Parse schemas from JSON (simplified)
    // In production, use proper JSON library
}

bool FunctionParser::ValidateCall(const FunctionCall& call) const {
    const FunctionSchema* schema = FindSchema(call.name);
    if (!schema) {
        return false;  // Unknown function
    }
    
    return ValidateRequiredParams(call, *schema);
}

std::string FunctionParser::ExtractJsonFromMarkdown(const std::string& text) {
    // Look for JSON in markdown code blocks
    std::regex code_block_regex("```(?:json)?\\s*\\n?([\\s\\S]*?)```");
    std::smatch match;
    
    if (std::regex_search(text, match, code_block_regex)) {
        return match[1].str();
    }
    
    // Look for JSON between curly braces
    size_t start = text.find('{');
    size_t end = text.rfind('}');
    
    if (start != std::string::npos && end != std::string::npos && end > start) {
        return text.substr(start, end - start + 1);
    }
    
    return "";
}

std::vector<FunctionCall> FunctionParser::ParseMultipleCalls(const std::string& json_str) {
    std::vector<FunctionCall> calls;
    
    // Split by '},{' to get individual calls
    size_t pos = 0;
    size_t start = 0;
    int brace_depth = 0;
    
    for (size_t i = 0; i < json_str.length(); i++) {
        if (json_str[i] == '{') brace_depth++;
        else if (json_str[i] == '}') brace_depth--;
        
        if (brace_depth == 0 && json_str[i] == ',') {
            std::string call_json = json_str.substr(start, i - start);
            FunctionCall call = ParseSingleCallFromJson(call_json);
            if (call.IsValid()) {
                calls.push_back(call);
            }
            start = i + 1;
        }
    }
    
    // Last call
    if (start < json_str.length()) {
        std::string call_json = json_str.substr(start);
        FunctionCall call = ParseSingleCallFromJson(call_json);
        if (call.IsValid()) {
            calls.push_back(call);
        }
    }
    
    return calls;
}

bool FunctionParser::RequiresConfirmation(const std::string& function_name) const {
    return std::find(confirmation_required_.begin(),
                     confirmation_required_.end(),
                     function_name) != confirmation_required_.end();
}

std::vector<std::string> FunctionParser::GetConfirmationFunctions() const {
    return confirmation_required_;
}

FunctionCall FunctionParser::ParseSingleCall(const std::map<std::string, std::string>& call_data) {
    FunctionCall call;
    
    auto name_it = call_data.find("name");
    if (name_it != call_data.end()) {
        call.name = name_it->second;
    }
    
    auto args_it = call_data.find("arguments");
    if (args_it != call_data.end()) {
        // Parse arguments JSON
        // Simplified - in production use proper JSON parsing
        call.arguments = ParseArgumentsJson(args_it->second);
    }
    
    call.confidence = 1.0f;  // Default confidence
    
    return call;
}

FunctionCall FunctionParser::ParseSingleCallFromJson(const std::string& json_str) {
    FunctionCall call;
    
    // Extract name
    std::regex name_regex("\"name\"\\s*:\\s*\"([^\"]+)\"");
    std::smatch name_match;
    if (std::regex_search(json_str, name_match, name_regex)) {
        call.name = name_match[1].str();
    }
    
    // Extract arguments
    std::regex args_regex("\"arguments\"\\s*:\\s*(\\{[^}]*\\})");
    std::smatch args_match;
    if (std::regex_search(json_str, args_match, args_regex)) {
        call.arguments = ParseArgumentsJson(args_match[1].str());
    }
    
    // Extract confidence if present
    std::regex conf_regex("\"confidence\"\\s*:\\s*([0-9.]+)");
    std::smatch conf_match;
    if (std::regex_search(json_str, conf_match, conf_regex)) {
        call.confidence = std::stof(conf_match[1].str());
    }
    
    return call;
}

std::map<std::string, std::string> FunctionParser::ParseArgumentsJson(const std::string& args_json) {
    std::map<std::string, std::string> args;
    
    // Simple key-value extraction (simplified)
    std::regex kv_regex("\"([^\"]+)\"\\s*:\\s*\"?([^\"},]+)\"?");
    std::sregex_iterator iter(args_json.begin(), args_json.end(), kv_regex);
    std::sregex_iterator end;
    
    for (; iter != end; ++iter) {
        std::string key = (*iter)[1].str();
        std::string value = (*iter)[2].str();
        args[key] = value;
    }
    
    return args;
}

bool FunctionParser::ValidateRequiredParams(const FunctionCall& call,
                                             const FunctionSchema& schema) const {
    for (const auto& required : schema.required_params) {
        if (call.arguments.find(required) == call.arguments.end()) {
            return false;
        }
    }
    return true;
}

FunctionSchema* FunctionParser::FindSchema(const std::string& name) {
    for (auto& schema : schemas_) {
        if (schema.name == name) {
            return &schema;
        }
    }
    return nullptr;
}

const FunctionSchema* FunctionParser::FindSchema(const std::string& name) const {
    for (const auto& schema : schemas_) {
        if (schema.name == name) {
            return &schema;
        }
    }
    return nullptr;
}

} // namespace litert
} // namespace nwo
