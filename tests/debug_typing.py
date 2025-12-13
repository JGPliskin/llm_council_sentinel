
import sys
import traceback

with open("debug_output_typing.txt", "w") as f:
    f.write(f"Python Version: {sys.version}\n")
    try:
        from typing import NoReturn, Callable
        f.write("Typing imported.\n")
        
        # Reproduce the exact error
        try:
             # This is what trio/_core/_traps.py does that fails on older python sometimes
             x = Callable[[], NoReturn]
             f.write(f"Callable[[], NoReturn] worked: {x}\n")
        except TypeError as e:
             f.write(f"Callable[[], NoReturn] failed: {e}\n")

    except Exception:
        f.write(traceback.format_exc())
