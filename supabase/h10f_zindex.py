#!/usr/bin/env python3
# h10f_zindex.py — 修复 confirmModal 被 formModal 遮挡的 z-index 问题
src = open('index.html', encoding='utf-8').read()

anchor = ".form-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:260;align-items:flex-end;justify-content:center;}\n"
addition = ".form-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:260;align-items:flex-end;justify-content:center;}\n/* 确认弹窗要在表单弹窗之上（清空确认从设置弹窗里弹出） */\n#confirmModal{z-index:280;}\n"

c = src.count(anchor)
print(f'anchor: {c}')
if c == 1:
    src = src.replace(anchor, addition)
    open('index.html', 'w', encoding='utf-8').write(src)
    print(f'OK: {len(src.encode("utf-8"))} bytes')
else:
    print('NOT FOUND')
