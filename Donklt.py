#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
import traceback

class DonkLangTranspiler:
    def __init__(self, offset: int = 0):
        self.offset = int(offset)

    def decode(self, text: str) -> str:
        out = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == ' ':
                j = i
                while j < n and text[j] == ' ':
                    j += 1
                run_len = j - i
                codepoint = run_len + self.offset
                try:
                    out.append(chr(codepoint))
                except (ValueError, OverflowError):
                    out.append('\uFFFD')
                i = j
                continue
            if ch == '\n':
                out.append('\n')
            i += 1
        return ''.join(out)

    def decode_file(self, inpath: str) -> str:
        p = Path(inpath)
        if not p.exists():
            raise FileNotFoundError(inpath)
        return self.decode(p.read_text())

    def encode(self, text: str, sep: str = '|') -> str:
        parts = []
        for ch in text:
            if ch == '\n':
                parts.append('\n')
                continue
            code = ord(ch)
            run_len = code - self.offset
            if run_len < 1:
                raise ValueError(f"Character {repr(ch)} (ord={code}) cannot be encoded with offset={self.offset}")
            parts.append(' ' * run_len)
            if sep:
                parts.append(sep)
        return ''.join(parts)

    def encode_file(self, inpath: str, sep: str = '|') -> str:
        p = Path(inpath)
        if not p.exists():
            raise FileNotFoundError(inpath)
        return self.encode(p.read_text(), sep=sep)

def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(prog="donk", description="donk: encode | decode | run")
    sub = p.add_subparsers(dest='cmd', required=True)

    e = sub.add_parser('encode')
    e.add_argument('infile')
    e.add_argument('-o', '--out')
    e.add_argument('--offset', type=int, default=0)
    e.add_argument('--sep', default='|')

    d = sub.add_parser('decode')
    d.add_argument('infile')
    d.add_argument('-o', '--out')
    d.add_argument('--offset', type=int, default=0)

    r = sub.add_parser('run')
    r.add_argument('infile')
    r.add_argument('script_args', nargs=argparse.REMAINDER)
    r.add_argument('--offset', type=int, default=0)

    args = p.parse_args(argv)
    t = DonkLangTranspiler(offset=getattr(args, 'offset', 0))

    try:
        if args.cmd == 'encode':
            out = t.encode_file(args.infile, sep=args.sep)
            if args.out:
                Path(args.out).write_text(out)
            else:
                print(out, end='')
            return

        if args.cmd == 'decode':
            out = t.decode_file(args.infile)
            if args.out:
                Path(args.out).write_text(out)
            else:
                print(out, end='')
            return

        if args.cmd == 'run':
            decoded = t.decode_file(args.infile)
            globs = {"__name__": "__main__", "__file__": str(Path(args.infile).resolve())}
            saved_argv = sys.argv[:]
            sys.argv = [args.infile] + (args.script_args or [])
            try:
                compiled = compile(decoded, args.infile, 'exec')
                exec(compiled, globs)
            except SystemExit:
                raise
            except Exception:
                traceback.print_exc()
                sys.exit(1)
            finally:
                sys.argv = saved_argv
            return

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == '__main__':
    main()
