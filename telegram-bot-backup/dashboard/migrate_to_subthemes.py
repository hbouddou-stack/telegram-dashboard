import json
import os

file_path = "transcripts.json"
backup_path = "transcripts.json.bak_subthemes"

with open(file_path, "r", encoding="utf-8") as f:
    db = json.load(f)

# Backup
with open(backup_path, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

for lesson in db:
    blocks = lesson.get("thematic_blocks", [])
    segments = lesson.get("segments", [])
    
    # Check if already migrated
    if blocks and "subthemes" in blocks[0]:
        continue
        
    if not blocks:
        # Fallback if no blocks
        full_text = lesson.get("full_text", lesson.get("summary", ""))
        lesson["thematic_blocks"] = [{
            "title": "Leçon complète",
            "start_seconds": 0,
            "end_seconds": 99999,
            "subthemes": [{
                "title": "Contenu",
                "htmlContent": f"<p>{full_text}</p>"
            }]
        }]
        continue
        
    for i, block in enumerate(blocks):
        start_sec = block.get("start_seconds", 0)
        end_sec = 99999
        if i < len(blocks) - 1:
            end_sec = blocks[i+1].get("start_seconds", 99999)
            
        block_segments = [s for s in segments if start_sec <= s.get("sec", 0) < end_sec]
        
        # Combine text
        combined_text = " ".join([s.get("text", "") for s in block_segments])
        if not combined_text:
            combined_text = lesson.get("full_text", "")
            
        # Add subthemes array
        block["subthemes"] = [{
            "title": "Introduction",
            "htmlContent": f"<p>{combined_text}</p>"
        }]
        
    # We can safely delete segments now, or keep them just in case.
    # Let's keep them for now, but the new system won't use them.

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print("Migration terminée avec succès.")
