// Extracted from admin.html script block 2, original line 18718.
        async function deleteCustomView(event, id) {

            event.stopPropagation();

            if (!confirm('Voulez-vous vraiment supprimer cette vue ?')) return;



            const view = (state.customViews || []).find(v => v.id === id);

            if (view && view._fromDB) {

                if (view.isLocked && state.adminRole !== 'super_admin') {

                    showToast('🔒 هذه الوجهة مقفلة ولا يمكن حذفها', 'error');

                    return;

                }

                try {

                    const res = await fetch('/admin/custom-views/delete', {

                        method: 'POST',

                        headers: { 'Content-Type': 'application/json' },

                        body: JSON.stringify({ userId: state.userId, id })

                    });

                    const data = await res.json();

                    if (data.success) {

                        showToast('🗑️ تم حذف الوجهة من قاعدة البيانات', 'success');

                        await loadSharedCustomViews();

                    } else {

                        showToast('❌ ' + (data.error || 'فشل الحفظ'), 'error');

                    }

                } catch (e) {

                    showToast('❌ خطأ في الاتصال', 'error');

                }

            } else {

                state.customViews = state.customViews.filter(v => v.id !== id);

                localStorage.setItem('admin_custom_views', JSON.stringify(state.customViews));

                if (state.activeSheet === id) {

                    switchSheet('pending');

                } else {

                    renderInbox();

                }

            }

        }



        window.editCustomViewFromTab = function(id) {

            const view = (state.customViews || []).find(cv => cv.id === id);

            if (view) {

                openCustomViewModal(view);

            }

        };

        // ─── Media Dashboard (إدارة الوسائط) ───

        async function loadMediaDashboard() {

            const subject = document.getElementById('media-subject-select')?.value || 'aqeeda';

            const tbody = document.getElementById('media-table-body');

            if (!tbody) return;

            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:32px; color:var(--text-secondary);"><span style="font-size:1.5rem;">⏳</span><br>جاري تحميل البيانات...</td></tr>`;

            // Reset stat counters

            ['media-stat-mindmaps-ok','media-stat-mindmaps-missing','media-stat-summaries-ok','media-stat-summaries-missing'].forEach(id => {

                const el = document.getElementById(id);

                if (el) el.textContent = '…';

            });

            try {

                const res = await fetch('/admin/media/stats', {

                    method: 'POST',

                    headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify({ userId: state.userId, subject })

                });

                const data = await res.json();

                if (!data.success) {

                    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:32px; color:var(--danger);">❌ ${data.error || 'فشل التحميل'}</td></tr>`;

                    return;

                }

                // Update stat counters

                const s = data.stats || {};

                const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

                setEl('media-stat-mindmaps-ok', s.mindmaps_ok ?? 0);

                setEl('media-stat-mindmaps-missing', s.mindmaps_missing ?? 0);

                setEl('media-stat-summaries-ok', s.summaries_ok ?? 0);

                setEl('media-stat-summaries-missing', s.summaries_missing ?? 0);

                const lessons = data.lessons || [];

                if (lessons.length === 0) {

                    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:48px; color:var(--text-secondary);">

                        <div style="font-size:2rem; margin-bottom:8px;">📭</div>

                        <div>لا توجد دروس لهذه المادة في قاعدة البيانات أو ملف التفريغ</div>

                    </td></tr>`;

                    return;

                }

                tbody.innerHTML = lessons.map(lesson => {

                    const hasMM = lesson.has_mind_map;

                    const hasSumm = lesson.has_summary;

                    const mmId = lesson.mind_map_file_id || '';

                    const summId = lesson.summary_file_id || '';

                    return `<tr style="border-bottom: 1px solid var(--border); transition: background 0.2s;" 

                                onmouseover="this.style.background='var(--surface-hover)'" 

                                onmouseout="this.style.background=''">

                        <td style="padding:10px 8px; font-weight:bold; color:var(--gold-light); text-align:center;">${lesson.course_number}</td>

                        <td style="padding:10px 8px; font-size:0.85rem; color:var(--text-primary); max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${lesson.title}">${lesson.title}</td>

                        <td style="padding:10px 8px;">

                            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">

                                <span class="${hasMM ? 'pill pill-ok' : 'pill pill-danger'}">${hasMM ? '✅ موجود' : '❌ مفقود'}</span>

                                <input type="text" 

                                    id="mm-input-${subject}-${lesson.course_number}"

                                    value="${mmId}"

                                    placeholder="Telegram File ID..."

                                    class="form-input"

                                    style="flex:1; min-width:140px; font-size:0.75rem; padding:4px 8px; direction:ltr; font-family:monospace;"

                                    onkeydown="if(event.key==='Enter') saveLessonResource('${subject}', ${lesson.course_number}, 'mind_map', this.value)"

                                >

                                <button class="btn btn-sm btn-primary" 

                                    onclick="saveLessonResource('${subject}', ${lesson.course_number}, 'mind_map', document.getElementById('mm-input-${subject}-${lesson.course_number}').value)"

                                    style="padding:4px 10px; font-size:0.75rem; white-space:nowrap;">

                                    💾

                                </button>

                            </div>

                        </td>

                        <td style="padding:10px 8px;">

                            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">

                                <span class="${hasSumm ? 'pill pill-ok' : 'pill pill-danger'}">${hasSumm ? '✅ موجود' : '❌ مفقود'}</span>

                                <input type="text"

                                    id="summ-input-${subject}-${lesson.course_number}"

                                    value="${summId}"

                                    placeholder="Telegram File ID..."

                                    class="form-input"

                                    style="flex:1; min-width:140px; font-size:0.75rem; padding:4px 8px; direction:ltr; font-family:monospace;"

                                    onkeydown="if(event.key==='Enter') saveLessonResource('${subject}', ${lesson.course_number}, 'summary', this.value)"

                                >

                                <button class="btn btn-sm btn-primary"

                                    onclick="saveLessonResource('${subject}', ${lesson.course_number}, 'summary', document.getElementById('summ-input-${subject}-${lesson.course_number}').value)"

                                    style="padding:4px 10px; font-size:0.75rem; white-space:nowrap;">

                                    💾

                                </button>

                            </div>

                        </td>

                        <td style="padding:10px 8px; text-align:center;">

                            <div style="display:flex; flex-direction:column; gap:4px; align-items:center;">

                                ${hasMM ? `<button class="btn btn-sm" style="font-size:0.72rem; padding:3px 8px; background:rgba(239,68,68,0.1); color:#ef4444; border:1px solid rgba(239,68,68,0.3);" onclick="clearLessonResource('${subject}', ${lesson.course_number}, 'mind_map')">🗑️ مسح الخارطة</button>` : ''}

                                ${hasSumm ? `<button class="btn btn-sm" style="font-size:0.72rem; padding:3px 8px; background:rgba(239,68,68,0.1); color:#ef4444; border:1px solid rgba(239,68,68,0.3);" onclick="clearLessonResource('${subject}', ${lesson.course_number}, 'summary')">🗑️ مسح الملخص</button>` : ''}

                                ${!hasMM && !hasSumm ? '<span style="color:var(--text-secondary); font-size:0.75rem;">—</span>' : ''}

                            </div>

                        </td>

                    </tr>`;

                }).join('');

            } catch (err) {

                console.error('Error loading media dashboard:', err);

                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:32px; color:var(--danger);">❌ خطأ في الاتصال بالخادم: ${err.message}</td></tr>`;

            }

        }

        async function saveLessonResource(subject, lessonNum, resourceType, fileId) {

            if (!fileId || !fileId.trim()) {

                showToast('⚠️ يرجى إدخال File ID أولاً', 'error');

                return;

            }

            try {

                const res = await fetch('/admin/save-lesson-resources', {

                    method: 'POST',

                    headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify({

                        userId: state.userId,

                        subject,

                        lessonNum,

                        resourceType,

                        fileId: fileId.trim()

                    })

                });

                const data = await res.json();

                if (data.success) {

                    showToast(`✅ تم الحفظ بنجاح (درس ${lessonNum} - ${resourceType === 'mind_map' ? 'الخارطة الذهنية' : 'الملخص'})`, 'success');

                    // Reload to reflect new state

                    await loadMediaDashboard();

                } else {

                    showToast('❌ فشل الحفظ: ' + (data.error || 'خطأ'), 'error');

                }

            } catch (err) {

                showToast('❌ خطأ في الاتصال: ' + err.message, 'error');

            }

        }

        async function clearLessonResource(subject, lessonNum, resourceType) {

            if (!confirm(`هل تريد مسح ${resourceType === 'mind_map' ? 'الخارطة الذهنية' : 'الملخص'} للدرس ${lessonNum}؟`)) return;

            try {

                const res = await fetch('/admin/save-lesson-resources', {

                    method: 'POST',

                    headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify({

                        userId: state.userId,

                        subject,

                        lessonNum,

                        resourceType,

                        fileId: ''

                    })

                });

                const data = await res.json();

                if (data.success) {

                    showToast(`🗑️ تم المسح بنجاح`, 'success');

                    await loadMediaDashboard();

                } else {

                    showToast('❌ فشل المسح: ' + (data.error || 'خطأ'), 'error');

                }

            } catch (err) {

                showToast('❌ خطأ في الاتصال: ' + err.message, 'error');

            }

        }

        // ─── Phase 2: Apply visible sections from DB ───

        function applyVisibleSections(visibleSections, role) {

            if (!visibleSections || role === 'super_admin') return; // super_admin always sees everything

            // Map section keys → button IDs

            const sectionMap = {

                'inbox':       'btn-tab-courses-section', // handled via sidebar section

                'questions':   'btn-tab-questions',

                'transcripts': 'btn-tab-courses',

                'media':       'btn-tab-media',

                'students':    'btn-tab-students',

                'config':      'btn-tab-config',

            };

            // Hide all non-inbox sidebar sections first, then show allowed

            Object.entries(sectionMap).forEach(([key, btnId]) => {

                const btn = document.getElementById(btnId);

                if (!btn) return;

                if (!visibleSections.includes(key)) {

                    btn.style.display = 'none';

                }

            });

            // Handle inbox separately (hide the whole sidebar section)

            if (!visibleSections.includes('inbox')) {

                const inboxSection = document.getElementById('section-inbox');

                if (inboxSection) inboxSection.style.display = 'none';

            }

        }

        // ─── Phase 3: Load shared custom views from DB ───

        async function loadSharedCustomViews() {

            try {

                const res = await fetch('/admin/custom-views/list', {

                    method: 'POST',

                    headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify({ userId: state.userId })

                });

                const data = await res.json();

                if (!data.success) return;

                // Mark DB views and merge with localStorage views (avoid duplicates by id)

                const dbViews = (data.views || []).map(v => ({ ...v, _fromDB: true }));

                const localViews = (state.customViews || []).filter(v => !v._fromDB);

                // DB views take precedence

                const dbIds = new Set(dbViews.map(v => v.id));

                const merged = [...dbViews, ...localViews.filter(v => !dbIds.has(v.id))];

                state.customViews = merged;

                // Re-render the custom views tabs bar

                renderInbox();

            } catch (e) {

                console.warn('Could not load shared custom views:', e);

            }

        }

        function renderCustomViewTabs() {

            const container = document.getElementById('custom-views-tabs');

            if (!container) return;

            container.innerHTML = '';

            (state.customViews || []).forEach(view => {

                const tab = document.createElement('div');

                tab.className = 'qb-sheet-tab';

                tab.id = `cv-tab-${view.id}`;

                tab.style.cssText = 'font-size:0.82rem; position:relative;';

                tab.innerHTML = `${view.icon || '📌'} ${view.name}

                    ${view._fromDB && view.isLocked ? '<span style="font-size:0.6rem; opacity:0.6;">🔒</span>' : ''}`;

                tab.onclick = () => switchSheet(view.id);

                // Edit button for super_admin or own private views

                if (state.adminRole === 'super_admin' || (!view._fromDB && view.createdBy === state.userId)) {

                    const editBtn = document.createElement('span');

                    editBtn.innerHTML = ' ✏️';

                    editBtn.style.cssText = 'font-size:0.7rem; cursor:pointer; opacity:0.6;';

                    editBtn.title = 'Modifier cette vue';

                    editBtn.onclick = (e) => { e.stopPropagation(); openCustomViewModal(view); };

                    tab.appendChild(editBtn);

                }

                container.appendChild(tab);

            });

            // Add "+" button for super_admin

            if (state.adminRole === 'super_admin') {

                const addBtn = document.createElement('div');

                addBtn.className = 'qb-sheet-tab';

                addBtn.style.cssText = 'font-size:0.82rem; opacity:0.7; cursor:pointer;';

                addBtn.innerHTML = '＋ إضافة وجهة';

                addBtn.onclick = () => openCustomViewModal(null);

                container.appendChild(addBtn);

            }

        }

        // ─── Custom View Modal ───

        function openCustomViewModal(view = null) {

            const isNew = !view;

            const admins = state.adminsList || [];

            const modal = document.getElementById('custom-view-modal');

            if (!modal) return;

            document.getElementById('cvm-title').textContent = isNew ? '➕ إنشاء وجهة جديدة' : '✏️ تعديل الوجهة';

            document.getElementById('cvm-id').value = view?.id || '';

            document.getElementById('cvm-name').value = view?.name || '';

            document.getElementById('cvm-icon').value = view?.icon || '📌';

            document.getElementById('cvm-visibility').value = view?.visibility || 'private';

            document.getElementById('cvm-locked').checked = view?.isLocked || false;

            // Filters

            const f = view?.filters || {};

            document.getElementById('cvm-filter-status').value = f.status || '';

            document.getElementById('cvm-filter-type').value = f.type || '';

            document.getElementById('cvm-filter-subject').value = f.subject || '';

            // Target admin checkboxes

            const targetContainer = document.getElementById('cvm-target-admins');

            targetContainer.innerHTML = admins.map(a => `

                <label style="display:flex; align-items:center; gap:6px; font-size:0.82rem; cursor:pointer; padding:4px 0;">

                    <input type="checkbox" value="${a.user_id}" ${(view?.targetIds || []).includes(a.user_id) ? 'checked' : ''}

                        style="width:16px; height:16px; cursor:pointer;">

                    ${a.first_name || a.username || a.user_id} 

                    <span style="color:var(--text-secondary); font-size:0.75rem;">(${arabicRoleLabel(a.role)})</span>

                </label>

            `).join('') || '<span style="color:var(--text-secondary); font-size:0.82rem;">لا يوجد admins</span>';

            toggleCvmTargetVisibility();

            const backdrop = document.getElementById('cvm-backdrop');

            if (modal && backdrop) {

                backdrop.style.opacity = '1';

                backdrop.style.pointerEvents = 'auto';

                modal.style.opacity = '1';

                modal.style.pointerEvents = 'auto';

                modal.style.transform = 'translate(-50%, -50%) scale(1)';

            }

        }

        function toggleCvmTargetVisibility() {

            const vis = document.getElementById('cvm-visibility')?.value;

            const targetSection = document.getElementById('cvm-target-section');

            if (targetSection) targetSection.style.display = (vis === 'targeted') ? 'block' : 'none';

        }

        function closeCustomViewModal() {

            const modal = document.getElementById('custom-view-modal');

            const backdrop = document.getElementById('cvm-backdrop');

            if (modal && backdrop) {

                backdrop.style.opacity = '0';

                backdrop.style.pointerEvents = 'none';

                modal.style.opacity = '0';

                modal.style.pointerEvents = 'none';

                modal.style.transform = 'translate(-50%, -50%) scale(0.95)';

            }

        }

        async function saveCustomViewModal() {

            const id = document.getElementById('cvm-id').value || null;

            const name = document.getElementById('cvm-name').value.trim();

            if (!name) { showToast('⚠️ يرجى إدخال اسم للوجهة', 'error'); return; }

            const icon = document.getElementById('cvm-icon').value.trim() || '📌';

            const visibility = document.getElementById('cvm-visibility').value;

            const isLocked = document.getElementById('cvm-locked').checked;

            const filters = {

                status: document.getElementById('cvm-filter-status').value || '',

                type:   document.getElementById('cvm-filter-type').value || '',

                subject: document.getElementById('cvm-filter-subject').value || '',

            };

            const targetIds = [...document.querySelectorAll('#cvm-target-admins input[type=checkbox]:checked')]

                .map(cb => parseInt(cb.value));

            try {

                const res = await fetch('/admin/custom-views/save', {

                    method: 'POST',

                    headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify({

                        userId: state.userId, id, name, icon, visibility, isLocked, filters, targetIds

                    })

                });

                const data = await res.json();

                if (data.success) {

                    showToast('✅ تم حفظ الوجهة بنجاح', 'success');

                    closeCustomViewModal();

                    await loadSharedCustomViews();

                } else {

                    showToast('❌ فشل الحفظ: ' + (data.error || ''), 'error');

                }

            } catch (e) {

                showToast('❌ خطأ في الاتصال', 'error');

            }

        }

        async function deleteCustomViewFromModal() {

            const id = document.getElementById('cvm-id').value;

            if (!id || !confirm('هل تريد حذف هذه الوجهة نهائياً؟')) return;

            try {

                const res = await fetch('/admin/custom-views/delete', {

                    method: 'POST',

                    headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify({ userId: state.userId, id })

                });

                const data = await res.json();

                if (data.success) {

                    showToast('🗑️ تم الحذف', 'success');

                    closeCustomViewModal();

                    await loadSharedCustomViews();

                } else {

                    showToast('❌ ' + (data.error || 'فشل الحذف'), 'error');

                }

            } catch (e) {

                showToast('❌ خطأ في الاتصال', 'error');

            }

        }

        // ─── Phase 2: Admin permissions panel in gestion des admins ───

        async function saveAdminPermissions(targetId) {

            const subjectCheckboxes = document.querySelectorAll(`#admin-subjects-${targetId} input[type=checkbox]:checked`);

            const sectionCheckboxes = document.querySelectorAll(`#admin-sections-${targetId} input[type=checkbox]:checked`);

            const allowedSubjects = subjectCheckboxes.length > 0 

                ? [...subjectCheckboxes].map(cb => cb.value) 

                : null;  // null = all subjects

            const visibleSections = sectionCheckboxes.length > 0 

                ? [...sectionCheckboxes].map(cb => cb.value) 

                : null;  // null = all sections

            try {

                const res = await fetch('/admin/update-permissions', {

                    method: 'POST',

                    headers: { 'Content-Type': 'application/json' },

                    body: JSON.stringify({

                        userId: state.userId,

                        targetId,

                        allowedSubjects,

                        visibleSections

                    })

                });

                const data = await res.json();

                if (data.success) {

                    showToast('✅ تم حفظ صلاحيات المشرف', 'success');

                } else {

                    showToast('❌ ' + (data.error || 'فشل الحفظ'), 'error');

                }

            } catch (e) {

                showToast('❌ خطأ في الاتصال', 'error');

            }

        }

    
