import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# I will find the block starting with `<span id="f-date-group-joined"`
# and ending before `<div style="display:flex; flex-direction:column; gap:8px; margin-bottom:18px;`

start_marker = '<span id="f-date-group-joined" dir="ltr" style="font-weight:bold;">-</span>'
end_marker = '<div style="display:flex; flex-direction:column; gap:8px; margin-bottom:18px; width: 100%; box-sizing:border-box;">'

idx1 = c.find(start_marker)
idx2 = c.find(end_marker)

if idx1 != -1 and idx2 != -1:
    chunk = c[idx1 + len(start_marker):idx2]
    print("Found chunk to replace:")
    print(repr(chunk))
    
    # We want exactly 6 closing divs.
    # 1. close timeline-sub-item
    # 2. close timeline-subs
    # 3. close timeline-content
    # 4. close timeline-block
    # 5. close timeline
    # 6. close mcontent-funnel
    
    new_chunk = '''
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

            '''
    
    c = c[:idx1 + len(start_marker)] + new_chunk + c[idx2:]
    
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Fixed!")
else:
    print("Could not find markers")
