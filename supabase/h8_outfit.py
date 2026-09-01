#!/usr/bin/env python3
# h8_outfit.py — 每日穿搭页面：行程和穿搭并列展示
import sys
src = open('index.html', encoding='utf-8').read()

# 1) 加 CSS（在 .outfit-actions 后面）
CSS_ANCHOR = ".outfit-actions{display:flex;gap:6px;margin-top:8px;}\n"
CSS = """/* ========== 每日穿搭并列布局 ========== */
.day-outfit-card{background:var(--card);border-radius:var(--radius);padding:14px;margin-bottom:10px;box-shadow:var(--shadow);border-left:4px solid var(--primary-light);}
.day-outfit-card.today{border-left-color:var(--accent);background:linear-gradient(135deg,#fff 0%,#fff6ea 100%);}
.day-outfit-card.past{opacity:0.6;}
.day-outfit-head{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;}
.day-outfit-head .day-num{font-size:0.92rem;font-weight:700;color:var(--primary-dark);}
.day-outfit-head .day-date{font-size:0.76rem;color:var(--text-light);}
.day-outfit-head .day-badge{font-size:0.66rem;padding:2px 8px;border-radius:10px;background:var(--primary-bg);color:var(--primary-dark);white-space:nowrap;}
.day-outfit-grid{display:grid;grid-template-columns:1fr;gap:10px;}
@media(min-width:640px){.day-outfit-grid{grid-template-columns:1fr 1fr;}}
.day-outfit-route{background:var(--primary-bg);border-radius:var(--radius-sm);padding:8px 10px;font-size:0.8rem;}
.day-outfit-route .r-line{margin:3px 0;color:var(--text);line-height:1.45;}
.day-outfit-route .r-line strong{color:var(--primary-dark);}
.day-outfit-route .r-temp{display:inline-block;font-size:0.72rem;padding:1px 7px;border-radius:6px;background:var(--card);color:var(--primary-dark);font-weight:600;margin:4px 0 2px;}
.day-outfit-route .r-tip{font-size:0.74rem;color:var(--text-light);margin-top:4px;line-height:1.45;}
.day-outfit-list{display:flex;flex-direction:column;gap:6px;}
.outfit-row{background:var(--card);border:1px solid var(--border);border-radius:var(--radius-sm);padding:6px 10px;font-size:0.78rem;display:flex;align-items:flex-start;gap:6px;}
.outfit-row .o-person{font-weight:600;color:var(--primary);white-space:nowrap;flex-shrink:0;}
.outfit-row .o-desc{color:var(--text);flex:1;line-height:1.45;}
.outfit-row .o-del{border:none;background:transparent;color:var(--text-light);cursor:pointer;padding:0;flex-shrink:0;display:flex;align-items:center;opacity:0.5;}
.outfit-row .o-del:hover{opacity:1;color:var(--danger);}
.outfit-row .o-del svg{width:13px;height:13px;}
.outfit-empty{font-size:0.74rem;color:var(--text-light);font-style:italic;padding:6px 8px;}
"""
if src.count(CSS_ANCHOR) != 1:
    print(f'!! CSS anchor ({src.count(CSS_ANCHOR)})')
    sys.exit(1)
src = src.replace(CSS_ANCHOR, CSS_ANCHOR + CSS)

# 2) 重写 renderOutfit
ro_start = src.index('function renderOutfit(){')
ro_end = src.index('function showOutfitForm(){')
old_ro = src[ro_start:ro_end]

NEW_RO = r"""function renderOutfit(){
  var p=document.getElementById('panel-outfit');
  var data=viewData();
  if(!data.outfits){state.data.outfits=[];data=viewData();}
  var today=todayStr();
  var todayIdx=daysBetween(TRIP_START,today);
  var todayDayNum=todayIdx>=0&&todayIdx<11?(todayIdx+1):null;
  /* 穿搭建议卡片（基于历史同期气候）—— 只留总建议，逐日气候合到下面的并列卡片里 */
  var weatherHtml='<div class="today-section"><div class="today-title">'+svgIcon('thermo')+'行程穿搭建议 <span style="font-size:0.68rem;color:var(--text-light);font-weight:400">（9月底-10月初历史同期气候参考）</span></div>'+
    '<div class="weather-brief">'+
      '<div class="weather-brief-item">'+svgIcon('layers')+'<span><strong>洋葱式穿法</strong>：昼夜温差 15°C+，内层速干/保暖 + 抓绒 + 冲锋衣，热了脱冷了加，脱下的衣服放车上</span></div>'+
      '<div class="weather-brief-item">'+svgIcon('sun')+'<span><strong>紫外线极强</strong>：墨镜 + 50倍防晒霜 + 遮阳帽；盐湖、戈壁、雪线反光加倍，防晒霜每 3 小时补涂</span></div>'+
      '<div class="weather-brief-item">'+svgIcon('glasses')+'<span><strong>羽绒必带</strong>：看星空、日出、青海湖/大柴旦早晚 0°C 左右；高原干燥，润唇膏和补水喷雾随身</span></div>'+
    '</div></div>';
  /* 按日期分组穿搭记录 */
  var byDate={};
  for(var k=0;k<data.outfits.length;k++){
    var dd=data.outfits[k].date;
    if(!byDate[dd]){byDate[dd]=[];}
    byDate[dd].push(data.outfits[k]);
  }
  /* 工具栏 */
  var toolbar='<div class="toolbar"><button class="btn btn-primary btn-sm" id="addOutfitBtn">'+svgIcon('plus')+'记录穿搭</button></div>';
  /* 逐日：行程 + 穿搭并列 */
  var listHtml='<div class="card"><div class="card-title">'+svgIcon('outfit')+'行程与穿搭 <span style="font-size:0.72rem;color:var(--text-light);font-weight:400">（DAY1 兰州-西宁，右边是大家的穿搭记录）</span></div>';
  for(var i=0;i<PRESET_ROUTE.length;i++){
    var day=PRESET_ROUTE[i];
    var wt=WEATHER_TIPS[i]||{};
    var dayOutfits=byDate[day.date]||[];
    var cls='';
    if(todayDayNum===day.day){cls=' today';}
    else if(day.date<today){cls=' past';}
    listHtml+='<div class="day-outfit-card'+cls+'">';
    listHtml+='<div class="day-outfit-head"><span class="day-num">DAY'+day.day+'</span><span class="day-date">'+fmtDate(day.date)+'</span>';
    if(todayDayNum===day.day){listHtml+='<span class="day-badge" style="background:var(--accent-light);color:#8a5a1a">今日</span>';}
    else if(day.date<today){listHtml+='<span class="day-badge">已完成</span>';}
    else{listHtml+='<span class="day-badge">第'+day.day+'天</span>';}
    listHtml+='</div>';
    listHtml+='<div class="day-outfit-grid">';
    /* 左：行程 */
    listHtml+='<div class="day-outfit-route">';
    listHtml+='<div class="r-line"><strong>'+escapeHtml(day.route)+'</strong></div>';
    listHtml+='<div class="r-line">亮点：<strong>'+escapeHtml(day.highlight)+'</strong></div>';
    listHtml+='<div class="r-line">住宿：'+escapeHtml(day.stay)+'</div>';
    if(wt.temp){listHtml+='<span class="r-temp">'+escapeHtml(wt.temp)+'</span>';}
    if(wt.tip){listHtml+='<div class="r-tip">'+escapeHtml(wt.tip)+'</div>';}
    listHtml+='<div style="margin-top:6px"><button class="ai-suggest-btn" data-ai-outfit=\''+escapeHtml(JSON.stringify({day:day.day,area:day.city,temp:wt.temp||'',tip:wt.tip||''}))+'\'>'+'✨ AI 穿搭建议</button></div>';
    listHtml+='</div>';
    /* 右：穿搭记录 */
    listHtml+='<div class="day-outfit-list">';
    if(dayOutfits.length===0){
      listHtml+='<div class="outfit-empty">还没有穿搭记录</div>';
    }else{
      for(var n=0;n<dayOutfits.length;n++){
        var o=dayOutfits[n];
        listHtml+='<div class="outfit-row"><span class="o-person">'+escapeHtml(o.person||'未署名')+'</span><span class="o-desc">'+escapeHtml(o.desc||'')+'</span><button class="o-del" data-action="delOutfit" data-id="'+o.id+'" title="删除">'+svgIcon('trash')+'</button></div>';
      }
    }
    listHtml+='</div>';
    listHtml+='</div>'; /* grid */
    listHtml+='</div>'; /* day-outfit-card */
  }
  listHtml+='</div>';
  p.innerHTML=weatherHtml+toolbar+listHtml;
  var addBtn=document.getElementById('addOutfitBtn');
  if(addBtn){addBtn.onclick=function(){showOutfitForm();};}
  var delBtns=p.querySelectorAll('[data-action="delOutfit"]');
  for(var db=0;db<delBtns.length;db++){
    delBtns[db].onclick=function(){
      var id=this.getAttribute('data-id');
      showConfirm('删除穿搭','确定删除这条穿搭记录吗？',function(){
        for(var i2=0;i2<state.data.outfits.length;i2++){
          if(state.data.outfits[i2].id===id){state.data.outfits[i2]._deleted=true;state.data.outfits[i2]._ts=Date.now();break;}
        }
        saveData();renderOutfit();showToast('已删除');
      });
    };
  }
  /* AI 穿搭建议按钮 */
  var outfitAiBtns=p.querySelectorAll('[data-ai-outfit]');
  for(var ob=0;ob<outfitAiBtns.length;ob++){
    outfitAiBtns[ob].onclick=function(){
      var info;
      try{info=JSON.parse(this.getAttribute('data-ai-outfit'));}catch(e){info={};}
      var prompt='我们在青甘大环线第'+info.day+'天，地点：'+info.area+'，气温：'+info.temp+'。气候参考：'+info.tip+'。请为我们4人（小美、阿杰、丸子、老王）分别给出今天的具体穿搭建议（含层次搭配、必备单品、防晒/防风重点），用简洁的列表格式。';
      prefillAI(prompt);
    };
  }
}
"""

src = src[:ro_start] + NEW_RO + src[ro_end:]
open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
