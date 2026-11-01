#!/usr/bin/env python3
import argparse
from .config import SOURCES 
from .downloaders import HANDLERS

def main():
    parser = argparse.ArgumentParser()
    arg_choices = list(SOURCES.keys())
    arg_choices.append("all")
    parser.add_argument('puzzle_code', choices=arg_choices)
    
    args = parser.parse_args()
    
    if args.puzzle_code == "all":
        for code in SOURCES.keys():
            get_puzzle(HANDLERS[SOURCES[code]["source"]], code)
    else:
        get_puzzle(HANDLERS[SOURCES[args.puzzle_code]["source"]], args.puzzle_code)

def get_puzzle(handler, code):
    try:
        puzzle = handler(code)
    except RuntimeError as e:
        print(f"Failed to initialize handler for {args.puzzle_code}: {e}")
        return
    puzzle.write_file()


if __name__ == '__main__':
    main()
