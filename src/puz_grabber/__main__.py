#!/usr/bin/env python3
import argparse
from .config import SOURCES 
from .downloaders import HANDLERS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('puzzle_code', choices=SOURCES.keys())
    
    args = parser.parse_args()
    
    handler = HANDLERS[SOURCES[args.puzzle_code]["source"]]
    try:
        puzzle = handler(args.puzzle_code)
    except RuntimeError as e:
        print(f"Failed to initialize handler for {args.puzzle_code}: {e}")
        return
    puzzle.write_file()

if __name__ == '__main__':
    main()
