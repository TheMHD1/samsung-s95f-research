set -eu
STAGE=/home/researcher/share/tmp/sdk_tools/researcher-live-cast
LOG=$STAGE/display-lock-trial-20261026.log
PIDFILE=$STAGE/display-lock-trial-20261026.pid
test ! -e "$LOG"
test ! -e "$PIDFILE"
dbus-send --system --print-reply --reply-timeout=1000 --dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display org.tizen.system.deviced.display.BurnInProtectionInProgress | grep -q 'int32 0'
date -u
cat /proc/uptime
dbus-send --system --print-reply --reply-timeout=1000 --dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display org.tizen.system.deviced.display.GetLockCount string:lcdon
umask 077
/usr/bin/dotnet "$STAGE/S95fDisplayLockTrial.dll" trial > "$LOG" 2>&1 < /dev/null &
TRIAL_PID=$!
printf '%s\n' "$TRIAL_PID" > "$PIDFILE"
sleep 2
cat "$LOG"
kill -0 "$TRIAL_PID"
dbus-send --system --print-reply --reply-timeout=1000 --dest=org.tizen.system.deviced /Org/Tizen/System/DeviceD/Display org.tizen.system.deviced.display.GetLockCount string:lcdon
