#!/usr/bin/env python3
# h13_prep_top.py — 把「添加计划」按钮移到出发准备页顶部
src = open('index.html', encoding='utf-8').read()

# 1. 把 toolbar 从末尾移到开头
old1 = "  p.innerHTML=todayHtml+calHtml+todoCard+memberHtml+boardHtml+toolbar;"
new1 = "  p.innerHTML=toolbar+todayHtml+calHtml+todoCard+memberHtml+boardHtml;"
c1 = src.count(old1)
print(f'innerHTML anchor: {c1}')
if c1 != 1:
    print('!! innerHTML anchor not unique'); exit(1)
src = src.replace(old1, new1)

# 2. 修正空状态文案：从"点下方"改成"点上方"
old2 = "todoCard+='<div class=\"empty\">'+svgIcon('check')+'<div>暂无计划，点下方「添加计划」</div></div>';"
new2 = "todoCard+='<div class=\"empty\">'+svgIcon('check')+'<div>暂无计划，点上方「添加计划」</div></div>';"
c2 = src.count(old2)
print(f'empty text anchor: {c2}')
if c2 != 1:
    print('!! empty text anchor not unique'); exit(1)
src = src.replace(old2, new2)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
