set -eu
echo BOOT_ID
cat /proc/sys/kernel/random/boot_id
echo APPLICATIONS
sqlite3 -readonly -header -separator '|' /opt/dbspace/.pkgmgr_parser.db "select a.app_id,a.package,a.app_type,a.app_disable,a.app_root_path,l.app_label from package_app_info a left join package_app_localized_info l on a.app_id=l.app_id and l.app_locale='No Locale' order by a.app_id;"
echo CONFIGTOOLS
vconftool --help
echo STARTUP_SCRIPTS
ls -l /sbin/reboot /usr/bin/reboot /etc/profile /etc/rc.local /etc/systemd/system /opt/etc/profile /opt/usr/share/systemd/system 2>/dev/null || true
echo HOME_KEYS
vconftool list | grep -Ei 'smarthub|smart_hub|home_app|home.*app|autorun|auto_start|startup|start_screen|last_app|ads|advert|promotion|recommend|sponsor' || true
echo HOMEFILES
find /opt/usr/apps -maxdepth 3 -iname '*home*' -o -iname '*eden*' -o -iname '*recomm*' -o -iname '*adagent*' 2>/dev/null | head -80
echo CURRENT_APPS
app_launcher --status
