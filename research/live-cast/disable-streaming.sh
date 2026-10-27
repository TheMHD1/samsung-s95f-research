set -eu
umask 077
STATE=/opt/usr/home/owner/researcher-live-cast
DB=/opt/dbspace/.pkgmgr_parser.db
test ! -e "$STATE"
mkdir -m 700 "$STATE"
test ! -L "$STATE"
test ! -e "$STATE/apps.before"
APPS='30IKH0OX8U.TestBGService
30IKH0OX8U.cwservice
30IKH0OX8U.tilesservice
3KA0pm7a7V.TubiTV
3KA0pm7a7V.preview
9Ur5IzDKqV.TizenYouTube
AQKO41xyKP.AmazonAlexa
GHI3a0zMSx.Service
GHI3a0zMSx.XboxGamePass
MCmYXNxgcu.DisneyPlus
MCmYXNxgcu.DisneyPlusService
RBElmUtjfo.PerplexityAI
UWI92dRGJZ.MagellanTV
adplatform.ADPlayer
com.samsung.tv.ContentsBrowser
com.samsung.tv.ContentsBrowserDetail
com.samsung.tv.adplayer
com.samsung.tv.aria-dummy
com.samsung.tv.aria-video
com.samsung.tv.bixby-promotion
com.samsung.tv.coba.adagent
com.samsung.tv.cobalt-app-1566
com.samsung.tv.cobalt-app-2146
com.samsung.tv.cobalt-app-3436
com.samsung.tv.cobalt-app-3488
com.samsung.tv.cobalt-app-5494
com.samsung.tv.cobalt-app-6019
com.samsung.tv.cobalt-app-7507
com.samsung.tv.cobalt-app-8346
com.samsung.tv.cobalt-app-9224
com.samsung.tv.cobalt-app-9878
com.samsung.tv.cobalt-app-test
com.samsung.tv.cobalt-gpm
com.samsung.tv.cobalt-yt
com.samsung.tv.cobalt-ytkids
com.samsung.tv.cobalt-yttv
n00V5BRzYd.Empty2
org.tizen.netflix-app
org.tizen.primevideo
org.tizen.primevideo-dummy
org.tizen.primevideo_companionapp
rJeHak5zRg.ContinueWatchingService
rJeHak5zRg.Spotify
rJeHak5zRg.SpotifyService
rTn6ClEurC.Jellyfin
yL49PNFmjW.PromotionApp
yL49PNFmjW.service'
MARKERS=''
UNITS=''
# Validate every selected original state before making the first change.
for app in $APPS; do
    flag=$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='$app';")
    test "$flag" = false
    printf '%s|%s
' "$app" "$flag" >> "$STATE/apps.pending"
done
mv "$STATE/apps.pending" "$STATE/apps.before"
app_launcher --status > "$STATE/running.before"
for unit in $UNITS; do
    active=$(systemctl show "$unit" -p ActiveState --value)
    printf '%s|%s
' "$unit" "$active" >> "$STATE/units.before"
done
for marker in $MARKERS; do
    target=/opt/usr/share/systemd/system/$marker
    if [ ! -e "$target" ] && [ ! -L "$target" ]; then
        # Record intent before writing. Restoration checks our exact content.
        printf '%s
' "$marker" >> "$STATE/markers.created"
        (set -C; printf '%s
' researcher-debloat-20261025 > "$target")
    fi
done
for app in $APPS; do
    printf '%s
' "$app" >> "$STATE/apps.changed"
    pkgcmd -D -t app -n "$app" --uid 5001
    flag=$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='$app';")
    test "$flag" = true
    echo DISABLED:$app
done
# Stop only the approved components. Package contents remain installed.
for unit in $UNITS; do
    echo STOP_UNIT:$unit
    systemctl --no-block stop "$unit"
done
app_launcher --status > "$STATE/running.after-disable"
for app in $APPS; do
    if awk -v a="$app" '$1 == a { found=1 } END { exit !found }' "$STATE/running.after-disable"; then
        echo STOP_APP:$app
        app_launcher -k "$app"
    fi
done
printf '%s
' COMPLETE > "$STATE/apply.status"
echo APPLY_COMPLETE
