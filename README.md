# apk-split-analysis

APK chunk split + CI decompile workspace (GitHub Actions).

- `apk_parts/` : 45MB chunks of the target APK
- `.github/workflows/analyze.yml` : reassemble + jadx/apktool decompile + keyword report
