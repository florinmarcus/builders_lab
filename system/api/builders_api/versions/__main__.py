"""python -m builders_api.versions [--lock]"""

import sys

from builders_api.versions import check_lock, lock_new

if "--lock" in sys.argv:
    print("locked:", ", ".join(lock_new()) or "nothing new")
else:
    problems = check_lock()
    print("\n".join(problems) or "all versions locked and unchanged")
    sys.exit(1 if problems else 0)
