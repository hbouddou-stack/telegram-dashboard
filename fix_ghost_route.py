import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the route for student_timeline and inject ghost_visitors right before it
target = "app.router.add_get('/api/admin/gateway/student_timeline', api_admin_gateway_student_timeline)"
new_route = "app.router.add_get('/api/admin/gateway/ghost_visitors', api_admin_gateway_ghost_visitors)\n    " + target

if "ghost_visitors" in c and "app.router" in c and "ghost_visitors" not in c[c.find("app.router"):c.find("app.router")+5000]:
    c = c.replace(target, new_route)
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Route injected")
elif "ghost_visitors" in c and "/api/admin/gateway/ghost_visitors" in c:
    print("Route already exists")
else:
    # Force inject before student_timeline route
    if target in c:
        c = c.replace(target, new_route)
        with io.open('main.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print("Force injected")
    else:
        print("ERROR: target route not found!")
        # Show all routes
        for line in c.split('\n'):
            if 'app.router.add_get' in line:
                print(line)
