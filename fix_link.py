import subprocess

result = subprocess.run(['git', 'show', 'b5fe66ee:dashboard/link.html'], capture_output=True)
content = result.stdout.decode('utf-8')

old_block = """            } else if (type === 'month') {
                title.innerText = 'اختيار الشهر';
                for(let i=1; i<=12; i++) items.push({val: i<10?'0'+i:i, label: i});
            } else if (type === 'year') {"""

new_block = """            } else if (type === 'month') {
                title.innerText = 'اختيار الشهر';
                const months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
                for(let i=1; i<=12; i++) items.push({val: i<10?'0'+i:i, label: months[i-1]});
            } else if (type === 'year') {"""

content = content.replace(old_block, new_block)

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\dashboard\link.html', 'w', encoding='utf-8') as f:
    f.write(content)
