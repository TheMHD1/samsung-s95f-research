#!/bin/sh
set -u
umask 077
cd /tmp/researcher-usb-onset-00000000000000000000000000000000 || exit 91
printf '%s\n' "$$" > supervisor.pid.tmp
mv supervisor.pid.tmp supervisor.pid
cat /proc/$$/stat > supervisor.stat.tmp
mv supervisor.stat.tmp supervisor.stat
rc=0
/usr/bin/dotnet /tmp/researcher-usb-onset-00000000000000000000000000000000/ManagedUsbSecondaryLoggerOnset.dll --execute > native.stdout 2> native.stderr </dev/null &
child=$!
printf '%s\n' "$child" > native.pid.tmp
mv native.pid.tmp native.pid
wait "$child" || rc=$?
out_bytes=$(wc -c < native.stdout)
err_bytes=$(wc -c < native.stderr)
out_sha=$(sha256sum native.stdout | cut -d ' ' -f1)
err_sha=$(sha256sum native.stderr | cut -d ' ' -f1)
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf '{"schema":"secondary-logger-onset-exit-v1","supervisor_pid":%s,"child_pid":%s,"child_exit":%s,"stdout_bytes":%s,"stderr_bytes":%s,"stdout_sha256":"%s","stderr_sha256":"%s","boot_id":"%s","uptime":"%s"}\n' "$$" "$child" "$rc" "$out_bytes" "$err_bytes" "$out_sha" "$err_sha" "$boot" "$up" > native.exit.tmp
mv native.exit.tmp native.exit
