

        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();

        let allStudents = [];
        let filters = { status: 'all', gender: 'all', level: 'all', color: 'all' };
        let activeSosId = null;
        let activeSosTid = null;
        let activeSosEmail = null;
        let activeSosStudentId = null;
        let activeStudentId = null;
        let activeSosSubtabState = 'open';

        
        const LOG_RULES = {
            'AUTH_FAILED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '❌', label: 'فشل تسجيل الدخول' },
            'LINK_FAILED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '❌', label: 'فشل الربط' },
            'LINK_INVALID': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '⛔', label: 'رابط غير صالح' },
            'INVALID_LINK_ATTEMPT': { bg: '#1a1a1a', border: '#333333', text: '#ffffff', icon: '🏴‍☠️', label: 'محاولة رابط غير صالح' },
            'SOS_SUBMITTED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '🆘', label: 'طلب مساعدة (SOS)' },
            'MANUAL_UNLINK': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '💔', label: 'إلغاء الربط اليدوي' },
            'NAME_VIOLATION_DETECTED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '🚩', label: 'اسم غير مسموح' },

            'AUTH_SUCCESS': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '✅', label: 'تسجيل دخول ناجح' },
            'LINK_SUCCESS': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '🔗', label: 'تم ربط الحساب بنجاح' },
            'ACCOUNT_LINKED': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '🔗', label: 'تم ربط الحساب' },
            'LINK_SUCCESS_APPROVED': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '🔗', label: 'تم اعتماد الربط' },
            'JOIN_GROUP_CLICK': { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '🎓', label: 'دخول المجموعة' },
            
            'APP_OPENED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📱', label: 'فتح التطبيق' },
            'APP_OPENED_UNLINKED': { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '⛔', label: 'محاولة دخول مرفوضة (غير مربوط)' },
            'FOLDER_CLICKED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📁', label: 'فتح مجلد الدروس' },
            'QUIZ_STARTED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📝', label: 'بدأ اختبار' },
            'TUTO_OPENED': { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '📖', label: 'فتح الشرح' },

            'EMAIL_SENT': { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.4)', text: '#d97706', icon: '📨', label: 'إرسال إيميل' },
            'WHATSAPP_SENT': { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.4)', text: '#d97706', icon: '💬', label: 'إرسال واتساب' },
            'MAGIC_LINK_GENERATED': { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.4)', text: '#d97706', icon: '⚙️', label: 'توليد رابط' },
            'DEFAULT': { bg: 'var(--surface)', border: 'var(--border)', text: 'var(--text1)', icon: '📌', label: 'نشاط' }
        };

        function getLogStyle(action_type) {
            let r = LOG_RULES[action_type];
            if (r) return r;
            if (action_type.includes('SUCCESS') || action_type.includes('JOIN')) return { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.4)', text: '#16a34a', icon: '✅', label: action_type };
            if (action_type.includes('FAIL') || action_type.includes('UNLINK') || action_type.includes('SOS')) return { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.4)', text: '#dc2626', icon: '❌', label: action_type };
            if (action_type.includes('OPEN') || action_type.includes('CLICK')) return { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.4)', text: '#2563eb', icon: '🖱️', label: action_type };
            if (action_type.includes('SENT')) return { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.4)', text: '#d97706', icon: '📤', label: action_type };
            return LOG_RULES['DEFAULT'];
        }
        
        function colorizeDescription(desc) {
            if (!desc) return '';
            let colored = desc.replace(/\b(\d{6})\b/g, '<span style="color:#ff9f0a; font-family:monospace; font-weight:800; padding:2px 4px; background:rgba(255,159,10,0.15); border-radius:4px; letter-spacing:1px;">$1</span>');
            colored = colored.replace(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/gi, '<span style="color:#0a84ff; font-family:monospace; font-weight:700; padding:2px 4px; background:rgba(10,132,255,0.15); border-radius:4px;">$1</span>');
            return colored;
        }

        function renderLogCard(l, showUserInfo = false) {
            const style = getLogStyle(l.action_type);
            let desc = colorizeDescription(l.description || '');
            
            let countBadge = l.count && l.count > 1 ? `<span class="log-badge" style="background:${style.text};">x${l.count}</span>` : '';
            
            let userInfo = '';
            if (showUserInfo) {
                let tgUname = l.telegram_username || l.tg_username || '';
                let unameSpan = tgUname ? ` <span dir="ltr" style="color:#0a84ff;">(@${tgUname})</span>` : '';
                let tgDisplay = l.telegram_name || '';
                if (!tgDisplay && l.tg_first_name) {
                    tgDisplay = l.tg_first_name + (l.tg_last_name ? ' ' + l.tg_last_name : '');
                }
                
                userInfo = `
                <div class="log-card-user">
                    ${l.first_name ? `<span>👤 <strong>${l.first_name} ${l.last_name||''}</strong></span>` : ''}
                    ${tgDisplay ? `<span>📱 <strong>${tgDisplay}</strong>${unameSpan}</span>` : ''}
                    ${l.telegram_id ? `<span style="font-family:monospace;">ID: ${l.telegram_id}</span>` : ''}
                </div>`;
            }

            return `
            <div class="log-card" style="background:${style.bg}; border:1px solid ${style.border}; border-left:4px solid ${style.text};">
                <div class="log-card-header">
                    <div class="log-card-title" style="color:${style.text};">
                        ${style.icon} ${style.label} ${countBadge}
                    </div>
                    <div class="log-card-time" dir="ltr">${formatDateArabic(l.timestamp)}</div>
                </div>
                <div class="log-card-desc">${desc}</div>
                ${userInfo}
            </div>
            `;
        }
        
        function groupLogs(logsArr) {
            let grouped = [];
            logsArr.forEach(l => {
                if (grouped.length > 0) {
                    let prev = grouped[grouped.length-1];
                    // Si même action, même description et même user, on groupe
                    if (prev.action_type === l.action_type && prev.description === l.description && prev.student_id === l.student_id && prev.telegram_id === l.telegram_id) {
                        prev.count = (prev.count || 1) + 1;
                        return;
                    }
                }
                l.count = 1;
                grouped.push(l);
            });
            return grouped;
        }

        // ============ DATE FORMATTER IN ARABIC ============
        function formatDateArabic(dateStr) {
            if (!dateStr) return '-';
            const date = new Date(dateStr.replace(' ', 'T'));
            if (isNaN(date.getTime())) return dateStr;
            const options = { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            };
            return new Intl.DateTimeFormat('ar-MA', options).format(date);
        }

        // ============ THEME CONTROL ============
        function changeTheme(themeName) {
            document.body.className = '';
            if (themeName !== 'dark') {
                document.body.classList.add('theme-' + themeName);
            }
            document.querySelectorAll('#tab-settings .chip').forEach(c => c.classList.remove('active'));
            const activeChip = document.getElementById('theme-btn-' + themeName);
            if (activeChip) activeChip.classList.add('active');
            localStorage.setItem('admin-theme', themeName);
        }

        const savedTheme = localStorage.getItem('admin-theme') || 'cpi';
        changeTheme(savedTheme);

        // ============ TABS ============
        
        // ============ BULK EMAIL DISPATCH ENGINE ============
        let emailPollInterval = null;

        async function startBulkEmailDispatch() {
            const btn = document.getElementById('btn-start-bulk-email');
            btn.disabled = true;
            btn.innerHTML = '⏳ جاري البدء...';
            
            try {
                const res = await fetch('/api/admin/gateway/send_bulk_emails', { method: 'POST' });
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

                    if (data.count === 0) {
                        alert('✅ ' + data.message);
                        btn.disabled = false;
                        btn.innerHTML = '🚀 بدء إرسال الإيميلات الآن';
                        return;
                    }
                    document.getElementById('email-progress-container').style.display = 'block';
                    startEmailProgressPolling();
                } else {
                    alert('❌ خطأ: ' + data.error);
                    btn.disabled = false;
                    btn.innerHTML = '🚀 بدء إرسال الإيميلات الآن';
                }
            } catch(e) {
                alert('حدث خطأ في الاتصال: ' + e);
                btn.disabled = false;
                btn.innerHTML = '🚀 بدء إرسال الإيميلات الآن';
            }
        }

        // ============ KPI LIVE METRICS ============
        async function fetchKpiMetrics() {
            try {
                const res = await fetch('/api/admin/gateway/kpi');
                const data = await res.json();
                if (data.success && data.kpi) {
                    const k = data.kpi;
                    const elPaid = document.getElementById('kpi-total-paid');
                    const elSent = document.getElementById('kpi-emails-sent');
                    const elOpen = document.getElementById('kpi-open-rate');
                    const elWaSent = document.getElementById('kpi-wa-sent');
                    const elWaConv = document.getElementById('kpi-wa-converted');
                    const elConv = document.getElementById('kpi-conversion-rate');
                    
                    if (elPaid) elPaid.innerText = k.total_paid || 0;
                    if (elSent) elSent.innerText = k.email_sent || 0;
                    if (elOpen) elOpen.innerText = `${k.open_rate || 0}% (${k.email_opened || 0})`;
                    if (elWaSent) elWaSent.innerText = `${k.wa_sent || 0} مرسل`;
                    if (elWaConv) elWaConv.innerText = `${k.joined_after_wa || 0} طالب`;
                    if (elConv) elConv.innerText = `${k.conversion_rate || 0}% (${k.telegram_linked || 0})`;
                }
            } catch(e) {
                console.error('Error fetching KPI metrics:', e);
            }
        }

        function startEmailProgressPolling() {
            if (emailPollInterval) clearInterval(emailPollInterval);
            emailPollInterval = setInterval(async () => {
                try {
                    const res = await fetch('/api/admin/gateway/email_dispatch_status');
                    const data = await res.json();
                    if (data.success && data.state) {
                        const st = data.state;
                        const total = st.total || 1;
                        const sent = st.sent + st.failed;
                        const pct = Math.min(100, Math.round((sent / total) * 100));
                        
                        document.getElementById('email-progress-bar').style.width = pct + '%';
                        document.getElementById('email-progress-counter').innerText = `${sent} / ${total} (${pct}%)`;
                        document.getElementById('email-current-student').innerText = st.current_student || '';
                        
                        if (!st.is_running && sent >= total) {
                            clearInterval(emailPollInterval);
                            document.getElementById('email-progress-status').innerText = '🎉 تم اكتمال الإرسال بنجاح!';
                            const btn = document.getElementById('btn-start-bulk-email');
                            btn.disabled = false;
                            btn.innerHTML = '🚀 بدء إرسال الإيميلات الآن';
                            fetchStudents(); fetchKpiMetrics(); // Refresh student list
                        }
                    }
                } catch(e) {}
            }, 1500);
        }

        function switchTab(id) {
            document.querySelectorAll('.nav-item').forEach((b,i) => {
                b.classList.toggle('active', ['overview','students','sos','links','logs','settings'][i] === id);
            });
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const tabEl = document.getElementById('tab-' + id);
            if (tabEl) tabEl.classList.add('active');
            if(id === 'students') filterStudents();
            if(id === 'sos') fetchSos();
            if(id === 'links') fetchLinks();
            if(id === 'logs') fetchGlobalLogs();
            if(id === 'settings') loadGeneralSettings();
        }

        // ============ FILTER TRIGGERS ============
        function setGenderFilter(val, el) {
            filters.gender = val;
            if (el && el.parentElement) {
                el.parentElement.querySelectorAll('.chip-gender').forEach(c => c.classList.remove('active'));
                el.classList.add('active');
            }
            filterStudents();
        }
        function setLevelFilter(val) {
            filters.level = val;
            filterStudents();
        }
        function setStatusFilter(val) {
            filters.status = val;
            filterStudents();
        }
        function setColorFilter(val, el) {
            filters.color = val;
            if (el && el.parentElement) {
                el.parentElement.querySelectorAll('.chip-color').forEach(c => c.classList.remove('active'));
                el.classList.add('active');
            }
            filterStudents();
        }

        // ============ SETTINGS API ============
        async function loadGeneralSettings() {
            try {
                const res = await fetch('/api/admin/gateway/settings');
                const data = await res.json();
                if (data.success && data.settings) {
                    const force = data.settings.force_telegram_name === 'true';
                    document.getElementById('setting-force-name').checked = force;
                    
                    if(data.settings.student_theme) document.getElementById('setting-student-theme').value = data.settings.student_theme;
                    if(data.settings.student_font) document.getElementById('setting-student-font').value = data.settings.student_font;
                }
            } catch(e) { console.error('Error loading settings', e); }
        }

        async function toggleForceName(checkbox) {
            try {
                await fetch('/api/admin/gateway/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ key: 'force_telegram_name', value: checkbox.checked ? 'true' : 'false' })
                });
            } catch(e) { console.error(e); }
        }
        
        // ============ GOOGLE SHEETS SYNC ============
        async function syncGoogleSheets() {
            const btn = document.getElementById('btn-sync-sheets');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span>⏳ جاري المزامنة...</span>';
            btn.disabled = true;
            try {
                const res = await fetch('/api/admin/gateway/sync_sheets', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({})
                });
                const data = await res.json();
                if(data.success) {
                    alert('✅ تمت المزامنة بنجاح! تم استيراد/تحديث ' + data.count + ' طالب.');
                    fetchStudents(); fetchKpiMetrics();
                } else {
                    alert('❌ خطأ في المزامنة: ' + data.error);
                }
            } catch(e) { 
                console.error(e); 
                alert('حدث خطأ غير متوقع أثناء المزامنة.');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }

        async function exportGoogleSheets() {
            const btn = document.getElementById('btn-export-sheets');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span>⏳ جاري التصدير...</span>';
            btn.disabled = true;
            try {
                const res = await fetch('/api/admin/gateway/export_sheets', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({})
                });
                const data = await res.json();
                if(data.success) {
                    alert('✅ تم التصدير بنجاح! تم تصدير بيانات ' + data.count + ' طالب إلى ورقة "Suivi Élèves".');
                } else {
                    alert('❌ خطأ في التصدير: ' + data.error);
                }
            } catch(e) { 
                console.error(e); 
                alert('حدث خطأ غير متوقع أثناء التصدير.');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
        
        async function saveStudentTheme() {
            try {
                const theme = document.getElementById('setting-student-theme').value;
                const font = document.getElementById('setting-student-font').value;
                await fetch('/api/admin/gateway/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ key: 'student_theme', value: theme })
                });
                await fetch('/api/admin/gateway/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ key: 'student_font', value: font })
                });
            } catch(e) { console.error(e); }
        }

        // ============ EXCEL IMPORT ============
        async function importExcel(input) {
            if(!input.files || input.files.length === 0) return;
            const file = input.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const res = await fetch('/api/admin/gateway/import_students', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if(data.success) {
                    alert('تم استيراد أو تحديث ' + data.count + ' طالب بنجاح.');
                    fetchStudents(); fetchKpiMetrics();
                } else {
                    alert('خطأ: ' + data.error);
                }
            } catch(e) {
                alert('خطأ في الاتصال: ' + e.message);
            }
            input.value = '';
        }
        async function addStudentManually() {
            const email = document.getElementById('manual-student-email').value.trim();
            const dob = document.getElementById('manual-student-dob').value.trim();
            const first_name = document.getElementById('manual-student-fn').value.trim();
            const last_name = document.getElementById('manual-student-ln').value.trim();
            const student_id = document.getElementById('manual-student-id').value.trim();
            
            if(!email || !dob) {
                alert("يرجى إدخال البريد الإلكتروني وتاريخ الميلاد على الأقل.");
                return;
            }
            
            try {
                const res = await fetch('/api/admin/gateway/add_student', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ email, dob, first_name, last_name, student_id })
                });
                const data = await res.json();
                if(data.success) {
                    alert('تم إضافة الطالب بنجاح!');
                    document.getElementById('manual-student-email').value = '';
                    document.getElementById('manual-student-dob').value = '';
                    document.getElementById('manual-student-fn').value = '';
                    document.getElementById('manual-student-ln').value = '';
                    document.getElementById('manual-student-id').value = '';
                    fetchStudents(); fetchKpiMetrics();
                } else {
                    alert('خطأ: ' + data.error);
                }
            } catch(e) {
                alert('حدث خطأ في الاتصال: ' + e.message);
            }
        }

        // ============ STUDENTS ============
        async function fetchStudents() {
            try {
                const res = await fetch('/api/admin/gateway/students?t=' + Date.now());
                const data = await res.json();
                if(data.success) {
                    allStudents = data.students;
                    filterStudents();
                }
            } catch(e) { console.error(e); }
        }

        function filterStudents() {
            const q = document.getElementById('search-input').value.toLowerCase();
            const filtered = allStudents.filter(s => {
                const name = String(s.first_name || '').toLowerCase();
                const lname = String(s.last_name || '').toLowerCase();
                const email = String(s.email || '').toLowerCase();
                const source = String(s.source || '').toLowerCase();
                const dob = String(s.dob || '').toLowerCase();
                const year = String(s.year || '');
                const telegramId = String(s.telegram_id || '');
                const tgFirstName = String(s.tg_first_name || '').toLowerCase();
                
                const matchSearch = name.includes(q) || lname.includes(q) || email.includes(q) || 
                                  source.includes(q) || dob.includes(q) || year.includes(q) ||
                                  telegramId.includes(q) || tgFirstName.includes(q);

                const g = String(s.gender || '').toLowerCase();
                const isM = g.startsWith('h') || g === 'm' || g === 'male' || g.includes('ذك');
                const isF = g.startsWith('f') || g === 'female' || g === 'fille' || g.includes('أنث');
                const matchGender = filters.gender === 'all'
                    || (filters.gender === 'homme' && isM)
                    || (filters.gender === 'femme' && isF)
                    || (filters.gender === 'inconnu' && !isM && !isF);

                const yr = String(s.year || '');
                const yrLower = yr.toLowerCase();
                const matchLevel = filters.level === 'all' 
                    || yrLower.includes(filters.level)
                    || (filters.level === '1' && (yrLower.includes('أول') || yrLower.includes('1')))
                    || (filters.level === '2' && (yrLower.includes('ثاني') || yrLower.includes('2')))
                    || (filters.level === '3' && (yrLower.includes('ثالث') || yrLower.includes('3')))
                    || (filters.level === '4' && (yrLower.includes('رابع') || yrLower.includes('4')));

                const linked = !!s.telegram_id;
                const matchStatus = filters.status === 'all'
                    || (filters.status === 'linked' && linked)
                    || (filters.status === 'unlinked' && !linked);

                let studentColor = 'red';
                if (s.excluded) studentColor = 'black';
                else if (s.group_joined) studentColor = 'green';
                else if (s.email_clicked_at || s.folder_clicked_at || s.bot_started_at) studentColor = 'orange';

                const matchColor = filters.color === 'all' || filters.color === studentColor;

                return matchSearch && matchGender && matchLevel && matchStatus && matchColor;
            });

            const linkedCount = filtered.filter(s => s.telegram_id).length;
            const elTotal = document.getElementById('stat-total');
            const elLinked = document.getElementById('stat-linked');
            const elPct = document.getElementById('stat-pct');
            if (elTotal) elTotal.textContent = filtered.length;
            if (elLinked) elLinked.textContent = linkedCount;
            if (elPct) elPct.textContent = filtered.length ? Math.round(linkedCount / filtered.length * 100) + '%' : '—';
            const countDisplay = document.getElementById('students-count-display');
            if (countDisplay) {
                countDisplay.innerHTML = `📊 <span>العدد الإجمالي: <span style="color:#0084ff;">${filtered.length}</span> طالب</span> <span style="color:var(--text2); font-size:0.8rem; margin-right:10px;">(منهم ${linkedCount} مربوط)</span>`;
            }

            const list = document.getElementById('students-list');
            list.innerHTML = '';
            if(filtered.length === 0) {
                list.innerHTML = '<div class="no-items">لم يتم العثور على أي طالب.</div>';
                return;
            }
            const fragment = document.createDocumentFragment();
            const displayLimit = Math.min(filtered.length, 500);
            for(let i=0; i<displayLimit; i++) {
                const s = filtered[i];
                const linked = !!s.telegram_id;
                const div = document.createElement('div');
                div.className = 'list-item';
                div.style.padding = '12px 14px';
                div.style.display = 'flex';
                div.style.flexDirection = 'column';
                div.style.gap = '6px';
                
                const g = String(s.gender || '').toLowerCase();
                if (g.startsWith('h') || g === 'm' || g === 'male' || g.includes('ذك')) {
                    div.style.borderRight = '5px solid #0084ff';
                    div.style.background = 'rgba(0, 132, 255, 0.08)';
                } else if (g.startsWith('f') || g === 'female' || g === 'fille' || g.includes('أنث')) {
                    div.style.borderRight = '5px solid #ec4899';
                    div.style.background = 'rgba(236, 72, 153, 0.08)';
                }

                div.onclick = () => openStudentCard(s);
                
                // Status dot
                let dotColor, dotTitle;
                if (s.excluded) { dotColor = '#111'; dotTitle = 'مستبعد'; }
                else if (s.group_joined) { dotColor = '#16a34a'; dotTitle = 'منضم ✅'; }
                else if (s.email_clicked_at || s.folder_clicked_at || s.bot_started_at) { dotColor = '#f97316'; dotTitle = 'في طور الانضمام'; }
                else { dotColor = '#ef4444'; dotTitle = 'لم ينضم'; }
                const dot = `<span title="${dotTitle}" style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${dotColor};flex-shrink:0;"></span>`;

                // Year in Arabic
                const yrStr = String(s.year || '');
                const yrMatch = yrStr.match(/\d+/);
                const yrNum = yrMatch ? yrMatch[0] : '';
                const yearAr = yrNum ? `السنة ${yrNum}` : '';

                // Payment badge
                const paid = String(s.payment_status || '').toUpperCase();
                const isPaid = paid.includes('PAID') || paid.includes('مدفوع') || paid.includes('OUI');
                const payBadge = isPaid
                    ? `<span style="font-size:0.72rem;background:rgba(22,163,74,0.15);color:#16a34a;padding:2px 8px;border-radius:10px;font-weight:700;">مدفوع</span>`
                    : `<span style="font-size:0.72rem;background:rgba(239,68,68,0.15);color:#ef4444;padding:2px 8px;border-radius:10px;font-weight:700;">غير مدفوع</span>`;

                // Source
                const src = String(s.source || 'غير محدد');

                // Telegram info
                let tgLine = '';
                if (linked) {
                    let tgName = String(s.tg_first_name || '');
                    if (s.tg_last_name) tgName += ' ' + String(s.tg_last_name);
                    const tgUser = s.telegram_username ? `@${s.telegram_username}` : '';
                    tgLine = `<div style="font-size:0.78rem;color:#0088cc;display:flex;align-items:center;gap:4px;">✈️ ${tgUser || tgName.trim() || 'مرتبط'}</div>`;
                }

                const acaId = String(s.academic_id || s.student_id || '').trim();
                div.innerHTML = `
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0.95rem;color:var(--text1);">
                            ${dot} ${String(s.first_name || '')} ${String(s.last_name || '')}
                        </div>
                        ${payBadge}
                    </div>
                    <div style="font-size:0.8rem;color:var(--text2);" dir="ltr">${String(s.email || '')}</div>
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        ${acaId ? `<span style="font-size:0.72rem;background:rgba(0,0,0,0.1);color:var(--text1);padding:2px 8px;border-radius:10px;font-family:monospace;font-weight:bold;">ID: ${acaId}</span>` : ''}
                        ${yearAr ? `<span style="font-size:0.72rem;background:rgba(255,159,10,0.15);color:#ff9f0a;padding:2px 8px;border-radius:10px;font-weight:600;">${yearAr}</span>` : ''}
                        <span style="font-size:0.72rem;color:var(--text2);">م. ${src}</span>
                    </div>
                    ${tgLine}
                `;
                fragment.appendChild(div);
            }
            list.appendChild(fragment);
            if(filtered.length > 500) {
                const more = document.createElement('div');
                more.style.cssText = 'text-align:center;padding:15px;color:var(--text2);font-size:0.85rem;';
                more.innerHTML = `تم إخفاء ${filtered.length - 500} طالب لتحسين الأداء. استخدم البحث للوصول إليهم.`;
                list.appendChild(more);
            }
            if (typeof renderStudents === 'function') {
                renderStudents(filtered);
            }
        }


        
        function switchModalTab(tabId) {
            ['general', 'academy', 'telegram', 'funnel'].forEach(t => {
                const mt = document.getElementById('mtab-' + t);
                const mc = document.getElementById('mcontent-' + t);
                if(mt) mt.classList.remove('active');
                if(mc) mc.classList.remove('active');
            });
            const amt = document.getElementById('mtab-' + tabId);
            const amc = document.getElementById('mcontent-' + tabId);
            if(amt) amt.classList.add('active');
            if(amc) amc.classList.add('active');
        }
        
        function setFunnelStep(stepId, dateVal) {
            const icon = document.getElementById('f-icon-' + stepId);
            const dateEl = document.getElementById('f-date-' + stepId);
            if(!icon) return;
            if (dateVal && dateVal !== '0' && dateVal !== 'false') {
                icon.className = 'funnel-icon success';
                icon.innerHTML = '✔';
                dateEl.textContent = String(dateVal).substring(0,16).replace('T', ' ');
            } else {
                icon.className = 'funnel-icon pending';
                icon.innerHTML = '✖';
                dateEl.textContent = 'لم يتم بعد';
            }
        }

        
        async function sendFunnelAction(actionType) {
            if (!activeStudentId) return;
            if (!confirm('Voulez-vous vraiment effectuer cette action ?')) return;
            
            const student = allStudents.find(s => s.student_id === activeStudentId);
            let finalUrl = null;
            
            if (student) {
                const token = student.magic_token || student.student_id;
                let text = encodeURIComponent(`السلام عليكم، هذا رابط الدخول الخاص بك للأكاديمية:\nhttps://t.me/Oswah_academy_bot?start=${actionType === 'log_wa_1' ? 'w1' : 'w2'}_${token}`);
                let phoneStr = String(student.phone || '').replace(/\D/g, '');
                
                if (actionType === 'log_wa_1' || actionType === 'log_wa_2') {
                    if (phoneStr) {
                        finalUrl = `https://wa.me/${phoneStr}?text=${text}`;
                    } else {
                        alert("Aucun numéro de téléphone pour cet étudiant.");
                        return;
                    }
                } else if (actionType === 'log_tg_1') {
                    if (phoneStr) {
                        finalUrl = `https://t.me/+${phoneStr}`;
                    } else {
                        alert("Aucun numéro de téléphone pour cet étudiant.");
                        return;
                    }
                }
            }
            
            if (finalUrl) {
                window.open(finalUrl, '_blank');
            }
            
            try {
                const res = await fetch('/api/admin/gateway/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action: actionType,
                        student_id: activeStudentId
                    })
                });
                const data = await res.json();
                if (data.success) {
                    if(actionType.includes('email')) {
                        alert('Action réussie !');
                    }
                    loadStudents();
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch(e) {}
        }

        async function openStudentCard(student) {
            activeStudentId = student.student_id;
            
            // Name - ONLY first + last name
            const first = String(student.first_name || '').trim();
            const last = String(student.last_name || '').trim();
            document.getElementById('profile-name-text').innerHTML = `${last || '-'} <span style="font-size:0.9rem; color:var(--text2); font-weight:normal; margin-left:10px;">${first || ''}</span>`;
            
            const tgContainer = document.getElementById('profile-tg-container');
            const tgUsernameContainer = document.getElementById('profile-tg-username-container');
            
            // Gender with colors
            let displayGender = 'غير محدد';
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
            if(srcEl) srcEl.textContent = student.source || 'غير محدد';
            
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
    