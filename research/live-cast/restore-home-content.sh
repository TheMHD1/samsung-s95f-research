set -eu
vconftool set -f -t string db/eden/homeRecommendation true
vconftool set -f -t string db/eden/launcher/list '{"version":"1.0.0","app_layer":{"max_tile":40,"list":[{"id":"3202509041599","p":"f","component_id":"d/webapp@3202509041599","t":"app"},{"id":"TVPLUS","p":"f","component_id":"s/livetv@TVPLUS","t":"tv"},{"id":"3201907018807","p":"t","component_id":"d/webapp@3201907018807","t":"app"},{"id":"3201910019365","p":"f","component_id":"d/webapp@3201910019365","t":"app"},{"id":"3201901017640","p":"f","component_id":"d/webapp@3201901017640","t":"app"},{"id":"111299001912","p":"f","component_id":"d/webapp@111299001912","t":"app"},{"id":"3201807016597","p":"f","component_id":"d/webapp@3201807016597","t":"app"},{"id":"3201606009684","p":"f","component_id":"d/webapp@3201606009684","t":"app"},{"id":"3202311033054","p":"f","component_id":"d/webapp@3202311033054","t":"app"},{"id":"3202205027543","p":"f","component_id":"d/webapp@3202205027543","t":"app"},{"id":"3202010022079","p":"f","component_id":"d/webapp@3202010022079","t":"app"}],"count":9}}'
app_launcher -k com.samsung.tv.home.media || true
sleep 1
app_launcher -s com.samsung.tv.home.media
vconftool get db/eden/homeRecommendation
vconftool get db/eden/launcher/list
