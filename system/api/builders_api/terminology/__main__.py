import json
import sys

from builders_api.terminology import JSON_FILE, SOURCE, build

if "--build" in sys.argv:
    data = {"$comment": "Generated from research/domain/glossary.md. Do not edit by hand.", "entries": build()}
    JSON_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {len(data['entries'])} entries to {JSON_FILE} from {SOURCE}")
