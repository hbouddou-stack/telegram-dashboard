let dupCurrentView = 'cards'; // 'cards' or 'table'
        let dupLastGroups = [];

        function setDupView(mode) {
            dupCurrentView = mode;
            document.getElementById('dup-view-cards').style.background = mode === 'cards' ? 'var(--accent)' : 'var(--bg)';
            document.getElementById('dup-view-cards').style.color = mode === 'cards' ? 'white' : 'var(--text2)';
            document.getElementById('dup-view-cards').style.border = mode === 'cards' ? 'none' : '1px solid var(--border)';
            document.getElementById('dup-view-table').style.background = mode === 'table' ? 'var(--accent)' : 'var(--bg)';
            document.getElementById('dup-view-table').style.color = mode === 'table' ? 'white' : 'var(--text2)';
            document.getElementById('dup-view-table').style.border = mode === 'table' ? 'none' : '1px solid var(--border)';
            renderDuplicateGroups(dupLastGroups);
        }

        function closeDuplicateScanner() {
            const modal = document.getElementById('modal-duplicates');
            modal.style.display = 'none';
        }

        function openDuplicateScanner() {
            const modal = document.getElementById('modal-duplicates');
            const container = document.getElementById('duplicates-container');
            
            if (!modal || !container) { alert('خطأ: العنصر غير موجود'); return; }
            
            // Move to body to escape any overflow:hidden parent (Telegram WebView fix)
            document.body.appendChild(modal);
            
            modal.style.cssText = 'display:flex !important; position:fixed !important; top:0 !important; left:0 !important; right:0 !important; bottom:0 !important; width:100% !important; height:100% !important; z-index:2147483647 !important; background:rgba(0,0,0,0.88) !important; align-items:flex-end !important; justify-content:center !important; margin:0 !important; padding:0 !important;';
            
            // Determine which students to scan: currently filtered subset
            // We use the same filtering logic applied on screen
            const q = (document.getElementById('search-input') ? document.getElementById('search-input').value.toLowerCase() : '');
            const payFilter = typeof currentPayFilter !== 'undefined' ? currentPayFilter : 'all';
            const linkFilter = typeof currentLinkFilter !== 'undefined' ? currentLinkFilter : 'all';
            
            let sourceList = allStudents.filter(s => s.excluded != 1); // exclude already-excluded
            
            // Apply pay filter
            if (payFilter === 'paid') sourceList = sourceList.filter(s => s.payment_status === 'PAID' || s.payment_status === 'مدفوع');
            else if (payFilter === 'unpaid') sourceList = sourceList.filter(s => s.payment_status !== 'PAID' && s.payment_status !== 'مدفوع');
            
            // Apply link filter
            if (linkFilter === 'linked') sourceList = sourceList.filter(s => s.telegram_id);
            else if (linkFilter === 'unlinked') sourceList = sourceList.filter(s => !s.telegram_id);
            
            // Apply search query
            if (q) {
                sourceList = sourceList.filter(s => {
                    const name = ((s.first_name || '') + ' ' + (s.last_name || '')).toLowerCase();
                    const email = (s.email || '').toLowerCase();
                    const phone = (s.phone || '').toLowerCase();
                    return name.includes(q) || email.includes(q) || phone.includes(q);
                });
            }
            
            container.innerHTML = '<div style="text-align:center; padding:40px; font-size:1.1rem; color:var(--text2);" dir="rtl">⏳ جارٍ التحليل...</div>';
            
            const infoEl = document.getElementById('dup-scan-info');
            if (infoEl) infoEl.textContent = `يتم الفحص على ${sourceList.length} طالب من إجمالي ${allStudents.filter(s => s.excluded != 1).length}`;
            
            setTimeout(() => {
                try {
                    const byEmail = {};
                    const byPhone = {};
                    const byName = {};
                    
                    sourceList.forEach(s => {
                        // By Email
                        if (s.email && s.email.includes('@')) {
                            const k = s.email.toLowerCase().trim();
                            if (!byEmail[k]) byEmail[k] = [];
                            byEmail[k].push(s);
                        }
                        // By Phone
                        const rawPhone = (s.phone || s.telephone || s.mobile || '').replace(/\D/g, '');
                        if (rawPhone.length >= 8) {
                            const kp = rawPhone.slice(-9); // last 9 digits for matching
                            if (!byPhone[kp]) byPhone[kp] = [];
                            byPhone[kp].push(s);
                        }
                        // By Name (supports Arabic and Latin)
                        let n = ((s.first_name || '') + ' ' + (s.last_name || '')).trim().toLowerCase();
                        n = n.replace(/\s+/g, ' ').trim();
                        if (n.length >= 3 && n !== ' ') {
                            if (!byName[n]) byName[n] = [];
                            byName[n].push(s);
                        }
                    });

                    const finalGroups = [];
                    const processedIds = new Set();
                    
                    const addGroup = (g, type, icon) => {
                        if (g.length > 1) {
                            const unhandled = g.filter(st => !processedIds.has(st.student_id));
                            if (unhandled.length > 1) {
                                finalGroups.push({ type, icon, students: unhandled });
                                unhandled.forEach(st => processedIds.add(st.student_id));
                            }
                        }
                    };
                    
                    Object.values(byEmail).forEach(g => addGroup(g, 'بريد إلكتروني مكرر', '📧'));
                    Object.values(byPhone).forEach(g => addGroup(g, 'هاتف مكرر', '📞'));
                    Object.values(byName).forEach(g => addGroup(g, 'اسم مكرر', '👤'));
                    
                    dupLastGroups = finalGroups;
                    renderDuplicateGroups(finalGroups);
                    renderExcludedList();
                    
                } catch(err) {
                    container.innerHTML = `<div style="color:red; padding:20px; direction:rtl;">خطأ: ${err.message}</div>`;
                    console.error(err);
                }
            }, 80);
        }

        function renderDuplicateGroups(finalGroups) {
            const container = document.getElementById('duplicates-container');
            if (!container) return;

            if (finalGroups.length === 0) {
                container.innerHTML = '<div style="text-align:center; padding:60px; color:#10b981; font-weight:bold; font-size:1.3rem;" dir="rtl">✅ لا توجد تكرارات!</div>';
                return;
            }

            let html = `<div dir="rtl" style="font-size:0.85rem; color:var(--text2); margin-bottom:8px;">وُجِد <strong style="color:var(--accent2);">${finalGroups.length}</strong> مجموعة مكررة</div>`;
            
            finalGroups.forEach((groupObj, gi) => {
                const group = [...groupObj.students].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
                
                if (dupCurrentView === 'table') {
                    // TABLE VIEW: side-by-side columns
                    html += `<div style="border:2px solid var(--border); border-radius:14px; overflow:hidden; background:var(--bg);">
                        <div style="padding:10px 14px; background:rgba(139,92,246,0.1); border-bottom:1px solid var(--border); display:flex; align-items:center; gap:8px;" dir="rtl">
                            <span style="font-size:1rem;">${groupObj.icon}</span>
                            <strong style="color:var(--text1); font-size:0.9rem;">${groupObj.type}</strong>
                            <span style="font-size:0.75rem; color:var(--text2); margin-right:auto;">${group.length} حسابات</span>
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(${Math.min(group.length, 2)}, 1fr); gap:0;">`;
                    
                    group.forEach((s, idx) => {
                        const isNewest = idx === 0;
                        const isExcluded = s.excluded == 1;
                        const borderColor = isExcluded ? '#64748b' : (isNewest ? '#10b981' : '#f59e0b');
                        const badgeAr = isExcluded ? 'مُستبعَد 👻' : (isNewest ? '⭐ الأحدث' : 'القديم');
                        const dateStr = s.created_at ? new Date(s.created_at).toLocaleDateString('ar-MA') : '-';
                        const phone = s.phone || s.telephone || s.mobile || '-';
                        
                        html += `<div style="padding:12px; border-left:${idx > 0 ? '1px solid var(--border)' : 'none'}; opacity:${isExcluded ? 0.5 : 1}; background:${isExcluded ? 'rgba(100,116,139,0.05)' : 'transparent'}; border-top:3px solid ${borderColor};">
                            <div style="font-size:0.7rem; background:${borderColor}20; color:${borderColor}; padding:2px 8px; border-radius:10px; font-weight:bold; display:inline-block; margin-bottom:8px;" dir="rtl">${badgeAr}</div>
                            <div style="font-weight:900; font-size:1rem; color:var(--text1); margin-bottom:4px;" dir="rtl">${s.first_name || ''}</div>
                            <div style="font-size:0.85rem; color:var(--text2); margin-bottom:4px;" dir="ltr">${s.last_name || ''}</div>
                            <div style="font-size:0.78rem; color:#0a84ff; word-break:break-all; margin-bottom:4px;" dir="ltr">${s.email || '-'}</div>
                            <div style="font-size:0.78rem; color:var(--text2); margin-bottom:4px;" dir="ltr">📞 ${phone}</div>
                            <div style="font-size:0.72rem; color:var(--text2);" dir="rtl">📂 ${s.source_file || s.source || '-'}</div>
                            <div style="font-size:0.72rem; color:var(--text2); margin-bottom:8px;" dir="rtl">📅 تاريخ الإضافة: ${dateStr}</div>
                            <div style="font-size:0.72rem; font-weight:bold; color:${s.payment_status === 'PAID' ? '#10b981' : '#ef4444'};" dir="rtl">${s.payment_status === 'PAID' ? '✅ مسدَّد' : '❌ غير مسدَّد'}</div>
                            <div style="margin-top:10px;">
                                ${isExcluded
                                    ? `<button onclick="confirmDupAction('${s.student_id}', 0, '${(s.first_name||'').replace(/'/g,'')} ${(s.last_name||'').replace(/'/g,'')}')" style="background:var(--bg); border:1px solid var(--border); color:var(--text1); padding:5px 10px; border-radius:8px; cursor:pointer; font-size:0.78rem; width:100%;" dir="rtl">🔄 إعادة تفعيل</button>`
                                    : `<button onclick="confirmDupAction('${s.student_id}', 1, '${(s.first_name||'').replace(/'/g,'')} ${(s.last_name||'').replace(/'/g,'')}')" style="background:#ef4444; border:none; color:white; padding:5px 10px; border-radius:8px; cursor:pointer; font-size:0.78rem; font-weight:bold; width:100%;" dir="rtl">👻 استبعاد</button>`
                                }
                            </div>
                        </div>`;
                    });
                    
                    html += `</div></div>`;
                    
                } else {
                    // CARDS VIEW: stacked with arrow
                    html += `<div style="border:2px solid var(--border); border-radius:14px; overflow:hidden; background:var(--bg);">
                        <div style="padding:10px 14px; background:rgba(139,92,246,0.1); border-bottom:1px solid var(--border); display:flex; align-items:center; gap:8px;" dir="rtl">
                            <span style="font-size:1rem;">${groupObj.icon}</span>
                            <strong style="color:var(--text1); font-size:0.9rem;">${groupObj.type}</strong>
                            <span style="font-size:0.75rem; color:var(--text2); margin-right:auto;">${group.length} حسابات</span>
                        </div>
                        <div style="padding:12px; display:flex; flex-direction:column; gap:8px;">`;
                    
                    group.forEach((s, idx) => {
                        const isNewest = idx === 0;
                        const isExcluded = s.excluded == 1;
                        const borderColor = isExcluded ? '#64748b' : (isNewest ? '#10b981' : '#f59e0b');
                        const badgeAr = isExcluded ? 'مُستبعَد 👻' : (isNewest ? '⭐ الأحدث' : 'القديم');
                        const dateStr = s.created_at ? new Date(s.created_at).toLocaleDateString('ar-MA') : '-';
                        const phone = s.phone || s.telephone || s.mobile || '-';
                        
                        if (idx > 0) {
                            html += `<div style="text-align:center; color:var(--text2); font-size:1.2rem; padding:2px 0;">⬇️ مقارنة مع ⬇️</div>`;
                        }
                        
                        html += `<div id="dup-row-${s.student_id}" style="border:2px solid ${borderColor}; border-radius:12px; padding:12px; opacity:${isExcluded ? 0.5 : 1}; background:${isExcluded ? 'rgba(100,116,139,0.05)' : 'var(--surface)'};">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                                <div style="font-size:0.7rem; background:${borderColor}20; color:${borderColor}; padding:2px 8px; border-radius:10px; font-weight:bold;" dir="rtl">${badgeAr}</div>
                                <div>
                                    ${isExcluded
                                        ? `<button onclick="confirmDupAction('${s.student_id}', 0, '${(s.first_name||'').replace(/'/g,'')} ${(s.last_name||'').replace(/'/g,'')}')" style="background:var(--bg); border:1px solid var(--border); color:var(--text1); padding:4px 10px; border-radius:8px; cursor:pointer; font-size:0.78rem;" dir="rtl">🔄 إعادة تفعيل</button>`
                                        : `<button onclick="confirmDupAction('${s.student_id}', 1, '${(s.first_name||'').replace(/'/g,'')} ${(s.last_name||'').replace(/'/g,'')}')" style="background:#ef4444; border:none; color:white; padding:4px 10px; border-radius:8px; cursor:pointer; font-size:0.78rem; font-weight:bold;" dir="rtl">👻 استبعاد</button>`
                                    }
                                </div>
                            </div>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:0.82rem;">
                                <div>
                                    <div style="font-weight:900; font-size:1rem; color:var(--text1);" dir="rtl">${s.first_name || '—'}</div>
                                    <div style="color:var(--text2);" dir="ltr">${s.last_name || '—'}</div>
                                </div>
                                <div style="text-align:left;">
                                    <div style="color:#0a84ff; word-break:break-all;" dir="ltr">${s.email || '-'}</div>
                                    <div style="color:var(--text2);" dir="ltr">📞 ${phone}</div>
                                </div>
                            </div>
                            <div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:6px; font-size:0.72rem;" dir="rtl">
                                <span style="color:${s.payment_status === 'PAID' ? '#10b981' : '#ef4444'}; font-weight:bold;">${s.payment_status === 'PAID' ? '✅ مسدَّد' : '❌ غير مسدَّد'}</span>
                                <span style="color:var(--text2);">📅 تاريخ الإضافة: ${dateStr}</span>
                                <span style="color:var(--text2);">📂 ${s.source_file || s.source || '-'}</span>
                            </div>
                        </div>`;
                    });
                    
                    html += `</div></div>`;
                }
            });
            
            container.innerHTML = html;
        }

        function renderExcludedList() {
            const excluded = allStudents.filter(s => s.excluded == 1);
            const section = document.getElementById('dup-excluded-section');
            const list = document.getElementById('dup-excluded-list');
            const count = document.getElementById('dup-excluded-count');
            if (!section || !list) return;
            
            if (excluded.length === 0) {
                section.style.display = 'none';
                return;
            }
            section.style.display = 'block';
            count.textContent = excluded.length + ' حساب';
            
            list.innerHTML = excluded.map(s => `
                <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 10px; background:var(--surface); border-radius:8px; border:1px solid var(--border);" dir="rtl">
                    <div>
                        <span style="font-weight:bold; color:var(--text1); font-size:0.85rem;">${s.first_name || ''} ${s.last_name || ''}</span>
                        <span style="font-size:0.75rem; color:var(--text2); margin-right:8px;">${s.email || '-'}</span>
                    </div>
                    <button onclick="confirmDupAction('${s.student_id}', 0, '${(s.first_name||'').replace(/'/g,'')} ${(s.last_name||'').replace(/'/g,'')}')" style="background:var(--bg); border:1px solid var(--border); color:var(--text1); padding:4px 8px; border-radius:6px; cursor:pointer; font-size:0.75rem; flex-shrink:0;">🔄 إعادة تفعيل</button>
                </div>
            `).join('');
        }

        function confirmDupAction(studentId, excludedState, name) {
            const msg = excludedState === 1
                ? `هل أنت متأكد أنك تريد استبعاد حساب "${name}"؟\n\nسيُصبح هذا الحساب غير مرئي في الإحصائيات ولكن يمكنك إعادة تفعيله لاحقًا.`
                : `هل تريد إعادة تفعيل حساب "${name}"؟`;
            
            if (confirm(msg)) {
                toggleDuplicateExclude(studentId, excludedState);
            }
        }

        async function toggleDuplicateExclude(studentId, excludedState) {
            try {
                const res = await fetch('/api/admin/gateway/toggle_exclude', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ student_id: studentId, excluded: excludedState })
                });
                const data = await res.json();
                if(data.success) {
                    const student = allStudents.find(s => s.student_id === studentId);
                    if (student) student.excluded = excludedState;
                    
                    // Re-scan with same scope
                    openDuplicateScanner();
                } else {
                    alert('خطأ: ' + (data.error || 'غير معروف'));
                }
            } catch(e) {
                alert('خطأ في الشبكة');
            }
        }
