
                        let currentCardStyle = localStorage.getItem('cardStyle') || '1';
            let currentViewMode = localStorage.getItem('viewMode') || 'grid';
            let currentSort = { key: 'date', order: 'desc' };
            
            
        function toggleAllStudents() {
            const isChecked = document.getElementById('selectAllCheckbox').checked;
            const checkboxes = document.querySelectorAll('.student-select-cb');
            checkboxes.forEach(cb => cb.checked = isChecked);
            updateMassSmsButton();
        }
        document.addEventListener('change', (e) => {
            if(e.target && e.target.classList && e.target.classList.contains('student-select-cb')) {
                updateMassSmsButton();
            }
        });
        function updateMassSmsButton() {
            const selected = document.querySelectorAll('.student-select-cb:checked').length;
            const btn = document.getElementById('btn-mass-sms');
            if(btn) {
                if(selected > 0) {
                    btn.style.display = 'inline-block';
                    document.getElementById('mass-sms-count').innerText = selected;
                } else {
                    btn.style.display = 'none';
                }
            }
        }
        async function sendMassSms() {
            const cbs = document.querySelectorAll('.student-select-cb:checked');
            const ids = Array.from(cbs).map(cb => cb.value);
            if(ids.length === 0) return;
            if(!confirm(`هل أنت متأكد من وضع ${ids.length} طالب في قائمة انتظار SMS ؟`)) return;
            
            try {
                const res = await fetch('/api/admin/gateway/queue_sms', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ student_ids: ids })
                });
                const data = await res.json();
                if(data.success) {
                    alert(`✅ تم وضع ${data.queued} رسالة SMS في قائمة الانتظار للروبوت بنجاح.`);
                    cbs.forEach(cb => cb.checked = false);
                    document.getElementById('selectAllCheckbox').checked = false;
                    updateMassSmsButton();
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch(e) {
                console.error(e);
                alert('Erreur réseau.');
            }
        }

        
            
            function sortTable(key) {
                if(currentSort.key === key) {
                    currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSort.key = key;
                    currentSort.order = 'asc';
                }
                filterStudents();
            }

            document.addEventListener("DOMContentLoaded", () => {
                const sel = document.getElementById('card-style-selector');
                if (sel) sel.value = currentCardStyle;
                const vSel = document.getElementById('view-mode-selector');
                if (vSel) vSel.value = currentViewMode;
            });
            function changeCardStyle(style) {
                currentCardStyle = style;
                localStorage.setItem('cardStyle', style);
                filterStudents();
            }
        