"""
Hyperspell integration for storing and retrieving agent gossip context.
Uses Hyperspell Python SDK to manage accumulated gossip and maintain context across interrogations.
"""

import os
import uuid
from dotenv import load_dotenv
from hyperspell import Hyperspell

load_dotenv()

HYPERSPELL_API_KEY = os.getenv("HYPERSPELL_API_KEY")


class HyperspellGossipManager:
    """Manages gossip context storage and retrieval using Hyperspell"""

    def __init__(self, collection_id=None):
        """
        Initialize Hyperspell gossip manager.

        Args:
            collection_id: Optional collection ID for grouping memories.
                          If not provided, generates a new UUID for this game session.
        """
        self.client = Hyperspell(api_key=HYPERSPELL_API_KEY)
        self.collection_id = collection_id or str(uuid.uuid4())
        self.agent_memory_ids = {}  # Cache of memory IDs for agents (agent_name -> memory_id)
        print(f"🎮 Initialized Hyperspell with collection: {self.collection_id[:8]}...")

    def store_gossip(self, agent_name, gossip_list):
        """
        Store an agent's accumulated gossip in Hyperspell as a new memory.
        Each time gossip is updated, a new memory is created.

        Args:
            agent_name: Name of the agent
            gossip_list: List of gossip dictionaries with 'from', 'info', 'relationship'

        Returns:
            The memory resource ID
        """
        if not gossip_list:
            return None

        # Format gossip for Hyperspell
        gossip_text = self._format_gossip_for_storage(agent_name, gossip_list)

        try:
            # Create new memory - each update creates a new memory
            memory_status = self.client.memories.add(
                text=gossip_text,
                collection=self.collection_id
            )
            memory_id = memory_status.resource_id
            # Store the latest memory ID for this agent
            self.agent_memory_ids[agent_name] = memory_id
            print(f"✅ Created gossip memory for {agent_name} in Hyperspell (Memory ID: {memory_id})")
            return memory_id

        except Exception as e:
            print(f"❌ Error storing gossip for {agent_name}: {e}")
            return None

    def retrieve_gossip_context(self, agent_name):
        """
        Retrieve formatted gossip context for an agent from Hyperspell.

        Args:
            agent_name: Name of the agent

        Returns:
            Formatted gossip context string or empty string if not found
        """
        memory_id = self.agent_memory_ids.get(agent_name)
        if not memory_id:
            return ""

        try:
            # Query the memory from Hyperspell using search (more reliable than get)
            query_result = self.client.memories.search(query=agent_name)

            if query_result and hasattr(query_result, 'documents'):
                # Find the document that matches our resource_id
                for doc in query_result.documents:
                    if doc.resource_id == memory_id:
                        text = doc.summary if hasattr(doc, 'summary') else None
                        if text:
                            return f"\n📢 GOSSIP CONTEXT (from Hyperspell):\n{text}"

            return ""

        except Exception as e:
            print(f"⚠️ Error retrieving gossip for {agent_name}: {e}")
            return ""

    def get_gossip_summary(self, agent_name):
        """
        Search Hyperspell for the agent's gossip memory and extract the summary.

        Args:
            agent_name: Name of the agent

        Returns:
            Tuple of (memory_id, summary) or (None, None) if not found
        """
        memory_id = self.agent_memory_ids.get(agent_name)
        if not memory_id:
            return None, None

        try:
            # Search for the memory by querying agent's name
            query_result = self.client.memories.search(query=agent_name)

            if query_result and hasattr(query_result, 'documents'):
                # Find the document that matches our resource_id
                for doc in query_result.documents:
                    if doc.resource_id == memory_id:
                        summary = doc.summary if hasattr(doc, 'summary') else None
                        print(f"📝 Retrieved gossip summary for {agent_name}:")
                        print(f"   Memory ID: {memory_id}")
                        print(f"   Summary: {summary}")
                        return memory_id, summary

            return memory_id, None

        except Exception as e:
            print(f"⚠️ Error retrieving gossip summary for {agent_name}: {e}")
            return memory_id, None

    def update_gossip(self, agent_name, gossip_list):
        """
        Update an agent's gossip in Hyperspell.
        Creates a new memory with the complete updated gossip list.
        """
        return self.store_gossip(agent_name, gossip_list)

    def _format_gossip_for_storage(self, agent_name, gossip_list):
        """Format gossip data for storage in Hyperspell"""
        formatted = f"Gossip accumulated by {agent_name}:\n\n"

        # Group by source
        gossip_by_source = {}
        for gossip in gossip_list:
            from_agent = gossip.get("from", "Unknown")
            if from_agent not in gossip_by_source:
                gossip_by_source[from_agent] = []
            gossip_by_source[from_agent].append(gossip)

        # Format with context
        for from_agent, gossips in gossip_by_source.items():
            rel_type = gossips[0].get("relationship", "Unknown")
            formatted += f"From {from_agent} ({rel_type}):\n"
            for i, gossip in enumerate(gossips, 1):
                info = gossip.get("info", "")
                formatted += f"  {i}. {info}\n"
            formatted += "\n"

        return formatted


# Global instance - will be initialized when game starts
hyperspell_manager = None


def initialize_gossip_manager(collection_id=None):
    """Initialize the Hyperspell gossip manager. Call this when starting a new game."""
    global hyperspell_manager
    hyperspell_manager = HyperspellGossipManager(collection_id)
    return hyperspell_manager


def store_agent_gossip(agent_name, gossip_list):
    """Convenience function to store gossip"""
    if not hyperspell_manager:
        print("⚠️ Hyperspell not initialized. Call initialize_gossip_manager() first.")
        return None
    return hyperspell_manager.store_gossip(agent_name, gossip_list)


def get_agent_gossip_context(agent_name):
    """Convenience function to retrieve gossip context"""
    if not hyperspell_manager:
        return ""
    return hyperspell_manager.retrieve_gossip_context(agent_name)


def update_agent_gossip(agent_name, gossip_list):
    """Convenience function to update gossip"""
    if not hyperspell_manager:
        print("⚠️ Hyperspell not initialized. Call initialize_gossip_manager() first.")
        return None
    return hyperspell_manager.update_gossip(agent_name, gossip_list)


def get_gossip_summary(agent_name):
    """
    Convenience function to retrieve gossip summary and memory ID from Hyperspell.
    Returns a tuple of (memory_id, summary).
    """
    if not hyperspell_manager:
        return None, None
    return hyperspell_manager.get_gossip_summary(agent_name)
