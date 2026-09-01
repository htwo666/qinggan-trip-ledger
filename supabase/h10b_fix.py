#!/usr/bin/env python3
# h10b_fix.py — 修复 renderSummary 里 clearAllBtn 的删除
src = open('index.html', encoding='utf-8').read()

old = "<button class=\"btn btn-danger btn-sm\" id=\"clearAllBtn\">'+svgIcon('trash')+'清空数据</button></div>';"
new = "</div>';"
c1 = src.count(old)
print(f'toolbar anchor count: {c1}')
if c1 == 1:
    src = src.replace(old, new)

handler_old = """  document.getElementById('clearAllBtn').onclick=function(){
    showConfirm('清空全部数据','将删除所有模块的全部数据（预付大项除外），此操作不可撤销。确定继续吗？',function(){
      state.data.expenses=[];state.data.outfits=[];state.data.todos=[];state.data.prepItems=[];
      saveData();renderSummary();showToast('已清空');
    });
  };
"""
c2 = src.count(handler_old)
print(f'handler anchor count: {c2}')
if c2 == 1:
    src = src.replace(handler_old, "")

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
