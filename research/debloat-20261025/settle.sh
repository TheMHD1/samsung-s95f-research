set -eu
STATE=/opt/usr/home/owner/researcher-debloat-20261025
test "$(cat "$STATE/apply.status")" = COMPLETE
echo INTENTIONAL_STOP_RESULTS
systemctl show adagent-service.service pisa-service.service -p Id -p ActiveState -p Result -p ExecMainCode -p ExecMainStatus -p NRestarts -p MainPID
# These two units were not failed in our initial snapshot. Deactivation killed
# their applications before the explicit stop arrived. Preserve the evidence,
# then clear only those intentional-stop flags after verifying the disable gate.
for unit in adagent-service.service pisa-service.service; do
    test "$(systemctl show "$unit" -p MainPID --value)" = 0
    test "$(cat /opt/usr/share/systemd/system/pisa-service)" = researcher-debloat-20261025
    if grep -Fx "$unit|failed" "$STATE/units.before" >/dev/null; then
        echo 'Preserving original failure flag.'
    else
        systemctl reset-failed "$unit"
    fi
done
echo FINAL_UNIT_STATES
systemctl show adagent-service.service pisa-service.service pisa-service.socket -p Id -p MainPID -p ActiveState
echo FAILED_UNITS
systemctl --failed --no-pager --no-legend
echo AD_START_GATE
systemctl show adagent-service.service -p Conditions
echo MARKER_CONTENTS
while IFS= read -r marker; do
    printf '%s|' "$marker"
    cat "/opt/usr/share/systemd/system/$marker"
done < "$STATE/markers.created"
echo STREAM_AUDIO_UNITS
systemctl list-units --all --no-pager --no-legend | grep -E 'muse-server|audioserver|audio-server|pulseaudio|source-service|connman.service|airplay-service-2|googlecast-service'
