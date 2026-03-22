# Test Strategy - Cloud Storage Tiering System

The system moves files between 3 tiers: HOT, WARM, COLD - Based on how frequently files are accessed.

This document covers what all I tested, how I tested it, and what I found.

--- 

## APIs Tested
| Category | Endpoint | Purpose |
|---|---|---|
| File Ops | `POST /files` | Upload a file |
| File Ops | `GET /files/{fileId}` | Download a file |
| File Ops | `GET /files/{fileId}/metadata` | Get file metadata |
| File Ops | `DELETE /files/{fileId}` | Delete a file |
| Admin | `POST /admin/tiering/run` | Trigger tier transitions |
| Admin | `GET /admin/stats` | Get system-wide stats |

---

## Tiering Rules
```
HOT to WARM: After 30 days of inactivity
WARM to COLD: After 90 days of inactivity, LEGAL_HOLD files get 180 days before moving to COLD
_PRIORITY files are always kept in HOT tier
```

## What I Tested

### Upload (POST /files)
- Valid file (1MB to 10GB) : 201, file lands in HOT tier
- Below 1MB file: 400
- Above 10GB file: 400
- Exactly 1MB file: 201, file lands in HOT tier
- Exactly 10GB file: 201, file lands in HOT tier
- 1MB minus 1 byte file: fails
- 0 byte and 0.9MB files: fails
- File with special characters in name (#$%): passes (suspicious but allowed)
- metadata with valid values: passes

### Download (GET /files/{fileId})
- Existing file: 200
- Non-existing file: 404
- invalid file ID: 404
- `last_accessed` field in metadata: updated on download

### Metadata (GET /files/{fileId}/metadata)
- valid file: 200, all fields present and correct (`file_id`, `filename`, `size`, `tier`, `created_at`, `last_accessed`)
- non-existing file: 404

### Delete (DELETE /files/{fileId})
- valid file: 204, content and metadata both deleted
- follow-up get request after delete returns 404
- non-existing file: 404
- delete same file twice: first gets 204, second gets 404

### Tiering (POST /admin/tiering/run)
- 29 days: stays in HOT
- 30 days: moves to WARM
- 31 days: moves in WARM
- 89 days in WARM: stays in WARM
- 90 days in WARM: moves to COLD
- 91 days in WARM: moves to COLD
- file already in COLD: stays in COLD
- `_PRIORIY_` files in 90 days: stays in HOT
- `LEGAL_` file at 120 days in warm: stays in WARM
- `LEGAL_` file at 179 days in warm: stays in WARM
- `LEGAL_` file at 181 days in warm: moves to COLD

### Fetch Stats (GET /admin/stats)
- Empty system: all zero
- Single upload: correct count and size
- Multiple uploads: total adds up
- Files accross HOT and WARM: per tier count are accuratre
- after deletion: count and size drops correctly

---

## Performance and Concurrency

- 10 simultaneous uploads: all succeed, not duplicate ids
- 10 simultaneous downloads of the same file: all succeed
- Tearing run on 50 files: all move correctly

---

## FAult Injection

- Storage goes down mid download: return 500, doesn't hang
- content missing but metadata present (corrupted state): return 500

---

## Test Data

**File Sizes:** 0 bytes | 500KB | 0.9MB | 1MB | 5MB | 10GB | 10GB + 1 byte | 11GB

**File Names:** test_file.txt | file@$m%.txt | _PRIORIY_report.txt | LEGAL_contract.txt

**Time Intervals:** 0 | 29 | 30 | 31 | 89 | 90 | 91 | 120 | 179 | 181

---

## Results

- Total Testcases: 38
- Passed: 35
- Skipped: 3 (10GB test skipped intentionally to avoid allocating real memory)
- Bugs found and documented in `BUGS_AND_IMPROVEMENTS.md`












