import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace the HTML
old_crm_content = re.search(r'<div id="mcontent-crm".*?<!-- Tab 4: Funnel -->', c, re.DOTALL)
if old_crm_content:
    new_crm_html = r'''<div id="mcontent-crm" class="mcontent" style="flex-direction:column; flex:1; overflow:hidden;">
                <!-- Top Action Area -->
                <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:15px; margin-bottom:15px;">
                    <h4 style="margin:0 0 10px 0; font-size:0.9rem; color:var(--text1);">➕ إضافة ملاحظة CRM</h4>
                    <div style="display:flex; gap:10px; margin-bottom:10px;">
                        <select id="crm-type" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; flex:1;">
                            <option value="APPEL">📞 اتصال عادي</option>
                            <option value="APPEL_WA">📞 اتصال واتساب</option>
                            <option value="WHATSAPP">💬 رسالة واتساب</option>
                            <option value="TELEGRAM">✈️ تيليجرام</option>
                            <option value="EMAIL">📧 بريد إلكتروني</option>
                            <option value="AUTRE">📌 أخرى</option>
                        </select>
                        <select id="crm-tag" style="padding:8px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); outline:none; flex:1;">
                            <option value="TECHNIQUE">⚙️ مشكلة تقنية</option>
                            <option value="REMBOURSEMENT">💳 استرداد أموال</option>
                            <option value="MALADIE">🏥 مرض</option>
                            <option value="VOYAGE">✈️ سفر</option>
                            <option value="MOTIVATION">📉 نقص تحفيز</option>
                            <option value="INFO">ℹ️ معلومة</option>
                            <option value="AUTRE">📌 أخرى</option>
                        </select>
                    </div>
                    <textarea id="crm-note" placeholder="تفاصيل المحادثة..." style="width:100%; height:60px; padding:10px; box-sizing:border-box; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-family:inherit; outline:none; resize:none; margin-bottom:10px;"></textarea>
                    <button class="btn btn-primary" onclick="addCrmNote()" style="width:100%; padding:10px; border-radius:8px;">💾 حفظ الملاحظة</button>
                </div>

                <!-- Filters -->
                <div style="display:flex; gap:10px; margin-bottom:15px; overflow-x:auto; padding-bottom:5px; flex-shrink:0;">
                    <div class="chip crm-filter active" onclick="filterCrm('all')" id="crm-flt-all" style="cursor:pointer; background:rgba(10,132,255,0.15); color:#0a84ff; border-color:#0a84ff;">🔘 عرض الكل</div>
                    <div class="chip crm-filter" onclick="filterCrm('notes')" id="crm-flt-notes" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🗣️ الملاحظات</div>
                    <div class="chip crm-filter" onclick="filterCrm('tickets')" id="crm-flt-tickets" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🚨 التذاكر</div>
                    <div class="chip crm-filter" onclick="filterCrm('system')" id="crm-flt-system" style="cursor:pointer; background:var(--surface); color:var(--text2); border-color:var(--border);">🤖 النظام</div>
                </div>

                <!-- Timeline -->
                <div id="crm-timeline-container" style="flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:12px; padding-right:5px; margin-bottom:20px;">
                    <!-- JS populated -->
                </div>
            </div>

            <!-- Tab 4: Funnel -->'''
    c = c.replace(old_crm_content.group(0), new_crm_html)
    print("Replaced CRM HTML")
else:
    print("COULD NOT FIND mcontent-crm block")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
