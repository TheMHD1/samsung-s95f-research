set -eu
DB=/opt/dbspace/.pkgmgr_parser.db
echo PACKAGES
sqlite3 -readonly -header -separator '|' "$DB" "select package,package_type,package_support_disable,package_disable,root_path from package_info where package in ('com.samsung.tv.acr-service-app','com.samsung.tv.pisa-service','com.samsung.tizen.samsung-analytics','com.samsung.tv.targeted-ad-service');"
echo APPLICATIONS
sqlite3 -readonly -header -separator '|' "$DB" "select app_id,package,app_support_disable,app_disable,app_onboot,app_autorestart from package_app_info where package in ('com.samsung.tv.acr-service-app','com.samsung.tv.pisa-service','com.samsung.tizen.samsung-analytics','com.samsung.tv.targeted-ad-service');"
echo PERUSER
sqlite3 -readonly -header -separator '|' "$DB" "select * from package_app_info_for_uid where app_id in ('com.samsung.tv.acr','com.samsung.tv.adagent-service','com.samsung.tizen.samsung-analytics','com.samsung.tv.targeted-ad-service');"
echo DEPENDENCIES
sqlite3 -readonly -header -separator '|' "$DB" "select * from package_dependency_info where depends_on in ('com.samsung.tv.acr-service-app','com.samsung.tv.pisa-service','com.samsung.tizen.samsung-analytics','com.samsung.tv.targeted-ad-service');"
echo UNITCONDITIONS
systemctl cat pisa-service.service pisa-service.socket
echo CORE
systemctl show muse-server.service connman.service sdbd.service display-manager.service source-service.service -p Id -p LoadState -p ActiveState -p MainPID -p NRestarts
