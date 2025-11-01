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
    args = parser.parse_args()

    # Convert test argument to boolean
    test_mode = args.test.lower() == "true"

    # Load environment variables
    load_dotenv()

    # Create and run the game
    game = MurderMysteryGame(test_mode=test_mode)
    game.run()


if __name__ == "__main__":
    main()
