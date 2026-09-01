#!/usr/bin/env python3
# h3_prep_css.py — 加必买清单板块的 CSS
import sys
src = open('index.html', encoding='utf-8').read()

CSS = r"""/* ========== 必买清单板块 ========== */
.prep-board-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;}
@media(min-width:640px){.prep-board-grid{grid-template-columns:repeat(3,1fr);}}
.prep-board{background:var(--primary-bg);border:1px solid var(--border);border-radius:var(--radius);padding:10px;display:flex;flex-direction:column;gap:8px;min-height:120px;}
.prep-board-head{display:flex;align-items:center;gap:6px;border-bottom:1px dashed var(--border);padding-bottom:6px;}
.prep-board-name{flex:1;font-size:0.86rem;font-weight:600;color:var(--primary-dark);background:transparent;border:1px solid transparent;border-radius:6px;padding:3px 6px;min-width:0;}
.prep-board-name:focus{outline:none;background:#fff;border-color:var(--primary-light);}
.prep-board-del{border:none;background:transparent;color:var(--text-light);cursor:pointer;padding:2px;border-radius:6px;display:flex;align-items:center;}
.prep-board-del:hover{color:var(--danger);background:rgba(231,93,93,0.08);}
.prep-board-del svg{width:14px;height:14px;}
.prep-board-items{display:flex;flex-direction:column;gap:6px;flex:1;}
.prep-item{background:var(--card);border-radius:var(--radius-sm);padding:6px 8px;display:flex;flex-direction:column;gap:5px;border:1px solid transparent;}
.prep-item.all-ready{border-color:var(--primary-light);background:linear-gradient(135deg,#fff 0%,#eafaf1 100%);}
.prep-item-top{display:flex;align-items:center;gap:6px;}
.prep-item-name{flex:1;font-size:0.82rem;color:var(--text);background:transparent;border:1px solid transparent;border-radius:5px;padding:2px 4px;min-width:0;}
.prep-item-name:focus{outline:none;background:#fff;border-color:var(--primary-light);}
.prep-item-del{border:none;background:transparent;color:var(--text-light);cursor:pointer;padding:0 2px;display:flex;align-items:center;opacity:0.5;}
.prep-item-del:hover{opacity:1;color:var(--danger);}
.prep-item-del svg{width:13px;height:13px;}
.prep-ready-row{display:flex;flex-wrap:wrap;gap:4px;}
.prep-ready{width:24px;height:24px;border-radius:50%;border:1.5px solid var(--border);background:var(--card);color:var(--text-light);font-size:0.72rem;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;line-height:1;transition:transform 0.1s;}
.prep-ready:active{transform:scale(0.88);}
.prep-ready.on{color:#fff;border-color:transparent;}
.prep-add-row{margin-top:4px;}
.prep-add-input{width:100%;font-size:0.78rem;color:var(--text);background:rgba(255,255,255,0.5);border:1px dashed var(--border);border-radius:var(--radius-sm);padding:6px 8px;}
.prep-add-input:focus{outline:none;border-color:var(--primary);background:#fff;border-style:solid;}
.prep-empty-board{font-size:0.74rem;color:var(--text-light);text-align:center;padding:8px 0;font-style:italic;}
"""

ANCHOR = ".owner-chip.on{font-weight:600;}\n"
if src.count(ANCHOR) != 1:
    print(f'!! 找锚点失败: owner-chip.on ({src.count(ANCHOR)})')
    sys.exit(1)
src = src.replace(ANCHOR, ANCHOR + CSS)

open('index.html', 'w', encoding='utf-8').write(src)
print(f'OK: {len(src.encode("utf-8"))} bytes')
