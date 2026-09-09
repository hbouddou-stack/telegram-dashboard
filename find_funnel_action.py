with open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'function sendFunnelAction' in line:
            print(f"sendFunnelAction at line {i+1}")
