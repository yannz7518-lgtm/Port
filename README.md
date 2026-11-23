# Chess Titans Android Port

A native Android reimplementation/prototype inspired by the Windows 7 Chess Titans game. This is **not yet a full original-game port** and does not currently render the original 3D assets or sound.

## Current prototype
- Native Android landscape UI and board renderer
- Legal chess move generation, check/checkmate and stalemate
- Castling, en passant, automatic queen promotion
- Undo, restart, two-player local mode
- Play vs computer, player-side selection, three difficulty levels
- 50-move rule, threefold repetition, basic insufficient-material detection
- Wood / classic green / marble board themes and last-move highlight
- Unit tests for initial move count, move/undo, check restrictions, promotion, castling and en passant

## Build
The GitHub Actions workflow runs unit tests and builds a debug APK on pushes.

Locally with Android SDK installed:
```bash
gradle testDebugUnitTest assembleDebug
```

APK output:
`app/build/outputs/apk/debug/app-debug.apk`

## Still missing for a faithful port
- Original Chess Titans 3D models, textures, materials, environments and camera
- Original sound and animations
- Original menus, visual effects, hints and difficulty/AI behavior
- Full fidelity reverse engineering of the original binary assets and game logic
- Device testing and a verified APK release
