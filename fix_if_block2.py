import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# The exact bad string (what's currently in the file):
bad = "                switchModalTab('general');\n\n    \n\n\n            // Translation dictionaries"
# The fixed string (adding the closing } for the if block):
fixed = "                switchModalTab('general');\n            }\n\n            // Translation dictionaries"

if bad in c:
    c = c.replace(bad, fixed)
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("SUCCESS: Fixed! Added missing } to close the if(typeof setFunnelStep) block")
else:
    print("String not found - already fixed or different whitespace")
    # Count occurrences
    cnt = c.count("switchModalTab('general');")
    print(f"switchModalTab('general') found {cnt} times")
