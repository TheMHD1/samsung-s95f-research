set -eu
STATE=/opt/usr/home/owner/researcher-debloat-20261025
test "$(cat "$STATE/acr-before.txt")" = 'com.samsung.tv.acr|false'
test ! -s "$STATE/acr-peruser-before.txt"
DB=/opt/dbspace/.pkgmgr_parser.db
CURRENT=$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='com.samsung.tv.acr';")
if [ "$CURRENT" = true ]; then
    pkgcmd -A -t app -n com.samsung.tv.acr --uid 5001
elif [ -n "$CURRENT" ] && [ "$CURRENT" != false ]; then
    echo 'Unexpected ACR disable state; review before restoring.' >&2
    exit 1
fi
test "$(sqlite3 -readonly "$DB" "select app_disable from package_app_info where app_id='com.samsung.tv.acr';")" = false
echo 'ACR activation restored to its original false disable flag.'
sqlite3 -readonly -header "$DB" "select app_id,app_disable from package_app_info where app_id='com.samsung.tv.acr';"
