# Bugs and Improvements

Below are the list of bugs found while reviewing and testing `src/storage_service.py`.

---

## Bug 1: Two methods exists with the wrong logic and are never called

**Severity**: High

**File**: `src/storage_service.py`

**Lines**: 35-41 (broken methods), 165-181 (actual working logic in `apply_special_rules` function)

**Description**: 
FileMetadata class has two methods `is_priority()` and `is_legal_document()` 
- That were clearly written to check if the file is priority or legal document
- But both of them check the `file_id` instead of the `filename`, so they will never return the correct result
- On top of that, neither of these methodsa are called anywhere.
- The real logic lives seperately in `apply_special_rules` function which correclt checks the `filename` 
- These two methods are dead code that would silently return wrong results if ever called

**Fix**: Replace `self.file_id` with `self.filename` in both methods and call them from `apply_special_rules` function or remove them entirely 

---

## Bug 2: No validation on file names

**Severity**: Medium

**File**: `src/storage_service.py`

**Description**: The upload handler does not validate the filename in any way.
- Files with special characters, very long names, or even path traversal pattern uploads without anu issue

**Steps to Reproduce**:
1. Upload a file names `file@#$%^&*().txt` : returns 201, accepted
2. Upload a file named `../../etc/passwd` : returns 201, accepted
3. Testcase: `tests/functional/test_file_operations.py::test_upload_file_with_special_characters`

**Expected Behavior**:
- Files with special characters should be rejected or sanitized
- Path traversal patterns should be rejected
- limit length of file name

**Actual Behavior**: Any name is accepted as valid

This is a security risk and cause real problems in production.

