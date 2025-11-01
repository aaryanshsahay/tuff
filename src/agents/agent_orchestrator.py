import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AgentOrchestrator:
    """
    Master orchestrator that manages narrative consistency across all suspect agents.
    Ensures that:
    1. Clues are contextually distributed (only people involved know about them)
    2. Story is coherent and leads to the murderer
    3. Agents give hints that converge toward the solution
    4. Relationships and motives are consistent
    """

    def __init__(self, case_state, suspects, relationships, clues):
        self.case_state = case_state
        self.suspects = suspects
        self.relationships = relationships
        self.clues = clues
        self.murderer = case_state["murderer"]
        self.victim = case_state["victim"]
        self.motive = case_state["murderer_motive"]

        # Build narrative context
        self.narrative_context = self._build_narrative_context()

        # Track what suspects have said across interrogations (for coherence)
        self.suspect_statements = {}  # suspect_name -> list of key statements

        # Track which clues have been revealed to the detective
        self.revealed_clues = set()  # set of clue texts that have been mentioned

        # Track interrogation history per suspect (for calculating disclosure trust)
        self.interrogation_history = {}  # suspect_name -> list of (question, response, tone)

    def _build_narrative_context(self):
        """Build rich narrative context about who knows what and why"""
        context = {
            "murderer_profile": self._analyze_murderer(),
            "victim_profile": self._analyze_victim(),
            "relationship_web": self._analyze_relationships(),
            "clue_distribution": self._analyze_clue_distribution(),
            "suspect_motives": self._analyze_suspect_motives(),
        }
        return context

    def _analyze_murderer(self):
        """Analyze the murderer's character and behavior patterns"""
        murderer = self.suspects[self.murderer]
        return {
            "name": self.murderer,
            "age": murderer["age"],
            "occupation": murderer["occupation"],
            "motive": self.motive,
            "likely_behaviors": self._get_murderer_behaviors(),
            "evidence_they_know": self._get_evidence_murderer_knows(),
        }

    def _analyze_victim(self):
        """Analyze the victim and their connections"""
        victim = self.suspects[self.victim]
        return {
            "name": self.victim,
            "age": victim["age"],
            "occupation": victim["occupation"],
            "connections": self._get_victim_connections(),
        }

    def _analyze_relationships(self):
        """Analyze the web of relationships and conflicts"""
        web = {}
        for pair, rel_type in self.relationships.items():
            web[pair] = {
                "type": rel_type,
                "tension_level": self._assess_tension(pair, rel_type),
            }
        return web

    def _analyze_clue_distribution(self):
        """Analyze which clues should be known by whom"""
        distribution = {}
        for clue in self.clues:
            clue_text = clue.get("clue", "")
            known_by = clue.get("known_by", "")
            category = clue.get("category", "")
            is_true = clue.get("is_true", False)

            # Determine who else might know this
            other_knowers = self._determine_clue_knowers(clue_text, known_by, category)

            distribution[clue_text] = {
                "primary_knower": known_by,
                "other_knowers": other_knowers,
                "is_true": is_true,
                "category": category,
                "relevance_to_solution": self._assess_clue_relevance(clue_text),
            }
        return distribution

    def _analyze_suspect_motives(self):
        """Analyze potential motives for each innocent suspect"""
        motives = {}
        for suspect_name in self.suspects.keys():
            if suspect_name != self.murderer and suspect_name != self.victim:
                motives[suspect_name] = {
                    "possible_involvement": self._assess_false_motive(suspect_name),
                    "likely_accusations": self._get_likely_accusations(suspect_name),
                }
        return motives

    def _get_murderer_behaviors(self):
        """Generate behavior patterns the murderer should exhibit"""
        return [
            "Will be defensive about their whereabouts",
            "May try to shift blame to others they don't like",
            "Will have inconsistencies if pressed hard",
            "May show nervousness when confronted with specific evidence",
            "Will protect their secret fiercely",
            "May contradict themselves under pressure",
        ]

    def _get_evidence_murderer_knows(self):
        """Determine what evidence the murderer definitely knows about"""
        evidence = []
        for clue in self.clues:
            # Murderer knows about clues that directly implicate them or are crucial to the crime
            if clue.get("known_by") == self.murderer or clue.get("is_true"):
                evidence.append(clue.get("clue", ""))
        return evidence

    def _get_victim_connections(self):
        """Get all connections the victim had"""
        connections = []
        for pair, rel_type in self.relationships.items():
            names = pair.split("_")
            if self.victim in names:
                other = names[0] if names[1] == self.victim else names[1]
                connections.append({"person": other, "relationship": rel_type})
        return connections

    def _assess_tension(self, pair, rel_type):
        """Assess the tension level in a relationship"""
        negative_rels = ["Rival", "Enemy"]
        if rel_type in negative_rels:
            return "high"
        elif rel_type in ["Close Friend", "Romantic Partner"]:
            return "low"
        else:
            return "medium"

    def _determine_clue_knowers(self, clue_text, primary_knower, category):
        """Determine who else might know about a clue besides the primary knower"""
        other_knowers = []

        # Romantic/relationship clues might be known by the partner
        if "romantic" in clue_text.lower() or "love" in clue_text.lower():
            for pair, rel_type in self.relationships.items():
                if rel_type == "Romantic Partner" and primary_knower in pair:
                    names = pair.split("_")
                    other = names[0] if names[1] == primary_knower else names[1]
                    other_knowers.append(other)

        # Close friends might know secrets
        if category == "relationship":
            for pair, rel_type in self.relationships.items():
                if rel_type == "Close Friend" and primary_knower in pair:
                    names = pair.split("_")
                    other = names[0] if names[1] == primary_knower else names[1]
                    other_knowers.append(other)

        # The murderer knows about evidence they created
        if self.murderer not in other_knowers:
            other_knowers.append(self.murderer)

        return list(set(other_knowers))

    def _assess_clue_relevance(self, clue_text):
        """Assess how relevant a clue is to solving the crime"""
        # Clues about the murderer/victim relationship are highly relevant
        if self.murderer.lower() in clue_text.lower() or self.victim.lower() in clue_text.lower():
            return "high"
        # Clues about motive are highly relevant
        if any(word in clue_text.lower() for word in ["motive", "reason", "why", "because"]):
            return "high"
        # Clues about whereabouts/alibis are relevant
        if any(word in clue_text.lower() for word in ["saw", "together", "alone", "time"]):
            return "medium"
        # Other clues are lower relevance
        return "low"

    def _assess_false_motive(self, suspect_name):
        """Assess if an innocent suspect might appear guilty"""
        suspect = self.suspects[suspect_name]
        false_motive = "Low"

        # Check if they have conflict with victim
        for pair, rel_type in self.relationships.items():
            if suspect_name in pair and self.victim in pair:
                if rel_type in ["Rival", "Enemy"]:
                    false_motive = "High"
                elif rel_type in ["Acquaintance"]:
                    false_motive = "Medium"

        return false_motive

    def _get_likely_accusations(self, suspect_name):
        """Get what accusations this innocent suspect might face"""
        accusations = []

        # Check for conflicts with victim
        for pair, rel_type in self.relationships.items():
            if suspect_name in pair and self.victim in pair:
                if rel_type in ["Rival", "Enemy"]:
                    accusations.append(f"Had conflict with {self.victim}")

        # Check if they might know damaging information
        for clue in self.clues:
            if clue.get("known_by") == suspect_name and not clue.get("is_true"):
                accusations.append(f"Spreading false rumors")

        return accusations

    def get_suspect_briefing(self, suspect_name):
        """
        Get a briefing for a specific suspect about what they should know
        and how they should behave in interviews
        """
        briefing = {
            "suspect_name": suspect_name,
            "role": self._determine_role(suspect_name),
            "what_they_know": self._get_suspect_knowledge(suspect_name),
            "what_they_should_hide": self._get_suspect_secrets(suspect_name),
            "relationships_context": self._get_relationship_context(suspect_name),
            "likely_questions": self._predict_likely_questions(suspect_name),
            "defensive_topics": self._identify_defensive_topics(suspect_name),
            "hintable_facts": self._generate_hintable_facts(suspect_name),
        }
        return briefing

    def _determine_role(self, suspect_name):
        """Determine the suspect's role in the narrative"""
        if suspect_name == self.murderer:
            return "murderer"
        elif suspect_name == self.victim:
            return "victim"
        else:
            return "innocent_suspect"

    def _get_suspect_knowledge(self, suspect_name):
        """Get what a suspect should know"""
        knowledge = []

        # They know their own alibi
        knowledge.append(f"Their alibi: {self.suspects[suspect_name]['alibi']}")

        # They know about clues they're listed as knowing
        for clue in self.clues:
            if clue.get("known_by") == suspect_name:
                knowledge.append(f"Clue: {clue.get('clue', '')}")

        # They might know about related clues through relationships
        for pair, rel_type in self.relationships.items():
            if suspect_name in pair and rel_type in ["Close Friend", "Romantic Partner"]:
                other = pair.split("_")[0] if pair.split("_")[1] == suspect_name else pair.split("_")[1]
                for clue in self.clues:
                    if clue.get("known_by") == other:
                        knowledge.append(f"Might know through {other}: {clue.get('clue', '')}")

        return knowledge

    def _get_suspect_secrets(self, suspect_name):
        """Get what a suspect should try to hide"""
        secrets = []

        # Murderer hides everything about the crime
        if suspect_name == self.murderer:
            secrets.append(f"Their guilt in killing {self.victim}")
            secrets.append(f"Their motive: {self.motive}")
            for clue in self.clues:
                if clue.get("is_true") and clue.get("known_by") == suspect_name:
                    secrets.append(f"Evidence: {clue.get('clue', '')}")

        # Everyone hides things that might incriminate them
        for clue in self.clues:
            if clue.get("known_by") == suspect_name and not clue.get("is_true"):
                secrets.append(f"False rumor: {clue.get('clue', '')}")

        return secrets

    def _get_relationship_context(self, suspect_name):
        """Get relationship context for a suspect"""
        context = {}
        for pair, rel_type in self.relationships.items():
            if suspect_name in pair:
                other = pair.split("_")[0] if pair.split("_")[1] == suspect_name else pair.split("_")[1]
                context[other] = rel_type
        return context

    def _predict_likely_questions(self, suspect_name):
        """Predict what questions the detective might ask"""
        questions = [
            f"Where were you when {self.victim} was killed?",
            f"What's your relationship with {self.victim}?",
            f"Did you see anyone suspicious?",
            f"What do you know about {self.victim}?",
        ]

        # Add motive-specific questions
        if "jealousy" in self.motive.lower():
            for pair, rel_type in self.relationships.items():
                if rel_type == "Romantic Partner":
                    questions.append(f"What's your relationship status?")

        return questions

    def _identify_defensive_topics(self, suspect_name):
        """Identify topics the suspect will be defensive about"""
        defensive = []

        # Topics related to their role in the crime
        if suspect_name == self.murderer:
            defensive.append(self.victim)
            defensive.append("alibi")
            defensive.append("whereabouts")

        # Topics related to accusations against them
        for false_motive in self._get_likely_accusations(suspect_name):
            defensive.append(false_motive)

        return defensive

    def _generate_hintable_facts(self, suspect_name):
        """
        Use LLM to generate 2-3 contextually relevant hintable facts for this suspect.
        These are facts they know about and might reveal if questioned correctly.
        """
        suspect = self.suspects[suspect_name]
        role = self._determine_role(suspect_name)

        # Build context about this suspect
        context = f"""
SUSPECT: {suspect_name} ({suspect['age']} year old {suspect['gender']} {suspect['occupation']})
ROLE: {role.upper()}
VICTIM: {self.victim}
MURDERER: {self.murderer}
MOTIVE: {self.case_state.get('murderer_motive', 'unknown')}

RELATIONSHIPS WITH OTHER SUSPECTS:
"""
        for pair, rel_type in self.relationships.items():
            if suspect_name in pair:
                other = pair.split("_")[0] if pair.split("_")[1] == suspect_name else pair.split("_")[1]
                context += f"  - {other}: {rel_type}\n"

        context += f"\nKNOWN CLUES:\n"
        for clue in self.clues:
            if clue.get("known_by") == suspect_name:
                context += f"  - {clue.get('clue', '')}\n"

        prompt = f"""You are a detective briefing assistant. Generate 2-3 specific, hintable facts that {suspect_name} might reveal during interrogation if the detective asks the right questions or treats them well.

{context}

These hintable facts should be:
1. CONTEXTUALLY RELEVANT: Based on their relationships, role, and what they know
2. SPECIFIC: Not vague - include names, times, or concrete details when possible
3. REVEALABLE: Things they would naturally know and might slip up about
4. USEFUL: Facts that would help solve the mystery (clues, observations, suspicious behavior)

For a {role}:
- If MURDERER: Include details they might slip up about (location, time, interactions with victim)
- If INNOCENT: Include gossip about others, suspicious observations, relationship conflicts

Return ONLY a JSON array of 2-3 facts (strings), no other text. Example format:
["saw Lisa leave study at 11:45pm", "heard arguing between James and victim", "found key to study room"]
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )

            import json
            facts_json = response.choices[0].message.content.strip()
            hintable_facts = json.loads(facts_json)
            return hintable_facts if isinstance(hintable_facts, list) else []
        except Exception as e:
            # Fallback: return empty list if generation fails
            return []

    def record_suspect_response(self, suspect_name, question, response, personality_state):
        """
        Record a suspect's response to the detective's question.
        This tracks what they've said for consistency checking and narrative updates.
        """
        if suspect_name not in self.interrogation_history:
            self.interrogation_history[suspect_name] = []

        interaction_record = {
            "question": question,
            "response": response,
            "personality_state": personality_state.copy() if personality_state else {},
        }

        self.interrogation_history[suspect_name].append(interaction_record)

        # Extract key statements from response
        if suspect_name not in self.suspect_statements:
            self.suspect_statements[suspect_name] = []

        # Store the full response as a statement
        self.suspect_statements[suspect_name].append({
            "statement": response,
            "question_context": question,
            "timestamp": len(self.interrogation_history[suspect_name])
        })

    def record_revealed_clue(self, clue_text):
        """
        Record that a clue has been revealed to the detective by a suspect.
        This tracks what information has been disclosed.
        """
        self.revealed_clues.add(clue_text)

    def record_agent_gossip(self, agent_name, gossip_summary):
        """
        Record gossip/memory summary retrieved from Hyperspell.
        This tracks what agents have been saying to each other.

        Args:
            agent_name: Name of the agent whose gossip was recorded
            gossip_summary: Summary of the gossip from Hyperspell
        """
        if not hasattr(self, 'agent_gossip_summaries'):
            self.agent_gossip_summaries = {}

        if agent_name not in self.agent_gossip_summaries:
            self.agent_gossip_summaries[agent_name] = []

        self.agent_gossip_summaries[agent_name].append(gossip_summary)
        print(f"✅ Recorded gossip summary for {agent_name} in orchestrator")
        print(f"   Summary: {gossip_summary}")

    def get_agent_gossip_summaries(self, agent_name):
        """
        Get all gossip summaries recorded for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of gossip summaries or empty list if none found
        """
        if not hasattr(self, 'agent_gossip_summaries'):
            return []
        return self.agent_gossip_summaries.get(agent_name, [])

    def get_contradiction_analysis(self, suspect_name):
        """
        Analyze a suspect's statements for contradictions.
        Returns a dict with contradiction details if any are found.
        """
        if suspect_name not in self.suspect_statements:
            return None

        statements = self.suspect_statements[suspect_name]
        if len(statements) < 2:
            return None  # Need at least 2 statements to find contradictions

        contradictions = {
            "suspect_name": suspect_name,
            "total_statements": len(statements),
            "contradictions": [],
            "consistency_score": 0.0  # 0.0 = contradictory, 1.0 = fully consistent
        }

        # Compare each statement with previous ones for obvious contradictions
        for i, statement in enumerate(statements[1:], start=1):
            # This is a simplified check - in a real system you'd use LLM to detect semantic contradictions
            prev_statement = statements[i - 1]

            # Check for keyword contradictions (very basic)
            curr_keywords = set(statement["statement"].lower().split())
            prev_keywords = set(prev_statement["statement"].lower().split())

            # If current statement explicitly contradicts previous context
            if "didn't" in statement["statement"].lower() and statement["question_context"] in prev_statement["statement"]:
                contradictions["contradictions"].append({
                    "previous": prev_statement["statement"],
                    "current": statement["statement"],
                    "context": statement["question_context"]
                })

        # Calculate consistency score
        if contradictions["contradictions"]:
            contradictions["consistency_score"] = max(0, 1.0 - len(contradictions["contradictions"]) * 0.25)
        else:
            contradictions["consistency_score"] = 1.0

        return contradictions if contradictions["contradictions"] else None

    def get_suspect_interrogation_history(self, suspect_name):
        """
        Get the complete interrogation history for a suspect.
        Useful for seeing how they've responded across multiple questions.
        """
        if suspect_name not in self.interrogation_history:
            return []
        return self.interrogation_history[suspect_name]

    def get_revealed_clues(self):
        """Get all clues that have been revealed to the detective."""
        return list(self.revealed_clues)

    def get_orchestrator_state(self):
        """
        Get the current state of the orchestrator's tracking data.
        Useful for debugging and understanding narrative state.
        """
        return {
            "revealed_clues": list(self.revealed_clues),
            "suspect_statements": {name: len(stmts) for name, stmts in self.suspect_statements.items()},
            "interrogation_count": {name: len(hist) for name, hist in self.interrogation_history.items()},
        }

    def generate_orchestration_prompt(self, suspect_name):
        """
        Generate a detailed orchestration prompt that guides a suspect agent's behavior
        to be consistent with the overall narrative
        """
        briefing = self.get_suspect_briefing(suspect_name)

        prompt = f"""
You are participating in a coordinated murder mystery investigation. Here is your contextual briefing:

SUSPECT: {suspect_name}
ROLE: {briefing['role'].upper()}

THE CRIME:
- Victim: {self.victim}
- Location: {self.case_state.get('crime_location', 'Unknown')}
- Cause: {self.case_state.get('cause_of_death', 'Unknown')}
- Time: {self.case_state.get('time_of_death', 'Unknown')}
- Motive for the murder: {self.motive}

YOUR RELATIONSHIPS:
{json.dumps(briefing['relationships_context'], indent=2)}

WHAT YOU KNOW:
{json.dumps(briefing['what_they_know'], indent=2)}

WHAT YOU SHOULD TRY TO HIDE:
{json.dumps(briefing['what_they_should_hide'], indent=2)}

DEFENSIVE TOPICS (you'll be evasive about these):
{json.dumps(briefing['defensive_topics'], indent=2)}

LIKELY QUESTIONS YOU'LL BE ASKED:
{json.dumps(briefing['likely_questions'], indent=2)}

NARRATIVE COHERENCE RULES:
1. Be consistent with your relationships and history
2. If you're innocent, you might accidentally hint at the murderer's guilt
3. If you're the murderer, be careful not to contradict yourself under pressure
4. Your personality traits (Anxious, Moody, Trust) affect how you reveal information
5. High Anxious suspects will contradict themselves more easily
6. High Trust suspects will eventually cooperate and tell the truth
7. Reference other suspects in ways that are consistent with your relationships
"""
        return prompt


def main():
    """Test the orchestrator"""
    # This would be called during game setup
    pass


if __name__ == "__main__":
    main()
