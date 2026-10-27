# Observed recovery sequence

On 2026-10-27, ordinary local Tizen key events navigated the cached Home page
from `d/ug.tab@ForYou` to `d/apps.tab`. The successful path was deliberately
stepwise: an initial **Right** moved focus from the sidebar into Home content;
two **Up** presses reached the tab-navigation level; the next **Right** changed
the cached tab to Live; one further **Right** changed it to Apps. Each key was
a stock `input_keyevent` keysym down/up pair held for 150 ms and each tab result
was checked after the key. Cached state is a software observation, not panel
light.

With Apps selected, one stock operation 41/mode 2 controller lifecycle ran.
The helper accepted the request and cleaned up. The owner then reported that
Apps was visible and the panel stayed on; later the screensaver was visible
while the panel remained on. This differs from the reported For You startup
case, which displayed briefly and then went black.

The bounded routine in `recover.py` automates only the checked navigation,
public reject checks, and one stock lifecycle request. It intentionally stops
before a post-reset wake key and requires an owner confirmation of the physical
picture. It is not evidence that the defect is permanently fixed.
