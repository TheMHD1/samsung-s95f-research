#!/bin/sh
set -eu
umask 077
cd /tmp/researcher-launch-qual-ddb7ac47a0b24f3baeaba4651070f3ed
test "$(pwd)" = /tmp/researcher-launch-qual-ddb7ac47a0b24f3baeaba4651070f3ed
p=$$
test ! -e marker.pid.tmp; test ! -e marker.pid
printf '%s
' "$p" > marker.pid.tmp
chmod 600 marker.pid.tmp
mv marker.pid.tmp marker.pid
test ! -e marker.stat.tmp; test ! -e marker.stat
cat "/proc/$p/stat" > marker.stat.tmp
chmod 600 marker.stat.tmp
mv marker.stat.tmp marker.stat
test ! -e marker.start.tmp; test ! -e marker.start
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf 'BOOT=%s
UPTIME=%s
' "$boot" "$up" > marker.start.tmp
chmod 600 marker.start.tmp
mv marker.start.tmp marker.start
sleep 3
test ! -e marker.done.tmp; test ! -e marker.done
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf 'BOOT=%s
UPTIME=%s
' "$boot" "$up" > marker.done.tmp
chmod 600 marker.done.tmp
mv marker.done.tmp marker.done
