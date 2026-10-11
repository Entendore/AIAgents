import sys
import math  # Moved to top
import yaml
import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from jsonschema import validate, ValidationError as SchemaValidationError
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPlainTextEdit, QTreeWidget, QTreeWidgetItem, 
    QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, 
    QGraphicsPathItem, QGraphicsTextItem, QPushButton, QLabel, QStatusBar
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

# ==============================================================================
# 1. CORE AGENTML PARSER (Enhanced from original)
# ==============================================================================

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
                        "model": {"type": "string"},
                        "temperature": {"type": "number"},
                        "max_tokens": {"type": "integer"}
                    }
                }
            }
        },
        "tools": {"type": "array"},
        "state_model": {"type": "object"}
    }
}

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

@dataclass
class StateTransition:
    from_state: str
    on_event: str
    to_states: List[str]

@dataclass
class StateModel:
    type: str
    initial_state: str
    transitions: List[StateTransition] = field(default_factory=list)

@dataclass
class AgentDefinition:
    identity: AgentIdentity
    config: AgentConfig
    instructions: str
    raw_config: Dict[str, Any] = field(default_factory=dict)
    tools: List[Dict] = field(default_factory=list)
    state_model: Optional[StateModel] = None

class AgentMLParser:
    def parse_string(self, content: str) -> AgentDefinition:
        # FIX 1: Strip leading/trailing whitespace so the regex doesn't fail on empty first lines
        content = content.strip()
        
        if not content.startswith('---'):
            raise ValueError("AgentML file must start with '---' front matter delimiter.")

        pattern = r'^---\s*\n(.*?)^---\s*\n?(.*)'
        match = re.match(pattern, content, re.DOTALL | re.MULTILINE)
        if not match:
            raise ValueError("Could not find closing '---' for front matter.")

        yaml_part = match.group(1)
        markdown_part = match.group(2)

        try:
            config_dict = yaml.safe_load(yaml_part) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error: {e}")

        try:
            validate(instance=config_dict, schema=AGENTML_SCHEMA)
        except SchemaValidationError as e:
            raise ValueError(f"Schema validation failed: {e.message}")

        return self._map_to_domain(config_dict, markdown_part)

    def _map_to_domain(self, config: Dict, instructions: str) -> AgentDefinition:
        id_data = config.get('identity', {})
        identity = AgentIdentity(
            name=id_data.get('name'), version=id_data.get('version'),
            description=id_data.get('description'), author=id_data.get('author'),
            tags=id_data.get('tags', [])
        )

        llm_data = config.get('config', {}).get('llm', {})
        llm_config = LLMConfig(
            provider=llm_data.get('provider'), model=llm_data.get('model'),
            temperature=llm_data.get('temperature', 0.7), max_tokens=llm_data.get('max_tokens', 2000)
        )

        state_model = None
        if 'state_model' in config:
            sm_data = config['state_model']
            transitions = []
            for t in sm_data.get('transitions', []):
                to_states = t.get('to')
                if isinstance(to_states, str): to_states = [to_states]
                transitions.append(StateTransition(
                    from_state=t.get('from'), on_event=t.get('on'), to_states=to_states
                ))
            state_model = StateModel(
                type=sm_data.get('type', 'dfa'), initial_state=sm_data.get('initial_state'),
                transitions=transitions
            )

        return AgentDefinition(
            identity=identity, config=AgentConfig(llm=llm_config),
            instructions=instructions, raw_config=config, 
            tools=config.get('tools', []), state_model=state_model
        )

# ==============================================================================
# 2. GRAPHICS WIDGETS FOR STATE MACHINE VISUALIZATION
# ==============================================================================

class StateNode(QGraphicsEllipseItem):
    def __init__(self, name, is_initial=False):
        radius = 40
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.name = name
        self.is_initial = is_initial
        
        color = QColor("#4CAF50") if is_initial else QColor("#2196F3")
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 2))
        
        text = QGraphicsTextItem(name, self)
        text.setDefaultTextColor(Qt.white)
        font = QFont("Arial", 10, QFont.Bold)
        text.setFont(font)
        br = text.boundingRect()
        text.setPos(-br.width()/2, -br.height()/2)

class TransitionEdge(QGraphicsPathItem):
    def __init__(self, start_item, end_item, event_name):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.event_name = event_name
        
        self.setPen(QPen(Qt.black, 2))
        self.setBrush(QBrush(Qt.black))
        
        self.label = QGraphicsTextItem(event_name, self)
        self.label.setFont(QFont("Arial", 9))
        
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        
        start_center = self.start_item.sceneBoundingRect().center()
        end_center = self.end_item.sceneBoundingRect().center()
        
        if self.start_item == self.end_item:
            path.moveTo(0, -40)
            path.cubicTo(50, -100, 50, -100, 0, -80)
            self.setPath(path)
            self.label.setPos(-20, -110)
            return

        radius = 40
        line = QPointF(end_center.x() - start_center.x(), end_center.y() - start_center.y())
        length = (line.x()**2 + line.y()**2)**0.5
        if length == 0: return
        
        dx, dy = line.x()/length, line.y()/length
        
        start_point = QPointF(start_center.x() + dx * radius, start_center.y() + dy * radius)
        end_point = QPointF(end_center.x() - dx * radius, end_center.y() - dy * radius)
        
        arrow_size = 10
        end_point_adjusted = QPointF(end_point.x() - dx * arrow_size, end_point.y() - dy * arrow_size)

        path.moveTo(start_point)
        path.lineTo(end_point_adjusted)
        self.setPath(path)
        
        mid_point = QPointF((start_point.x() + end_point.x())/2, (start_point.y() + end_point.y())/2)
        self.label.setPos(mid_point.x() - 20, mid_point.y() - 20)

class StateDiagramScene(QGraphicsScene):
    def __init__(self, state_model: StateModel):
        super().__init__()
        self.setSceneRect(0, 0, 800, 400)
        self.setBackgroundBrush(QBrush(QColor("#F5F5F5")))
        
        if not state_model: return
        
        nodes = {}
        states_list = list(set(
            [state_model.initial_state] + 
            [t.from_state for t in state_model.transitions] + 
            [s for t in state_model.transitions for s in t.to_states]
        ))

        cx, cy = 400, 200
        radius = 150
        
        for i, state_name in enumerate(states_list):
            angle = (2 * math.pi * i) / len(states_list)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            
            is_initial = (state_name == state_model.initial_state)
            node = StateNode(state_name, is_initial)
            node.setPos(x, y)
            self.addItem(node)
            nodes[state_name] = node

        for trans in state_model.transitions:
            start_node = nodes.get(trans.from_state)
            if not start_node: continue
            for dest_name in trans.to_states:
                end_node = nodes.get(dest_name)
                if end_node:
                    edge = TransitionEdge(start_node, end_node, trans.on_event)
                    self.addItem(edge)

# ==============================================================================
# 3. MAIN WINDOW (PySide6 UI)
# ==============================================================================

class AgentMLStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgentML Studio - Visual Parser")
        self.resize(1200, 800)
        
        self.parser = AgentMLParser()
        self.current_agent = None
        
        self._init_ui()
        self._load_sample_data()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        self.code_editor = QPlainTextEdit()
        self.code_editor.setFont(QFont("Consolas", 11))
        self.code_editor.setPlaceholderText("Paste AgentML here...")
        splitter.addWidget(self.code_editor)

        right_splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(right_splitter)

        self.tree_view = QTreeWidget()
        self.tree_view.setHeaderHidden(True)
        right_splitter.addWidget(self.tree_view)

        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        right_splitter.addWidget(self.graphics_view)

        ctrl_layout = QVBoxLayout()
        parse_btn = QPushButton("Parse & Visualize")
        parse_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        parse_btn.clicked.connect(self.parse_content)
        main_layout.addLayout(ctrl_layout)
        ctrl_layout.addWidget(parse_btn)
        ctrl_layout.addStretch()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def parse_content(self):
        content = self.code_editor.toPlainText()
        try:
            self.current_agent = self.parser.parse_string(content)
            self.status_bar.showMessage(f"✅ Success: Parsed {self.current_agent.identity.name}", 5000)
            self.status_bar.setStyleSheet("color: green;")
            
            self._update_tree_view()
            self._update_state_diagram()
            
        except Exception as e:
            self.status_bar.showMessage(f"❌ Error: {str(e)}", 5000)
            self.status_bar.setStyleSheet("color: red;")
            self.tree_view.clear()
            
            # FIX 2: PySide6 does not allow passing QColor directly into addText()
            self.graphics_scene.clear()
            error_text = self.graphics_scene.addText("Invalid AgentML", QFont("Arial", 20, QFont.Bold))
            error_text.setDefaultTextColor(Qt.red)

    def _update_tree_view(self):
        self.tree_view.clear()
        if not self.current_agent: return
        
        agent = self.current_agent
        
        id_root = QTreeWidgetItem(self.tree_view, ["Identity"])
        id_root.addChild(QTreeWidgetItem([f"Name: {agent.identity.name}"]))
        id_root.addChild(QTreeWidgetItem([f"Version: {agent.identity.version}"]))
        id_root.addChild(QTreeWidgetItem([f"Author: {agent.identity.author}"]))
        id_root.setExpanded(True)

        cfg_root = QTreeWidgetItem(self.tree_view, ["Config"])
        llm = QTreeWidgetItem(cfg_root, ["LLM"])
        llm.addChild(QTreeWidgetItem([f"Provider: {agent.config.llm.provider}"]))
        llm.addChild(QTreeWidgetItem([f"Model: {agent.config.llm.model}"]))
        llm.addChild(QTreeWidgetItem([f"Temp: {agent.config.llm.temperature}"]))
        cfg_root.setExpanded(True)

        if agent.tools:
            tools_root = QTreeWidgetItem(self.tree_view, [f"Tools ({len(agent.tools)})"])
            for tool in agent.tools:
                tools_root.addChild(QTreeWidgetItem([f"- {tool.get('name', 'Unknown')} ({tool.get('type')})"]))

        inst_root = QTreeWidgetItem(self.tree_view, ["Instructions"])
        preview = agent.instructions[:100].replace('\n', ' ') + "..."
        inst_root.addChild(QTreeWidgetItem([preview]))

    def _update_state_diagram(self):
        self.graphics_scene.clear()
        if self.current_agent and self.current_agent.state_model:
            diagram_scene = StateDiagramScene(self.current_agent.state_model)
            self.graphics_view.setScene(diagram_scene)
            self.graphics_scene = diagram_scene # Update reference
            self.graphics_view.fitInView(diagram_scene.sceneRect(), Qt.KeepAspectRatio)
        else:
            self.graphics_view.setScene(QGraphicsScene())
            self.graphics_scene = self.graphics_view.scene() # Update reference
            
            # FIX 2: Correct way to add colored text
            no_state_text = self.graphics_scene.addText("No State Model Defined", QFont("Arial", 14))
            no_state_text.setDefaultTextColor(Qt.gray)

    def _load_sample_data(self):
        sample = """
---
identity:
  name: "PatternBot"
  version: "1.0.0"
  description: "An agent using NFA"
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
    - from: "processing"
      on: "complete"
      to: "listening"
    - from: "alerting"
      on: "acknowledge"
      to: "listening"
    - from: "processing"
      on: "error"
      to: "processing"

tools:
  - name: "console"
    type: "function"
---
# Instructions
You are a PatternBot. Watch the data stream and react using your state model.
When in 'processing', analyze the data. If you see an error, retry.
"""
        self.code_editor.setPlainText(sample)
        self.parse_content()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AgentMLStudio()
    window.show()
    sys.exit(app.exec())