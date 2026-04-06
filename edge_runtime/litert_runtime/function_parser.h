/**
 * Function Parser
 * Parses function calls from model output
 */

#ifndef FUNCTION_PARSER_H
#define FUNCTION_PARSER_H

#include <string>
#include <vector>
#include <map>
#include <optional>

namespace nwo {
namespace litert {

// Function call representation
struct FunctionCall {
    std::string name;
    std::map<std::string, std::string> arguments;
    float confidence;
    
    bool IsValid() const { return !name.empty(); }
};

// Parsed result
struct ParsedResult {
    std::vector<FunctionCall> calls;
    bool success;
    std::string error_message;
    float overall_confidence;
};

// Function schema
struct FunctionSchema {
    std::string name;
    std::string description;
    std::vector<std::string> required_params;
    std::map<std::string, std::string> param_types;
    std::map<std::string, std::string> param_defaults;
};

class FunctionParser {
public:
    FunctionParser();
    explicit FunctionParser(const std::vector<FunctionSchema>& schemas);
    
    // Main parsing methods
    ParsedResult Parse(const std::string& model_output);
    ParsedResult ParseJson(const std::string& json_str);
    
    // Schema management
    void AddSchema(const FunctionSchema& schema);
    void LoadSchemasFromJson(const std::string& json_path);
    bool ValidateCall(const FunctionCall& call) const;
    
    // Utility methods
    std::string ExtractJsonFromMarkdown(const std::string& text);
    std::vector<FunctionCall> ParseMultipleCalls(const std::string& json_str);
    
    // Safety checks
    bool RequiresConfirmation(const std::string& function_name) const;
    std::vector<std::string> GetConfirmationFunctions() const;

private:
    std::vector<FunctionSchema> schemas_;
    std::vector<std::string> confirmation_required_ = {
        "emergency_stop",
        "calibration_run", 
        "swarm_deploy"
    };
    
    FunctionCall ParseSingleCall(const std::map<std::string, std::string>& call_data);
    bool ValidateRequiredParams(const FunctionCall& call, const FunctionSchema& schema) const;
    FunctionSchema* FindSchema(const std::string& name);
};

} // namespace litert
} // namespace nwo

#endif // FUNCTION_PARSER_H
