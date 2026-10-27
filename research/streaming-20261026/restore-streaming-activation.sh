set -eu
for APP in org.tizen.netflix-app org.tizen.primevideo org.tizen.primevideo-dummy org.tizen.primevideo_companionapp com.samsung.tv.cobalt-yt; do
 pkgcmd -D -t app -n "$APP" --uid 5001
done
