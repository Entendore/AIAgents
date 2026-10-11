# AgentML Specification v1.0.0

**Author:** AI Agent Framework Working Group  
**Status:** Draft  
**Version:** 1.0.0  
**Last Updated:** October 2023

## 1. Introduction

AgentML is a declarative markup language for defining AI agents, their behavior, capabilities, and lifecycle. It provides a standardized, framework-agnostic format that bridges the gap between human intent and machine execution. AgentML specifications are both human-readable and machine-parseable, enabling portability, governance, and collaboration.

### 1.1 Design Philosophy

- **Declarative over Imperative**: Define *what* an agent is, not *how* it executes.
- **Separation of Concerns**: Distinguish between definition, execution, and orchestration.
- **Composable and Extensible**: Design to work with existing standards (OpenAPI, MCP, etc.).
- **Security by Design**: Make permissions and boundaries first-class citizens.
- **Human-Centric Authoring**: Prioritize readability for developers and domain experts.

### 1.2 Core Components

AgentML specifications consist of:

1. **Identity and Metadata**: Name, version, description, author, tags.
2. **Configuration**: LLM settings, runtime parameters, dependencies.
3. **Capabilities**: Tools, knowledge sources, interfaces.
4. **Permissions and Boundaries**: Access control, network policies, data governance.
5. **Instructions and Logic**: Natural language directives and reasoning strategies.
6. **State Model**: DFA/NFA definitions for behavioral transitions.
7. **Pattern Matching**: Aho-Corasick dictionaries for real-time event detection.
8. **Testing**: Built-in test suites for validation.
9. **Governance**: Audit logging, ethical constraints, compliance rules.
10. **Performance**: Optimization hints for execution.

## 2. File Structure

An AgentML file uses a YAML/Markdown hybrid format:

```yaml
---
# YAML configuration (metadata, config, tools, etc.)
---

# Markdown content (instructions, examples, documentation)
```

The YAML section contains structured configuration, while the Markdown section provides natural language instructions.

## 3. Core Specification

### 3.1 Identity and Metadata

```yaml
identity:
  name: string                # Required. Human-readable agent name
  version: string             # Required. Semantic version (e.g., "1.2.3")
  description: string         # Required. Purpose and functionality
  author: string              # Required. Creator or organization
  license: string             # Optional. License identifier (SPDX)
  repository: string          # Optional. Source repository URL
  tags: [string]              # Optional. Classification tags
  created: timestamp          # Optional. ISO 8601 creation timestamp
  modified: timestamp         # Optional. ISO 8601 modification timestamp
```

### 3.2 Configuration

```yaml
config:
  llm:
    provider: string          # Required. LLM provider (e.g., "openai", "anthropic")
    model: string             # Required. Model identifier
    temperature: float        # Optional. 0.0-1.0 (default: 0.7)
    max_tokens: integer       # Optional. Maximum output tokens
    top_p: float              # Optional. Nucleus sampling parameter
    frequency_penalty: float  # Optional. Frequency penalty
    presence_penalty: float   # Optional. Presence penalty
    stop_sequences: [string]  # Optional. Stop generation sequences
    
  runtime:
    timeout_seconds: integer  # Optional. Execution timeout (default: 300)
    max_iterations: integer   # Optional. Maximum reasoning loops
    execution_mode: string    # Optional. "sequential" or "parallel" (default: "sequential")
    
  dependencies:
    - name: string
      version: string
      source: string          # Optional. Registry or repository URL
```

### 3.3 Capabilities

#### 3.3.1 Tools

```yaml
tools:
  - name: string              # Required. Unique tool identifier
    type: string              # Required. "mcp", "function", "openapi", or "agent_delegation"
    description: string       # Required. Tool functionality description
    parameters:               # JSON Schema for parameters
      type: object
      properties: ...
    returns:                  # JSON Schema for return value
      type: object
      properties: ...
    config:                   # Tool-specific configuration
      # For MCP tools
      transport: string       # "http" or "websocket"
      url: string
      authentication:
        type: string          # "bearer", "basic", "api_key"
        token: string         # Can use ${env:VAR_NAME} syntax
        
      # For function tools
      module: string          # Python/JavaScript module path
      function: string        # Function name within module
      
      # For OpenAPI tools
      spec_url: string        # URL to OpenAPI specification
      operations: [string]    # Allowed operations
      
      # For agent delegation
      target_agent: string    # Reference to another agent definition
      input_schema: object    # JSON Schema for delegation input
      output_schema: object   # JSON Schema for delegation output
```

#### 3.3.2 Knowledge Sources

```yaml
knowledge:
  sources:
    - name: string
      type: string            # "vector_store", "relational_db", "file_system", "api"
      description: string
      config:                 # Source-specific configuration
        # For vector stores
        provider: string      # "pinecone", "weaviate", "milvus", etc.
        index: string
        embedding_model: string
        credentials: string   # ${env:VAR_NAME} syntax
        
        # For relational databases
        connection_string: string
        tables: [string]
        
      retrieval_strategy:
        type: string          # "semantic", "keyword", "hybrid"
        top_k: integer
        rerank: boolean
        rerank_model: string
        
      context_management:
        max_source_tokens: integer
        prioritization: string  # "relevance_score", "recency", "custom"
```

### 3.4 Permissions and Boundaries

```yaml
permissions:
  file_system:
    read: [string]           # Glob patterns for readable paths
    write: [string]          # Glob patterns for writable paths
    
  network:
    allow_domains: [string]  # Allowed domain patterns
    deny_domains: [string]   # Denied domain patterns
    allow_ports: [integer]   # Allowed network ports
    
  data:
    redact_patterns: [string]  # Regex patterns for data redaction
    sensitive_data_detection: boolean
    
  execution:
    max_memory_mb: integer
    max_cpu_percent: integer
    allow_shell: boolean     # Allow shell command execution
```

### 3.5 Instructions and Reasoning

#### 3.5.1 Basic Instructions (Markdown Body)

```markdown
# Role
You are a [detailed role description].

# Instructions
- [Guideline 1]
- [Guideline 2]
- [Guideline 3]

# Constraints
- [Constraint 1]
- [Constraint 2]

# Examples
[Example interactions or demonstrations]
```

#### 3.5.2 Advanced Reasoning Strategies

```yaml
reasoning:
  strategy: string           # "chain_of_thought", "tree_of_thoughts", "meta_prompting", "role_based", "self_consistency"
  
  parameters:
    # Chain-of-Thought
    cot_trigger: string
    few_shot_examples: boolean
    scratchpad_format: string
    
    # Tree of Thoughts
    thought_generators: integer
    evaluation_prompt: string
    search_algorithm: string  # "beam_search", "breadth_first", "depth_first"
    max_depth: integer
    beam_width: integer
    
    # Meta-Prompting
    meta_template: string
    
    # Role-Based
    role: string
    persona: string
    
    # Self-Consistency
    num_samples: integer
    aggregation_method: string  # "majority_vote", "weighted"
    
  enhancements:
    - type: string           # "few_shot_learning", "context_management", "instruction_anchoring"
      parameters: ...
```

### 3.6 State Model (Automata Theory)

```yaml
state_model:
  type: string               # "dfa" or "nfa"
  initial_state: string
  
  states:
    - name: string
      description: string
      is_final: boolean
      metadata: object       # Additional state properties
      
  transitions:
    - from: string
      on: string             # Event name
      to: string | [string]  # Single state (DFA) or set of states (NFA)
      action: string         # Optional. Tool call or action identifier
      guard: string          # Optional. Condition for transition
      metadata: object       # Additional transition properties
      
  # Aho-Corasick pattern matching
  pattern_dictionary:
    pattern_string: event_name  # Maps patterns to events
```

### 3.7 Testing

```yaml
tests:
  suite:
    - name: string
      description: string
      input: object          # Test input
      mock_tools:            # Tool mocks for testing
        - tool: string
          action: string
          return_value: object
      expected_flow:         # Expected state transitions
        - state: string
          tool: string
          action: string
      evaluators:            # Success criteria
        - type: string       # "output_contains", "tool_call_accuracy", "state_reached"
          parameters: ...
```

### 3.8 Governance

```yaml
governance:
  access_control:
    allowed_users: [string]
    allowed_groups: [string]
    rbac_policies: object
    
  audit:
    enabled: boolean
    level: string            # "minimal", "standard", "verbose"
    destinations:
      - type: string         # "cloudwatch", "file", "elk", "splunk"
        config: object
        
  ethical_constraints:
    - "constraint_identifier"
    
  compliance:
    frameworks: [string]     # "soc2", "hipaa", "gdpr"
    data_residency: string   # "us", "eu", etc.
```

### 3.9 Performance Optimization

```yaml
performance:
  execution_strategy:
    mode: string             # "sequential", "parallel", "adaptive"
    max_concurrency: integer
    
  caching:
    enabled: boolean
    rules:
      - tool: string
        action: string
        key: string          # Cache key expression
        ttl: integer         # Time-to-live in seconds
        
  token_optimization:
    compress_intermediate_thoughts: boolean
    document_truncation_strategy: string  # "semantic-summary", "head-tail"
```

### 3.10 Interfaces

```yaml
interfaces:
  - type: string             # "console", "webchat", "webhook", "api", "agent_delegation"
    name: string             # Interface identifier
    description: string
    config:                  # Interface-specific configuration
      # For webchat
      endpoint: string
      authentication: object
      
      # For webhook
      path: string
      method: string
      headers: object
      
    input_schema: object     # JSON Schema for input
    output_schema: object    # JSON Schema for output
```

## 4. Advanced Features

### 4.1 Multi-Agent Orchestration

AgentML supports defining how agents interact through delegation:

```yaml
tools:
  - name: "delegate_to_specialist"
    type: "agent_delegation"
    config:
      target_agent: "specialist-agent@v1.2.0"
      input_schema:
        type: object
        properties:
          task: string
          context: object
      output_schema:
        type: object
        properties:
          result: string
          status: string
```

### 4.2 Error Handling and Resilience

```yaml
resilience:
  max_retries: integer
  timeout_seconds: integer
  
  on_failure:
    - tool: string
      error_type: string     # "timeout", "service_unavailable", "rate_limit"
      action: string         # "retry", "use_fallback", "ask_human"
      fallback_tool: string  # For "use_fallback" action
      
  fallback_behavior: string  # "ask_human_for_help", "log_and_stop", "continue_partial"
  
  self_correction:
    enabled: boolean
    evaluator_agent: string  # Reference to evaluator agent
    max_iterations: integer
```

### 4.3 Versioning and Lifecycle

```yaml
lifecycle:
  status: string             # "development", "staging", "production", "deprecated"
  deprecation_date: date     # ISO 8601 date if deprecated
  successor: string          # Version or agent to migrate to
```

## 5. Ecosystem and Tooling

### 5.1 Registry Integration

Agents can be published to a central registry:

```bash
# Publishing
agentml publish ./my-agent --registry https://registry.agentml.org

# Discovering
agentml search "customer support"

# Pulling
agentml pull organization/support-agent --version 1.2.0
```

### 5.2 CLI Commands

```bash
agentml init [template]              # Create new agent from template
agentml validate [file]              # Validate syntax and schema
agentml test [file]                  # Run test suite
agentml run [file] [options]         # Execute agent locally
agentml debug [file]                 # Interactive debugging
agentml package [file]               # Create distributable package
agentml publish [file] [registry]    # Publish to registry
```

### 5.3 Visual Tooling

- **Agent Studio**: Visual designer with drag-and-drop components
- **State Diagram Viewer**: Visualize DFA/NFA state models
- **Execution Graph Debugger**: Time-travel debugging with state inspection
- **Performance Profiler**: Token usage and execution time analysis

## 6. Examples

### 6.1 Minimal Agent

```yaml
---
identity:
  name: "EchoBot"
  version: "1.0.0"
  description: "Repeats user input in reverse"
  author: "Developer"

config:
  llm:
    provider: "openai"
    model: "gpt-3.5-turbo"
    temperature: 0.0

interfaces:
  - type: "console"
---
# Instructions

You are **EchoBot**. Your only purpose is to take the user's input string and return it reversed.

## Rules
1. Do not add commentary.
2. Do not explain what you are doing.
3. Simply return the reversed string.
```

### 6.2 Complex Agent with All Features

```yaml
---
identity:
  name: "Financial Risk Analyst"
  version: "2.0.0"
  description: "Comprehensive financial risk assessment"
  author: "Finance Team"
  tags: ["finance", "risk", "analysis"]

config:
  llm:
    provider: "anthropic"
    model: "claude-3-opus"
    temperature: 0.1
    max_tokens: 4096
  runtime:
    timeout_seconds: 600

tools:
  - name: "financial_data_api"
    type: "mcp"
    description: "Access financial market data"
    config:
      transport: "http"
      url: "https://api.financialdata.com/mcp"
      authentication:
        type: "bearer"
        token: "${env:FINANCIAL_API_KEY}"
        
  - name: "risk_model"
    type: "function"
    description: "Calculate Value at Risk (VaR)"
    config:
      module: "risk_models.var"
      function: "calculate_var"

knowledge:
  sources:
    - name: "risk_database"
      type: "relational_db"
      config:
        connection_string: "${env:RISK_DB_CONNECTION}"
      retrieval_strategy:
        type: "keyword"
        top_k: 10

permissions:
  data_access:
    - "financial_statements"
    - "market_data"
  network:
    allow_domains: ["api.financialdata.com", "internal-risk.service"]

reasoning:
  strategy: "tree_of_thoughts"
  parameters:
    thought_generators: 3
    evaluation_prompt: "Rate risk level 1-10"
    search_algorithm: "beam_search"
  enhancements:
    - type: "role_based"
      role: "senior risk analyst"
      persona: "Conservative, data-driven, detail-oriented"

state_model:
  type: "nfa"
  initial_state: "intake"
  states:
    - name: "intake"
      description: "Initial request processing"
    - name: "analysis"
      description: "Risk analysis in progress"
    - name: "review"
      description: "Human review checkpoint"
      is_final: true
  transitions:
    - from: "intake"
      on: "request"
      to: ["analysis", "escalation"]
    - from: "analysis"
      on: "complete"
      to: "review"
  pattern_dictionary:
    "urgent": "escalate"
    "confidential": "security_check"

tests:
  suite:
    - name: "test_high_risk_scenario"
      input:
        company_id: "test-company-high-risk"
      mock_tools:
        - tool: "financial_data_api"
          action: "get_company_data"
          return_value:
            debt_to_equity: 3.5
            cash_flow: -500000
      expected_flow:
        - state: "analysis"
          tool: "risk_model"
      evaluators:
        - type: "output_contains"
          value: "High Risk"

governance:
  audit:
    enabled: true
    level: "verbose"
  ethical_constraints:
    - "do_not_disclose_insider_info"

interfaces:
  - type: "webhook"
    path: "/api/risk-analysis"
    input_schema:
      type: object
      properties:
        company_id:
          type: string
    output_schema:
      type: object
      properties:
        risk_level:
          type: string
        report:
          type: string
---
# Role
You are a **Senior Financial Risk Analyst** with expertise in credit and market risk assessment.

# Instructions
1. **Gather Data**: Use financial_data_api to retrieve company financials.
2. **Analyze**: Apply risk models and reasoning strategies.
3. **Report**: Provide clear risk assessment with justification.

# Constraints
- Never share confidential client data.
- Always cite data sources.
- Flag potential conflicts of interest.
```

## 7. Validation and Compliance

### 7.1 Schema Validation

AgentML files must validate against the official JSON Schema:

```bash
agentml validate ./my-agent.yaml
```

### 7.2 Security Scanning

The registry performs security scans for:
- Overly permissive permissions
- Hardcoded secrets
- Vulnerable dependencies
- Unsafe configuration

## 8. Versioning and Compatibility

AgentML follows semantic versioning (MAJOR.MINOR.PATCH). The specification is designed to be backward-compatible for minor and patch versions.

## 9. Extension Points

AgentML is designed to be extended through:

1. **Custom Tool Types**: Frameworks can define new tool types.
2. **Reasoning Strategies**: New strategies can be added to the `reasoning.strategy` enum.
3. **State Model Extensions**: Additional automata types can be supported.
4. **Governance Frameworks**: New compliance frameworks can be added.

## 10. Adoption Roadmap

1. **Phase 1**: Core specification release with YAML/Markdown format.
2. **Phase 2**: Reference runtime implementation.
3. **Phase 3**: CLI tooling and visual editors.
4. **Phase 4**: Registry and ecosystem buildout.
5. **Phase 5**: Standardization through industry consortium.

---

**Contributing**: See CONTRIBUTING.md for details on how to contribute to the specification.

**License**: This specification is licensed under the [CC BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).

**Contact**: For questions or feedback, please open an issue on the GitHub repository.