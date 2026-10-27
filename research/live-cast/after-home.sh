set -eu
echo CURRENT_HOME_ROWS
sqlite3 -readonly -header /opt/usr/home/owner/apps_rw/com.samsung.tv.home.media/shared/trusted/sqlite.db "select componentID,elementID,visible,elementCount from TableEntity where componentID like 'd/ug%' or componentID like 'd/dhcategory%' or componentID like 'd/webapp%' or componentID like 'd/launcher%';"
echo CONTENT_CACHE
find /home/researcher/share/voltapps/firstscreen_data -maxdepth 2 -type f | head -25
echo DEV_STORE_DATA
ls -lh /home/researcher/apps_rw/com.samsung.tv.store/data | head -20
echo OPTIONAL_DOTNET_UNIT
systemctl cat com.samsung.tv.hybrid-aot-manager.service dotnet-init.service
