with open('dashboard/reader.html', 'rb') as f:
    lines = f.readlines()

print('Lines 1160-1188:')
for i in range(1159, 1188):
    try:
        print(f'{i+1}: {lines[i].decode("utf-8").strip()}')
    except Exception as e:
        print(f'{i+1}: ERROR DECODING')
