import re

def update_to_300ms():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    old_timeout = "if (Date.now() - lastUserScrollTime > 500 && !isTouching)"
    new_timeout = "if (Date.now() - lastUserScrollTime > 300 && !isTouching)"

    if old_timeout in js:
        js = js.replace(old_timeout, new_timeout)
        with open('reader.js', 'w', encoding='utf-8') as f:
            f.write(js)
        print("Updated to 300ms snapback")
    else:
        print("Could not find 500ms timeout block")

if __name__ == '__main__':
    update_to_300ms()
