"""
Agent-to-agent communication system for chaos mode.
Handles inter-agent conversations and information sharing based on relationships.
"""

import os
import threading
from dotenv import load_dotenv
from openai import OpenAI
from .hyperspell_context import update_agent_gossip, get_gossip_summary

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AgentCommunicationManager:
    """
    Manages communication between agents after detective interrogations.
    Agents share information based on their relationships and personalities.
    """

    def __init__(self, agents_dict, relationships, case_state, visualizer=None, orchestrator=None):
        """
        Args:
            agents_dict: Dict of agent_name -> SuspectAgent
            relationships: Dict of relationship_pair -> relationship_type
            case_state: The case state dict
            visualizer: Optional visualization manager to show communication arrows
            orchestrator: Optional orchestrator agent to receive gossip summaries
        """
        self.agents = agents_dict
        self.relationships = relationships
        self.case_state = case_state
        self.visualizer = visualizer
        self.orchestrator = orchestrator
        self.communication_log = []

    def _get_relationship_type(self, agent1_name, agent2_name):
        """Get the relationship type between two agents"""
        for pair, rel_type in self.relationships.items():
            names = pair.split("_")
            if set(names) == {agent1_name, agent2_name}:
                return rel_type
        return None

    def _should_share_and_how(self, from_agent_name, to_agent_name, rel_type):
        """
        Determine if agent should share information based on relationship.
        Returns: (should_share: bool, truthfulness: float)
        truthfulness: 1.0 = full truth, 0.3 = partial truth/lies
        """
        if rel_type is None:
            return False, 0.0

        sharing_rules = {
            "Close Friend": (True, 0.95),
            "Romantic Partner": (True, 0.98),
            "Enemy": (True, 0.15),
            "Rival": (True, 0.35),
        }
        return sharing_rules.get(rel_type, (False, 0.0))

    def trigger_agent_communications(self, last_interrogated_suspect, detective_question, suspect_response):
        """
        Trigger communications between agents after a detective interrogation.
        Runs in background thread to prevent UI freeze.
        """
        print(f"\n🔄 CHAOS MODE: Agents are gossiping about {last_interrogated_suspect}...\n")

        interrogated_agent = self.agents.get(last_interrogated_suspect)
        if not interrogated_agent:
            return

        # Start communications in background thread
        thread = threading.Thread(
            target=self._conduct_all_communications,
            args=(last_interrogated_suspect, detective_question, suspect_response),
            daemon=True
        )
        thread.start()

    def _conduct_all_communications(self, last_interrogated_suspect, detective_question, suspect_response):
        """
        Conduct all agent communications in background.
        """
        for other_agent_name in self.agents.keys():
            if other_agent_name == last_interrogated_suspect:
                continue

            rel_type = self._get_relationship_type(last_interrogated_suspect, other_agent_name)
            should_share, truthfulness = self._should_share_and_how(last_interrogated_suspect, other_agent_name, rel_type)

            if should_share and rel_type:
                self._conduct_agent_conversation(
                    last_interrogated_suspect,
                    other_agent_name,
                    detective_question,
                    suspect_response,
                    rel_type,
                    truthfulness
                )

    def _conduct_agent_conversation(self, agent1_name, agent2_name, detective_question, agent1_response, rel_type, truthfulness):
        """
        Conduct a conversation between two agents where one shares interrogation details.
        """
        agent1 = self.agents[agent1_name]
        agent2 = self.agents[agent2_name]

        share_prompt = f"""You are {agent1_name}. You were just interrogated by a detective.

Detective asked: "{detective_question}"
You responded: "{agent1_response}"

Now you're telling {agent2_name} ({rel_type}) about it.

Your personality: Trust {agent1.personality_levels.get('Trust', 3)}/5, Anxious {agent1.personality_levels.get('Anxious', 3)}/5, Moody {agent1.personality_levels.get('Moody', 3)}/5
Truthfulness level: {truthfulness:.2f}

Tell them about the interrogation naturally (1-2 sentences). Adjust honesty to match your truthfulness level."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": share_prompt}],
                temperature=0.8,
                max_tokens=150
            )

            agent1_share = response.choices[0].message.content

            react_prompt = f"""You are {agent2_name}.

{agent1_name} ({rel_type}) just told you: "{agent1_share}"

Your personality: Trust {agent2.personality_levels.get('Trust', 3)}/5, Anxious {agent2.personality_levels.get('Anxious', 3)}/5, Moody {agent2.personality_levels.get('Moody', 3)}/5

React to what they said naturally (1-2 sentences)."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": react_prompt}],
                temperature=0.8,
                max_tokens=150
            )

            agent2_response = response.choices[0].message.content

            comm_record = {
                "from": agent1_name,
                "to": agent2_name,
                "relationship": rel_type,
                "agent1_share": agent1_share,
                "agent2_reaction": agent2_response
            }
            self.communication_log.append(comm_record)

            print(f"💬 {agent1_name} → {agent2_name}:")
            print(f"   \"{agent1_share}\"")
            print(f"   {agent2_name}: \"{agent2_response}\"\n")

            # Show visualization arrow if visualizer is available
            if self.visualizer:
                self.visualizer.send_agent_communication(agent1_name, agent2_name, duration=120)

            self._update_agent_from_conversation(agent2_name, agent1_share, agent1_name, rel_type)

        except Exception as e:
            print(f"Error in communication between {agent1_name} and {agent2_name}: {e}")

    def _update_agent_from_conversation(self, agent_name, shared_info, from_agent, rel_type):
        """
        Update agent's personality and knowledge based on conversation with another agent.
        """
        agent = self.agents.get(agent_name)
        if not agent:
            return

        # Store the gossip/shared information
        if not hasattr(agent, 'gossip_heard'):
            agent.gossip_heard = []

        agent.gossip_heard.append({
            "from": from_agent,
            "info": shared_info,
            "relationship": rel_type
        })

        print(f"📝 [DEBUG] {agent_name} now knows gossip from {from_agent}: \"{shared_info}\"")

        if rel_type == "Close Friend":
            agent.personality_levels['Trust'] = min(5, agent.personality_levels['Trust'] + 0.5)

        elif rel_type == "Romantic Partner":
            agent.personality_levels['Trust'] = min(5, agent.personality_levels['Trust'] + 0.7)

        elif rel_type == "Enemy":
            agent.personality_levels['Anxious'] = min(5, agent.personality_levels['Anxious'] + 0.5)
            agent.personality_levels['Trust'] = max(0, agent.personality_levels['Trust'] - 0.5)

        elif rel_type == "Rival":
            agent.personality_levels['Moody'] = min(5, agent.personality_levels['Moody'] + 0.3)
            agent.personality_levels['Trust'] = max(0, agent.personality_levels['Trust'] - 0.3)

        # Store gossip in Hyperspell for persistent context management
        if agent.gossip_heard:
            memory_id = update_agent_gossip(agent_name, agent.gossip_heard)

            # Retrieve the gossip summary from Hyperspell and send to orchestrator
            if memory_id and self.orchestrator:
                try:
                    memory_id, summary = get_gossip_summary(agent_name)
                    if summary:
                        # Send gossip summary to orchestrator for narrative tracking
                        self.orchestrator.record_agent_gossip(agent_name, summary)
                        print(f"📡 Sent gossip summary for {agent_name} to orchestrator")
                except Exception as e:
                    print(f"⚠️ Error sending gossip summary to orchestrator: {e}")

        # Visualize the personality update
        if self.visualizer:
            self.visualizer.send_personality_update(agent_name, agent.personality_levels)

    def get_communication_log(self):
        """Get the full log of inter-agent communications"""
        return self.communication_log
