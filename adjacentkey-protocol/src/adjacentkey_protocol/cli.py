import argparse
from adjacentkey_protocol.codec import encode_adjacent, decode_adjacent

def main():
    parser = argparse.ArgumentParser(description="AdjacentKey Protocol CLI")
    subparsers = parser.add_subparsers(dest="command")

    enc = subparsers.add_parser("encode", help="Encode text with adjacent-key protocol")
    enc.add_argument("text", type=str, help="Text to encode")
    enc.add_argument("--direction", choices=["left", "right"], default="right", help="Neighbor direction")

    dec = subparsers.add_parser("decode", help="Decode text with adjacent-key protocol")
    dec.add_argument("text", type=str, help="Text to decode")
    dec.add_argument("--direction", choices=["left", "right"], default="right", help="Neighbor direction")

    args = parser.parse_args()
    if args.command == "encode":
        print(encode_adjacent(args.text, args.direction))
    elif args.command == "decode":
        print(decode_adjacent(args.text, args.direction))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
