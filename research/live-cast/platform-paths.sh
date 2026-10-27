set -eu
echo DEVELOPER_FILE
ls -l /home/researcher/apps_rw/com.samsung.tv.store/data/develop_mode
cat /home/researcher/apps_rw/com.samsung.tv.store/data/develop_mode
echo UNIT_PATHS
systemctl show -p UnitPath || true
cat /proc/mounts | grep -E ' /etc | /opt | / '
echo HOME_CONTENT
find /opt/usr/apps/com.samsung.tv.coba.newhome -maxdepth 3 -type f | head -35
echo HOME_RUNTIME
cat /opt/usr/apps/com.samsung.tv.home.media/tizen-manifest.xml
echo KEY_PATHS
strings /usr/bin/csfs | grep -Ei 'home_app|first_screen|KEY_HOME|HomeKey' | head -25 || true
echo DEVELOP_PATHS
strings /usr/sbin/sdbd | grep -Ei 'develop|host_ip|hostip' | head -30
echo ACTIVE_CORE
systemctl is-active muse-server.service source.service network.service pulseaudio.service || true
