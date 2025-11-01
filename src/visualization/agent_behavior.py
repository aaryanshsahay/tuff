"""
Agent behavior visualization - embedded in the game window using Pygame
Shows suspect nodes, personality states, information flow, orchestrator influence,
and conversation traces with feedback loops
"""

import pygame
import math


class AgentNode:
    """Represents a suspect as a node in the network"""

    def __init__(self, suspect_name, suspect_data, position):
        self.name = suspect_name
        self.suspect_data = suspect_data
        self.position = position

        # Visual properties
        self.radius = 30
        self.color = (100, 150, 255)  # Default blue
        self.border_color = (200, 200, 200)
        self.border_width = 2

        # Animation
        self.is_interacting = False
        self.interaction_timer = 0
        self.blink_timer = 0

        # State
        self.personality_state = {"Anxious": 3, "Moody": 3, "Trust": 3}
        self.previous_personality = {"Anxious": 3, "Moody": 3, "Trust": 3}

        # Personality change indicators
        self.personality_change_timer = 0
        self.personality_changes = {}
        self.has_personality_change = False  # Flag for blinking border

        # Conversation trace
        self.conversation_trace = []  # List of messages in this conversation

    def update(self):
        """Update node animation state"""
        self.blink_timer = (self.blink_timer + 1) % 60

        if self.is_interacting:
            self.interaction_timer -= 1
            if self.interaction_timer <= 0:
                self.is_interacting = False
                self.border_color = (200, 200, 200)
                self.border_width = 2

        # Update personality change timer
        if self.personality_change_timer > 0:
            self.personality_change_timer -= 1
        else:
            self.has_personality_change = False

        # Update color based on personality
        self._update_color_from_personality()

    def _update_color_from_personality(self):
        """Change node color based on personality state"""
        anxiety = self.personality_state.get("Anxious", 3)
        mood = self.personality_state.get("Moody", 3)
        trust = self.personality_state.get("Trust", 3)

        # Calculate color based on personality mix
        r = int(100 + anxiety * 20)
        g = int(100 + trust * 20)
        b = int(100 + (5 - mood) * 20)

        self.color = (
            min(255, r),
            min(255, g),
            min(255, b)
        )

    def set_interacting(self, duration=30):
        """Mark this node as currently interacting"""
        self.is_interacting = True
        self.interaction_timer = duration
        self.border_color = (255, 255, 0)
        self.border_width = 4

    def update_personality(self, new_personality_state):
        """Update personality and track what changed"""
        self.previous_personality = self.personality_state.copy()
        self.personality_state = new_personality_state.copy()

        # Track which traits changed
        self.personality_changes = {}
        for trait in ["Anxious", "Moody", "Trust"]:
            prev = self.previous_personality.get(trait, 3)
            curr = self.personality_state.get(trait, 3)
            if prev != curr:
                self.personality_changes[trait] = curr - prev

        # Show personality change indicator
        if self.personality_changes:
            self.personality_change_timer = 30
            self.has_personality_change = True

    def add_conversation_trace(self, message_type, content=""):
        """Add a trace to show conversation history"""
        self.conversation_trace.append({
            "type": message_type,  # "question", "response", "analysis"
            "content": content,
            "timestamp": len(self.conversation_trace)
        })

    def draw(self, surface):
        """Draw the node"""
        # Draw outer glow if interacting
        if self.is_interacting:
            glow_radius = self.radius + 8 + (3 * math.sin(self.blink_timer * 0.1))
            pygame.draw.circle(surface, (255, 255, 100), self.position, int(glow_radius), 2)

        # Draw main circle
        pygame.draw.circle(surface, self.color, self.position, self.radius)

        # Draw blinking border for personality changes (thick yellow, prominent)
        if self.has_personality_change:
            # Blinking effect - cycles every 20 frames: 10 on, 10 off
            if (self.blink_timer % 20) < 10:  # Visible for 10 frames, invisible for 10 frames
                pygame.draw.circle(surface, (255, 255, 0), self.position, self.radius, 5)  # Thick yellow blink

        # Draw normal border
        pygame.draw.circle(surface, self.border_color, self.position, self.radius, self.border_width)

        # Draw personality change indicators
        if self.personality_change_timer > 0:
            self._draw_personality_indicators(surface)

        # Draw name label
        font = pygame.font.Font(None, 14)
        name_text = font.render(self.name[:3].upper(), True, (255, 255, 255))
        name_x = self.position[0] - name_text.get_width() // 2
        name_y = self.position[1] - name_text.get_height() // 2
        surface.blit(name_text, (name_x, name_y))

    def _draw_personality_indicators(self, surface):
        """Draw small indicators showing personality changes"""
        font = pygame.font.Font(None, 10)
        y_offset = -45
        for trait, change in self.personality_changes.items():
            if change > 0:
                color = (0, 255, 0)
                symbol = "↑"
            else:
                color = (255, 0, 0)
                symbol = "↓"

            abbr = {"Anxious": "A", "Moody": "M", "Trust": "T"}.get(trait, "?")
            text = f"{abbr}{symbol}"

            indicator_text = font.render(text, True, color)
            surface.blit(indicator_text, (self.position[0] - 8, self.position[1] + y_offset))
            y_offset += 10

    def get_personality_string(self):
        """Get personality state as string"""
        anxiety = self.personality_state.get("Anxious", 3)
        mood = self.personality_state.get("Moody", 3)
        trust = self.personality_state.get("Trust", 3)
        return f"A:{anxiety} M:{mood} T:{trust}"


class RelationshipConnection:
    """Represents a relationship between two suspects"""

    def __init__(self, from_node, to_node, relationship_type):
        self.from_node = from_node
        self.to_node = to_node
        self.relationship_type = relationship_type

        self.color = self._get_color_from_type()
        self.is_active = False
        self.active_timer = 0
        self.thickness = 1

        self.info_flow_active = False
        self.info_flow_timer = 0
        self.info_flow_progress = 0

    def _get_color_from_type(self):
        """Get color based on relationship type"""
        color_map = {
            "Close Friend": (100, 200, 100),
            "Romantic Partner": (255, 100, 150),
            "Enemy": (200, 50, 50),
            "Rival": (150, 100, 200),
            "Business Partner": (100, 150, 255),
            "Acquaintance": (150, 150, 150),
            "Family Member": (200, 150, 100),
        }
        return color_map.get(self.relationship_type, (150, 150, 150))

    def set_active(self, duration=30):
        """Highlight this connection as active"""
        self.is_active = True
        self.active_timer = duration
        self.thickness = 3

    def set_info_flow(self, duration=60):
        """Animate information flowing through this connection"""
        self.info_flow_active = True
        self.info_flow_timer = duration

    def update(self):
        """Update connection animation"""
        if self.is_active:
            self.active_timer -= 1
            if self.active_timer <= 0:
                self.is_active = False
                self.thickness = 1

        if self.info_flow_active:
            self.info_flow_timer -= 1
            self.info_flow_progress = (60 - self.info_flow_timer) / 60.0
            if self.info_flow_timer <= 0:
                self.info_flow_active = False

    def draw(self, surface):
        """Draw the connection line"""
        if self.is_active:
            for i in range(3):
                glow_color = tuple(int(c * (1 - i * 0.2)) for c in self.color)
                glow_thickness = max(1, self.thickness - i)
                pygame.draw.line(
                    surface,
                    glow_color,
                    self.from_node.position,
                    self.to_node.position,
                    glow_thickness
                )
        else:
            pygame.draw.line(
                surface,
                self.color,
                self.from_node.position,
                self.to_node.position,
                self.thickness
            )

        # Draw information flow animation
        if self.info_flow_active:
            self._draw_info_flow(surface)

    def _draw_info_flow(self, surface):
        """Draw animated information flowing through connection"""
        start_x, start_y = self.from_node.position
        end_x, end_y = self.to_node.position

        current_x = start_x + (end_x - start_x) * self.info_flow_progress
        current_y = start_y + (end_y - start_y) * self.info_flow_progress

        flow_color = (255, 255, 100)
        pygame.draw.circle(surface, flow_color, (int(current_x), int(current_y)), 3)


class OrchestratorNode:
    """Represents the narrative orchestrator/master agent"""

    def __init__(self, position):
        self.position = position
        self.radius = 35
        self.color = (200, 100, 255)
        self.border_color = (255, 255, 255)
        self.border_width = 3

        self.pulse_timer = 0
        self.is_active = False
        self.active_timer = 0

    def update(self):
        """Update orchestrator animation"""
        self.pulse_timer = (self.pulse_timer + 1) % 60
        if self.is_active:
            self.active_timer -= 1
            if self.active_timer <= 0:
                self.is_active = False

    def set_active(self, duration=30):
        """Mark orchestrator as active"""
        self.is_active = True
        self.active_timer = duration

    def draw(self, surface):
        """Draw the orchestrator node"""
        pulse_radius = self.radius + 5 * math.sin(self.pulse_timer * 0.1)

        if self.is_active:
            pygame.draw.circle(surface, (200, 100, 255), self.position, int(pulse_radius), 2)

        pygame.draw.circle(surface, self.color, self.position, self.radius)
        pygame.draw.circle(surface, self.border_color, self.position, self.radius, self.border_width)

        font = pygame.font.Font(None, 12)
        label_text = font.render("ORCHESTRATOR", True, (255, 255, 255))
        label_x = self.position[0] - label_text.get_width() // 2
        label_y = self.position[1] - label_text.get_height() // 2
        surface.blit(label_text, (label_x, label_y + 5))


class ArrowConnection:
    """Animated arrow showing data flow from orchestrator to agents"""

    def __init__(self, from_node, to_node, arrow_type="briefing"):
        self.from_node = from_node
        self.to_node = to_node
        self.arrow_type = arrow_type  # "briefing", "feedback", or "communication"
        self.is_active = False
        self.active_timer = 0
        self.active_timer_duration = 0
        self.progress = 0

        # Colors based on type
        if arrow_type == "briefing":
            self.color = (200, 100, 255)  # Purple: orchestrator -> agent
        elif arrow_type == "feedback":
            self.color = (100, 255, 200)  # Cyan: agent -> orchestrator
        else:  # communication
            self.color = (100, 200, 100)  # Green: agent -> agent

    def set_active(self, duration=180):
        """Activate the arrow (duration in frames, default 180 = 3 seconds at 60 FPS)"""
        self.is_active = True
        self.active_timer = duration
        self.active_timer_duration = duration

    def update(self):
        """Update arrow animation"""
        if self.is_active:
            self.active_timer -= 1
            self.progress = (self.active_timer_duration - self.active_timer) / self.active_timer_duration
            if self.active_timer <= 0:
                self.is_active = False

    def draw(self, surface):
        """Draw arrow with animated progress"""
        if not self.is_active:
            return

        start_x, start_y = self.from_node.position
        end_x, end_y = self.to_node.position

        # Calculate arrow position
        arrow_x = start_x + (end_x - start_x) * self.progress
        arrow_y = start_y + (end_y - start_y) * self.progress

        # Draw line
        pygame.draw.line(surface, self.color, (start_x, start_y), (arrow_x, arrow_y), 2)

        # Draw arrow head
        angle = math.atan2(end_y - start_y, end_x - start_x)
        arrow_size = 8

        # Arrow tip
        tip_x, tip_y = int(arrow_x), int(arrow_y)

        # Arrow wings
        wing1_x = int(arrow_x - arrow_size * math.cos(angle - math.pi / 6))
        wing1_y = int(arrow_y - arrow_size * math.sin(angle - math.pi / 6))
        wing2_x = int(arrow_x - arrow_size * math.cos(angle + math.pi / 6))
        wing2_y = int(arrow_y - arrow_size * math.sin(angle + math.pi / 6))

        # Draw arrow head
        pygame.draw.polygon(surface, self.color, [(tip_x, tip_y), (wing1_x, wing1_y), (wing2_x, wing2_y)])


class OrchestratorConnection:
    """Connection from orchestrator to suspect nodes (with arrows)"""

    def __init__(self, from_node, to_node):
        self.from_node = from_node
        self.to_node = to_node
        self.is_active = False
        self.active_timer = 0

    def set_active(self, duration=30):
        """Highlight this connection"""
        self.is_active = True
        self.active_timer = duration

    def update(self):
        """Update animation"""
        if self.is_active:
            self.active_timer -= 1
            if self.active_timer <= 0:
                self.is_active = False

    def draw(self, surface):
        """Draw dashed line to show orchestrator guidance"""
        if not self.is_active:
            return

        start_x, start_y = self.from_node.position
        end_x, end_y = self.to_node.position

        dash_length = 5
        gap_length = 5
        distance = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
        num_dashes = int(distance / (dash_length + gap_length))

        for i in range(num_dashes):
            progress = (dash_length + gap_length) * i / distance
            next_progress = progress + dash_length / distance

            p1_x = start_x + (end_x - start_x) * progress
            p1_y = start_y + (end_y - start_y) * progress
            p2_x = start_x + (end_x - start_x) * next_progress
            p2_y = start_y + (end_y - start_y) * next_progress

            pygame.draw.line(surface, (200, 100, 255), (int(p1_x), int(p1_y)), (int(p2_x), int(p2_y)), 2)


class ConversationTrace:
    """Visual trace showing conversation flow and updates"""

    def __init__(self, suspect_node, trace_type="conversation"):
        self.suspect_node = suspect_node
        self.trace_type = trace_type  # "conversation", "personality_update", "feedback"
        self.lifetime = 120  # frames
        self.age = 0

    def update(self):
        """Update trace lifetime"""
        self.age += 1
        return self.age < self.lifetime

    def draw(self, surface, y_offset):
        """Draw trace indicator above node"""
        # Fade out as it gets older
        alpha_progress = 1.0 - (self.age / self.lifetime)

        # Color based on type
        if self.trace_type == "conversation":
            color = (100, 200, 255)
        elif self.trace_type == "personality_update":
            color = (255, 200, 100)
        else:  # feedback
            color = (100, 255, 200)

        # Draw trace circle
        radius = 4
        trace_x = self.suspect_node.position[0]
        trace_y = self.suspect_node.position[1] - self.suspect_node.radius - 20 - y_offset

        # Fading circle
        faded_color = tuple(int(c * alpha_progress) for c in color)
        pygame.draw.circle(surface, faded_color, (trace_x, trace_y), radius, 1)


class AgentBehaviorVisualizer:
    """Embedded visualization showing agent network in game window"""

    def __init__(self, suspects, relationships, start_x, start_y, width, height):
        self.suspects = suspects
        self.relationships = relationships

        self.start_x = start_x
        self.start_y = start_y
        self.width = width
        self.height = height

        self.nodes = {}
        self.connections = []
        self.orchestrator = None
        self.orchestrator_connections = []
        self.briefing_arrows = []
        self.feedback_arrows = []
        self.conversation_traces = []

        self._initialize_nodes()
        self._initialize_connections(relationships)
        self._initialize_orchestrator()

    def _initialize_nodes(self):
        """Create nodes for all suspects"""
        suspect_names = [
            s for s in self.suspects.keys() if not self.suspects[s]["is_victim"]
        ]
        num_suspects = len(suspect_names)

        center_x = self.start_x + self.width // 2
        center_y = self.start_y + self.height // 2 + 20
        radius = min(self.width, self.height) // 3.5

        for i, suspect_name in enumerate(suspect_names):
            angle = (2 * math.pi * i) / num_suspects
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))

            node = AgentNode(suspect_name, self.suspects[suspect_name], (x, y))
            self.nodes[suspect_name] = node

    def _initialize_orchestrator(self):
        """Create orchestrator node in the center"""
        center_x = self.start_x + self.width // 2
        center_y = self.start_y + self.height // 2 + 20
        self.orchestrator = OrchestratorNode((int(center_x), int(center_y)))

        for suspect_name in self.nodes.keys():
            conn = OrchestratorConnection(self.orchestrator, self.nodes[suspect_name])
            self.orchestrator_connections.append(conn)

    def _initialize_connections(self, relationships):
        """Create connections between suspects"""
        seen_pairs = set()

        for pair, rel_type in relationships.items():
            names = pair.split("_")
            if len(names) == 2:
                name1, name2 = names[0], names[1]

                pair_key = tuple(sorted([name1, name2]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                if name1 in self.nodes and name2 in self.nodes:
                    connection = RelationshipConnection(
                        self.nodes[name1],
                        self.nodes[name2],
                        rel_type
                    )
                    self.connections.append(connection)

    def send_interaction(self, suspect_name, duration=60):
        """Notify of suspect interaction"""
        if suspect_name in self.nodes:
            self.nodes[suspect_name].set_interacting(duration)
            self.conversation_traces.append(ConversationTrace(self.nodes[suspect_name], "conversation"))

    def send_personality_update(self, suspect_name, personality_state):
        """Update personality and show trace"""
        if suspect_name in self.nodes:
            self.nodes[suspect_name].update_personality(personality_state)
            self.conversation_traces.append(ConversationTrace(self.nodes[suspect_name], "personality_update"))

    def send_orchestrator_briefing(self, suspect_name, duration=180):
        """Show orchestrator sending briefing to suspect (default 180 frames = 3 seconds)"""
        self.orchestrator.set_active(duration)

        # Create arrow from orchestrator to suspect
        arrow = ArrowConnection(self.orchestrator, self.nodes[suspect_name], "briefing")
        arrow.set_active(duration)
        self.briefing_arrows.append(arrow)

        # Update orchestrator connection
        for conn in self.orchestrator_connections:
            if conn.to_node.name == suspect_name:
                conn.set_active(duration)

    def send_feedback_to_orchestrator(self, suspect_name, duration=180):
        """Show feedback from suspect to orchestrator (default 180 frames = 3 seconds)"""
        self.orchestrator.set_active(duration)

        # Create arrow from suspect to orchestrator (feedback)
        if suspect_name in self.nodes:
            arrow = ArrowConnection(self.nodes[suspect_name], self.orchestrator, "feedback")
            arrow.set_active(duration)
            self.feedback_arrows.append(arrow)
            self.conversation_traces.append(ConversationTrace(self.nodes[suspect_name], "feedback"))

    def send_agent_communication(self, from_suspect, to_suspect, duration=120):
        """Show communication between two agents (different color from orchestrator arrows)"""
        if from_suspect in self.nodes and to_suspect in self.nodes:
            # Create a green arrow for agent-to-agent communication
            arrow = ArrowConnection(self.nodes[from_suspect], self.nodes[to_suspect], "communication")
            arrow.set_active(duration)
            self.feedback_arrows.append(arrow)  # Reuse feedback arrows list for display

    def send_relationship_interaction(self, suspect1, suspect2, duration=60):
        """Highlight relationship between two suspects"""
        for conn in self.connections:
            if ((conn.from_node.name == suspect1 and conn.to_node.name == suspect2) or
                (conn.from_node.name == suspect2 and conn.to_node.name == suspect1)):
                conn.set_active(duration)

    def send_info_flow(self, suspect1, suspect2, duration=60):
        """Animate information flowing between suspects"""
        for conn in self.connections:
            if ((conn.from_node.name == suspect1 and conn.to_node.name == suspect2) or
                (conn.from_node.name == suspect2 and conn.to_node.name == suspect1)):
                conn.set_info_flow(duration)

    def update(self):
        """Update all nodes and connections"""
        for node in self.nodes.values():
            node.update()

        for connection in self.connections:
            connection.update()

        if self.orchestrator:
            self.orchestrator.update()

        for conn in self.orchestrator_connections:
            conn.update()

        # Update arrows
        for arrow in self.briefing_arrows[:]:
            arrow.update()
            if not arrow.is_active:
                self.briefing_arrows.remove(arrow)

        for arrow in self.feedback_arrows[:]:
            arrow.update()
            if not arrow.is_active:
                self.feedback_arrows.remove(arrow)

        # Update traces
        for trace in self.conversation_traces[:]:
            if not trace.update():
                self.conversation_traces.remove(trace)

    def draw(self, surface):
        """Draw the visualization"""
        pygame.draw.rect(surface, (30, 30, 40), (self.start_x, self.start_y, self.width, self.height))
        pygame.draw.rect(surface, (100, 100, 120), (self.start_x, self.start_y, self.width, self.height), 2)

        title_font = pygame.font.Font(None, 16)
        title_text = title_font.render("AGENT NETWORK", True, (200, 200, 200))
        surface.blit(title_text, (self.start_x + 10, self.start_y + 5))

        # Draw orchestrator connections
        for conn in self.orchestrator_connections:
            conn.draw(surface)

        # Draw suspect connections
        for connection in self.connections:
            connection.draw(surface)

        # Draw orchestrator
        if self.orchestrator:
            self.orchestrator.draw(surface)

        # Draw briefing arrows (orchestrator -> agents)
        for arrow in self.briefing_arrows:
            arrow.draw(surface)

        # Draw feedback arrows (agents -> orchestrator)
        for arrow in self.feedback_arrows:
            arrow.draw(surface)

        # Draw nodes
        for node in self.nodes.values():
            node.draw(surface)

        # Draw conversation traces above nodes
        trace_offset = 0
        for trace in self.conversation_traces:
            trace.draw(surface, trace_offset)
            trace_offset += 8

        self._draw_info_panel(surface)

    def _draw_info_panel(self, surface):
        """Draw information panel"""
        info_y = self.start_y + self.height - 120
        info_x = self.start_x + 10

        font_small = pygame.font.Font(None, 12)
        font_large = pygame.font.Font(None, 14)

        label_text = font_large.render("Personality: A(nxious) M(oody) T(rust) | Blinking = Change", True, (200, 200, 200))
        surface.blit(label_text, (info_x, info_y))

        legend_y = info_y + 18
        legend_items = [
            ("Friend", (100, 200, 100)),
            ("Romantic", (255, 100, 150)),
            ("Enemy", (200, 50, 50)),
            ("Rival", (150, 100, 200)),
        ]

        for i, (label, color) in enumerate(legend_items):
            x = info_x + (i % 2) * 110
            y = legend_y + (i // 2) * 16

            pygame.draw.line(surface, color, (x, y + 5), (x + 12, y + 5), 3)
            label_text = font_small.render(label, True, (200, 200, 200))
            surface.blit(label_text, (x + 16, y))

        info_text = font_large.render("Purple arrow: Briefing → agents", True, (200, 100, 255))
        surface.blit(info_text, (info_x, legend_y + 38))

        info_text2 = font_large.render("Cyan arrow: Feedback → orchestrator", True, (100, 255, 200))
        surface.blit(info_text2, (info_x, legend_y + 54))

        info_text3 = font_large.render("Green arrow: Agent → Agent (gossip)", True, (100, 200, 100))
        surface.blit(info_text3, (info_x, legend_y + 70))
