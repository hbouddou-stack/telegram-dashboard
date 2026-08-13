import re

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Change Home Tab to Inbox Tab in Nav
html = html.replace(
    '<button class="nav-btn active" onclick="switchTab(\'home\',this)"><span class="icon">??</span><span>????????</span></button>',
    '<button class="nav-btn active" onclick="switchTab(\'inbox\',this)"><span class="icon">??</span><span>????? ??????</span></button>'
)
html = html.replace(
    '<button class="nav-btn" onclick="switchTab(\'flashcards\',this)"><span class="icon">??</span><span>????????</span></button>',
    '<button class="nav-btn" onclick="switchTab(\'support\',this)"><span class="icon">??</span><span>?????</span></button>'
)

inbox_content = '''
    <div class="tab-panel active" id="tab-inbox" style="padding: 20px; direction: rtl; text-align: right; background: var(--bg); min-height: 100vh; padding-bottom: 90px;">
        <h2 style="color:var(--primary); font-weight:800; margin-bottom:20px; text-align: center;">?? ????? ??????</h2>
        
        <div style="background: var(--surface); border-radius: 12px; padding: 15px; margin-bottom: 12px; border-right: 4px solid var(--primary); box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <strong style="color: var(--text-1);">????? ??????????</strong>
                <span style="font-size: 11px; color: var(--text-3);">????</span>
            </div>
            <div style="font-size: 14px; color: var(--text-2);">?????? ?? ?? ???? ?????? ?????????! ??? ??? ???????? ?? ?? ???.</div>
        </div>

        <div style="background: var(--surface); border-radius: 12px; padding: 15px; margin-bottom: 12px; border-right: 4px solid #10b981; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <strong style="color: var(--text-1);">????? ????? #102</strong>
                <span style="font-size: 11px; color: var(--text-3);">???</span>
            </div>
            <div style="font-size: 14px; color: var(--text-2);">?? ?? ??????? ??????? ???? ????? ????. ????? ?????!</div>
            <div id="ticket-resolve-actions-102" style="display: flex; gap: 10px; margin-top: 15px;">
                <button onclick="document.getElementById('ticket-resolve-actions-102').innerHTML='<span style=\\'color: #10b981; font-weight: bold; font-size: 13px;\\'>? ????? ??! ?????? ?? ??????? ????.</span>';" style="flex: 1; background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; padding: 8px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 13px;">?? ??????? ????</button>
                <button onclick="document.getElementById('ticket-resolve-actions-102').innerHTML='<span style=\\'color: #ef4444; font-weight: bold; font-size: 13px;\\'>???? ????? ??? ??????? ?????? ???????...</span>';" style="flex: 1; background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; padding: 8px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 13px;">?? ????? ?????? ?? ?????</button>
            </div>
        </div>
    </div>
'''

html = re.sub(r'<div class="tab-panel active" id="tab-home">.*?<div class="tab-panel" id="tab-search">', inbox_content + '\n    <div class="tab-panel" id="tab-search">', html, flags=re.DOTALL)

support_funnel_content = '''
    <div class="tab-panel" id="tab-support" style="background: #f0f2f5; min-height: 100vh; display: flex; flex-direction: column; direction: rtl; padding-bottom: 90px;">
        <div style="background: var(--primary); color: white; padding: 15px 20px; text-align: center; font-weight: bold; font-size: 18px; position: sticky; top: 0; z-index: 10; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            ?? ??????? ?????
        </div>
        
        <div id="support-chat-history-index" style="flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; padding-bottom: 120px;">
            <!-- Initial Bot Message -->
            <div style="align-self: flex-start; background: white; padding: 12px 16px; border-radius: 16px 16px 0 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); max-width: 85%;">
                ?????? ??! ??<br>?? ??? ?? ??????? ????? ???????
            </div>
            
            <div id="support-step-1-options-index" style="display: flex; flex-direction: column; gap: 8px; align-self: flex-start; width: 100%; max-width: 85%;">
                <button onclick="supportFlowIndex.selectCategory('?????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 10px; border-radius: 12px; font-weight: bold;">?? ????? ?????</button>
                <button onclick="supportFlowIndex.selectCategory('??????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 10px; border-radius: 12px; font-weight: bold;">?? ????? ?????? (???? ?????)</button>
                <button onclick="supportFlowIndex.selectCategory('?????????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 10px; border-radius: 12px; font-weight: bold;">?? ????? ?? ?????? (?????????)</button>
            </div>
        </div>

        <div id="support-chat-input-area-index" style="display: none; background: white; padding: 10px 15px; border-top: 1px solid #e5e7eb; position: fixed; bottom: 70px; width: 100%; box-sizing: border-box; align-items: center; gap: 10px; z-index: 20;">
            <input type="text" id="support-chat-input-index" placeholder="???? ?????? ?????? ???..." style="flex: 1; border: none; background: #f3f4f6; padding: 12px 16px; border-radius: 24px; outline: none; font-family: inherit;">
            <button onclick="supportFlowIndex.sendMessage()" style="background: var(--primary); color: white; border: none; width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
        </div>
    </div>
'''

html = html.replace('<div class="tab-panel" id="tab-profile">', support_funnel_content + '\n    <div class="tab-panel" id="tab-profile">')

js_content = '''
const supportFlowIndex = {
    category: '', subcategory: '', message: '', currentOptsId: '',
    selectCategory: function(cat) {
        this.category = cat;
        this.addMessage(cat, 'user');
        document.getElementById('support-step-1-options-index').style.display = 'none';
        
        setTimeout(() => {
            let subText = ''; let subBtns = '';
            if(cat === '?????') {
                subText = '?? ??????? ?????? ??:';
                subBtns = 
                    <button onclick="supportFlowIndex.selectSubcategory('??????? ?? ????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">??????? ?? ????</button>
                    <button onclick="supportFlowIndex.selectSubcategory('?? ???? ???')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">?? ???? ???</button>
                    <button onclick="supportFlowIndex.selectSubcategory('????? ?? ???????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">????? ?? ???????</button>
                ;
            } else if(cat === '??????') {
                subText = '?????? ????? ???????:';
                subBtns = 
                    <button onclick="supportFlowIndex.selectSubcategory('????? ????????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">????? ????????</button>
                    <button onclick="supportFlowIndex.selectSubcategory('????? ?? ?????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">????? ?? ?????</button>
                ;
            } else {
                subText = '?? ??????? ??:';
                subBtns = 
                    <button onclick="supportFlowIndex.selectSubcategory('??? ?????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">??? ?????</button>
                    <button onclick="supportFlowIndex.selectSubcategory('???? ??? ????????')" style="background: white; border: 1px solid var(--primary); color: var(--primary); padding: 8px 12px; border-radius: 20px; font-weight: bold;">???? ??? ????????</button>
                ;
            }
            this.addMessage(subText, 'bot');
            const optsId = 'subopts-idx-' + Date.now();
            const optsHtml = <div id="" style="display: flex; flex-wrap: wrap; gap: 8px; align-self: flex-start; max-width: 85%;"></div>;
            document.getElementById('support-chat-history-index').insertAdjacentHTML('beforeend', optsHtml);
            this.currentOptsId = optsId;
            this.scrollToBottom();
        }, 500);
    },
    selectSubcategory: function(sub) {
        this.subcategory = sub;
        this.addMessage(sub, 'user');
        if(this.currentOptsId) { document.getElementById(this.currentOptsId).style.display = 'none'; }
        
        setTimeout(() => {
            let tip = '';
            if (sub === '??????? ?? ????' || sub === '?? ???? ???') { tip = '?? ????? ?????: 90% ?? ????? ??????? ???? ????? ????? ?????? ?? ??? ????? ??????? ?????? (Cache). ?? ???? ????? ????<br><br>'; }
            else if (sub === '????? ?? ?????' || sub === '????? ????????') { tip = '?? ??????: ????? ?????????? ?? ???? ?? ??? 5 ??? 15 ????? ?????? ?? ??????? ??? ?????.<br><br>'; }
            else if (sub === '??? ?????') { tip = '?? ?? ????? ????? ??????? "??????? ???????" ?? "???? ?????" ???????? ?? ????? ????? ?????? ??? ???? ???? ??? ??? ??????.<br><br>'; }
            this.addMessage(tip + '??? ???? ??????? ??????? ???? ????? ???????? ?????:', 'bot');
            document.getElementById('support-chat-input-area-index').style.display = 'flex';
            document.getElementById('support-chat-input-index').focus();
            this.scrollToBottom();
        }, 500);
    },
    sendMessage: function() {
        const inp = document.getElementById('support-chat-input-index');
        const text = inp.value.trim();
        if(!text) return;
        this.message = text; inp.value = '';
        document.getElementById('support-chat-input-area-index').style.display = 'none';
        this.addMessage(text, 'user');
        setTimeout(() => {
            const typingId = 'typing-idx-' + Date.now();
            const typingHtml = <div id="" style="align-self: flex-start; background: white; padding: 12px 16px; border-radius: 16px 16px 0 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); display: flex; gap: 4px; align-items: center;"><span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;"></span><span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.2s;"></span><span style="width: 8px; height: 8px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.4s;"></span><span style="font-size: 12px; color: #6b7280; margin-right: 8px;">???? ?????...</span></div>;
            document.getElementById('support-chat-history-index').insertAdjacentHTML('beforeend', typingHtml);
            this.scrollToBottom();
            setTimeout(() => {
                document.getElementById(typingId).remove();
                this.showFaqAndEscalate();
            }, 2500);
        }, 400);
    },
    showFaqAndEscalate: function() {
        this.addMessage(????? ?? ??? ????? ??????. ????? ???? ??????? ??????? ?? ????? ??????? ???????., 'bot');
        const faqs = <div style="background: white; border-radius: 12px; padding: 10px; align-self: flex-start; width: 100%; max-width: 90%; margin-top: 5px;"><details style="padding: 8px; border-bottom: 1px solid #f3f4f6;"><summary style="font-weight: bold; cursor: pointer;">??? ??? ???? ??????</summary><p style="margin-top: 8px; font-size: 13px;">?????? ????? ?? ????? ????? ??? ?? (??????? ???????).</p></details></div><div style="align-self: center; margin-top: 15px;"><button onclick="supportFlowIndex.escalateToAdmin()" style="background: #ef4444; color: white; border: none; padding: 12px 20px; border-radius: 24px; font-weight: bold; cursor: pointer;">????? ??????? ??? ??????? ??</button></div>;
        document.getElementById('support-chat-history-index').insertAdjacentHTML('beforeend', faqs);
        this.scrollToBottom();
    },
    escalateToAdmin: function() {
        event.target.style.display = 'none';
        this.addMessage("????? ??????? ??? ???????", "user");
        setTimeout(() => { this.addMessage("? ??? ????? ???? ?????. ?????? ???? ?? ????? ??????.", "bot"); }, 800);
    },
    addMessage: function(text, sender) {
        const isBot = sender === 'bot';
        const bg = isBot ? 'white' : 'var(--primary)';
        const color = isBot ? 'var(--text-1)' : 'white';
        const align = isBot ? 'flex-start' : 'flex-end';
        const radius = isBot ? '16px 16px 0 16px' : '16px 16px 16px 0';
        const html = <div style="align-self: ; background: ; color: ; padding: 12px 16px; border-radius: ; box-shadow: 0 1px 2px rgba(0,0,0,0.1); max-width: 85%;"></div>;
        document.getElementById('support-chat-history-index').insertAdjacentHTML('beforeend', html);
        this.scrollToBottom();
    },
    scrollToBottom: function() { const hist = document.getElementById('support-chat-history-index'); hist.scrollTop = hist.scrollHeight; }
};
'''

html = html.replace('</script>', js_content + '\n</script>')

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Success applying inbox/support to index.html")
