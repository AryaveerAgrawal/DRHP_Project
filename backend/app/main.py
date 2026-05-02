from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
from app.processor import process_file
from app.engine import run_ai_pipeline
import shutil, os, re

App = FastAPI()
os.makedirs("uploads", exist_ok=True)

App.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Single file ──────────────────────────────────────────────────────────────
@App.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    try:
        file_path = os.path.join("uploads", file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        _, raw_text = process_file(file_path)
        return run_ai_pipeline(None, raw_text)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Batch / folder upload ─────────────────────────────────────────────────────
@App.post("/upload-folder")
async def upload_folder(files: List[UploadFile] = File(...)):
    try:
        os.makedirs("uploads", exist_ok=True)

        # STEP 1 — Save all files, normalise names
        saved = []
        for file in files:
            # webkitRelativePath comes as folder/filename — keep just filename
            safe_name = file.filename.replace("\\", "/").split("/")[-1]
            # also capture the folder prefix sent by browser
            folder_prefix = file.filename.replace("\\", "/").split("/")[0] \
                            if "/" in file.filename.replace("\\", "/") else ""
            file_path = os.path.join("uploads", safe_name)
            with open(file_path, "wb") as buf:
                shutil.copyfileobj(file.file, buf)
            saved.append({"name": safe_name, "path": file_path, "folder": folder_prefix})
            print(f"Saved: {safe_name}  (folder={folder_prefix})")

        # STEP 2 — Group: parent = file whose name matches sh7_N exactly (no extra suffix like _board)
        #          e.g.  sh7_1.md  is parent;  sh7_1_board.md  is attachment
        def get_group_id(name):
            """Extract group prefix like 'sh7_1' from any filename."""
            m = re.match(r'(sh7_\d+)', name.lower())
            return m.group(1) if m else None

        def is_parent(name):
            """Parent = matches sh7_N.md exactly (no extra _word after number)."""
            return bool(re.match(r'sh7_\d+\.md$', name.lower()))

        groups = {}
        for f in saved:
            gid = get_group_id(f["name"])
            if not gid:
                print(f"  Skipping (no group id): {f['name']}")
                continue
            if gid not in groups:
                groups[gid] = {"parent": None, "attachments": []}
            if is_parent(f["name"]):
                groups[gid]["parent"] = f
            else:
                groups[gid]["attachments"].append(f)

        print(f"\nGroups found: {list(groups.keys())}")

        # STEP 3 — Process each group
        month_map = {
            "january":"01","february":"02","march":"03","april":"04",
            "may":"05","june":"06","july":"07","august":"08",
            "september":"09","october":"10","november":"11","december":"12"
        }

        def date_sort_key(row):
            date = row.get("date","")
            if "incorporation" in date.lower(): return "0000-00-00"
            m = re.match(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date, re.IGNORECASE)
            if m: return f"{m.group(3)}-{month_map.get(m.group(2).lower(),'00')}-{m.group(1).zfill(2)}"
            m = re.match(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', date, re.IGNORECASE)
            if m: return f"{m.group(3)}-{month_map.get(m.group(1).lower(),'00')}-{m.group(2).zfill(2)}"
            m = re.match(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})', date)
            if m: return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
            return date

        final_table = []
        group_classifications = {}
        company_name = "Not found"

        for gid, group in groups.items():
            if not group["parent"]:
                print(f"  No parent found for group {gid}, skipping")
                continue

            print(f"\nProcessing {gid}: parent={group['parent']['name']}, "
                  f"attachments={[a['name'] for a in group['attachments']]}")

            # Read parent SH-7
            _, parent_text = process_file(group["parent"]["path"])
            combined = parent_text

            # Append each attachment
            for att in group["attachments"]:
                _, att_text = process_file(att["path"])
                combined += f"\n\n--- Attachment: {att['name']} ---\n\n" + att_text

            # Run pipeline
            result = run_ai_pipeline(None, combined)
            group_classifications[gid] = result["result1_classification"]

            cap = result["result2_capital_table"]
            if cap.get("company_name") and cap["company_name"] != "Not found":
                company_name = cap["company_name"]

            for row in cap.get("capital_table", []):
                if row.get("to") in [None, "[UNCONFIRMED]"] and row.get("from") in [None, "[UNCONFIRMED]"]:
                    continue          # skip fully empty rows
                final_table.append({
                    "date":       row.get("date", "[UNCONFIRMED]"),
                    "from":       row.get("from", "[UNCONFIRMED]"),
                    "to":         row.get("to",   "[UNCONFIRMED]"),
                    "agm_egm":    row.get("agm_egm", "[UNCONFIRMED]"),
                    "source_doc": row.get("source_doc", "[UNCONFIRMED]"),
                    "group":      gid,
                })

        # STEP 4 — Sort chronologically
        final_table.sort(key=date_sort_key)

        # STEP 5 — Fix from/to chain (each row's from = previous row's to)
        for i in range(1, len(final_table)):
            prev_to = final_table[i-1]["to"]
            if final_table[i]["from"] in ["[UNCONFIRMED]", "-", "Not found", None]:
                final_table[i]["from"] = prev_to

        print(f"\nFinal table: {len(final_table)} row(s)")

        return {
            "message": f"Processed {len(groups)} SH-7 group(s)",
            "company_name": company_name,
            "groups_found": list(groups.keys()),
            "final_capital_table": final_table,
            "debug_classifications": group_classifications,
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})