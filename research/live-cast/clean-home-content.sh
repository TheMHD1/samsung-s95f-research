set -eu
umask 077
STATE=/opt/usr/home/owner/researcher-live-cast
test "$(cat "$STATE/apply.status")" = COMPLETE
test ! -e "$STATE/home-content.applied"
vconftool get db/eden/homeRecommendation > "$STATE/recommendation.before"
vconftool get db/eden/launcher/list > "$STATE/launcher.before"
sqlite3 /opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted/sqlite.db ".backup $STATE/home-media.before.db"
restore_preferences() {
    vconftool set -f -t string db/eden/homeRecommendation true
    vconftool set -f -t string db/eden/launcher/list '{"version":"1.0.0","app_layer":{"max_tile":40,"list":[{"id":"3202509041599","p":"f","component_id":"d/webapp@3202509041599","t":"app"},{"id":"TVPLUS","p":"f","component_id":"s/livetv@TVPLUS","t":"tv"},{"id":"3201907018807","p":"t","component_id":"d/webapp@3201907018807","t":"app"},{"id":"3201910019365","p":"f","component_id":"d/webapp@3201910019365","t":"app"},{"id":"3201901017640","p":"f","component_id":"d/webapp@3201901017640","t":"app"},{"id":"111299001912","p":"f","component_id":"d/webapp@111299001912","t":"app"},{"id":"3201807016597","p":"f","component_id":"d/webapp@3201807016597","t":"app"},{"id":"3201606009684","p":"f","component_id":"d/webapp@3201606009684","t":"app"},{"id":"3202311033054","p":"f","component_id":"d/webapp@3202311033054","t":"app"},{"id":"3202205027543","p":"f","component_id":"d/webapp@3202205027543","t":"app"},{"id":"3202010022079","p":"f","component_id":"d/webapp@3202010022079","t":"app"}],"count":9}}'
}
trap restore_preferences EXIT
vconftool set -f -t string db/eden/homeRecommendation false
vconftool set -f -t string db/eden/launcher/list '{"version":"1.0.0","app_layer":{"max_tile":40,"list":[{"id":"TVPLUS","p":"f","component_id":"s/livetv@TVPLUS","t":"tv"}],"count":1}}'
echo PREFERENCE_READBACK
vconftool get db/eden/homeRecommendation
vconftool get db/eden/launcher/list
# Rebuild only the Home media component's cached tiles and recommendations.
app_launcher -k com.samsung.tv.home.media
sleep 1
app_launcher -s com.samsung.tv.home.media
sleep 3
echo HOME_MEDIA_RUNNING
app_launcher --status | grep -F 'com.samsung.tv.home.media ('
printf 'COMPLETE
' > "$STATE/home-content.applied"
trap - EXIT
