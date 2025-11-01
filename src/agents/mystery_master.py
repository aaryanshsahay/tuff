import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 6 Fixed characters with consistent traits
FIXED_SUSPECTS = {
    "Nick": {
        "age": 30,
        "gender": "Male",
        "occupation": "Lawyer",
        "personality_traits": ["Intelligent", "Ambitious", "Witty"]
    },
    "Sarah": {
        "age": 28,
        "gender": "Female",
        "occupation": "Artist",
        "personality_traits": ["Creative", "Sensitive", "Observant"]
    },
    "James": {
        "age": 35,
        "gender": "Male",
        "occupation": "Chef",
        "personality_traits": ["Charming", "Confident", "Jealous"]
    },
    "Emma": {
        "age": 32,
        "gender": "Female",
        "occupation": "Tech Worker",
        "personality_traits": ["Logical", "Introverted", "Calculated"]
    },
    "David": {
        "age": 29,
        "gender": "Male",
        "occupation": "Writer",
        "personality_traits": ["Observant", "Sarcastic", "Moody"]
    },
    "Lisa": {
        "age": 31,
        "gender": "Female",
        "occupation": "Musician",
        "personality_traits": ["Expressive", "Emotional", "Loyal"]
    }
}

SUSPECT_NAMES = list(FIXED_SUSPECTS.keys())

RELATIONSHIP_TYPES = [
    "Close Friend",
    "Romantic Partner",
    "Business Partner",
    "Rival",
    "Enemy",
    "Acquaintance",
    "Family Member"
]

MOTIVES = [
    "Jealousy over a romantic relationship",
    "Financial gain or inheritance",
    "Revenge for past wrongs",
    "Protecting a secret",
    "Eliminating competition",
    "Accidental crime during argument"
]

MANSION_LOCATIONS = [
    "The victim's bedroom",
    "The mansion's library",
    "The dining room",
    "The guest house",
    "The wine cellar",
    "The study",
    "The conservatory",
    "The drawing room"
]

CAUSES_OF_DEATH = [
    "Poisoning (antifreeze in their wine glass)",
    "Blunt force trauma (hit with a marble statue)",
    "Suffocation (smothered with a pillow)",
    "Stabbing (with a letter opener from the study)",
    "Strangulation (with a rope from the garden shed)",
    "Medication overdose (their own pills tampered with)"
]

TIMES_OF_DEATH = [
    "Around 10:30 PM last night",
    "Around 11:45 PM last night",
    "Around 9:15 PM last night",
    "Around 12:30 AM",
    "Around 8:45 PM last night"
]


class MurderMysteryMaster:
    def __init__(self):
        self.suspects = {}
        self.victim = None
        self.murderer = None
        self.relationships = {}
        self.motives = {}
        self.case_state = None

    def generate_case_state(self):
        """Use OpenAI to generate a cohesive murder mystery case state"""

        # Create suspect info string for the prompt
        suspects_info = "\n".join([
            f"- {name}: {FIXED_SUSPECTS[name]['age']} year old {FIXED_SUSPECTS[name]['gender']} {FIXED_SUSPECTS[name]['occupation']}, personality: {', '.join(FIXED_SUSPECTS[name]['personality_traits'])}"
            for name in SUSPECT_NAMES
        ])

        prompt = f"""You are a master storyteller for a murder mystery game set in a MANSION where all 6 suspects live together.

These are the 6 fixed characters (same traits every game):
{suspects_info}

Suspect names: Nick, Sarah, James, Emma, David, Lisa

MANSION CONTEXT:
- All 6 suspects live in a large mansion together
- They were all present in the mansion last night when the murder occurred
- The murder happened between 8 PM and 1 AM
- No one left the mansion - all doors were locked

Your job for THIS game:
1. Randomly select one suspect as the VICTIM (killed last night in the mansion)
2. Randomly select a DIFFERENT suspect as the MURDERER
3. For each pair of suspects, assign a RELATIONSHIP TYPE from: {', '.join(RELATIONSHIP_TYPES)}
4. Assign a MOTIVE to the murderer from: {', '.join(MOTIVES)}
5. Create a plausible ALIBI for each suspect (what they claim they were doing in the mansion)
6. Choose the LOCATION where the body was found from: {', '.join(MANSION_LOCATIONS)}
7. Choose the CAUSE OF DEATH from: {', '.join(CAUSES_OF_DEATH)}
8. Choose the ESTIMATED TIME OF DEATH from: {', '.join(TIMES_OF_DEATH)}
9. Generate 3 CLUES that could help or mislead the detective (some true, some false/misleading)

IMPORTANT:
- ALL 6 SUSPECTS must have alibis
- Relationships should be consistent (if Nick is Sarah's friend, Sarah is Nick's friend)
- The murderer's alibi should be vague or show signs they're lying
- Create alibis where some suspects can partially corroborate each other
- Clues should be distributed among suspects (some might know something, others might lie about it)
- Clues should be discoverable through interrogation

Return your response as a valid JSON object with this exact structure:
{{
    "victim": "name_of_victim",
    "murderer": "name_of_murderer",
    "murderer_motive": "detailed reason for killing",
    "crime_location": "location in mansion where body was found",
    "cause_of_death": "how the victim was killed",
    "time_of_death": "estimated time of death",
    "alibis": {{
        "Nick": "their alibi",
        "Sarah": "their alibi",
        "James": "their alibi",
        "Emma": "their alibi",
        "David": "their alibi",
        "Lisa": "their alibi"
    }},
    "relationships": {{
        "Nick_Sarah": "relationship_type",
        "Nick_James": "relationship_type",
        "Nick_Emma": "relationship_type",
        "Nick_David": "relationship_type",
        "Nick_Lisa": "relationship_type",
        "Sarah_James": "relationship_type",
        "Sarah_Emma": "relationship_type",
        "Sarah_David": "relationship_type",
        "Sarah_Lisa": "relationship_type",
        "James_Emma": "relationship_type",
        "James_David": "relationship_type",
        "James_Lisa": "relationship_type",
        "Emma_David": "relationship_type",
        "Emma_Lisa": "relationship_type",
        "David_Lisa": "relationship_type"
    }},
    "clues": [
        {{
            "clue": "description of the clue",
            "known_by": "which suspect knows this clue",
            "is_true": true/false,
            "category": "physical evidence/witness statement/financial/relationship"
        }},
        {{
            "clue": "description of the clue",
            "known_by": "which suspect knows this clue",
            "is_true": true/false,
            "category": "physical evidence/witness statement/financial/relationship"
        }},
        {{
            "clue": "description of the clue",
            "known_by": "which suspect knows this clue",
            "is_true": true/false,
            "category": "physical evidence/witness statement/financial/relationship"
        }}
    ]
}}

Make sure all relationships are bidirectional and consistent. Return ONLY the JSON object, no other text."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a JSON generator for a murder mystery game. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )

        try:
            self.case_state = json.loads(response.choices[0].message.content)
            return self.case_state
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {response.choices[0].message.content}")
            return None

    def build_world_state(self):
        """Build the complete world state from the case generation"""
        if not self.case_state:
            return None

        state = self.case_state

        # Extract basic info
        self.victim = state["victim"]
        self.murderer = state["murderer"]

        # Build suspect details (using fixed traits + dynamic alibi)
        for name in SUSPECT_NAMES:
            suspect_base = FIXED_SUSPECTS[name]
            # Handle missing alibis by providing a default
            alibi = state.get("alibis", {}).get(name, f"I was minding my own business.")
            self.suspects[name] = {
                "name": name,
                "age": suspect_base["age"],
                "gender": suspect_base["gender"],
                "occupation": suspect_base["occupation"],
                "personality_traits": suspect_base["personality_traits"],
                "alibi": alibi,
                "is_victim": (name == self.victim),
                "is_murderer": (name == self.murderer),
            }

        # Build relationships (handle missing relationships)
        self.relationships = state.get("relationships", {})

        # Add motive to murderer
        self.motives[self.murderer] = state.get("murderer_motive", "Unknown motive")

        # Store crime scene details
        self.crime_location = state.get("crime_location", "Unknown location")
        self.cause_of_death = state.get("cause_of_death", "Unknown cause")
        self.time_of_death = state.get("time_of_death", "Unknown time")
        self.clues = state.get("clues", [])

        return self.suspects

    def print_world_state(self):
        """Print the entire world state to terminal"""
        if not self.suspects:
            print("No world state generated yet!")
            return

        print("\n" + "="*80)
        print("MURDER MYSTERY GAME - WORLD STATE")
        print("="*80 + "\n")

        # Print basic case info
        print(f"🔴 VICTIM: {self.victim}")
        print(f"🔪 MURDERER: {self.murderer}")
        print(f"📋 MOTIVE: {self.motives[self.murderer]}")
        print(f"📍 CRIME LOCATION: {self.crime_location}")
        print(f"☠️  CAUSE OF DEATH: {self.cause_of_death}")
        print(f"⏰ TIME OF DEATH: {self.time_of_death}\n")

        # Print suspect details
        print("-"*80)
        print("SUSPECTS:")
        print("-"*80)
        for name in SUSPECT_NAMES:
            suspect = self.suspects[name]
            marker = ""
            if suspect["is_victim"]:
                marker = " 🔴 [VICTIM]"
            elif suspect["is_murderer"]:
                marker = " 🔪 [MURDERER]"

            print(f"\n{name}{marker}")
            print(f"  Age: {suspect['age']} | Gender: {suspect['gender']}")
            print(f"  Occupation: {suspect['occupation']}")
            print(f"  Personality: {', '.join(suspect['personality_traits'])}")
            print(f"  Alibi: {suspect['alibi']}")

        # Print relationships
        print("\n" + "-"*80)
        print("RELATIONSHIPS:")
        print("-"*80)
        for pair, relationship in self.relationships.items():
            print(f"  {pair}: {relationship}")

        print("\n" + "="*80 + "\n")


def main():
    # Create master agent
    master = MurderMysteryMaster()

    print("🎭 Generating Murder Mystery Case...")
    print("(Using OpenAI API to create victim, murderer, relationships, and alibis)\n")

    # Generate the case state
    if master.generate_case_state():
        print("✅ Case generated successfully!\n")

        # Build the world state
        master.build_world_state()

        # Print the world state
        master.print_world_state()
    else:
        print("❌ Failed to generate case state")


if __name__ == "__main__":
    main()
