# Managed fixed UI-tab launch helper

This is an offline-built, dry-by-default normal Tizen `AppControl` sender. It
supports only the CSFS Apps and For You page identifiers. It does not send a
key, patch UI state, modify persistent settings, retry, or claim that a
successful API return proves a visible physical transition.

The host wrapper separates preparation, each single send, and cleanup so the
managed assembly and its three pinned framework dependencies can be staged before a bounded
logger window. No command is run against the TV during build or verification.

Live use requires an independently reviewed `build-manifest.json` hash:

```text
run-once.py --prepare --manifest-sha256 HASH --output NEW_ABSOLUTE_DIRECTORY
run-once.py --send --prepared PREPARED_JSON --apps --output NEW_ABSOLUTE_DIRECTORY
run-once.py --send --prepared PREPARED_JSON --for-you --output NEW_ABSOLUTE_DIRECTORY
run-once.py --cleanup --prepared PREPARED_JSON --output NEW_ABSOLUTE_DIRECTORY
```

Each action directory retains the full authenticated root transport response.
The private stage is deleted only by the separate cleanup command after its
inventory, ownership, modes, sizes, and hashes all match.
