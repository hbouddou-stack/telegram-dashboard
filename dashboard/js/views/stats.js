// stats.js - Admin Statistics View

export function initStatsView(container) {
    container.innerHTML = `
        <section class="view active module-view" style="position:relative; background: var(--bg); overflow-y: auto;">
            <header class="app-header" style="border-bottom: 1px solid var(--border);">
                <div class="header-left">
                    <button class="hamburger-btn" onclick="toggleSidebar()">☰</button>
                    <div class="header-titles">
                        <h1>📊 الإحصائيات</h1>
                        <span class="header-subtitle">أداء فريق الدعم</span>
                    </div>
                </div>
            </header>
            
            <div style="padding: 20px;">
                <!-- KPIs -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px;">
                    <div class="stat-card" style="background: var(--surface-solid); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid var(--border);">
                        <div style="font-size: 2rem; color: var(--gold); font-weight: bold;">142</div>
                        <div style="color: var(--text-muted); font-size: 0.9rem;">إجمالي التذاكر</div>
                    </div>
                    <div class="stat-card" style="background: var(--surface-solid); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid var(--border);">
                        <div style="font-size: 2rem; color: #2ecc71; font-weight: bold;">128</div>
                        <div style="color: var(--text-muted); font-size: 0.9rem;">تم الحل</div>
                    </div>
                    <div class="stat-card" style="background: var(--surface-solid); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid var(--border);">
                        <div style="font-size: 2rem; color: #e74c3c; font-weight: bold;">14</div>
                        <div style="color: var(--text-muted); font-size: 0.9rem;">قيد الانتظار</div>
                    </div>
                    <div class="stat-card" style="background: var(--surface-solid); padding: 20px; border-radius: 12px; text-align: center; border: 1px solid var(--border);">
                        <div style="font-size: 2rem; color: #3498db; font-weight: bold;">15 د</div>
                        <div style="color: var(--text-muted); font-size: 0.9rem;">متوسط الرد</div>
                    </div>
                </div>

                <!-- Admin Leaderboard -->
                <h2 style="color: var(--text-1); font-size: 1.2rem; margin-bottom: 15px;">🏆 أداء المشرفين</h2>
                <div style="background: var(--surface-solid); border-radius: 12px; border: 1px solid var(--border); overflow: hidden;">
                    <table style="width: 100%; border-collapse: collapse; color: var(--text-1); text-align: right;">
                        <thead>
                            <tr style="border-bottom: 1px solid var(--border); background: rgba(0,0,0,0.2);">
                                <th style="padding: 15px;">المشرف</th>
                                <th style="padding: 15px;">التذاكر المحلولة</th>
                                <th style="padding: 15px;">تقييم الرضا CSAT</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 15px; font-weight: bold;">حسام (أنت)</td>
                                <td style="padding: 15px; color: #2ecc71;">85 تذكرة</td>
                                <td style="padding: 15px; color: var(--gold);">⭐⭐⭐⭐⭐ (4.9)</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 15px; font-weight: bold;">أحمد</td>
                                <td style="padding: 15px; color: #2ecc71;">30 تذكرة</td>
                                <td style="padding: 15px; color: var(--gold);">⭐⭐⭐⭐ (4.2)</td>
                            </tr>
                            <tr>
                                <td style="padding: 15px; font-weight: bold;">فاطمة</td>
                                <td style="padding: 15px; color: #2ecc71;">13 تذكرة</td>
                                <td style="padding: 15px; color: var(--gold);">⭐⭐⭐⭐⭐ (4.8)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Funnel Stats -->
                <h2 style="color: var(--text-1); font-size: 1.2rem; margin-top: 30px; margin-bottom: 15px;">📁 التوزيع حسب الأقسام</h2>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; background: var(--surface-solid); padding: 15px; border-radius: 8px;">
                        <span>⚙️ تقني</span>
                        <div style="flex:1; margin: 0 15px; background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="width: 45%; background: var(--accent); height: 100%;"></div>
                        </div>
                        <span>45%</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; background: var(--surface-solid); padding: 15px; border-radius: 8px;">
                        <span>💳 مالي</span>
                        <div style="flex:1; margin: 0 15px; background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="width: 25%; background: #2ecc71; height: 100%;"></div>
                        </div>
                        <span>25%</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; background: var(--surface-solid); padding: 15px; border-radius: 8px;">
                        <span>📚 دعم الدروس</span>
                        <div style="flex:1; margin: 0 15px; background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="width: 20%; background: #3498db; height: 100%;"></div>
                        </div>
                        <span>20%</span>
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; background: var(--surface-solid); padding: 15px; border-radius: 8px;">
                        <span>📝 امتحان</span>
                        <div style="flex:1; margin: 0 15px; background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="width: 10%; background: #e74c3c; height: 100%;"></div>
                        </div>
                        <span>10%</span>
                    </div>
                </div>

            </div>
        </section>
    `;
}
