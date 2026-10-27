set -eu
echo CONFIGTOOLS

vconftool || true
echo STARTUP_SCRIPTS
ls -l /sbin/reboot /usr/bin/reboot /etc/profile /etc/rc.local /etc/systemd/system /opt/etc/profile /opt/usr/share/systemd/system 2>/dev/null || true
echo HOME_KEYS
vconftool list | grep -Ei 'smarthub|smart_hub|home_app|home.*app|autorun|auto_start|startup|start_screen|last_app|ads|advert|promotion|recommend|sponsor' || true
echo HOMEFILES
find /opt/usr/apps -maxdepth 3 -iname '*home*' -o -iname '*eden*' -o -iname '*recomm*' -o -iname '*adagent*' 2>/dev/null | head -80
echo CURRENT_APPS
app_launcher --status
