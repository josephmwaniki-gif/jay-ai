# Jay AI Windows Release Plan

## Current build status

The private source repository builds the Windows desktop prototype with PyInstaller on Python 3.12. The current workflow uploads a temporary GitHub Actions artifact; it does not create a permanent public download or install automatic updates.

## Distribution design

- Keep this source repository private.
- Publish compiled Windows ZIP packages to the separate public repository `josephmwaniki-gif/jay-ai-releases`.
- Package the complete `dist/JayAI/` directory, including `JayAI.exe` and its `_internal/` dependencies.
- Include a SHA-256 checksum for accidental-corruption detection.
- Do not treat a checksum hosted beside the ZIP as proof of publisher identity. A future updater must verify a signed manifest or equivalent trusted provenance before installing updates.
- Do not embed a personal GitHub token in the desktop application.

## Remaining release setup

1. Create `josephmwaniki-gif/jay-ai-releases` as a public repository containing compiled releases only.
2. Add a narrowly scoped GitHub token as the private source repository Actions secret `JAY_AI_RELEASES_TOKEN`; grant access only to the public releases repository and Contents write.
3. Add and test the workflow that builds the app, packages the full PyInstaller directory, calculates a checksum, and publishes a versioned GitHub Release.
4. Implement a per-user Windows installer under `%LOCALAPPDATA%`.
5. Implement the updater only after defining a signature-verification method, safe staging, app shutdown/restart, backup, and rollback.
6. Test installation and upgrade on a clean Windows environment before claiming automatic updates work.

## Current app limitations

The chat remains a UI prototype. Online AI, voice, news, weather, the intended cartoon avatar, a Windows installer, and automatic updates are not yet implemented.
