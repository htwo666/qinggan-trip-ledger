#!/usr/bin/env python3
# h10_settings.py — 把"清空数据"按钮藏到设置弹窗，分类清空
import sys
src = open('index.html', encoding='utf-8').read()

# === 1) CSS：在 .feedback-btn @media 后面加 .settings-btn ===
css_anchor = "@media(min-width:768px){.feedback-btn{top:20px;right:24px;font-size:0.8rem;padding:5px 14px;}}\n"
css_new = """@media(min-width:768px){.feedback-btn{top:20px;right:24px;font-size:0.8rem;padding:5px 14px;}}
/* ========== 设置按钮 ========== */
.settings-btn{
  position:absolute;top:16px;right:62px;z-index:5;
  background:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.35);
  color:#fff;border-radius:14px;padding:4px 10px;font-size:0.95rem;line-height:1;
  font-family:inherit;cursor:pointer;backdrop-filter:blur(4px);
  -webkit-backdrop-filter:blur(4px);transition:background 0.2s;
}
.settings-btn:active{background:rgba(255,255,255,0.35);}
@media(min-width:768px){.settings-btn{top:20px;right:78px;font-size:1rem;padding:5px 11px;}}
/* 设置弹窗内的清空按钮列表 */
.danger-list{display:flex;flex-direction:column;gap:8px;margin-top:10px;}
.danger-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--card);}
.danger-item .di-text{flex:1;}
.danger-item .di-text .di-title{font-size:0.85rem;font-weight:600;color:var(--text);}
.danger-item .di-text .di-desc{font-size:0.72rem;color:var(--text-light);margin-top:2px;line-height:1.4;}
.danger-item .di-btn{border:1px solid rgba(231,93,93,0.4);background:rgba(231,93,93,0.06);color:var(--danger);border-radius:8px;padding:6px 12px;font-size:0.78rem;font-weight:600;cursor:pointer;font-family:inherit;flex-shrink:0;}
.danger-item .di-btn:active{background:rgba(231,93,93,0.15);}
.settings-section{margin-top:14px;}
.settings-section-title{font-size:0.82rem;font-weight:600;color:var(--primary-dark);margin-bottom:6px;padding-left:4px;border-left:3px solid var(--primary-light);}
"""
if src.count(css_anchor) != 1:
    print(f'!! css anchor ({src.count(css_anchor)})')
    sys.exit(1)
src = src.replace(css_anchor, css_new)

# === 2) HTML：在 feedbackBtn 旁边加 settingsBtn ===
html_old = '  <button class="feedback-btn" id="feedbackBtn" title="反馈与建议">反馈</button>\n'
html_new = '  <button class="feedback-btn" id="feedbackBtn" title="反馈与建议">反馈</button>\n  <button class="settings-btn" id="settingsBtn" title="设置">⚙</button>\n'
if src.count(html_old) != 1:
    print(f'!! html anchor ({src.count(html_old)})')
    sys.exit(1)
src = src.replace(html_old, html_new)

# === 3) 删除 renderPrep 里的 clearPrepSampleBtn ===
prep_old = """  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="addTodoBtn">'+svgIcon('plus')+'添加计划</button><button class="btn btn-outline btn-sm" id="clearPrepSampleBtn">清空数据</button></div>';"""
prep_new = """  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="addTodoBtn">'+svgIcon('plus')+'添加计划</button></div>';"""
if src.count(prep_old) != 1:
    print(f'!! prep toolbar ({src.count(prep_old)})')
    sys.exit(1)
src = src.replace(prep_old, prep_new)

# 删除 renderPrep 里 clearBtn 的 onclick 绑定
prep_handler_old = """  var clearBtn=document.getElementById('clearPrepSampleBtn');
  if(clearBtn){clearBtn.onclick=function(){
    showConfirm('清空准备数据','将删除全部计划与物品记录，此操作不可撤销。确定继续吗？',function(){
      state.data.prepItems=[];state.data.prepCategories=[];state.data.todos=[];saveData();renderPrep();showToast('已清空');
    });
  };}
"""
if src.count(prep_handler_old) != 1:
    print(f'!! prep handler ({src.count(prep_handler_old)})')
    sys.exit(1)
src = src.replace(prep_handler_old, "")

# === 4) 删除 renderSummary 里的 clearAllBtn ===
sum_old = """<button class="btn btn-danger btn-sm" id="clearAllBtn">"+svgIcon('trash')+"清空数据</button></div>';"""
sum_new = "</div>';"
if src.count(sum_old) != 1:
    print(f'!! summary toolbar ({src.count(sum_old)})')
    sys.exit(1)
src = src.replace(sum_old, sum_new)

# 删除 renderSummary 里 clearAllBtn 的 onclick 绑定
sum_handler_old = """  document.getElementById('clearAllBtn').onclick=function(){
    showConfirm('清空全部数据','将删除所有模块的全部数据（预付大项除外），此操作不可撤销。确定继续吗？',function(){
      state.data.expenses=[];state.data.outfits=[];state.data.todos=[];state.data.prepItems=[];
      saveData();renderSummary();showToast('已清空');
    });
  };
"""
if src.count(sum_handler_old) != 1:
    print(f'!! summary handler ({src.count(sum_handler_old)})')
    sys.exit(1)
src = src.replace(sum_handler_old, "")

# === 5) 在 feedbackBtn 处理后面加 settingsBtn 处理 + showSettingsModal 函数 ===
settings_handler_anchor = """if(feedbackBtn){
  feedbackBtn.onclick=function(){
    var url='https://github.com/htwo666/qinggan-trip-ledger/issues/new';
    /* 优先用 a 标签 + target=_blank，兼容弹窗拦截 */
    var a=document.createElement('a');
    a.href=url;a.target='_blank';a.rel='noopener noreferrer';
    document.body.appendChild(a);a.click();document.body.removeChild(a);
  };
}"""
settings_handler_new = """if(feedbackBtn){
  feedbackBtn.onclick=function(){
    var url='https://github.com/htwo666/qinggan-trip-ledger/issues/new';
    /* 优先用 a 标签 + target=_blank，兼容弹窗拦截 */
    var a=document.createElement('a');
    a.href=url;a.target='_blank';a.rel='noopener noreferrer';
    document.body.appendChild(a);a.click();document.body.removeChild(a);
  };
}
/* 设置按钮：打开设置弹窗（藏在这里的"清空数据"分类操作） */
var settingsBtn=document.getElementById('settingsBtn');
if(settingsBtn){settingsBtn.onclick=function(){showSettingsModal();};}
/* 设置弹窗：分类清空 */
function showSettingsModal(){
  var sheet=document.getElementById('formModalSheet');
  var prepN=aliveList(state.data.prepItems).length;
  var catN=aliveList(state.data.prepCategories).length;
  var todoN=aliveList(state.data.todos).length;
  var outfitN=aliveList(state.data.outfits).length;
  var expN=aliveList(state.data.expenses).length;
  var preN=aliveList(state.data.prepaid).length;
  sheet.innerHTML='<div class="form-modal-title">设置 <button id="closeForm">✕</button></div>'+
    '<div style="font-size:0.78rem;color:var(--text-light);margin-bottom:6px">数据管理 · 分类清空当前空间的数据（不可撤销，请谨慎）</div>'+
    '<div class="settings-section">'+
      '<div class="settings-section-title">分类清空</div>'+
      '<div class="danger-list">'+
        '<div class="danger-item"><div class="di-text"><div class="di-title">清空必买清单</div><div class="di-desc">删除全部物品和分类板块（'+prepN+' 件物品 / '+catN+' 个板块）</div></div><button class="di-btn" data-clear="prep">清空</button></div>'+
        '<div class="danger-item"><div class="di-text"><div class="di-title">清空计划</div><div class="di-desc">删除全部待办计划（'+todoN+' 条）</div></div><button class="di-btn" data-clear="todo">清空</button></div>'+
        '<div class="danger-item"><div class="di-text"><div class="di-title">清空穿搭记录</div><div class="di-desc">删除全部每日穿搭记录（'+outfitN+' 条）</div></div><button class="di-btn" data-clear="outfit">清空</button></div>'+
        '<div class="danger-item"><div class="di-text"><div class="di-title">清空账目</div><div class="di-desc">删除全部途中花费记录（'+expN+' 笔，预付大项 '+preN+' 项保留）</div></div><button class="di-btn" data-clear="expense">清空</button></div>'+
      '</div>'+
    '</div>'+
    '<div class="settings-section">'+
      '<div class="settings-section-title" style="border-left-color:var(--danger)">全部清空</div>'+
      '<div class="danger-list">'+
        '<div class="danger-item"><div class="di-text"><div class="di-title" style="color:var(--danger)">清空全部数据</div><div class="di-desc">删除所有模块的全部数据（成员保留，预付大项保留）</div></div><button class="di-btn" data-clear="all" style="background:var(--danger);color:#fff;border-color:var(--danger)">全部清空</button></div>'+
      '</div>'+
    '</div>'+
    '<div style="font-size:0.72rem;color:var(--text-light);margin-top:10px;line-height:1.5">提示：清空只影响当前空间（团队/个人）。云端备份在 Supabase，但删除后同步给所有设备，不可恢复。</div>'+
    '<button class="btn btn-primary btn-block" style="margin-top:14px" id="closeSettings">关闭</button>';
  document.getElementById('formModal').classList.add('show');
  document.getElementById('closeForm').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  document.getElementById('closeSettings').onclick=function(){document.getElementById('formModal').classList.remove('show');};
  var clearBtns=sheet.querySelectorAll('[data-clear]');
  for(var ci=0;ci<clearBtns.length;ci++){
    clearBtns[ci].onclick=function(){
      var kind=this.getAttribute('data-clear');
      var title='',msg='',fn=null;
      if(kind==='prep'){
        title='清空必买清单';
        msg='将删除全部 '+prepN+' 件物品和 '+catN+' 个分类板块，此操作不可撤销。确定继续吗？';
        fn=function(){state.data.prepItems=[];state.data.prepCategories=[];saveData();renderAll();};
      }else if(kind==='todo'){
        title='清空计划';
        msg='将删除全部 '+todoN+' 条计划，此操作不可撤销。确定继续吗？';
        fn=function(){state.data.todos=[];saveData();renderAll();};
      }else if(kind==='outfit'){
        title='清空穿搭记录';
        msg='将删除全部 '+outfitN+' 条穿搭记录，此操作不可撤销。确定继续吗？';
        fn=function(){state.data.outfits=[];saveData();renderAll();};
      }else if(kind==='expense'){
        title='清空账目';
        msg='将删除全部 '+expN+' 笔途中花费记录（预付大项 '+preN+' 项保留），此操作不可撤销。确定继续吗？';
        fn=function(){state.data.expenses=[];saveData();renderAll();};
      }else if(kind==='all'){
        title='清空全部数据';
        msg='将删除所有模块的全部数据（成员保留，预付大项 '+preN+' 项保留），此操作不可撤销。确定继续吗？';
        fn=function(){
          state.data.prepItems=[];state.data.prepCategories=[];
          state.data.todos=[];state.data.outfits=[];state.data.expenses=[];
          saveData();renderAll();
        };
      }
      if(fn){
        showConfirm(title,msg,function(){
          fn();
          document.getElementById('formModal').classList.remove('show');
          showToast('已清空');
        });
      }
    };
  }
}"""
if src.count(settings_handler_anchor) != 1:
    print(f'!! settings handler anchor ({src.count(settings_handler_anchor)})')
    sys.exit(1)
src = src.replace(settings_handler_anchor, settings_handler_new)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
