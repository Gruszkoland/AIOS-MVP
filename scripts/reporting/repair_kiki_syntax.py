from pathlib import Path
import re
import py_compile

SRC = Path(r"C:\Users\adiha\Desktop\KIKI-AIOS_COMPLETE")
DST = Path(r"C:\Users\adiha\.1_Projekty\kimi_migration\source_fixed")


def repair_text(text: str) -> str:
    fixed = text
    # Fix patterns where string literals were split into two lines after opening quote.
    # Example:
    #   print(f"
    #   Text")
    # becomes:
    #   print(f"\nText")
    fixed = re.sub(r'print\(f"\s*\n\s*([^"]*)"\)', r'print(f"\\n\1")', fixed)
    fixed = re.sub(r'print\("\s*\n\s*([^"]*)"\)', r'print("\\n\1")', fixed)
    fixed = re.sub(r'return "\s*\n\s*([^"]*)"', r'return "\\n\1"', fixed)

    # Fix patterns like:
    #   print("
    #   " + "="*60)
    fixed = re.sub(r'print\("\s*\n\s*"\s*\+', r'print("\\n" +', fixed)

    # Keep compatibility with single-line malformed variants.
    fixed = re.sub(r'print\(f"\n', 'print(f"\\n', fixed)
    fixed = re.sub(r'print\("\n', 'print("\\n', fixed)
    fixed = re.sub(r'return "\n', 'return "\\n', fixed)
    return fixed


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)

    for file_path in SRC.iterdir():
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            repaired = repair_text(content)
            (DST / file_path.name).write_text(repaired, encoding="utf-8")

    ok = 0
    errs: list[tuple[str, str]] = []
    for py_file in DST.glob("*.py"):
        try:
            py_compile.compile(str(py_file), doraise=True)
            ok += 1
        except Exception as ex:
            errs.append((py_file.name, str(ex).splitlines()[0]))

    print("COPIED_AND_REPAIRED")
    print(f"PY_OK={ok}")
    print(f"PY_ERR={len(errs)}")
    for name, msg in errs:
        print(f"ERR|{name}|{msg}")

    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
