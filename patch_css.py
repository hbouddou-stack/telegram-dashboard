css_file = 'dashboard/reader.css'
with open(css_file, 'r', encoding='utf-8') as f:
    css = f.read()

quiz_css = """
/* ─── QUIZ ENGINE (PRACTICE TAB) STYLES ─── */
.quiz-option-btn {
    display: flex;
    align-items: center;
    background: var(--surface);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: right;
    width: 100%;
}
.quiz-option-btn:hover {
    border-color: var(--primary);
    background: var(--primary-light, rgba(79,70,229,0.05));
}
.quiz-option-btn .opt-letter {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: var(--bg);
    color: var(--text-2);
    font-weight: bold;
    margin-left: 16px;
    flex-shrink: 0;
}
.quiz-option-btn .opt-text {
    font-size: 16px;
    color: var(--text);
    line-height: 1.4;
}
.quiz-option-btn.correct {
    border-color: #10b981;
    background: rgba(16,185,129,0.1);
}
.quiz-option-btn.correct .opt-letter {
    background: #10b981;
    color: white;
}
.quiz-option-btn.wrong {
    border-color: #ef4444;
    background: rgba(239,68,68,0.1);
}
.quiz-option-btn.wrong .opt-letter {
    background: #ef4444;
    color: white;
}

/* Circular Chart Animation */
.circular-chart {
    display: block;
    margin: 0 auto;
    max-width: 80%;
    max-height: 250px;
}
.circle-bg {
    fill: none;
    stroke: var(--border-color);
    stroke-width: 3;
}
.circle {
    fill: none;
    stroke-width: 3;
    stroke-linecap: round;
    transition: stroke-dasharray 1s ease-out;
}
"""

if "QUIZ ENGINE (PRACTICE TAB) STYLES" not in css:
    css = css + '\n' + quiz_css

with open(css_file, 'w', encoding='utf-8') as f:
    f.write(css)

print("CSS Patch applied")
