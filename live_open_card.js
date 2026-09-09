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