set -eu
echo BOOT_HELPER_FILES
ls -l /bin/systemctl /usr/bin/systemctl
printf FRAMEWORK:
base64 /usr/share/dotnet.tizen/framework/Tizen.Applications.Common.dll
printf END_FRAMEWORK
printf TIZEN:
base64 /usr/share/dotnet.tizen/framework/Tizen.dll
printf END_TIZEN
printf MANIFEST:
base64 /opt/usr/apps/com.samsung.tv.ghservice/tizen-manifest.xml
printf END_MANIFEST
printf ORIGINAL_GH_DLL:
base64 /opt/usr/apps/com.samsung.tv.ghservice/bin/com.samsung.tv.ghservice.dll
printf END_ORIGINAL_GH_DLL
