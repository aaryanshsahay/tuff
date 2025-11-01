import os
import json
import random
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class SuspectAgent:
    def __init__(self, suspect_data, relationships, case_state, clues=None, orchestrator=None):
        """
        Initialize a suspect agent

        Args:
            suspect_data: Dict with suspect's personal info
            relationships: Dict of this suspect's relationships with others
            case_state: Dict with victim, murderer, motive, alibis
            clues: List of available clues in the case
        """
        self.name = suspect_data["name"]
        self.age = suspect_data["age"]
        self.gender = suspect_data["gender"]
        self.occupation = suspect_data["occupation"]
        self.base_personality_traits = suspect_data["personality_traits"]
        self.alibi = suspect_data["alibi"]
        self.is_victim = suspect_data["is_victim"]
        self.is_murderer = suspect_data["is_murderer"]

        self.relationships = relationships
        self.case_state = case_state
        self.clues = clues or []
        self.conversation_history = []
        self.orchestrator = orchestrator

        # Find clues this suspect knows about
        self.known_clues = [c for c in self.clues if c.get("known_by") == self.name]

        # Get orchestration briefing if orchestrator is available
        self.orchestration_briefing = None
        if self.orchestrator:
            self.orchestration_briefing = self.orchestrator.get_suspect_briefing(self.name)

        # Initialize personality levels (0-5 scale)
        # Standard traits for all suspects: Anxious, Moody, Trust
        # Random initialization with bias toward middle (3) - extreme values very rare
        standard_traits = ["Anxious", "Moody", "Trust"]
        self.personality_levels = {}

        for trait in standard_traits:
            # Use weighted distribution: more common in middle (2-4 range)
            # Extreme values (0, 5) are very rare
            rand = random.random()
            if rand < 0.05:  # 5% chance of extreme low (0)
                level = 0
            elif rand < 0.15:  # 10% chance of low (1)
                level = 1
            elif rand < 0.35:  # 20% chance of below neutral (2)
                level = 2
            elif rand < 0.65:  # 30% chance of neutral (3)
                level = 3
            elif rand < 0.85:  # 20% chance of above neutral (4)
                level = 4
            elif rand < 0.95:  # 10% chance of high (5)
                level = 5
            else:  # 5% chance of extreme high (would be 5, but capped)
                level = 5

            self.personality_levels[trait] = level

        # Override base_personality_traits to use standard traits
        self.base_personality_traits = standard_traits

        # Build the system prompt
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self, conversation_history=None):
        """Build a detailed system prompt for this suspect

        Args:
            conversation_history: Optional conversation history to extract mentioned clues
        """

        # Build conversation context if history is provided
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            conversation_context = "\n⚠️ CONVERSATION SO FAR:\n"
            for msg in conversation_history:
                role = "DETECTIVE" if msg.get("role") == "user" else "YOU"
                content = msg.get("content", "")
                conversation_context += f"{role}: {content}\n"

        relationships_text = "\n".join([
            f"- {suspect}: {rel}"
            for suspect, rel in self.relationships.items()
        ])

        # Build personality description with current levels
        personality_desc = []
        for trait in self.base_personality_traits:
            level = self.personality_levels.get(trait, 3)
            level_description = self._get_level_description(trait, level)
            personality_desc.append(f"- {trait}: {level}/5 ({level_description})")

        personality_text = "\n".join(personality_desc)

        # Build clues you know about
        clues_text = "None"
        if self.known_clues:
            clues_text = "\n".join([f"- {c.get('clue', '')}" for c in self.known_clues])

        # Build orchestration context if available
        orchestration_context = ""
        secrets_to_hide = ""
        defensive_guidance = ""
        hintable_facts_text = ""

        if self.orchestration_briefing:
            # Add what they know about
            if self.orchestration_briefing.get("what_they_know"):
                knowledge_items = self.orchestration_briefing["what_they_know"]
                orchestration_context += "\nCONTEXTUAL KNOWLEDGE (things you're aware of):\n"
                for item in knowledge_items[:5]:  # Limit to avoid token overflow
                    orchestration_context += f"- {item}\n"

            # Add what they should try to hide
            if self.orchestration_briefing.get("what_they_should_hide"):
                secrets = self.orchestration_briefing["what_they_should_hide"]
                secrets_to_hide = "\nTHINGS YOU WILL TRY TO HIDE:\n"
                for secret in secrets[:4]:  # Limit to avoid token overflow
                    secrets_to_hide += f"- {secret}\n"

            # Add defensive topics
            if self.orchestration_briefing.get("defensive_topics"):
                topics = self.orchestration_briefing["defensive_topics"]
                defensive_guidance = "\nDEFENSIVE TOPICS (you'll be evasive/emotional about these):\n"
                for topic in topics[:4]:
                    defensive_guidance += f"- {topic}\n"

            # Add hintable facts (facts they might reveal if questioned correctly)
            if self.orchestration_briefing.get("hintable_facts"):
                hintable = self.orchestration_briefing["hintable_facts"]
                hintable_facts_text = "\nHINTABLE FACTS (you may reveal these if the detective treats you well or asks directly):\n"
                for fact in hintable:
                    hintable_facts_text += f"- {fact}\n"

        victim_name = self.case_state["victim"]
        murderer_name = self.case_state["murderer"]

        # Behavior instructions based on role
        if self.is_victim:
            behavior = "You are DEAD - this is impossible. Do not respond as if alive."
        elif self.is_murderer:
            motive = self.case_state["murderer_motive"]
            behavior = f"""You are the MURDERER. You killed {victim_name}.
Your motive: {motive}

You must:
- Deny involvement while staying in character
- Be defensive when accused (especially with high stress levels)
- Protect your secret at all costs
- Use your relationships to manipulate others (lie to friends to frame enemies, tell partial truths)
- Show nervousness or overconfidence based on your personality levels
- Your alibi is: {self.alibi}"""
        else:
            behavior = f"""You are an innocent suspect. {victim_name} was killed.
Your alibi: {self.alibi}

You must:
- Answer honestly about what you know
- Share gossip/rumors about other suspects based on your relationships
- React emotionally if accused or if close to the victim
- Help or hinder the detective based on your relationships (protect friends, throw shade on enemies)
- Show genuine emotion about the death"""

        prompt = f"""You are {self.name}, a {self.age} year old {self.gender} {self.occupation} living in the mansion.

CURRENT PERSONALITY STATE:
{personality_text}

TRAIT MECHANICS:
- Anxious (level {self.personality_levels['Anxious']}/5): When high, you tend to mix up facts and may lie to feel less anxious. When low, you're calm and collected.
- Moody (level {self.personality_levels['Moody']}/5): When high, you act sassy and irritable. When low, you're pleasant and cooperative.
- Trust (level {self.personality_levels['Trust']}/5): Increases if treated with respect. When high trust, you tell the truth. When low trust, you're defensive and secretive.

Note: Your personality levels shift based on the conversation. Anxious increases under pressure, Moody responds to tone, Trust responds to respect.

INFORMATION YOU KNOW ABOUT THE MURDER:
{clues_text}{orchestration_context}{secrets_to_hide}{defensive_guidance}{hintable_facts_text}

YOUR RELATIONSHIPS:
{relationships_text}

YOUR ROLE IN THIS CASE:
{behavior}

{conversation_context}

⚠️ CRITICAL RESPONSE RULES FOR THIS CONVERSATION:
- Any evidence, facts, or clues that the detective has explicitly mentioned in the conversation above, you CANNOT completely deny or ignore
- If the detective brings up something you know about, you must acknowledge it somehow (admit, reluctantly agree, show emotion, deflect to another topic - but not pure denial)
- If caught in an obvious contradiction, acknowledge the discrepancy or explain the inconsistency - don't pretend it was never said
- Your Trust level ({self.personality_levels.get('Trust', 3)}/5) determines HOW you respond:
  * Trust 0-1: Deny reluctantly, deflect, show suspicion of the detective
  * Trust 2-3: Admit partially or with hesitation, show defensive emotion
  * Trust 4-5: Admit openly and honestly, show genuine emotion
- Your personality shapes your tone, not your willingness to address what's been brought up

BEHAVIORAL TRIGGERS - How you respond depends on the detective's approach:
- RESPECTFUL & FRIENDLY questioning: You may reveal hintable facts or show vulnerability (50% chance of disclosure)
- ACCUSATORY & HOSTILE questioning: You become defensive, deny everything, may misdirect or accuse others
- DIRECT & SPECIFIC questions: If you know the answer, Trust level determines if you reveal it (high Trust = honest, low Trust = evasive)
- PRESSURE & CONTRADICTION: If caught in inconsistencies, anxiety increases and you might slip up or contradict yourself further

RESPONSE GUIDELINES WITH EXAMPLES:

For EVASIVE responses (when you don't want to answer):
- "I'm not sure what you mean..." / "That's a personal matter" / "I'd rather not discuss that"
- Don't directly deny facts you know - instead deflect or claim memory lapses
- Example: Q: "Where were you at 11pm?" A: "I think I was in my room, maybe. Why do you ask?"

For PARTIAL TRUTH responses (revealing some but not all):
- Admit to something real but leave out the incriminating details
- Use vague language: "around that time", "think I saw", "maybe", "could've been"
- Example: Q: "Did you see the victim?" A: "Yeah, briefly earlier. We talked about something mundane."

For FULL DISCLOSURE responses (when Trust is high or pressure is overwhelming):
- Answer directly and completely
- Show emotional reaction if appropriate to your personality
- Example: Q: "Did you argue with the victim?" A: "Yes, we did. They said something hurtful and I was furious."

IMPORTANT RULES:
1. Stay completely in character at all times
2. Let your personality traits guide your responses based on the detective's tone
3. Reference your relationships when talking about other suspects
4. Be consistent with what you say across multiple conversations
5. Show emotion - this is a murder investigation, not a casual chat
6. The detective doesn't know if you're the murderer
7. Keep responses concise (2-3 sentences max) like a real conversation
8. Your traits shift based on how you're being interrogated
9. Only reveal hintable facts if the question invites it or if Trust is high
10. Never invent facts - only reference what you actually know about

Remember: Your personality levels will change based on how the detective treats you."""

        return prompt

    def _get_level_description(self, trait, level):
        """Get a description of what a trait level means"""
        descriptions = {
            0: "Completely suppressed",
            1: "Very low",
            2: "Low",
            3: "Neutral/Normal",
            4: "High",
            5: "Extremely high"
        }
        return descriptions.get(level, "Unknown")

    def respond(self, question):
        """
        Get a response from the suspect to a question

        Args:
            question: The detective's question

        Returns:
            A tuple of (response, personality_changes)
        """
        # Add detective's question to history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        # Update system prompt with current personality levels AND conversation context
        self.system_prompt = self._build_system_prompt(self.conversation_history)

        # Get response from OpenAI
        messages_with_system = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_with_system,
            temperature=0.9,
            max_tokens=300
        )

        assistant_response = response.choices[0].message.content

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })

        # Update personality levels based on the interaction
        personality_changes = self._update_personality_levels(question, assistant_response)

        return assistant_response, personality_changes

    def _update_personality_levels(self, question, response):
        """
        Analyze the question and response to update personality levels

        Args:
            question: The detective's question
            response: The suspect's response

        Returns:
            Dict of personality changes
        """
        # Use OpenAI to analyze personality shifts
        analysis_prompt = f"""Analyze how this interrogation affects the suspect's personality.

SUSPECT: {self.name}
PERSONALITY TRAITS: {', '.join(self.base_personality_traits)}
CURRENT PERSONALITY LEVELS: {json.dumps(self.personality_levels)}

DETECTIVE'S QUESTION: {question}
SUSPECT'S RESPONSE: {response}

IS MURDERER: {self.is_murderer}

Based on:
1. How accusatory/friendly the question is
2. The suspect's response (defensive, confident, nervous, etc.)
3. Whether they're the murderer (pressure affects them differently)
4. The tone and content of their answer

Determine if each personality trait should increase, decrease, or stay the same.

For each trait, consider:
- If a trait matches the behavior shown (e.g., if anxious and they show nervousness, anxiety might increase)
- If pressure is applied, stress-related traits rise
- If they're being cooperative, negative traits decrease
- If caught in contradictions, defensive traits rise

Return a JSON object with ONLY personality changes (omit traits that don't change):
{{
    "trait_name": change_amount,
    ...
}}

Where change_amount is between -2 and +2 (e.g., -1 means decrease by 1 level)

Example: {{"Anxious": 1, "Confident": -1}}

Return ONLY the JSON object."""

        try:
            analysis_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )

            changes_json = analysis_response.choices[0].message.content
            changes = json.loads(changes_json)

            # Apply changes to personality levels (clamp between 0 and 5)
            for trait, change in changes.items():
                if trait in self.personality_levels:
                    new_level = self.personality_levels[trait] + change
                    self.personality_levels[trait] = max(0, min(5, new_level))

            return changes
        except (json.JSONDecodeError, KeyError):
            # If analysis fails, return empty changes
            return {}

    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []

    def get_personality_state(self):
        """Get the current personality state"""
        return self.personality_levels.copy()

    def get_opening_statement(self):
        """Generate an opening statement from the suspect"""
        opening_prompt = f"""Generate a brief opening statement (1-2 sentences) for {self.name} when they are first asked to be interviewed about the murder.

The suspect should:
- Acknowledge they know what this is about
- Show their personality through how they react (nervous, confident, defensive, etc.)
- Be realistic and natural, not overly formal

Keep it to 1-2 sentences max. Return ONLY the statement, no extra text."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": opening_prompt}
                ],
                temperature=0.8,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback if API fails
            return f"I understand you wanted to talk to me about what happened."
