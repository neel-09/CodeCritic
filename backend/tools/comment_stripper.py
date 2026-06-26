import re

def strip_comments(sketch: str) -> str:
    """
    Remove all // and /* */ comments from an Arduino sketch, preserving
    only the first two header lines if they match // Board: / // FQBN:.
    Comments inside string literals (e.g. Serial.print("// note")) are
    preserved correctly.
    """
    lines = sketch.split("\n")
    header_lines = []
    body_start = 0

    # Preserve header comment lines (// Board:, // FQBN:) at the top
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("// Board:") or stripped.startswith("// FQBN:"):
            header_lines.append(line)
            body_start = i + 1
        elif stripped == "":
            body_start = i + 1
        else:
            break

    body = "\n".join(lines[body_start:])
    body = _strip_block_comments(body)
    body = _strip_line_comments(body)

    # Collapse 3+ consecutive blank lines down to 1
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = body.strip()

    result = "\n".join(header_lines)
    if header_lines:
        result += "\n"
    result += body

    return result.strip() + "\n"


def _strip_block_comments(code: str) -> str:
    """Remove /* ... */ comments, respecting string literals."""
    result = []
    i = 0
    in_string = False
    string_char = ""
    n = len(code)

    while i < n:
        c = code[i]

        if in_string:
            result.append(c)
            if c == "\\" and i + 1 < n:
                result.append(code[i + 1])
                i += 2
                continue
            if c == string_char:
                in_string = False
            i += 1
            continue

        if c in ('"', "'"):
            in_string = True
            string_char = c
            result.append(c)
            i += 1
            continue

        if c == "/" and i + 1 < n and code[i + 1] == "*":
            end = code.find("*/", i + 2)
            if end == -1:
                break  # unterminated — drop rest
            i = end + 2
            continue

        result.append(c)
        i += 1

    return "".join(result)


def _strip_line_comments(code: str) -> str:
    """Remove // ... comments per line, respecting string literals."""
    out_lines = []

    for line in code.split("\n"):
        result = []
        i = 0
        n = len(line)
        in_string = False
        string_char = ""

        while i < n:
            c = line[i]

            if in_string:
                result.append(c)
                if c == "\\" and i + 1 < n:
                    result.append(line[i + 1])
                    i += 2
                    continue
                if c == string_char:
                    in_string = False
                i += 1
                continue

            if c in ('"', "'"):
                in_string = True
                string_char = c
                result.append(c)
                i += 1
                continue

            if c == "/" and i + 1 < n and line[i + 1] == "/":
                break  # rest of line is comment — drop it

            result.append(c)
            i += 1

        cleaned = "".join(result).rstrip()
        if cleaned.strip() != "":
            out_lines.append(cleaned)
        elif out_lines and out_lines[-1].strip() != "":
            out_lines.append("")  # preserve single blank line for readability

    return "\n".join(out_lines)