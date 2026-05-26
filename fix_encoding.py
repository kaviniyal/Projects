"""
Fix app.py encoding corruption for Python 3.12+ / Render deployment.

Root cause:
  - UTF-8 BOM at the start
  - All non-ASCII content was double-encoded:
      original UTF-8 bytes -> mis-read as cp1252 -> re-encoded as UTF-8
  - Docstring delimiters use curly/smart quotes instead of ASCII "

Algorithm (order matters):
  1. Strip UTF-8 BOM.
  2. Build a COMPLETE cp1252 reverse-lookup that includes the 5 undefined
     bytes Python can decode but not re-encode with the standard codec.
  3. For every contiguous run of non-ASCII bytes attempt un-double-encoding:
       UTF-8 decode  ->  cp1252_lax encode  ->  UTF-8 decode
     Success  -> replace with recovered Unicode (UTF-8).
     Failure  -> leave as-is (not doubly-encoded, e.g. standalone em dash
                 or the curly-quote docstring delimiters).
  4. Replace any remaining curly/smart quotes with straight ASCII quotes.
"""
import re

# ── build cp1252 reverse-lookup (includes undefined-but-decodable bytes) ──
_CP1252_REVERSE = {}
for _b in range(256):
    try:
        _ch = bytes([_b]).decode("cp1252")
    except UnicodeDecodeError:
        _ch = chr(_b)          # undefined in cp1252; Python maps to same codepoint
    _CP1252_REVERSE[_ch] = _b


def _encode_cp1252_lax(text):
    """Encode a Unicode string to cp1252 bytes, including the 5 undefined bytes."""
    result = []
    for ch in text:
        if ch not in _CP1252_REVERSE:
            raise ValueError(f"U+{ord(ch):04X} not in cp1252")
        result.append(_CP1252_REVERSE[ch])
    return bytes(result)


# ── read original ──────────────────────────────────────────────────────────
with open("app.py", "rb") as f:
    data = f.read()

original_size = len(data)

# ── step 1: strip BOM ─────────────────────────────────────────────────────
if data.startswith(b"\xef\xbb\xbf"):
    data = data[3:]
    print("Step 1: stripped UTF-8 BOM")

# ── step 2: un-double-encode contiguous non-ASCII runs ────────────────────
fixed = failed = 0

def try_undouble(m):
    global fixed, failed
    seq = m.group(0)
    try:
        text      = seq.decode("utf-8")          # doubly-encoded -> Unicode
        cp1252_b  = _encode_cp1252_lax(text)     # reverse the cp1252 mis-read
        original  = cp1252_b.decode("utf-8")     # get the real Unicode
        fixed += 1
        return original.encode("utf-8")
    except Exception:
        failed += 1
        return seq

data = re.sub(b"[\x80-\xff]+", try_undouble, data)
print(f"Step 2: un-double-encoded {fixed} runs, left {failed} alone")

# ── step 3: replace remaining curly quotes with straight ASCII ─────────────
for pattern, name in [
    (b"\xe2\x80\x9c", "left  curly quote U+201C"),
    (b"\xe2\x80\x9d", "right curly quote U+201D"),
]:
    count = data.count(pattern)
    if count:
        data = data.replace(pattern, b'"')
        print(f"Step 3: replaced {count:3d}x {name}")

# ── write back ────────────────────────────────────────────────────────────
with open("app.py", "wb") as f:
    f.write(data)

print(f"\nFile: {original_size} -> {len(data)} bytes")

# ── verify Python syntax ──────────────────────────────────────────────────
import py_compile, sys
try:
    py_compile.compile("app.py", doraise=True)
    print("SYNTAX OK -- app.py compiles cleanly")
except py_compile.PyCompileError as e:
    # Print the error safely (avoiding cp1252 encode issues on Windows)
    msg = str(e).encode("ascii", errors="backslashreplace").decode("ascii")
    print(f"SYNTAX ERROR: {msg}")
    sys.exit(1)
