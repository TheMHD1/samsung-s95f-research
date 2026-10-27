sleep 195
grep -qx BUILD_ID=T-RSMFAKUC-0090-REL-202607141953 /etc/tizen-release || exit 70
attempt=0
while test "$attempt" -lt 120; do
attempt=$((attempt + 1))
current=$(dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.factory-service /TIFacSerObj org.tizen.tv.factoryservice.GetItem int32:60802)
if ! printf "%s\n" "$current" | grep -qx '      int32 60802'; then sleep 10; continue; fi
printf "%s\n" "$current" | grep -qx '      string "Screen Saver Brightness"' || exit 71
if printf "%s\n" "$current" | grep -qx '      string "7"'; then printf "%s\n" "$current"; exit 0; fi
if printf "%s\n" "$current" | grep -qx '      string "0"'; then
result=$(dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.factory-service /TIFacSerObj org.tizen.tv.factoryservice.SetDecimalValue int32:60802 int32:7)
printf "%s\n" "$result"
printf "%s\n" "$result" | grep -qx '      int32 1' || { sleep 10; continue; }
else exit 72
fi
verified=$(dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.factory-service /TIFacSerObj org.tizen.tv.factoryservice.GetItem int32:60802)
if printf "%s\n" "$verified" | grep -qx '      int32 60802' && printf "%s\n" "$verified" | grep -qx '      string "Screen Saver Brightness"' && printf "%s\n" "$verified" | grep -qx '      string "7"'; then printf "%s\n" "$verified"; exit 0; fi
sleep 1
done
exit 73
