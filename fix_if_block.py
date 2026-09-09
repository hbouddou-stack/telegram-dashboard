import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# The exact bug: the if(typeof setFunnelStep) block is opened at line 2296
# but switchModalTab('general'); is INSIDE the block (no closing } before it)
# and the rest of the code (translations, modal open, logs) are all trapped inside.
# We need to close the if-block RIGHT AFTER the switchModalTab call.

# Current bad code (the if block is never closed):
bad = """                switchModalTab('general');
    


            // Translation dictionaries"""

# Fixed code (closing the if block before translations):
fixed = """                switchModalTab('general');
            }

            // Translation dictionaries"""

if bad in c:
    c = c.replace(bad, fixed)
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("SUCCESS: Fixed closing brace of if(typeof setFunnelStep) block")
else:
    # Try to find what's actually there
    idx = c.find("switchModalTab('general');")
    print("Current context around switchModalTab:")
    print(repr(c[idx-20:idx+200]))
