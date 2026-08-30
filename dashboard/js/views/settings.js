// settings.js - Settings & Permissions Manager

export function initSettingsView(container) {
    container.innerHTML = `
        <section class="view active module-view" style="position:relative; background: var(--bg); overflow-y: auto;">
            <header class="app-header" style="border-bottom: 1px solid var(--border);">
                <div class="header-left">
                    <button class="hamburger-btn" onclick="toggleSidebar()">☰</button>
                    <div class="header-titles">
                        <h1>⚙️ الإعدادات والصلاحيات</h1>
                        <span class="header-subtitle">إدارة فريق العمل وتخصيص الواجهة</span>
                    </div>
                </div>
                <button class="btn-primary" id="btn-save-settings" style="padding: 8px 15px; border-radius: 20px; font-weight: bold; background: #2ecc71; color: white; border: none; cursor: pointer;">
                    💾 حفظ التغييرات
                </button>
            </header>
            
            <div style="padding: 20px; max-width: 900px; margin: 0 auto; color: var(--text-1);">
                
                <!-- Theme Settings -->
                <div style="background: var(--surface-solid); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 30px;">
                    <h2 style="font-size: 1.2rem; margin-bottom: 15px; border-bottom: 1px solid var(--border); padding-bottom: 10px;">🎨 تخصيص المظهر</h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label style="display: block; margin-bottom: 8px; color: var(--text-muted);">الوضع (Theme)</label>
                            <select id="theme-select" style="width: 100%; padding: 10px; border-radius: 8px; background: var(--surface-hover); color: var(--text-1); border: 1px solid var(--border);">
                                <option value="dark">🌙 الوضع الليلي (افتراضي)</option>
                                <option value="light">☀️ الوضع النهاري</option>
                            </select>
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 8px; color: var(--text-muted);">حجم الخط</label>
                            <select id="font-size-select" style="width: 100%; padding: 10px; border-radius: 8px; background: var(--surface-hover); color: var(--text-1); border: 1px solid var(--border);">
                                <option value="small">صغير</option>
                                <option value="medium" selected>متوسط</option>
                                <option value="large">كبير</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Admin Permissions -->
                <div style="background: var(--surface-solid); border: 1px solid var(--border); border-radius: 12px; padding: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid var(--border); padding-bottom: 10px;">
                        <h2 style="font-size: 1.2rem; margin: 0;">👥 إدارة المشرفين والصلاحيات</h2>
                        <button class="btn-icon" style="color: #3498db; font-size: 0.9rem;">+ إضافة مشرف</button>
                    </div>
                    
                    <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 20px;">
                        قم بتحديد الأقسام التي يمكن لكل مشرف رؤيتها والرد عليها. لن يرى المشرف التذاكر غير المصرح له بها.
                    </p>

                    <div style="display: flex; flex-direction: column; gap: 15px;">
                        
                        <!-- Admin 1 -->
                        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border: 1px solid var(--border);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <div style="font-weight: bold; font-size: 1.1rem;">حسام (مدير عام)</div>
                                <span class="tag tag-urgent">Admin</span>
                            </div>
                            <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.9rem;">
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox" checked disabled> ⚙️ تقني
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox" checked disabled> 💳 مالي
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox" checked disabled> 📚 دعم الدروس
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox" checked disabled> 📝 امتحان
                                </label>
                            </div>
                        </div>

                        <!-- Admin 2 -->
                        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border: 1px solid var(--border);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <div style="font-weight: bold; font-size: 1.1rem;">أحمد (دعم مالي)</div>
                                <span style="font-size: 0.8rem; color: #e74c3c; cursor: pointer;">حذف المشرف</span>
                            </div>
                            <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.9rem;">
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox"> ⚙️ تقني
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox" checked> 💳 مالي
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox"> 📚 دعم الدروس
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox"> 📝 امتحان
                                </label>
                            </div>
                        </div>

                        <!-- Admin 3 -->
                        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border: 1px solid var(--border);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <div style="font-weight: bold; font-size: 1.1rem;">فاطمة (دعم أكاديمي)</div>
                                <span style="font-size: 0.8rem; color: #e74c3c; cursor: pointer;">حذف المشرف</span>
                            </div>
                            <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.9rem;">
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox"> ⚙️ تقني
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox"> 💳 مالي
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox" checked> 📚 دعم الدروس
                                </label>
                                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                                    <input type="checkbox" checked> 📝 امتحان
                                </label>
                            </div>
                        </div>

                    </div>
                </div>

            </div>
        </section>
    `;

    // Load saved settings
    const savedTheme = localStorage.getItem('crm-theme') || 'dark';
    const savedFont = localStorage.getItem('crm-font') || 'medium';
    
    document.getElementById('theme-select').value = savedTheme;
    document.getElementById('font-size-select').value = savedFont;

    // Save button logic
    document.getElementById('btn-save-settings').addEventListener('click', () => {
        const theme = document.getElementById('theme-select').value;
        const font = document.getElementById('font-size-select').value;
        
        localStorage.setItem('crm-theme', theme);
        localStorage.setItem('crm-font', font);
        
        applyTheme(theme, font);
        alert('تم حفظ الإعدادات وتطبيقها بنجاح! 💾');
    });
}

export function applyTheme(theme, font) {
    // Theme application
    if (theme === 'light') {
        document.documentElement.style.setProperty('--bg', '#f8f9fa');
        document.documentElement.style.setProperty('--surface', '#ffffff');
        document.documentElement.style.setProperty('--surface-solid', '#ffffff');
        document.documentElement.style.setProperty('--surface-hover', '#e9ecef');
        document.documentElement.style.setProperty('--text-1', '#212529');
        document.documentElement.style.setProperty('--text-muted', '#6c757d');
        document.documentElement.style.setProperty('--border', '#dee2e6');
    } else {
        // Reset to dark (default)
        document.documentElement.style.removeProperty('--bg');
        document.documentElement.style.removeProperty('--surface');
        document.documentElement.style.removeProperty('--surface-solid');
        document.documentElement.style.removeProperty('--surface-hover');
        document.documentElement.style.removeProperty('--text-1');
        document.documentElement.style.removeProperty('--text-muted');
        document.documentElement.style.removeProperty('--border');
    }
    
    // Font application
    if (font === 'small') document.documentElement.style.fontSize = '14px';
    else if (font === 'large') document.documentElement.style.fontSize = '18px';
    else document.documentElement.style.fontSize = '16px';
}
