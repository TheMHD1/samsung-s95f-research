set -eu
echo REBOOT_TEST_EVIDENCE
systemctl show researcher-debloat-reboot.service -p Id -p ActiveState -p Result -p ExecMainCode -p ExecMainStatus
echo BOOT_ID
cat /proc/sys/kernel/random/boot_id
# Retire only our completed one-shot test, preserving the captured failure.
systemctl stop researcher-debloat-reboot.timer
systemctl reset-failed researcher-debloat-reboot.service
echo REBOOT_TIMER_FINAL
systemctl show researcher-debloat-reboot.timer -p LoadState -p ActiveState
echo FAILED_UNITS
systemctl --failed --no-pager --no-legend
echo STATUS
cat /opt/usr/home/owner/researcher-debloat-20261025/apply.status
echo FINAL_CORE
systemctl show muse-server.service source-service.service connman.service pulseaudio.service -p Id -p ActiveState -p MainPID -p NRestarts
