set -eu
tv_probe_dir=$(mktemp -d /tmp/researcher-kernel-abi-XXXXXX)
cleanup() {
 if test -d "$tv_probe_dir"; then
  rm -f "$tv_probe_dir/probe" "$tv_probe_dir/result"
  rmdir "$tv_probe_dir"
 fi
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
echo PROBE_BEGIN
date -u
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
echo "$tv_probe_dir"
grep -E '^(Uid|Gid|CapEff|NoNewPrivs|Seccomp):' /proc/self/status
printf %s '[encoded-payload-omitted]' | base64 -d > "$tv_probe_dir/probe"
test "$(sha256sum "$tv_probe_dir/probe" | awk '{print $1}')" = 7621e61295a1137bc542080bc43aab070b26a958f36560ad4531b0a61719fe2b
chmod 700 "$tv_probe_dir/probe"
probe_status=0
"$tv_probe_dir/probe" > "$tv_probe_dir/result" || probe_status=$?
echo "PROBE_EXIT=$probe_status"
echo RESULT_SIZE
wc -c "$tv_probe_dir/result"
echo RESULT_BASE64
base64 "$tv_probe_dir/result"
echo RESULT_SHA256
sha256sum "$tv_probe_dir/result"
echo RESULT_END
cat /proc/uptime
cleanup
trap - EXIT HUP INT TERM
test ! -e "$tv_probe_dir"
echo PRIVATE_TEMP_DIRECTORY_REMOVED

