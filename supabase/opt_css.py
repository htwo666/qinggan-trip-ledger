#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""认领 UI（成员卡片上加"这是我"按钮）+ 参与人勾选的 CSS"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

# ---------- CSS ----------
sub('css',
"""/* ========== 付款人标签 ========== */""",
"""/* ========== 参与人勾选（不等额分摊） ========== */
.part-grid{display:flex;flex-wrap:wrap;gap:6px;margin-top:2px;}
.part-chip{display:inline-flex;align-items:center;gap:5px;padding:6px 11px;border:1px solid var(--border);
  border-radius:16px;font-size:0.78rem;cursor:pointer;background:#fff;transition:all .15s;user-select:none;}
.part-chip input{margin:0;width:14px;height:14px;accent-color:var(--primary);cursor:pointer;}
.part-chip:has(input:checked){border-color:var(--primary);background:var(--primary-bg);color:var(--primary-dark);font-weight:600;}
/* 兼容不支持 :has 的老浏览器（微信X5）：靠 JS 加 class */
.part-chip.on{border-color:var(--primary);background:var(--primary-bg);color:var(--primary-dark);font-weight:600;}
/* ========== 成员认领 ========== */
.claim-btn{border:none;background:transparent;color:var(--text-light);font-size:0.62rem;
  cursor:pointer;padding:2px 6px;border-radius:8px;line-height:1.4;}
.claim-btn:hover{background:var(--primary-bg);color:var(--primary);}
.claim-btn.mine{background:var(--primary);color:#fff;font-weight:600;}
.claim-btn.taken{color:#bbb;cursor:not-allowed;}
/* ========== 付款人标签 ========== */""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
