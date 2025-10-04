# Git Large Files Issue - Resolved

## Problem

When trying to push to GitHub, the following error occurred:

```
remote: error: File external/ffmpeg/bin/ffplay.exe is 169.16 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File external/ffmpeg/bin/ffmpeg.exe is 167.23 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File external/ffmpeg/bin/ffprobe.exe is 167.04 MB; this exceeds GitHub's file size limit of 100.00 MB
```

GitHub has a 100MB file size limit, but the FFmpeg binaries we installed locally were accidentally committed.

## Root Cause

1. The `install_ffmpeg.ps1` script downloaded FFmpeg binaries to `external/ffmpeg/`
2. The `.gitignore` file didn't have `external/` listed (it was reset)
3. The binaries were accidentally committed in commit `9f99240`
4. Git keeps files in history even after removal, so pushing failed

## Solution Applied

### Step 1: Remove from Git Tracking
```powershell
git rm -r --cached external/
```

### Step 2: Update .gitignore
Added `external/` to `.gitignore`:
```gitignore
# External binaries
external/
```

### Step 3: Remove from Git History
Used `git filter-branch` to remove the files from all commits:
```powershell
git filter-branch --force --index-filter "git rm -r --cached --ignore-unmatch external/" --prune-empty --tag-name-filter cat -- --all
```

### Step 4: Clean Up and Force Push
```powershell
# Garbage collect old references
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push to update remote
git push --force origin main
```

## Result

✅ **Push successful!**
- Large files removed from git history
- FFmpeg binaries still available locally in `external/ffmpeg/`
- `.gitignore` properly configured to prevent future commits
- Repository size significantly reduced

## Verification

```powershell
# Git status is clean
PS> git status
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean

# FFmpeg still works locally
PS> Test-Path external\ffmpeg\bin\ffmpeg.exe
True
```

## Lessons Learned

1. **Always check .gitignore before committing** - Especially when adding large binary files
2. **Test locally first** - Run FFmpeg installation script and verify it's gitignored before committing
3. **Large files need special handling** - GitHub has a 100MB limit; use Git LFS for larger files if needed
4. **Force push with caution** - Only use `--force` when necessary and ensure no one else is working on the same branch

## Prevention for Future

The `.gitignore` now includes:
```gitignore
# External binaries
external/
```

This ensures:
- ✅ FFmpeg binaries are never committed
- ✅ Local installations work without affecting git
- ✅ Team members can install FFmpeg independently
- ✅ Repository stays lightweight

## For Other Team Members

If you cloned the repo before this fix, you may have large files in your local history. To clean up:

```powershell
# Fetch the cleaned history
git fetch origin

# Reset your main branch
git reset --hard origin/main

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## FFmpeg Installation

FFmpeg is **not** in the repository. Each developer must install it:

### Option 1: Run the Script
```powershell
.\install_ffmpeg.ps1
```

### Option 2: System-wide Installation
- Windows: `choco install ffmpeg`
- macOS: `brew install ffmpeg`  
- Linux: `sudo apt install ffmpeg`

See [SETUP_FFMPEG.md](SETUP_FFMPEG.md) for details.

---

**Status**: ✅ Resolved
**Repository Size**: Reduced by ~500MB
**FFmpeg Status**: Available locally, excluded from git
