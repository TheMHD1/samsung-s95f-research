set -eu
umask 077
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
test "$(id -u)" = 0
test "$(id -g)" = 0
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5
test -d /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5)" = "0:0:700"
count=0
for item in /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/* /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/.[!.]* /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/..?*; do
  test -e "$item" || test -L "$item" || continue
  name=${item##*/}
  case "$name" in CombinedEventSuccessor.deps.json|CombinedEventSuccessor.dll|CombinedEventSuccessor.runtimeconfig.json|baseline-ring.bin|native.receipt.json|native.stderr|native.stdout|post-ring.bin|selftest.receipt.json|selftest.stderr|selftest.stdout) ;; *) exit 91 ;; esac
  count=$((count+1))
done
test "$count" = 11
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.deps.json
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.deps.json
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.deps.json)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.deps.json)" = 436
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.deps.json | cut -d " " -f1)" = d5abe1cdb55778c53f779dc55f5995672b8cbbb5c794056f21aeeee961867483
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.dll
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.dll
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.dll)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.dll)" = 102400
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.dll | cut -d " " -f1)" = 1628ccfc09d761707a0241e9e3b66a03b85a85470dbef4c93d6758bd634ad9b2
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.runtimeconfig.json
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.runtimeconfig.json
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.runtimeconfig.json)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.runtimeconfig.json)" = 242
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/CombinedEventSuccessor.runtimeconfig.json | cut -d " " -f1)" = aeb46a15366e38511c192ccf65312442c64e8753b3c16fd2ca0b4cb34a5c59f3
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.receipt.json
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.receipt.json
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.receipt.json)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.receipt.json)" = 44
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.receipt.json | cut -d " " -f1)" = cc111d72682af87f681480654dce46d7edcad50c69b65b82679c5a99eeca63cd
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stdout
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stdout
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stdout)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stdout)" = 109
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stdout | cut -d " " -f1)" = 1dddb0b9d284048eabd3cd954cb3970124d0157e91f61bef4c1697890f9ba928
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stderr
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stderr
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stderr)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stderr)" = 0
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/selftest.stderr | cut -d " " -f1)" = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.receipt.json
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.receipt.json
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.receipt.json)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.receipt.json)" = 2263
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.receipt.json | cut -d " " -f1)" = 6a74a98bfc668c04007359395ceee5f6ba829dba9915a91c382d130d8092c940
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stdout
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stdout
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stdout)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stdout)" = 109
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stdout | cut -d " " -f1)" = 9c7f3ba12b76b649a2daa964304f38b59d0c2d58184eaffa4022ee453119bac8
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stderr
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stderr
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stderr)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stderr)" = 0
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/native.stderr | cut -d " " -f1)" = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/baseline-ring.bin
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/baseline-ring.bin
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/baseline-ring.bin)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/baseline-ring.bin)" = 15372
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/baseline-ring.bin | cut -d " " -f1)" = 275e8bdbdeeb670429190cc7136d2715dcd2b25921ab7e6c2e8038f5a543b5f9
test ! -L /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/post-ring.bin
test -f /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/post-ring.bin
test "$(stat -c "%u:%g:%a" /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/post-ring.bin)" = "0:0:600"
test "$(wc -c < /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/post-ring.bin)" = 0
test "$(sha256sum /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/post-ring.bin | cut -d " " -f1)" = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
echo FN_SIDECAR_BEGIN
base64 /tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5/baseline-ring.bin
echo FN_SIDECAR_END
