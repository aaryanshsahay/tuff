#!/usr/bin/env python3
"""
Murder Mystery Detective Game - Main Entry Point
"""
import sys
import argparse
from dotenv import load_dotenv
from src.game import MurderMysteryGame


def main():
    """Main entry point for the game"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Murder Mystery Detective Game")
    parser.add_argument("--test", type=str, default="false", help="Use cached test case (true/false)")
    parser.add_argument("--visualize", type=str, default="false", help="Show agent behavior visualization (true/false)")
    parser.add_argument("--chaos", type=str, default="false", help="Enable chaos mode - agents communicate with each other (true/false)")
    args = parser.parse_args()

    # Convert arguments to boolean
    test_mode = args.test.lower() == "true"
    visualize_mode = args.visualize.lower() == "true"
    chaos_mode = args.chaos.lower() == "true"

    # Load environment variables
    load_dotenv()

    # Create and run the game
    game = MurderMysteryGame(test_mode=test_mode, visualize_mode=visualize_mode, chaos_mode=chaos_mode)
    game.run()


if __name__ == "__main__":
    main()
