## 1.5.0 (2025-01-05)

### Feat

- add new command !dl to download music from music name directly

### Refactor

- remove unused file

## 1.4.0 (2025-01-05)

### Feat

- everyone can now subscribe to an artist, each user will receive its own musics

### Fix

- send message to user using only its id, adapt db because we don't need guild id anymore

## 1.3.3 (2025-01-05)

### Fix

- fix artist reading error

## 1.3.2 (2025-01-05)

### Fix

- fix artist reading error

### Refactor

- avoid repeated requests for artists idx

## 1.3.1 (2025-01-05)

### Refactor

- Can now use spaces in discord commands
- last_update for next run removed
- last_update for next run
- last_update for next run
- debug done
- debug and undo commit
- debug
- bringing back birthday bot!
- replace last update with yesterday date
- fix '&' in title

## 1.3.0 (2024-12-02)

### Feat

- add init_bot.py script for bot initialization and setup
- run daily task

### Fix

- fix async call
- fix file extension
- async call for solo converting
- don't trigger method
- m4a file or webm
- error during error
- handling quota exceeded

### Refactor

- don't request to add artist

## 1.1.9 (2024-11-24)

### Fix

- handling m4a files instead of webm files
- handle quota exceeded errors
- fix path

## 1.1.4 (2024-11-24)

### Fix

- fix file extension
- async call for solo converting
- handling quota exceeded
- don't request to add artist
- handling m4a files instead of webm files
- download at the end
- get all now uses video duration to avoid long answer time

## 1.1.3 (2024-11-13)

### Fix

- error with view count
- heartbeat blocked warning

## 1.1.1 (2024-11-05)

### Fix

- update id extraction from url
- handling errors
- couldn't download some musics
- couldn't download some musics
- fix error with private message convertor

### Refactor

- bring back high quality image metadata
- bring back high quality image metadata

## 1.1.0 (2024-10-19)

### Feat

- add pre-commit-config.yaml for pre-commit checks

### Fix

- update pre-commit checks
- not using bare exeption, fixing function names

## 1.0.0 (2024-10-19)

### BREAKING CHANGE

- Global reformat, adding versioning.

### Feat

- using last_update date to limit requests

### Fix

- Fix channel_id request
- correct metadata
