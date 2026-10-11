import yaml
import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from jsonschema import validate, ValidationError as SchemaValidationError
from pathlib import Path

# --- 1. JSON Schema for Validation (Simplified for Brevity) ---
# In a full implementation, this would be loaded from a separate schema.json file.
AGENTML_SCHEMA = {
    "type": "object",
    "required": ["identity", "config"],
    "properties": {
        "identity": {
            "type": "object",
            "required": ["name", "version", "description", "author"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
                "author": {"type": "string"}
            }
        },
        "config": {
            "type": "object",
            "required": ["llm"],
            "properties": {
                "llm": {
                    "type": "object",
                    "required": ["provider", "model"],
                    "properties": {
                        "provider": {"type": "string"},
                        "model": {"type": "string"}
                    }
                }
            }
        },
        "tools": {"type": "array"},
        "state_model": {"type": "object"},
        "reasoning": {"type": "object"},
        "permissions": {"type": "object"},
        "knowledge": {"type": "object"}
    }
}

# --- 2. Data Structures ---

@dataclass
class AgentIdentity:
    name: str
    version: str
    description: str
    author: str
    tags: List[str] = field(default_factory=list)

@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000

@dataclass
class AgentConfig:
    llm: LLMConfig
    runtime: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StateTransition:
    from_state: str
    on_event: str
    to_states: List[str] # DFA will have 1, NFA can have multiple

@dataclass
class StateModel:
    type: str # 'dfa' or 'nfa'
    initial_state: str
    transitions: List[StateTransition] = field(default_factory=list)
    pattern_dictionary: Dict[str, str] = field(default_factory=dict)

@dataclass
class AgentDefinition:
    """The final parsed and validated AgentML object."""
    identity: AgentIdentity
    config: AgentConfig
    instructions: str # The Markdown body
    raw_config: Dict[str, Any] = field(default_factory=dict) # Holds the full YAML dict
    tools: List[Dict] = field(default_factory=list)
    state_model: Optional[StateModel] = None
    knowledge: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, Any] = field(default_factory=dict)
    reasoning: Dict[str, Any] = field(default_factory=dict)

# --- 3. Custom Exceptions ---

class AgentMLSyntaxError(Exception):
    """Raised when the file format is invalid (e.g., missing --- separators)."""
    pass

class AgentMLValidationError(Exception):
    """Raised when the content fails schema validation."""
    pass

class AgentMLParsingError(Exception):
    """General parsing error."""
    pass

# --- 4. The Parser Class ---

class AgentMLParser:
    """
    Parses AgentML files (YAML + Markdown) into structured Python objects.
    """

    def parse_file(self, file_path: str) -> AgentDefinition:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"AgentML file not found: {file_path}")
        
        content = path.read_text(encoding='utf-8')
        return self.parse_string(content)

    def parse_string(self, content: str) -> AgentDefinition:
        # Step 1: Split YAML and Markdown
        yaml_content, markdown_content = self._split_front_matter(content)
        
        # Step 2: Parse YAML
        try:
            config_dict = yaml.safe_load(yaml_content)
            if config_dict is None:
                config_dict = {}
        except yaml.YAMLError as e:
            raise AgentMLParsingError(f"YAML parsing error: {e}")

        # Step 3: Validate against Schema
        self._validate_schema(config_dict)

        # Step 4: Map to Python Objects
        return self._map_to_domain(config_dict, markdown_content)

    def _split_front_matter(self, content: str) -> tuple:
        """
        Splits the document into YAML front matter and Markdown body.
        Expects content to start with '---'.
        """
        if not content.strip().startswith('---'):
            raise AgentMLSyntaxError("AgentML file must start with '---' front matter delimiter.")

        # Regex to find the second '---'
        # Pattern: --- ... (content) ... ---
        pattern = r'^---\s*\n(.*?\n?)^---\s*\n?(.*)'
        match = re.match(pattern, content, re.DOTALL | re.MULTILINE)

        if not match:
            raise AgentMLSyntaxError("Could not find closing '---' for front matter.")

        yaml_part = match.group(1)
        markdown_part = match.group(2)
        return yaml_part, markdown_part

    def _validate_schema(self, config_dict: Dict):
        """Validates the parsed YAML dictionary against the JSON Schema."""
        try:
            validate(instance=config_dict, schema=AGENTML_SCHEMA)
        except SchemaValidationError as e:
            raise AgentMLValidationError(f"Schema validation failed: {e.message}")

    def _map_to_domain(self, config: Dict, instructions: str) -> AgentDefinition:
        """Maps the raw dictionary to structured Data Classes."""
        
        # Map Identity
        id_data = config.get('identity', {})
        identity = AgentIdentity(
            name=id_data.get('name'),
            version=id_data.get('version'),
            description=id_data.get('description'),
            author=id_data.get('author'),
            tags=id_data.get('tags', [])
        )

        # Map Config
        llm_data = config.get('config', {}).get('llm', {})
        llm_config = LLMConfig(
            provider=llm_data.get('provider'),
            model=llm_data.get('model'),
            temperature=llm_data.get('temperature', 0.7),
            max_tokens=llm_data.get('max_tokens', 2000)
        )
        agent_config = AgentConfig(
            llm=llm_config,
            runtime=config.get('config', {}).get('runtime', {})
        )

        # Map State Model (Automata)
        state_model = None
        if 'state_model' in config:
            sm_data = config['state_model']
            transitions = []
            for t in sm_data.get('transitions', []):
                # Handle DFA (string) or NFA (list)
                to_states = t.get('to')
                if isinstance(to_states, str):
                    to_states = [to_states]
                
                transitions.append(StateTransition(
                    from_state=t.get('from'),
                    on_event=t.get('on'),
                    to_states=to_states
                ))
            
            state_model = StateModel(
                type=sm_data.get('type', 'dfa'),
                initial_state=sm_data.get('initial_state'),
                transitions=transitions,
                pattern_dictionary=sm_data.get('pattern_dictionary', {})
            )

        # Assemble Final Object
        return AgentDefinition(
            identity=identity,
            config=agent_config,
            instructions=instructions,
            raw_config=config, # Keep raw for access to extensions
            tools=config.get('tools', []),
            state_model=state_model,
            knowledge=config.get('knowledge', {}),
            permissions=config.get('permissions', {}),
            reasoning=config.get('reasoning', {})
        )

# --- 5. Usage Example ---

if __name__ == "__main__":
    # A sample AgentML string
    sample_agent = """
---
identity:
  name: "PatternBot"
  version: "1.0.0"
  description: "An agent using NFA and Aho-Corasick"
  author: "AI Team"
  tags: [state-machine, pattern]

config:
  llm:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.0

state_model:
  type: "nfa"
  initial_state: "listening"
  transitions:
    - from: "listening"
      on: "data_stream"
      to: ["processing", "alerting"]
  pattern_dictionary:
    "ERROR": "system_error"
    "STOP": "user_cancel"

tools:
  - name: "console"
    type: "function"
---
# Instructions
You are a PatternBot. Watch the data stream and react using your state model.
"""

    parser = AgentMLParser()
    
    try:
        agent_def = parser.parse_string(sample_agent)
        
        print(f"✅ Successfully Parsed: {agent_def.identity.name} v{agent_def.identity.version}")
        print(f"🤖 Model: {agent_def.config.llm.model}")
        print(f"📊 State Model Type: {agent_def.state_model.type if agent_def.state_model else 'None'}")
        
        if agent_def.state_model:
            print(f"🔄 Transitions: {len(agent_def.state_model.transitions)}")
            print(f"🔍 Patterns Tracked: {list(agent_def.state_model.pattern_dictionary.keys())}")
            
        print(f"\n📝 Instructions Preview:\n{agent_def.instructions[:50]}...")

    except AgentMLSyntaxError as e:
        print(f"Syntax Error: {e}")
    except AgentMLValidationError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")