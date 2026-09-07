#!/usr/bin/env python3
# h14_outfit_perday.py — 每个日期旁边加「记录穿搭」按钮
# 1. CSS: 加 .day-outfit-add-btn 样式
# 2. renderOutfit: 每个 day-outfit-head 末尾加按钮
# 3. renderOutfit: 加按钮事件绑定（预填日期）
# 4. showOutfitForm: 支持 presetDate 参数（新建时预填日期）

src = open('index.html', encoding='utf-8').read()

# ---- 1. CSS: 在 .day-outfit-head 后面加按钮样式 ----
css_old = ".day-outfit-grid{display:grid;grid-template-columns:1fr;gap:10px;}"
css_new = (
    ".day-outfit-grid{display:grid;grid-template-columns:1fr;gap:10px;}\n"
    ".day-outfit-add-btn{margin-left:auto;border:1px solid var(--primary-light);background:var(--primary-bg);color:var(--primary-dark);font-family:inherit;font-size:0.7rem;padding:3px 10px;border-radius:12px;cursor:pointer;display:inline-flex;align-items:center;gap:3px;white-space:nowrap;flex-shrink:0;}\n"
    ".day-outfit-add-btn:active{transform:scale(0.96);}\n"
    ".day-outfit-add-btn svg{width:12px;height:12px;}"
)
c1 = src.count(css_old)
print(f'css anchor: {c1}')
if c1 != 1:
    print('!! css anchor not unique'); exit(1)
src = src.replace(css_old, css_new)

# ---- 2. renderOutfit: 每个 day-outfit-head 末尾加按钮 ----
head_old = """    else{listHtml+='<span class="day-badge">第'+day.day+'天</span>';}
    listHtml+='</div>';"""
head_new = """    else{listHtml+='<span class="day-badge">第'+day.day+'天</span>';}
    listHtml+='<button class="day-outfit-add-btn" data-outfit-date="'+day.date+'" title="为这一天记录穿搭">'+svgIcon('plus')+'记录</button>';
    listHtml+='</div>';"""
c2 = src.count(head_old)
print(f'head anchor: {c2}')
if c2 != 1:
    print('!! head anchor not unique'); exit(1)
src = src.replace(head_old, head_new)

# ---- 3. renderOutfit: 加按钮事件绑定（在 addBtn 绑定后面插入）----
handler_old = """  var addBtn=document.getElementById('addOutfitBtn');
  if(addBtn){addBtn.onclick=function(){showOutfitForm();};}"""
handler_new = """  var addBtn=document.getElementById('addOutfitBtn');
  if(addBtn){addBtn.onclick=function(){showOutfitForm();};}
  var dayAddBtns=p.querySelectorAll('[data-outfit-date]');
  for(var da=0;da<dayAddBtns.length;da++){
    dayAddBtns[da].onclick=function(){
      var dt=this.getAttribute('data-outfit-date');
      showOutfitForm(null,dt);
    };
  }"""
c3 = src.count(handler_old)
print(f'handler anchor: {c3}')
if c3 != 1:
    print('!! handler anchor not unique'); exit(1)
src = src.replace(handler_old, handler_new)

# ---- 4. showOutfitForm: 支持 presetDate 参数 ----
form_old = "function showOutfitForm(editId){\n  var today=todayStr();"
form_new = "function showOutfitForm(editId,presetDate){\n  var today=todayStr();"
c4 = src.count(form_old)
print(f'form sig anchor: {c4}')
if c4 != 1:
    print('!! form sig anchor not unique'); exit(1)
src = src.replace(form_old, form_new)

# ---- 5. showOutfitForm: initDate 用 presetDate ----
init_old = "  var initDate=editing?editRec.date:today;"
init_new = "  var initDate=editing?editRec.date:(presetDate||today);"
c5 = src.count(init_old)
print(f'initDate anchor: {c5}')
if c5 != 1:
    print('!! initDate anchor not unique'); exit(1)
src = src.replace(init_old, init_new)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
