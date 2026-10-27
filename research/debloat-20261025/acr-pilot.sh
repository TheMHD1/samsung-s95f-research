set -eu
umask 077
STATE=/opt/usr/home/owner/researcher-debloat-20261025
test ! -e "$STATE"
test ! -L "$STATE"
mkdir -m 700 "$STATE"
DB=/opt/dbspace/.pkgmgr_parser.db
sqlite3 -readonly "$DB" "select app_id,app_disable from package_app_info where app_id='com.samsung.tv.acr';" > "$STATE/acr-before.txt"
sqlite3 -readonly "$DB" "select * from package_app_info_for_uid where app_id='com.samsung.tv.acr';" > "$STATE/acr-peruser-before.txt"
test "$(cat "$STATE/acr-before.txt")" = 'com.samsung.tv.acr|false'
test ! -s "$STATE/acr-peruser-before.txt"
echo 'PROGRAM_LABEL: deactivate ACR for owner UID 5001; no package deletion'
set +e
pkgcmd -D -t app -n com.samsung.tv.acr --uid 5001
RESULT=$?
set -e
echo "PKGCMD_EXIT=$RESULT"
echo AFTER
sqlite3 -readonly -header "$DB" "select app_id,app_disable from package_app_info where app_id='com.samsung.tv.acr'; select * from package_app_info_for_uid where app_id='com.samsung.tv.acr';"
echo PROCESS
ps -eo pid,uid,rss,comm | grep -E 'ACRService|acr' || true
