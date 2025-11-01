import os
import json
from dotenv import load_dotenv
from mystery_master import MurderMysteryMaster
from suspect_agent import SuspectAgent

load_dotenv()


class DetectiveGame:
    def __init__(self):
        self.master = MurderMysteryMaster()
        self.suspects_agents = {}
        self.investigation_log = []
        self.current_suspect = None

    def setup_game(self):
        """Initialize the game with a new case and suspect agents"""
        print("\n🔍 Setting up murder mystery case...\n")

        # Generate case
        if not self.master.generate_case_state():
            print("❌ Failed to generate case")
            return False

        # Build world state
        self.master.build_world_state()

        # Create suspect agents
        for suspect_name in self.master.suspects.keys():
            suspect_data = self.master.suspects[suspect_name]

            # Get relationships for this suspect
            relationships = {}
            for pair, rel_type in self.master.relationships.items():
                names = pair.split("_")
                if suspect_name in names:
                    other_name = names[0] if names[1] == suspect_name else names[1]
                    relationships[other_name] = rel_type

            # Create agent
            agent = SuspectAgent(suspect_data, relationships, self.master.case_state, self.master.clues)
            self.suspects_agents[suspect_name] = agent

        print("✅ Game setup complete!\n")
        return True

    def print_case_briefing(self):
        """Print the initial case briefing"""
        print("="*80)
        print("MURDER MYSTERY - CASE BRIEFING")
        print("="*80 + "\n")

        print("🏰 THE MANSION - A MURDER HAS BEEN COMMITTED\n")

        victim = self.master.case_state["victim"]
        print(f"🔴 VICTIM: {victim}")
        print(f"📍 CRIME LOCATION: {self.master.crime_location}")
        print(f"☠️  CAUSE OF DEATH: {self.master.cause_of_death}")
        print(f"⏰ ESTIMATED TIME OF DEATH: {self.master.time_of_death}\n")

        print("SUSPECTS (All living in the mansion):")
        for suspect_name in self.master.suspects.keys():
            if suspect_name != victim:
                suspect = self.master.suspects[suspect_name]
                print(f"  • {suspect_name} ({suspect['age']} year old {suspect['gender']} {suspect['occupation']})")

        print("\n" + "="*80 + "\n")

    def show_case_details(self):
        """Show detailed crime scene information"""
        print("\n" + "="*80)
        print("CRIME SCENE DETAILS")
        print("="*80 + "\n")

        victim = self.master.case_state["victim"]
        print(f"🔴 VICTIM: {victim}")
        print(f"📍 LOCATION: {self.master.crime_location}")
        print(f"☠️  CAUSE OF DEATH: {self.master.cause_of_death}")
        print(f"⏰ TIME OF DEATH: {self.master.time_of_death}\n")

        print("-"*80)
        print("KNOWN CLUES:")
        print("-"*80)
        for i, clue in enumerate(self.master.clues, 1):
            print(f"\n{i}. {clue.get('clue', 'Unknown clue')}")
            print(f"   Known by: {clue.get('known_by', 'Unknown')}")
            print(f"   Category: {clue.get('category', 'Unknown')}")

        print("\n" + "="*80 + "\n")

    def show_main_menu(self):
        """Show the main menu for selecting suspects to interview"""
        print("\n" + "-"*80)
        print("WHO WOULD YOU LIKE TO INTERVIEW?")
        print("-"*80 + "\n")

        available_suspects = []
        for i, suspect_name in enumerate(self.master.suspects.keys(), 1):
            if suspect_name != self.master.case_state["victim"]:
                available_suspects.append(suspect_name)
                print(f"{i}. {suspect_name}")

        print(f"{len(available_suspects) + 1}. View Crime Scene Details")
        print(f"{len(available_suspects) + 2}. View Investigation Log")
        print(f"{len(available_suspects) + 3}. Make an Accusation")
        print(f"{len(available_suspects) + 4}. Exit Game\n")

        while True:
            try:
                choice = int(input("Enter your choice (number): ").strip())
                if 1 <= choice <= len(available_suspects):
                    return available_suspects[choice - 1]
                elif choice == len(available_suspects) + 1:
                    return "details"
                elif choice == len(available_suspects) + 2:
                    return "log"
                elif choice == len(available_suspects) + 3:
                    return "accuse"
                elif choice == len(available_suspects) + 4:
                    return "exit"
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def interview_suspect(self, suspect_name):
        """Conduct an interview with a suspect"""
        agent = self.suspects_agents[suspect_name]

        print("\n" + "="*80)
        print(f"INTERVIEWING: {suspect_name}")
        print("="*80 + "\n")

        suspect = self.master.suspects[suspect_name]
        print(f"Age: {suspect['age']} | Gender: {suspect['gender']}")
        print(f"Occupation: {suspect['occupation']}")
        print(f"Alibi: {suspect['alibi']}\n")

        # Display personality state
        self._display_personality_state(suspect_name, agent)

        print("-"*80)
        print("(Type 'back' to return to main menu)\n")

        while True:
            question = input("You: ").strip()

            if question.lower() == "back":
                break

            if not question:
                print("Please ask a question.\n")
                continue

            print("\n⏳ Analyzing interrogation...\n")

            # Get response from suspect
            response, personality_changes = agent.respond(question)
            print(f"{suspect_name}: {response}\n")

            # Display personality changes
            if personality_changes:
                print("-" * 40)
                print("📊 PERSONALITY SHIFTS:")
                for trait, change in personality_changes.items():
                    direction = "📈" if change > 0 else "📉"
                    print(f"  {direction} {trait}: {change:+d}")
                print("-" * 40 + "\n")

            # Display updated personality state
            self._display_personality_state(suspect_name, agent)

            # Log the conversation
            self.investigation_log.append({
                "suspect": suspect_name,
                "question": question,
                "response": response,
                "personality_changes": personality_changes
            })

    def _display_personality_state(self, suspect_name, agent):
        """Display a suspect's current personality state"""
        personality_state = agent.get_personality_state()
        print("\n📋 CURRENT PERSONALITY STATE:")
        for trait, level in personality_state.items():
            # Create a visual bar
            bar = "█" * level + "░" * (5 - level)
            level_text = agent._get_level_description(trait, level)
            print(f"  {trait}: [{bar}] {level}/5 ({level_text})")
        print()

    def show_investigation_log(self):
        """Display all recorded conversations"""
        if not self.investigation_log:
            print("\n" + "-"*80)
            print("No conversations recorded yet.")
            print("-"*80 + "\n")
            return

        print("\n" + "="*80)
        print("INVESTIGATION LOG")
        print("="*80 + "\n")

        current_suspect = None
        for entry in self.investigation_log:
            if entry["suspect"] != current_suspect:
                print(f"\n--- Interview with {entry['suspect']} ---")
                current_suspect = entry["suspect"]

            print(f"You: {entry['question']}")
            print(f"{entry['suspect']}: {entry['response']}\n")

        print("="*80 + "\n")

    def make_accusation(self):
        """Allow the detective to make an accusation"""
        print("\n" + "-"*80)
        print("WHO DO YOU ACCUSE OF THE MURDER?")
        print("-"*80 + "\n")

        suspects = [s for s in self.master.suspects.keys() if s != self.master.case_state["victim"]]
        for i, suspect_name in enumerate(suspects, 1):
            print(f"{i}. {suspect_name}")

        print(f"{len(suspects) + 1}. Back to Menu\n")

        while True:
            try:
                choice = int(input("Enter your choice (number): ").strip())
                if 1 <= choice <= len(suspects):
                    accused = suspects[choice - 1]
                    return accused
                elif choice == len(suspects) + 1:
                    return None
                else:
                    print("Invalid choice. Try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def resolve_accusation(self, accused):
        """Resolve the accusation and end the game"""
        if accused == self.master.case_state["murderer"]:
            print("\n" + "="*80)
            print("🎉 CORRECT! You solved the case!")
            print("="*80)
            print(f"\n{accused} was indeed the murderer!")
            print(f"Motive: {self.master.case_state['murderer_motive']}\n")
            return True
        else:
            print("\n" + "="*80)
            print("❌ INCORRECT!")
            print("="*80)
            print(f"\n{accused} is not the murderer.")
            print(f"The real murderer was: {self.master.case_state['murderer']}")
            print(f"Motive: {self.master.case_state['murderer_motive']}\n")
            return False

    def run(self):
        """Main game loop"""
        print("\n" + "🔍 "*20)
        print("WELCOME TO MURDER MYSTERY DETECTIVE GAME")
        print("🔍 "*20 + "\n")

        # Setup game
        if not self.setup_game():
            return

        # Print case briefing
        self.print_case_briefing()

        # Main game loop
        game_over = False
        while not game_over:
            choice = self.show_main_menu()

            if choice == "exit":
                print("\nThanks for playing!\n")
                break
            elif choice == "details":
                self.show_case_details()
            elif choice == "log":
                self.show_investigation_log()
            elif choice == "accuse":
                accused = self.make_accusation()
                if accused:
                    game_over = self.resolve_accusation(accused)
            else:
                self.interview_suspect(choice)


def main():
    game = DetectiveGame()
    game.run()


if __name__ == "__main__":
    main()
