async function openStudentCard(student) {
            activeStudentId = student.student_id;
            activeStudentObj = student;
            
            // Name - ONLY first + last name
            const arabicName = String(student.first_name || '').trim();
            const foreignName = String(student.last_name || '').trim();
            document.getElementById('profile-name-text').innerHTML = `${arabicName || '-'}`;
            const foreignNameEl = document.getElementById('profile-foreign-name-text');
            const createdAt = student.created_at ? new Date(student.created_at + 'Z').toLocaleDateString() : 'N/A';
            const sourceFile = student.source_file ? student.source_file : (student.source === 'excel' ? 'Fichier Excel inconnu' : (student.source || 'Manuel'));
            document.getElementById('profile-import-text').innerHTML = `📅 ${createdAt} <br> 📁 ${sourceFile}`;
            if (foreignNameEl) foreignNameEl.textContent = foreignName || '-';
            
            const tgContainer = document.getElementById('profile-tg-container');
            const tgUsernameContainer = document.getElementById('profile-tg-username-container');
            
            // Gender with colors
            let displayGender = 'غير محدد';
            
            // Set level badge
            const yr = String(student.year || '').trim();
            const lvlBadge = document.getElementById('profile-level-badge');
            if(lvlBadge) {
                if(yr === '1') lvlBadge.textContent = '1ère Année';
                else if(yr === '2') lvlBadge.textContent = '2ème Année';
                else if(yr === '3') lvlBadge.textContent = '3ème Année';
                else if(yr === '4') lvlBadge.textContent = '4ème Année';
                else lvlBadge.textContent = 'Année: ' + yr;
            }

            const g = String(student.gender || '').toLowerCase();
            const profileNameChip = document.getElementById('profile-name');
            
            if (g.startsWith('h') || g === 'm' || g.includes('ذكر')) {
                displayGender = 'رجل';
                if (profileNameChip) { profileNameChip.style.background = 'rgba(10,132,255,0.15)'; profileNameChip.style.borderColor = '#0a84ff'; profileNameChip.style.color = '#0a84ff'; }
            } else if (g.startsWith('f') || g === 'fille' || g.includes('أنثى')) {
                displayGender = 'امرأة';
                if (profileNameChip) { profileNameChip.style.background = 'rgba(255,45,85,0.15)'; profileNameChip.style.borderColor = '#ff2d55'; profileNameChip.style.color = '#ff2d55'; }
            } else {
                if (profileNameChip) { profileNameChip.style.background = 'rgba(10,132,255,0.15)'; profileNameChip.style.borderColor = '#0a84ff'; profileNameChip.style.color = '#0a84ff'; }
            }
            document.getElementById('profile-gender-text').textContent = displayGender;
            
            // Telegram name + username
            if (student.telegram_id && student.tg_first_name) {
                tgContainer.style.display = 'flex';
                const tgName = String(student.tg_first_name || '') + (student.tg_last_name ? ' ' + String(student.tg_last_name) : '');
                document.getElementById('profile-tg-display').textContent = tgName;
            } else {
                tgContainer.style.display = 'none';
            }
            if (student.telegram_username) {
                tgUsernameContainer.style.display = 'flex';
                document.getElementById('profile-tg-username-text').textContent = '@' + student.telegram_username;
            } else {
                tgUsernameContainer.style.display = 'none';
            }
            
            document.getElementById('profile-email-text').textContent = student.email || 'غير متوفر';
            
            const studentIdEl = document.getElementById('profile-studentid-text');
            if(studentIdEl) studentIdEl.textContent = student.academic_id || 'غير متوفر';
            
            // Payment status in Arabic
            const paymentEl = document.getElementById('profile-payment-text');
            if(paymentEl) {
                const ps = String(student.payment_status || '').toUpperCase();
                if (ps.includes('PAID') || ps.includes('مدفوع') || ps.includes('OUI')) paymentEl.textContent = '✅ مدفوع';
                else if (ps.includes('UNPAID') || ps.includes('NON') || ps.includes('PENDING')) paymentEl.textContent = '❌ غير مدفوع';
                else paymentEl.textContent = student.payment_status || 'غير متوفر';
            }
            
            const inscriptionEl = document.getElementById('profile-inscription-text');
            if(inscriptionEl) inscriptionEl.textContent = student.created_at ? formatDateArabic(student.created_at) : 'غير متوفر';
            
            
            
            // Year in Arabic
            const yrStr = String(student.year || '').trim();
            const yrMatch = yrStr.match(/\d+/);
            const yrArabic = yrMatch ? 'السنة ' + yrMatch[0] : yrStr;
            document.getElementById('profile-year-text').textContent = yrArabic || 'غير محدد';
            
            document.getElementById('profile-dob-text').textContent = student.dob || 'غير متوفر';
            document.getElementById('profile-tgid-text').textContent = student.telegram_id || 'غير مرتبط';
            
            // Source
            const srcEl = document.getElementById('profile-source-text');
            if(srcEl) {
                const s = String(student.source || '').toLowerCase();
                if(s.includes('sheet') || s.includes('google')) {
                    srcEl.innerHTML = '<span style="background:#0f9d58; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.8rem;">Sheet</span>';
                } else if(s.includes('excel')) {
                    srcEl.innerHTML = '<span style="background:#107c41; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; font-size:0.8rem;">Excel</span>';
                } else {
                    srcEl.textContent = student.source || '-';
                }
            }
            
            // Profession (if available)
            const profEl = document.getElementById('profile-profession-text');
            if(profEl) profEl.textContent = student.profession || student.job || 'غير متوفر';

            const unlinkBtn = document.getElementById('profile-unlink-btn');
            if (student.telegram_id) {
                unlinkBtn.style.display = 'block';
            } else {
                unlinkBtn.style.display = 'none';
            }

            // Membership check and Telegram Name display
            const mEl = document.getElementById('profile-membership');
            if (student.telegram_id) {
                mEl.innerHTML = '<span style="color:#888;">جاري التحقق...</span>';
                try {
                    const checkRes = await fetch('/api/admin/gateway/check_member?telegram_id=' + student.telegram_id);
                    const checkData = await checkRes.json();
                    if (checkData.success) {
                        mEl.innerHTML = checkData.has_joined 
                            ? `<span class="badge badge-joined">انضم (${checkData.status})</span>`
                            : `<span class="badge badge-unlinked">لم ينضم (خارج المجموعة)</span>` + (checkData.debug_error ? `<br><small style="color:var(--danger);font-size:10px;">${checkData.debug_error}</small>` : '');
                    } else {
                        mEl.innerHTML = '<span style="color:var(--danger);">خطأ في التحقق</span>' + (checkData.error ? `<br><small style="color:var(--danger);font-size:10px;">${checkData.error}</small>` : '');
                    }
                } catch(e) {
                    mEl.innerHTML = '<span style="color:var(--danger);">خطأ في التحقق</span>';
                }
            } else {
                mEl.innerHTML = '<span style="color:var(--text2);">غير مطبق</span>';
                document.getElementById('profile-tg-display').textContent = 'غير مرتبط بتيليجرام';
            }

            // Student Logs
            document.getElementById('logs-body').innerHTML = '<div class="no-items">جاري التحميل...</div>';
            
            // Funnel & Tab logic
            if(typeof setFunnelStep === 'function') {
                setFunnelStep('email-sent', student.email_sent_at || (student.email_sent ? 'نعم' : null));
                setFunnelStep('email-opened', student.email_opened_at);
                setFunnelStep('email-clicked', student.email_clicked_at || student.folder_clicked_at);
                setFunnelStep('whatsapp-sent', student.whatsapp_sent_at || (student.whatsapp_sent ? 'نعم' : null));
                setFunnelStep('bot-started', student.bot_started_at);
                setFunnelStep('group-joined', student.joined_at || (student.group_joined ? 'نعم' : null));
                
                // CONDITION DE VICTOIRE
                const victoryBanner = document.getElementById('funnel-victory-banner');
                const stepEmail2 = document.getElementById('funnel-step-email2');
                const stepWa = document.getElementById('funnel-step-wa');
                
                if (student.telegram_id) {
                    if (victoryBanner) victoryBanner.style.display = 'block';
                    if (stepEmail2) stepEmail2.style.display = 'none';
                    if (stepWa) stepWa.style.display = 'none';
                } else {
                    if (victoryBanner) victoryBanner.style.display = 'none';
                    if (stepEmail2) stepEmail2.style.display = 'block';
                    if (stepWa) stepWa.style.display = 'block';
                }
                
                switchModalTab('general');

    // Re-added missing modal logic
    document.getElementById('logs-overlay').style.display = 'flex';
    if(typeof fetchCrmTimeline === 'function') fetchCrmTimeline(student.student_id, student.telegram_id);
    
    try {
        const res = await fetch('/api/admin/gateway/logs?id=' + student.student_id + '&tid=' + (student.telegram_id || 'null'));
        const data = await res.json();

        if (student.telegram_id) {
            let tgFullName = student.tg_first_name || '';
            if (student.tg_last_name) tgFullName += ' ' + student.tg_last_name;
            document.getElementById('profile-tg-display').textContent = tgFullName.trim() || 'Non défini (Nom caché)';

            document.getElementById('modal-tg-identity').innerHTML = `
                <strong>ID:</strong> ${student.telegram_id}<br>
                <strong>Prénom:</strong> ${student.tg_first_name || '-'}<br>
                <strong>Nom:</strong> ${student.tg_last_name || '-'}${student.telegram_username ? '<br><strong>Pseudo:</strong> @' + student.telegram_username : ''}
            `;
        } else {
            document.getElementById('modal-tg-identity').innerHTML = `<span style="color:var(--text2);">Non lié</span>`;
        }

        document.getElementById('modal-db-identity').innerHTML = `
            <strong>ID:</strong> ${student.student_id || '-'}<br>
            <strong>Nom complet:</strong> ${(student.first_name||'') + ' ' + (student.last_name||'')}<br>
            <strong>Email:</strong> ${student.email || '-'}<br>
            <strong>Genre:</strong> ${student.gender || '-'}
        `;

        if(data.success && data.logs.length > 0) {
            let grouped = groupLogs(data.logs);
            let html = grouped.map(l => renderLogCard(l, false)).join('');
            document.getElementById('logs-body').innerHTML = html;
        } else {
            document.getElementById('logs-body').innerHTML = '<div class="no-items">Aucun historique pour le moment.</div>';
        }
    } catch(e) {
        document.getElementById('logs-body').innerHTML = '<div class="no-items" style="color:var(--danger);">Erreur lors du chargement de l\'historique.</div>';
    }
}


            // Translation dictionaries
            const trPays = {'france':'فرنسا', 'maroc':'المغرب', 'algerie':'الجزائر', 'algérie':'الجزائر', 'belgique':'بلجيكا', 'suisse':'سويسرا', 'canada':'كندا', 'tunisie':'تونس'};
            const trNat = {'marocaine':'مغربية', 'marocain':'مغربي', 'algerienne':'جزائرية', 'algérienne':'جزائرية', 'algerien':'جزائري', 'algérien':'جزائري', 'francaise':'فرنسية', 'française':'فرنسية', 'francais':'فرنسي', 'français':'فرنسي', 'tunisienne':'تونسية', 'tunisien':'تونسي', 'moroccan':'مغربي', 'algerian':'جزائري', 'french':'فرنسي', 'tunisian':'تونسي', 'belgian':'بلجيكي', 'swiss':'سويسري', 'canadian':'كندي', 'egyptian':'مصري'};
            const trAr = {'debutant':'مبتدئ', 'débutant':'مبتدئ', 'intermediaire':'متوسط', 'intermédiaire':'متوسط', 'moyen':'متوسط', 'avance':'متقدم', 'avancé':'متقدم'};

            function tr(val, dict) {
                if(!val) return '-';
                const v = String(val).toLowerCase().trim();
                return dict[v] || val;
            }

            const cEl = document.getElementById('profile-country-text');
            if(cEl) cEl.textContent = tr(student.country, trPays);
            const natEl = document.getElementById('profile-nationality-text');
            if(natEl) natEl.textContent = tr(student.nationality, trNat);
            const arEl = document.getElementById('profile-arabiclevel-text');
            if(arEl) arEl.textContent = tr(student.arabic_level, trAr);
            
            const slEl = document.getElementById('profile-school-level-text');
            if(slEl) slEl.textContent = student.school_level || '-';

            const tgFEl = document.getElementById('profile-tg-firstname-text');
            if(tgFEl) tgFEl.textContent = student.tg_first_name || '-';
            const tgLEl = document.getElementById('profile-tg-lastname-text');
            if(tgLEl) tgLEl.textContent = student.tg_last_name || '-';
            const tgFolder = document.getElementById('profile-tg-folder-text');
            if(tgFolder) tgFolder.textContent = student.folder_clicked_at ? student.folder_clicked_at.substring(0, 16).replace('T', ' ') : '-';
            
            const inscEl = document.getElementById('profile-inscription-text');
            if(inscEl) inscEl.textContent = student.created_at ? student.created_at.split(' ')[0] : '-';

            // Phone number fancy display
            const phoneEl = document.getElementById('profile-phone-text');
            if (phoneEl) {
                let p = String(student.phone || '').trim();
                if (p && p !== '-' && p !== 'null') {
                    if (p.startsWith('+')) {
                        let ind = p.substring(0, 4); // basic guess
                        let rest = p.substring(4);
                        if (p.startsWith('+212') || p.startsWith('+213') || p.startsWith('+216')) {
                            ind = p.substring(0, 4); rest = p.substring(4);
                        } else if (p.startsWith('+33') || p.startsWith('+32') || p.startsWith('+41')) {
                            ind = p.substring(0, 3); rest = p.substring(3);
                        }
                        phoneEl.innerHTML = `<span style="background:var(--bg); border:1px solid var(--border); border-radius:4px; padding:2px 6px; font-size:0.8rem; margin-right:5px; color:var(--text1);">${ind}</span> <span dir="ltr">${rest}</span>`;
                    } else {
                        phoneEl.innerHTML = `<span dir="ltr">${p}</span>`;
                    }
                } else {
                    phoneEl.textContent = '-';
                }
            }

            // Age Calculator
            let ageText = student.dob || '-';
            if (student.dob) {
                try {
                    let parts = student.dob.split(/[\/\-]/);
                    let d = null;
                    if(parts.length === 3) {
                        if(parts[0].length === 4) d = new Date(parts[0], parts[1]-1, parts[2]);
                        else d = new Date(parts[2], parts[1]-1, parts[0]);
                    }
                    if(d && !isNaN(d.getTime())) {
                        let today = new Date();
                        let years = today.getFullYear() - d.getFullYear();
                        let months = today.getMonth() - d.getMonth();
                        if (months < 0 || (months === 0 && today.getDate() < d.getDate())) {
                            years--;
                            months += 12;
                        }
                        ageText = student.dob + ' (' + years + ' سنة و ' + months + ' أشهر)';
                    }
                } catch(e) {}
            }
            const dobEl = document.getElementById('profile-dob-text');
            if(dobEl) dobEl.textContent = ageText;

            document.getElementById('logs-overlay').style.display = 'flex';
            if(typeof fetchCrmTimeline === 'function') fetchCrmTimeline(student.student_id, student.telegram_id);
            try {
                const res = await fetch('/api/admin/gateway/logs?id=' + student.student_id + '&tid=' + (student.telegram_id || 'null'));
                const data = await res.json();
                
                if (student.telegram_id) {
                    let tgFullName = student.tg_first_name || '';
                    if (student.tg_last_name) tgFullName += ' ' + student.tg_last_name;
                    document.getElementById('profile-tg-display').textContent = tgFullName.trim() || 'غير معروف (لم يسجل دخول مؤخراً)';
                    
                    document.getElementById('modal-tg-identity').innerHTML = `
                        <strong>ID:</strong> ${student.telegram_id}<br>
                        <strong>المعرّف:</strong> ${student.telegram_id}<br>
                        <strong>الاسم:</strong> ${student.tg_first_name || '-'}<br>
                        <strong>اللقب:</strong> ${student.tg_last_name || '-'}${student.telegram_username ? '<br><strong>المستخدم:</strong> @' + student.telegram_username : ''}
                    `;
                } else {
                    document.getElementById('modal-tg-identity').innerHTML = `<span style="color:var(--text2);">غير مرتبط</span>`;
                }
                
                document.getElementById('modal-db-identity').innerHTML = `
                    <strong>المعرّف:</strong> ${student.student_id || '-'}<br>
                    <strong>الاسم:</strong> ${(student.first_name||'') + ' ' + (student.last_name||'')}<br>
                    <strong>البريد:</strong> ${student.email || '-'}<br>
                    <strong>الجنس:</strong> ${student.gender || '-'}
                `;

                if(data.success && data.logs.length > 0) {
                    let grouped = groupLogs(data.logs);
                    let html = grouped.map(l => renderLogCard(l, false)).join('');
                    document.getElementById('logs-body').innerHTML = html;
                } else {
                    document.getElementById('logs-body').innerHTML = '<div class="no-items">لا يوجد أي نشاط مسجل لهذا الطالب.</div>';
                }
            } catch(e) {
                document.getElementById('logs-body').innerHTML = '<div class="no-items" style="color:var(--danger);">خطأ في تحميل السجل.</div>';
            }
        }

        async function manualUnlink() {
            if(!activeStudentId) return;
            if(!confirm('هل أنت متأكد من رغبتك في إلغاء ربط حساب تيليجرام لهذا الطالب؟')) return;

            try {
                const res = await fetch('/api/admin/gateway/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ action: 'unlink', student_id: activeStudentId })
                });
                const data = await res.json();
                if (data.success) {
                    // Open WA or TG links based on action
                    const student = allStudents.find(s => s.student_id === activeStudentId);
                    if (student) {
                        const token = student.magic_token || student.student_id;
                        let text = encodeURIComponent(`السلام عليكم، هذا رابط الدخول الخاص بك للأكاديمية:\nhttps://t.me/Oswah_academy_bot?start=${actionType === 'log_wa_1' ? 'w1' : 'w2'}_${token}`);
                        
                        if (actionType === 'log_wa_1' || actionType === 'log_wa_2') {
                            let phoneStr = String(student.phone || '').replace(/\D/g, '');
                            if (phoneStr) {
                                window.open(`https://wa.me/${phoneStr}?text=${text}`, '_blank');
                            } else {
                                alert("Aucun numéro de téléphone pour cet étudiant.");
                            }
                        } else if (actionType === 'log_tg_1') {
                            let phoneStr = String(student.phone || '').replace(/\D/g, '');
                            if (phoneStr) {
                                window.open(`https://t.me/+${phoneStr}`, '_blank');
                            } else {
                                alert("Aucun numéro de téléphone pour cet étudiant.");
                            }
                        }
                    }

                    alert('تم إلغاء الربط بنجاح.');
                    document.getElementById('logs-overlay').style.display = 'none';
                    fetchStudents(); fetchKpiMetrics();
                } else {
                    alert('خطأ: ' + data.error);
                }
            } catch(e) {
                alert('خطأ في الاتصال: ' + e.message);
            }
        }

        // ============ SOS TABS (Active vs Resolved) ============
        function switchSosSubtab(state) {
            activeSosSubtabState = state;
            const btnOpen = document.getElementById('sos-filter-open');
            const btnClosed = document.getElementById('sos-filter-closed');
            if (state === 'open') {
                btnOpen.style.background = 'var(--accent)';
                btnOpen.style.color = 'white';
                btnClosed.style.background = 'var(--surface)';
                btnClosed.style.color = 'var(--text2)';
            } else {
                btnOpen.style.background = 'var(--surface)';
                btnOpen.style.color = 'var(--text2)';
                btnClosed.style.background = 'var(--accent)';
                btnClosed.style.color = 'white';
            }
            renderSosList();
        }

        let rawSosList = [];
        async function fetchSos() {
            try {
                const res = await fetch('/api/admin/sos');
                const data = await res.json();
                if(data.success) {
                    rawSosList = data.sos_list;
                    
                    const openCount = rawSosList.filter(s => s.status === 'open').length;
                    const badge = document.getElementById('sos-badge');
                    if(badge) {
                        if(openCount > 0) {
                            badge.style.display = 'block';
                            badge.textContent = openCount;
                        } else {
                            badge.style.display = 'none';
                        }
                    }

                    renderSosList();
                }
            } catch(e) {
                document.getElementById('sos-list').innerHTML = '<div class="no-items" style="color:var(--danger);">خطأ في الشبكة.</div>';
            }
        }

        function renderLogs() {
            const list = document.getElementById('logs-list');
            if(rawLogs.length === 0) {
                list.innerHTML = '<div class="no-items">لا توجد سجلات.</div>';
                return;
            }
            list.innerHTML = '';
            
            // Translation dictionary for action types
            const actionTranslations = {
                'LINK_FAILED': 'فشل الربط',
                'LINK_SUCCESS': 'نجاح الربط',
                'ACCOUNT_LINKED': 'نجاح الربط',
                'TUTO_OPENED': 'فتح دليل المساعدة',
                'APP_OPENED': 'فتح التطبيق',
                'start_bot': 'بدء البوت',
                'finish_quiz': 'إنهاء اختبار',
                'JOIN_GROUP_CLICK': 'ضغط الانضمام للمجموعة'
            };

            rawLogs.forEach(log => {
                const div = document.createElement('div');
                div.className = 'log-card';
                
                let studentStr = '';
                if (log.student_id == 0) {
                    studentStr = 'طالب غير معروف';
                } else if (log.student_id) {
                    const st = allStudents.find(s => s.student_id == log.student_id);
                    studentStr = st ? (st.first_name || '') + ' (' + log.student_id + ')' : log.student_id;
                } else {
                    studentStr = 'غير معروف';
                }
                
                const actionLabel = actionTranslations[log.action_type] || log.action_type;
                
                let labelColor = 'var(--accent)';
                if (log.action_type === 'LINK_FAILED') labelColor = 'var(--danger)';
                else if (log.action_type === 'LINK_SUCCESS' || log.action_type === 'ACCOUNT_LINKED') labelColor = 'var(--success)';
                
                let tgDisplay = log.telegram_name || '';
                if (!tgDisplay && log.tg_first_name) {
                    tgDisplay = log.tg_first_name + (log.tg_last_name ? ' ' + log.tg_last_name : '');
                }
                
                div.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span style="color:${labelColor}; font-weight:700; font-size:0.95rem;">[${actionLabel}]</span>
                        <span style="font-size:0.75rem; color:var(--text2);"><span dir="ltr">${formatDateArabic(log.timestamp)}</span></span>
                    </div>
                    <div style="font-size:0.85rem; color:var(--text1); margin-bottom:4px;">
                        <strong>الطالب:</strong> <span dir="ltr">${studentStr}</span>
                    </div>
                    <div style="font-size:0.85rem; color:var(--text1); margin-bottom:4px;">
                        <strong>تيليجرام:</strong> <span dir="ltr">${tgDisplay || 'غير معروف'}</span>
                    </div>
                    <div style="font-size:0.85rem; color:var(--text2); line-height:1.4;"><span dir="ltr">${log.description}</span></div>
                `;
                list.appendChild(div);
            });
        }

        let activeSosGenderFilter = 'all';
        function setSosGenderFilter(val, el) {
            activeSosGenderFilter = val;
            if (el && el.parentElement) {
                el.parentElement.querySelectorAll('.chip-gender').forEach(c => c.classList.remove('active'));
                el.classList.add('active');
            }
            renderSosList();
        }

        function renderSosList() {
            const list = document.getElementById('sos-list');
            const q = (document.getElementById('sos-search-input') ? document.getElementById('sos-search-input').value.toLowerCase() : '');
            
            const filtered = rawSosList.filter(s => {
                // State filter
                const matchState = (activeSosSubtabState === 'open') 
                    ? (s.status === 'open' || !s.status) 
                    : (s.status === 'closed' || s.status === 'resolved');
                if (!matchState) return false;
                
                // Gender filter
                const g = String(s.gender || '').toLowerCase();
                const isM = g.startsWith('h') || g === 'm' || g === 'male' || g.includes('ذك');
                const isF = g.startsWith('f') || g === 'female' || g === 'fille' || g.includes('أنث');
                
                const matchGender = (activeSosGenderFilter === 'all')
                    || (activeSosGenderFilter === 'homme' && isM)
                    || (activeSosGenderFilter === 'femme' && isF);
                if (!matchGender) return false;
                
                // Search filter
                if (q) {
                    const matchSearch = (s.email_tentative || '').toLowerCase().includes(q)
                        || (s.student_id_tentative || '').toLowerCase().includes(q)
                        || String(s.telegram_id || '').toLowerCase().includes(q)
                        || (s.first_name || '').toLowerCase().includes(q)
                        || (s.last_name || '').toLowerCase().includes(q);
                    if (!matchSearch) return false;
                }
                
                return true;
            });

            if(filtered.length === 0) {
                list.innerHTML = activeSosSubtabState === 'open' 
                    ? '<div class="no-items">✅ لا توجد أي طلبات مساعدة قيد المعالجة.</div>'
                    : '<div class="no-items">لا توجد طلبات تم حلها بعد.</div>';
                return;
            }

            list.innerHTML = '';
            filtered.forEach(sos => {
                const div = document.createElement('div');
                div.className = 'sos-item';
                div.onclick = () => openSosModal(sos);
                const statusBadge = sos.status === 'closed' || sos.status === 'resolved'
                    ? '<span class="badge badge-linked">تم حلها</span>'
                    : '<span class="badge badge-open">قيد المعالجة</span>';
                
                const matchedStudent = allStudents.find(st => st.telegram_id && String(st.telegram_id) === String(sos.telegram_id));
                const dbName = (sos.first_name || sos.last_name) ? ((sos.first_name || '') + ' ' + (sos.last_name || '')).trim() : 'غير معروف';
                const tgName = matchedStudent && matchedStudent.first_name ? matchedStudent.first_name : dbName;
                
                const g = (sos.gender || '').toLowerCase();
                if (g.startsWith('h') || g === 'm' || g === 'male' || g.includes('ذك')) {
                    div.style.borderLeft = '6px solid #0084ff';
                    div.style.backgroundColor = 'rgba(0,132,255,0.15)';
                } else if (g.startsWith('f') || g === 'female' || g === 'fille' || g.includes('أنث')) {
                    div.style.borderLeft = '6px solid #ec4899';
                    div.style.backgroundColor = 'rgba(236,72,153,0.15)';
                }
                
                div.innerHTML = `
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <div style="font-weight:800; color:var(--accent);">👤 ${tgName}</div>
                        ${statusBadge}
                    </div>
                    <div style="font-weight:700; font-size:0.9rem; color:var(--text1); margin-bottom:4px;">📧 ${sos.email_tentative || 'غير معروف'}</div>
                    <div style="font-size:0.8rem;color:var(--text2);margin-bottom:8px;">🕒 <span dir="ltr">${formatDateArabic(sos.timestamp)}</span></div>
                    <div style="font-size:0.9rem;color:var(--text1); background:rgba(0,0,0,0.2); padding:8px; border-radius:8px;">${sos.message || ''}</div>
                `;

                list.appendChild(div);
            });
        }

        function openSosModal(sos) {
            activeSosId = sos.id;
            activeSosTid = sos.telegram_id;
            activeSosEmail = sos.email_tentative;
            activeSosStudentId = sos.student_id_tentative;
            document.getElementById('sos-modal-meta').innerHTML =
                '<strong>البريد:</strong> ' + (sos.email_tentative || 'N/A') + '<br>' +
                '<strong>المطابقة:</strong> ' + (sos.student_id_tentative || 'N/A') + '<br>' +
                '<strong>TG ID:</strong> ' + (sos.telegram_id || 'غير معروف') + '<br>' +
                '<strong>الوقت:</strong> ' + formatDateArabic(sos.timestamp);
            document.getElementById('sos-modal-message').textContent = sos.message || '';
            document.getElementById('sos-reply-text').value = '';
            document.getElementById('debug-panel').innerHTML = '<span style="color:#555;">— سجل تصحيح الأخطاء —</span>';
            document.getElementById('sos-overlay').style.display = 'flex';
        }

        function viewUserHistoryFromSos() {
            document.getElementById('sos-overlay').style.display = 'none';
            switchTab('logs');
            fetchGlobalLogs(activeSosTid);
        }

        function dbg(msg, color) {
            const d = document.getElementById('debug-panel');
            const t = new Date().toTimeString().slice(0,8);
            d.innerHTML += '<div style="color:' + (color||'#aaa') + ';padding:2px 0;">' + t + ' — ' + msg + '</div>';
            d.scrollTop = d.scrollHeight;
        }

        async function sendSosReply() {
            const text = document.getElementById('sos-reply-text').value.trim();
            dbg('▶ sendSosReply() calling...');
            if(!text) { alert('يرجى كتابة رد.'); return; }

            const btn = document.querySelector('#sos-overlay button[onclick="sendSosReply()"]');
            if(btn) { btn.textContent = '...'; btn.disabled = true; }

            try {
                const res = await fetch('/api/admin/sos/reply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sos_id: activeSosId, reply_message: text, telegram_id: activeSosTid })
                });
                const data = await res.json();
                if(data.success) {
                    dbg('🎉 تم الإرسال والإغلاق بنجاح !', '#22c55e');
                    setTimeout(() => {
                        document.getElementById('sos-overlay').style.display = 'none';
                        fetchSos();
                    }, 800);
                } else {
                    alert('خطأ: ' + data.error);
                }
            } catch(e) {
                alert('خطأ شبكة: ' + e.message);
            } finally {
                if(btn) { btn.textContent = 'إرسال ✈️'; btn.disabled = false; }
            }
        }

        // ============ LINKS ============
        async function fetchLinks() {
            const c = document.getElementById('links-container');
            c.innerHTML = '<div class="no-items">جاري التحميل...</div>';
            try {
                const res = await fetch('/api/admin/links');
                const data = await res.json();
                c.innerHTML = '';
                const genders = ['homme', 'femme'];
                const years = [1, 2, 3, 4];
                genders.forEach(g => {
                    const grp = document.createElement('div');
                    grp.className = 'link-group';
                    grp.innerHTML = '<h3>' + (g === 'homme' ? '👨 الطلاب (ذكور)' : '👩 الطالبات (إناث)') + '</h3>';
                    years.forEach(y => {
                        const key = 'link_' + g + '_' + y;
                        const found = data.links ? data.links.find(l => l.key === key) : null;
                        grp.innerHTML += '<div class="link-label">السنة ' + y + '</div><input class="link-input" id="' + key + '" placeholder="https://t.me/..." value="' + (found ? found.value : '') + '">';
                    });
                    c.appendChild(grp);
                });
            } catch(e) { c.innerHTML = '<div class="no-items" style="color:var(--danger);">خطأ: ' + e.message + '</div>'; }
        }

        async function saveLinks() {
            const genders = ['homme', 'femme'];
            const years = [1, 2, 3, 4];
            for(let g of genders) {
                for(let y of years) {
                    const key = 'link_' + g + '_' + y;
                    const el = document.getElementById(key);
                    if(!el) continue;
                    await fetch('/api/admin/gateway/settings', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ key, value: el.value })
                    });
                }
            }
            alert('تم حفظ جميع الروابط بنجاح.');
        }

        // ============ GLOBAL LOGS (Clickable Cards) ============
        let rawLogs = [];
        let currentLogFilter = 'ALL';
        
        function setLogFilter(type) {
            currentLogFilter = type;
            ['all', 'success', 'fail', 'app', 'tuto'].forEach(id => {
                document.getElementById('filter-log-' + id).classList.remove('active');
            });
            document.getElementById('filter-log-' + type.toLowerCase()).classList.add('active');
            renderGlobalLogs();
        }

        async function fetchGlobalLogs(filterTid = null) {
            const list = document.getElementById('global-logs-list');
            list.innerHTML = '<div class="no-items">جاري التحميل...</div>';
            try {
                const res = await fetch('/api/admin/gateway/logs/all');
                const data = await res.json();
                if(data.success && data.logs.length > 0) {
                    rawLogs = data.logs;
                    renderGlobalLogs(filterTid);
                } else {
                    list.innerHTML = '<div class="no-items">لا يوجد أي سجل نشاط عام.</div>';
                }
            } catch(e) {
                list.innerHTML = '<div class="no-items" style="color:var(--danger);">خطأ في تحميل السجل: ' + e.message + '</div>';
            }
        }
        
        function renderGlobalLogs(filterTid = null) {
            const list = document.getElementById('global-logs-list');
            let filteredLogs = rawLogs;
            
            if (filterTid) {
                filteredLogs = filteredLogs.filter(l => String(l.telegram_id) === String(filterTid));
                if(filteredLogs.length === 0) {
                    list.innerHTML = '<div class="no-items">لا توجد سجلات سابقة لهذا المتصل.</div>';
                    return;
                }
            }
            
            if (currentLogFilter === 'SUCCESS') {
                filteredLogs = filteredLogs.filter(l => getLogStyle(l.action_type).text === '#16a34a' || l.action_type.includes('SUCCESS'));
            } else if (currentLogFilter === 'FAIL') {
                filteredLogs = filteredLogs.filter(l => getLogStyle(l.action_type).text === '#dc2626' || l.action_type.includes('FAILED') || l.action_type.includes('UNLINKED'));
            } else if (currentLogFilter === 'APP') {
                filteredLogs = filteredLogs.filter(l => getLogStyle(l.action_type).text === '#2563eb' || l.action_type.includes('OPEN') || l.action_type.includes('CLICK') || l.action_type.includes('QUIZ'));
            } else if (currentLogFilter === 'COMM') {
                filteredLogs = filteredLogs.filter(l => getLogStyle(l.action_type).text === '#d97706' || l.action_type.includes('SENT'));
            }

            const searchInput = document.getElementById('log-search-input');
            if (searchInput) {
                const q = searchInput.value.toLowerCase().trim();
                if (q) {
                    filteredLogs = filteredLogs.filter(l => {
                        const tName = l.telegram_name || '';
                        const tFirst = l.tg_first_name || '';
                        const tLast = l.tg_last_name || '';
                        const sName = l.student_name || '';
                        const desc = l.description || '';
                        const tId = String(l.telegram_id || '');
                        const tUname = l.telegram_username || l.tg_username || '';
                        
                        return tId.includes(q) || 
                               tName.toLowerCase().includes(q) || 
                               tFirst.toLowerCase().includes(q) || 
                               tLast.toLowerCase().includes(q) || 
                               tUname.toLowerCase().includes(q) || 
                               sName.toLowerCase().includes(q) || 
                               desc.toLowerCase().includes(q);
                    });
                }
            }

            const actionTranslations = {
                'LINK_FAILED': 'فشل الربط',
                'LINK_SUCCESS': 'نجاح الربط',
                'ACCOUNT_LINKED': 'نجاح الربط',
                'TUTO_OPENED': 'فتح دليل المساعدة',
                'APP_OPENED': 'فتح التطبيق',
                'start_bot': 'بدء البوت',
                'finish_quiz': 'إنهاء اختبار',
                'JOIN_GROUP_CLICK': 'ضغط الانضمام للمجموعة'
            };

            if(filteredLogs.length === 0) {
                list.innerHTML = '<div class="no-items">لا توجد نتائج مطابقة للفلتر.</div>';
                return;
            }

            function colorizeDescription(desc) {
                if (!desc) return '';
                // Colorize 6-digit student IDs
                let colored = desc.replace(/\b(\d{6})\b/g, '<span style="color:#ff9f0a; font-family:monospace; font-weight:800; padding:2px 4px; background:rgba(255,159,10,0.15); border-radius:4px; letter-spacing:1px;">$1</span>');
                // Colorize Emails
                colored = colored.replace(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/gi, '<span style="color:#0a84ff; font-family:monospace; font-weight:700; padding:2px 4px; background:rgba(10,132,255,0.15); border-radius:4px;">$1</span>');
                return colored;
            }

            
            let grouped = groupLogs(filteredLogs);
            list.innerHTML = grouped.map(l => renderLogCard(l, true)).join('');
           
        }

        function openLogDetail(index) {
            const log = rawLogs[index];
            if (!log) return;
            document.getElementById('log-detail-type').textContent = log.action_type || 'غير محدد';
            document.getElementById('log-detail-time').textContent = formatDateArabic(log.timestamp);
            document.getElementById('log-detail-name').textContent = log.first_name || 'غير معروف';
            let tgDisplay = log.telegram_name || '';
            if (!tgDisplay && log.tg_first_name) {
                tgDisplay = log.tg_first_name + (log.tg_last_name ? ' ' + log.tg_last_name : '');
            }
            document.getElementById('log-detail-tg').textContent = tgDisplay || 'غير معروف (أو غير مرتبط)';
            
            function colorizeDescDetail(desc) {
                if (!desc) return '';
                let colored = desc.replace(/\b(\d{6})\b/g, '<span style="color:#ff9f0a; font-family:monospace; font-weight:800; padding:2px 4px; background:rgba(255,159,10,0.15); border-radius:4px; letter-spacing:1px;">$1</span>');
                colored = colored.replace(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/gi, '<span style="color:#0a84ff; font-family:monospace; font-weight:700; padding:2px 4px; background:rgba(10,132,255,0.15); border-radius:4px;">$1</span>');
                return colored;
            }
            document.getElementById('log-detail-desc').innerHTML = colorizeDescDetail(log.description) || 'لا توجد تفاصيل إضافية.';
            document.getElementById('log-detail-overlay').style.display = 'flex';
        }

        // ============ INIT ============
        fetchStudents(); fetchKpiMetrics();
    
let funnelChartInstance = null;
let levelChartInstance = null;

async function loadHomeDashboard() {
    try {
        const res = await fetch('/api/admin/gateway/home_stats');
        const data = await res.json();
        if(data.success) {
            // Update KPIs
            document.getElementById('home-kpi-total').textContent = data.kpis.total;
            document.getElementById('home-kpi-linked').textContent = data.kpis.linked + ' (' + Math.round((data.kpis.linked/data.kpis.total)*100) + '%)';
            document.getElementById('home-kpi-groups').textContent = data.kpis.groups;
            document.getElementById('home-kpi-ghosts').textContent = data.kpis.ghosts;

            // Render Charts
            renderHomeCharts(data.funnel, data.demographics);

            // Render Alerts
            renderHomeAlerts(data.alerts);
        }
    } catch(e) {
        console.error("Erreur Home Dashboard:", e);
    }
}

function renderHomeCharts(funnel, demographics) {
    if(!window.Chart) return; // Prevent crash if chart.js failed to load
    
    // Funnel Chart
    const ctxFunnel = document.getElementById('funnelChart').getContext('2d');
    if(funnelChartInstance) funnelChartInstance.destroy();
    funnelChartInstance = new Chart(ctxFunnel, {
        type: 'bar',
        data: {
            labels: ['Importés', 'Contactés', 'Démarré Bot', 'Compte Lié', 'Dans groupe'],
            datasets: [{
                label: 'Étudiants',
                data: [funnel.imported, funnel.contacted, funnel.started_bot, funnel.linked, funnel.joined],
                backgroundColor: ['#94a3b8', '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });

    // Level Donut Chart
    const ctxLevel = document.getElementById('levelChart').getContext('2d');
    if(levelChartInstance) levelChartInstance.destroy();
    
    const lbls = [];
    const vals = [];
    for(let k in demographics.levels) {
        lbls.push((k === 'None' || k === 'null' || !k) ? 'Inconnu' : 'Niv ' + k);
        vals.push(demographics.levels[k]);
    }

    levelChartInstance = new Chart(ctxLevel, {
        type: 'doughnut',
        data: {
            labels: lbls,
            datasets: [{
                data: vals,
                backgroundColor: ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#06b6d4', '#6366f1']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: { legend: { position: 'right' } }
        }
    });
}

function renderHomeAlerts(alerts) {
    const container = document.getElementById('home-alerts-container');
    if(!container) return;
    container.innerHTML = '';
    
    if(alerts.uncontacted > 0) {
        container.innerHTML += `
            <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 15px; border-radius: 8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div>
                    <strong style="color: #d97706;">⚠️ ${alerts.uncontacted} élèves importés non contactés</strong>
                    <div style="font-size:0.85rem; color:var(--text2);">Ils n'ont reçu ni email ni WhatsApp.</div>
                </div>
                <button class="btn btn-primary" onclick="switchTab('actions')" style="padding: 6px 12px; font-size:0.85rem;">Actions</button>
            </div>
        `;
    }
    
    if(alerts.ghosts_today > 0) {
        container.innerHTML += `
            <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 15px; border-radius: 8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div>
                    <strong style="color: #b91c1c;">🚨 ${alerts.ghosts_today} nouveaux fantômes aujourd'hui</strong>
                    <div style="font-size:0.85rem; color:var(--text2);">Ils ont démarré le bot mais n'ont pas de compte.</div>
                </div>
                <button class="btn btn-primary" onclick="switchTab('ghosts')" style="padding: 6px 12px; font-size:0.85rem;">Fantômes</button>
            </div>
        `;
    }

    if(alerts.uncontacted === 0 && alerts.ghosts_today === 0) {
        container.innerHTML = `<div style="color: var(--text2); text-align:center; padding: 20px;">✅ Tout est au vert, aucune alerte.</div>`;
    }
}

