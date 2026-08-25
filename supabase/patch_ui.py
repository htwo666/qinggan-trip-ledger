#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""applySpaceModeUI 改为显示真实空间名 + 空间按钮永久可用"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src)

old = """function applySpaceModeUI(){
  var isPersonal=state.spaceMode==='personal';
  document.body.classList.toggle('space-personal',isPersonal);
  /* 切换器激活态 */
  var teamBtn=document.getElementById('spaceTeamBtn');
  var persBtn=document.getElementById('spacePersonalBtn');
  if(teamBtn){teamBtn.classList.toggle('active',!isPersonal);}
  if(persBtn){persBtn.classList.toggle('active',isPersonal);}
  /* 横幅标题与副标题 */
  var title=document.getElementById('bannerTitle');
  var sub=document.getElementById('bannerSub');
  if(title){title.textContent=isPersonal?'个人空间 · 旅行记账台':'青甘大环线 · 旅行记账台';}
  if(sub){sub.textContent=isPersonal?'私人记账 · 仅本地保存，不上传云端':'4人 11天自驾 · 2026-09-25 至 10-05';}
  /* 同步码按钮（个人空间禁用） */
  var syncCodeBtn=document.getElementById('syncCodeBtn');
  if(syncCodeBtn){
    syncCodeBtn.disabled=isPersonal;
    syncCodeBtn.style.opacity=isPersonal?'0.4':'1';
    syncCodeBtn.style.cursor=isPersonal?'not-allowed':'pointer';
    syncCodeBtn.title=isPersonal?'个人空间不需同步':'同步码';
  }
  /* 空间标签状态 */
  var teamTag=document.getElementById('teamTag');
  var persTag=document.getElementById('personalTag');
  if(teamTag){teamTag.textContent=isPersonal?'未激活':'同步中';}
  if(persTag){persTag.textContent=isPersonal?'仅本地':'未激活';}
}"""

new = """function applySpaceModeUI(){
  var isPersonal=state.spaceMode==='personal';
  var logged=!!(auth.session&&auth.currentWs);
  document.body.classList.toggle('space-personal',isPersonal);
  /* 切换器激活态 */
  var teamBtn=document.getElementById('spaceTeamBtn');
  var persBtn=document.getElementById('spacePersonalBtn');
  if(teamBtn){teamBtn.classList.toggle('active',!isPersonal);}
  if(persBtn){persBtn.classList.toggle('active',isPersonal);}
  /* 横幅标题：已登录时显示真实空间名（这样改名能多设备同步） */
  var title=document.getElementById('bannerTitle');
  var sub=document.getElementById('bannerSub');
  if(title){
    if(logged){
      title.textContent=auth.currentWs.name+(isPersonal?' · 私密记账':' · 旅行记账台');
    }else{
      title.textContent=isPersonal?'个人空间 · 旅行记账台':'青甘大环线 · 旅行记账台';
    }
  }
  if(sub){
    if(!logged){
      sub.textContent=isPersonal?'私人记账 · 本地模式':'4人 11天自驾 · 2026-09-25 至 10-05';
    }else if(isPersonal){
      sub.textContent='私密云端 · 只有你能看到 · 多设备同步';
    }else{
      var mc=auth.currentWs.member_count||1;
      sub.textContent=mc+'人共享 · 2026-09-25 至 10-05 · 实时同步';
    }
  }
  /* 空间按钮：任何时候都能点（打开空间管理弹窗） */
  var syncCodeBtn=document.getElementById('syncCodeBtn');
  if(syncCodeBtn){
    syncCodeBtn.disabled=false;
    syncCodeBtn.style.opacity='1';
    syncCodeBtn.style.cursor='pointer';
    syncCodeBtn.textContent=logged?'空间':'登录';
    syncCodeBtn.title='空间管理 / 邀请队友';
  }
  /* 空间标签状态 */
  var teamTag=document.getElementById('teamTag');
  var persTag=document.getElementById('personalTag');
  if(logged){
    if(teamTag){teamTag.textContent=isPersonal?'云端':'同步中';}
    if(persTag){persTag.textContent=isPersonal?'同步中':'云端';}
  }else{
    if(teamTag){teamTag.textContent=isPersonal?'未激活':'本地';}
    if(persTag){persTag.textContent=isPersonal?'本地':'未激活';}
  }
  updateUserBadge();
}"""

assert old in src, "applySpaceModeUI not found"
src=src.replace(old,new,1)
print("  OK    applySpaceModeUI")

io.open(P,'w',encoding='utf-8').write(src)
print("%d -> %d bytes"%(orig,len(src)))
