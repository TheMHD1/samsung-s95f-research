sleep 105
grep -qx BUILD_ID=T-RSMFAKUC-0090-REL-202607141953 /etc/tizen-release || exit 70
enlightenment_info -hwc 0
sleep 1
enlightenment_info -hwc_wins
