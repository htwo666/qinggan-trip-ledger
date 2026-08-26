#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出图片：用 Canvas 手绘结算卡（不引第三方库，微信里可长按保存/转发）
"""
import io
P='index.html'
src=io.open(P,encoding='utf-8').read()
orig=len(src);ok=[]
def sub(name,old,new,count=1):
    global src
    if old not in src: print('  MISS  %s'%name);return False
    src=src.replace(old,new,count);ok.append(name);print('  OK    %s'%name);return True

sub('exportSettleImage',
"""function exportExpensesCsv(){""",
"""/* ---------- 导出图片 ----------
   纯 Canvas 手绘，不引第三方库（html2canvas 那种在微信里经常出问题）。
   2 倍像素密度保证在手机上不糊。画完弹出预览，微信里长按可保存/转发。 */
function exportSettleImage(){
  var d=viewData();
  var R=computeSettlement(d);
  var members=aliveList(d.members);
  var budget=getDailyBudget();

  /* 汇总数字 */
  var preSum=0,i;
  for(i=0;i<d.prepaid.length;i++){preSum+=Number(d.prepaid[i].amount)||0;}
  var enC=0,enP=0,byCat={};
  for(i=0;i<d.expenses.length;i++){
    var e=d.expenses[i],a=Number(e.amount)||0;
    if(e.type==='collective'){enC+=a;}else{enP+=a;}
    byCat[e.category]=(byCat[e.category]||0)+a;
  }
  var cats=[];
  for(var k in byCat){if(byCat.hasOwnProperty(k)){cats.push({n:k,v:byCat[k]});}}
  cats.sort(function(a,b){return b.v-a.v;});
  cats=cats.slice(0,5);

  /* 先量高度，避免留白或截断 */
  var W=750,PAD=40,y=0;
  var H=200;                                  /* 头部 */
  H+=150;                                     /* 三个大数字 */
  if(cats.length){H+=60+cats.length*46;}      /* 分类排行 */
  if(R&&R.N>=2){
    H+=70+R.N*44;                             /* 成员表 */
    H+=R.transfers.length?(60+R.transfers.length*44):60;
    if(R.settled){H+=56;}
  }
  H+=90;                                      /* 页脚 */

  var S=2,c=document.createElement('canvas');
  c.width=W*S;c.height=H*S;
  var g=c.getContext('2d');
  g.scale(S,S);
  g.textBaseline='top';
  var F='-apple-system,"PingFang SC","Microsoft YaHei",sans-serif';

  function txt(s,x,yy,size,color,weight,align){
    g.font=(weight||'400')+' '+size+'px '+F;
    g.fillStyle=color||'#2d3436';
    g.textAlign=align||'left';
    g.fillText(String(s),x,yy);
  }
  function rrect(x,yy,w,h,r,fill){
    g.beginPath();
    g.moveTo(x+r,yy);g.lineTo(x+w-r,yy);g.quadraticCurveTo(x+w,yy,x+w,yy+r);
    g.lineTo(x+w,yy+h-r);g.quadraticCurveTo(x+w,yy+h,x+w-r,yy+h);
    g.lineTo(x+r,yy+h);g.quadraticCurveTo(x,yy+h,x,yy+h-r);
    g.lineTo(x,yy+r);g.quadraticCurveTo(x,yy,x+r,yy);
    g.closePath();g.fillStyle=fill;g.fill();
  }
  function line(yy){
    g.beginPath();g.moveTo(PAD,yy);g.lineTo(W-PAD,yy);
    g.strokeStyle='#eee';g.lineWidth=1;g.stroke();
  }
  function money(v){return '¥'+(Number(v)||0).toFixed(2);}

  /* 背景 */
  g.fillStyle='#fff';g.fillRect(0,0,W,H);

  /* 头部渐变 */
  var grd=g.createLinearGradient(0,0,W,150);
  grd.addColorStop(0,'#4a90d9');grd.addColorStop(1,'#67b8a4');
  g.fillStyle=grd;g.fillRect(0,0,W,150);
  var title=(state.spaceMode==='team'
    ?((auth&&auth.currentWs&&auth.currentWs.name)||'团队账本')
    :'我的个人账本');
  txt(title,PAD,38,34,'#fff','700');
  txt(TRIP_START+' ~ '+TRIP_END+'  ·  '+members.length+' 人',PAD,88,17,'rgba(255,255,255,.9)');
  txt('导出于 '+fmtDate(todayStr()),W-PAD,92,14,'rgba(255,255,255,.75)','400','right');
  y=150;

  /* 三个大数字 */
  y+=28;
  var bw=(W-PAD*2-20)/3;
  var boxes=[['预付款',preSum,'#4a90d9'],['途中AA',enC,'#67b8a4'],['个人花费',enP,'#e8a44a']];
  for(i=0;i<3;i++){
    var bx=PAD+i*(bw+10);
    rrect(bx,y,bw,96,12,'#f8f9fa');
    txt(boxes[i][0],bx+bw/2,y+18,15,'#8a9199','400','center');
    txt(money(boxes[i][1]),bx+bw/2,y+46,23,boxes[i][2],'700','center');
  }
  y+=96+26;

  /* 分类排行 */
  if(cats.length){
    txt('花费构成',PAD,y,19,'#2d3436','700');y+=32;
    var maxV=cats[0].v||1;
    for(i=0;i<cats.length;i++){
      var barW=Math.max(4,Math.round((W-PAD*2-210)*cats[i].v/maxV));
      txt(cats[i].n,PAD,y+6,16,'#555');
      rrect(PAD+95,y+8,barW,14,7,'#4a90d9');
      txt(money(cats[i].v),W-PAD,y+5,16,'#2d3436','600','right');
      y+=46;
    }
    y+=14;
  }

  /* AA 结算 */
  if(R&&R.N>=2){
    line(y);y+=22;
    txt('AA 结算',PAD,y,19,'#2d3436','700');y+=34;
    if(R.settled){
      rrect(PAD,y,W-PAD*2,40,8,'#eafaf1');
      txt('✅ '+(R.settled.at||'')+' 已结清 '+(R.settled.count||0)+' 笔 / '+money(R.settled.total||0),
          PAD+14,y+12,15,'#1e7d52','600');
      y+=56;
    }
    /* 表头 */
    txt('成员',PAD,y,14,'#8a9199');
    txt('实付',PAD+250,y,14,'#8a9199','400','right');
    txt('应承担',PAD+420,y,14,'#8a9199','400','right');
    txt('净额',W-PAD,y,14,'#8a9199','400','right');
    y+=26;
    for(i=0;i<R.N;i++){
      var m=R.members[i],n=R.net[m.id];
      if(i%2===0){rrect(PAD-8,y-6,W-PAD*2+16,40,6,'#fafbfc');}
      txt(m.name,PAD,y+4,16,'#2d3436','600');
      txt(money(R.paid[m.id]),PAD+250,y+4,15,'#555','400','right');
      txt(money(R.owed[m.id]),PAD+420,y+4,15,'#555','400','right');
      var nc=n>0.01?'#1e7d52':(n<-0.01?'#c0392b':'#8a9199');
      var nl=n>0.01?' 应收':(n<-0.01?' 应付':' 已平');
      txt(money(Math.abs(n))+nl,W-PAD,y+4,15,nc,'600','right');
      y+=44;
    }
    y+=18;
    /* 转账清单 */
    if(R.transfers.length){
      txt('谁给谁',PAD,y,17,'#2d3436','700');y+=32;
      for(i=0;i<R.transfers.length;i++){
        var t=R.transfers[i];
        rrect(PAD,y-4,W-PAD*2,38,8,'#fff6e5');
        txt(t.from+'  →  '+t.to,PAD+14,y+6,16,'#b8730a','600');
        txt(money(t.amt),W-PAD-14,y+6,17,'#c0392b','700','right');
        y+=44;
      }
    }else{
      rrect(PAD,y,W-PAD*2,40,8,'#eafaf1');
      txt('✅ '+(R.settled?'已结清，无新增待结算':'所有人已平衡，无需结算'),PAD+14,y+12,15,'#1e7d52','600');
      y+=60;
    }
  }

  /* 页脚 */
  y=H-60;
  line(y-14);
  txt('青甘环线记账 · 每日预算 '+money(budget),PAD,y,13,'#b2bec3');
  txt('htwo666.github.io/qinggan-trip-ledger',W-PAD,y,13,'#b2bec3','400','right');

  /* 弹预览 */
  try{
    var url=c.toDataURL('image/png');
    showImagePreview(url);
  }catch(err){
    showToast('生成图片失败：'+(err.message||err));
  }
}

/* 图片预览弹窗：微信里长按可保存/转发，电脑上给个下载按钮 */
function showImagePreview(url){
  var old=document.getElementById('imgPreviewMask');
  if(old){old.parentNode.removeChild(old);}
  var mask=document.createElement('div');
  mask.id='imgPreviewMask';
  mask.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.82);z-index:9999;'+
    'display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px;';
  mask.innerHTML=
    '<div style="color:#fff;font-size:0.82rem;margin-bottom:10px;text-align:center;line-height:1.6">'+
      '长按图片即可保存 / 转发到微信<br>'+
      '<span style="opacity:.65;font-size:0.74rem">电脑上点下面的下载按钮</span></div>'+
    '<img src="'+url+'" style="max-width:100%;max-height:72vh;border-radius:10px;'+
      'box-shadow:0 8px 32px rgba(0,0,0,.4)">'+
    '<div style="display:flex;gap:10px;margin-top:14px">'+
      '<a id="imgDl" href="'+url+'" download="账单_'+todayStr()+'.png" '+
        'style="background:#fff;color:#2d3436;padding:10px 22px;border-radius:20px;'+
        'font-size:0.86rem;font-weight:600;text-decoration:none">下载图片</a>'+
      '<button id="imgClose" style="background:rgba(255,255,255,.2);color:#fff;border:none;'+
        'padding:10px 22px;border-radius:20px;font-size:0.86rem;cursor:pointer">关闭</button>'+
    '</div>';
  document.body.appendChild(mask);
  document.getElementById('imgClose').onclick=function(){
    mask.parentNode&&mask.parentNode.removeChild(mask);
  };
  mask.onclick=function(ev){
    if(ev.target===mask){mask.parentNode&&mask.parentNode.removeChild(mask);}
  };
  showToast('图片已生成');
}

function exportExpensesCsv(){""")

io.open(P,'w',encoding='utf-8').write(src)
print('\n%d 处. %d -> %d bytes'%(len(ok),orig,len(src)))
