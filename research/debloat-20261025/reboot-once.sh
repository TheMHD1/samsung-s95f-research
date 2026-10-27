set -eu
test "$(cat /opt/usr/home/owner/researcher-debloat-20261025/apply.status)" = COMPLETE
test -x /usr/bin/systemd-run
test "$(systemctl show researcher-debloat-reboot.timer -p LoadState --value)" = not-found
echo BEFORE_BOOT_ID
cat /proc/sys/kernel/random/boot_id
echo BEFORE_UPTIME
cat /proc/uptime
# Give the authenticated root session time to close and clean its staging.
# The transient timer exists only for this boot and schedules exactly one reboot.
systemd-run --unit=researcher-debloat-reboot --on-active=30s /usr/bin/systemctl reboot --no-block
systemctl show researcher-debloat-reboot.timer -p ActiveState -p NextElapseUSecMonotonic
