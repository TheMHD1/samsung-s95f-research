set -eu
echo GHSERVICE_MANIFEST
cat /opt/usr/apps/com.samsung.tv.ghservice/tizen-manifest.xml
ls -lh /opt/usr/apps/com.samsung.tv.ghservice/bin/*dll /opt/usr/apps/com.samsung.tv.ghservice/bin/*json
echo HOME_DLL
base64 /opt/usr/apps/com.samsung.tv.home.media/bin/HomeMedia.dll
echo END_HOME_DLL
echo GH_MOUNT
cat /proc/mounts | grep -E 'ghservice| /opt '
echo FRAMEWORK_SIZE
ls -lh /usr/share/dotnet.tizen/framework/Tizen.Applications.Common.dll /usr/share/dotnet.tizen/framework/Tizen.NUI.dll
