"""Geometric material regions with measured openings; no RGB gating on final walls."""
from PIL import Image,ImageDraw
from scipy import ndimage

import numpy as np,json
from pathlib import Path
root=Path(__file__).parent;out=root/'dist/assets';qa=root/'qa';qa.mkdir(parents=True,exist_ok=True)
building=[[(184,66),(603,79),(604,58),(744,63),(747,91),(1558,124),(1559,137),(1657,141),(1660,132),(1970,147),(1975,981),(183,1020)],[(188,0),(1600,287),(1604,389),(1727,362),(1823,381),(1849,861),(1605,917),(126,1083)]]
accent=[[(735,94),(1167,107),(1173,995),(733,1003)],[(1095,184),(1333,236),(1343,925),(1097,984)]]
dark=[[
 [(603,58),(744,63),(733,1004),(606,1010)],[(1558,135),(1658,141),(1663,983),(1562,987)],
 [(183,893),(604,882),(608,1011),(183,1020)],[(1171,878),(1972,858),(1975,981),(1174,995)]],
 [[(139,929),(1096,844),(1341,825),(1605,803),(1846,797),(1849,861),(1605,917),(126,1083)]]]
def maskpoly(points,size):
 im=Image.new('L',size);ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)>0
def rect(x,y,w,h):return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def trace_outline(m,x,y):
 edges={}
 for yy,xx in zip(*np.nonzero(m)):
  yy=int(yy);xx=int(xx)
  if yy==0 or not m[yy-1,xx]:edges[(xx,yy)]=(xx+1,yy)
  if xx==m.shape[1]-1 or not m[yy,xx+1]:edges[(xx+1,yy)]=(xx+1,yy+1)
  if yy==m.shape[0]-1 or not m[yy+1,xx]:edges[(xx+1,yy+1)]=(xx,yy+1)
  if xx==0 or not m[yy,xx-1]:edges[(xx,yy+1)]=(xx,yy)
 loops=[]
 while edges:
  start=next(iter(edges));p=start;points=[]
  while p in edges:
   points.append(p);p=edges.pop(p)
   if p==start:break
  if len(points)>3:loops.append(points)
 if not loops:return rect(x,y,m.shape[1],m.shape[0])
 points=max(loops,key=len);clean=[]
 for i,p in enumerate(points):
  a=points[i-1];b=points[(i+1)%len(points)]
  if (p[0]-a[0])*(b[1]-p[1])!=(p[1]-a[1])*(b[0]-p[0]):clean.append([p[0]+x,p[1]+y])
 return clean

def component_polygons(binary,minarea=40):
 cc,k=ndimage.label(binary);slices=ndimage.find_objects(cc)
 for i,s in enumerate(slices):
  if not s:continue
  ys,xs=s;hh=ys.stop-ys.start;ww=xs.stop-xs.start;m=cc[s]==i+1
  if m.sum()<minarea or ww<10 or hh<9 or ww>150 or hh>160:continue
  yield xs.start,ys.start,ww,hh,m
views=[]
for n in [0,1]:
 im=Image.open(out/f'view-{n}.jpg');a=np.array(im).astype(float);l=a@np.array([.2126,.7152,.0722]);r,g,b=a.transpose(2,0,1);size=im.size
 facade=maskpoly(building[n],size);acc=maskpoly(accent[n],size);dr=np.zeros(l.shape,bool)
 for p in dark[n]:dr|=maskpoly(p,size)
 shapes=[{'zone':1,'name':'Основная поверхность','points':building[n]},{'zone':2,'name':'Акцентная секция','points':accent[n]}]
 shapes.extend({'zone':4,'name':'Тёмная стена / цоколь','points':p} for p in dark[n])
 # Measure inset rectangles, then paint entire rectangles independent of pixel color.
 warm=(r-b>4)&(abs(r-g)<12)&(l>78)&(l<190)&facade&~dr
 warm=ndimage.binary_opening(warm,iterations=1)
 panels=0
 for x,y,w,h,m in component_polygons(warm,100):
  if w>65 or h>160 or m.mean()<.60:continue
  # Solid rectangular fields only; bright glass does not pass the area test.
  shapes.append({'zone':3,'name':'Вставка '+str(panels+1),'points':rect(x-1,y-1,w+1,h+1)});panels+=1
 # Identify each opaque opening individually, rather than repeating a guessed grid.
 edges=ndimage.binary_closing((l<68)&facade&~dr,iterations=1)
 holes=[]
 for x,y,w,h,m in component_polygons(edges,45):
  if n==0 and acc[min(y+h//2,l.shape[0]-1),min(x+w//2,l.shape[1]-1)]:continue
  if y>1020 or w>110:continue
  filled=ndimage.binary_fill_holes(m)
  # Polygon follows the actual connected boundary; it does not include detached shadows.
  boundary=filled&~ndimage.binary_erosion(filled)
  yy,xx=np.nonzero(boundary)
  if len(xx)<4:continue
  pts=np.column_stack([xx+x,yy+y])
  p=trace_outline(filled,x,y)
  holes.append({'zone':0,'name':'Окно / корзина '+str(len(holes)+1),'points':p})
 # Fit the accent windows in individual search boxes so a dark shadow cannot merge rows.
 cols = [(752,787),(817,852),(879,914),(941,975),(999,1032),(1059,1093),(1119,1152)] if n==0 else [(1108,1131),(1150,1172),(1190,1212),(1228,1250),(1267,1289),(1305,1327)]
 for j,(xl,xr) in enumerate(cols):
  top=(149+j*2.5) if n==0 else (233+j*8.5)
  bottom=(962-j*.25) if n==0 else (949-j*12.1)
  for k in range(15):
   y=top+(bottom-top)*k/14;hh=31 if n==0 else 30-j*.8
   if n==1:
    y=[234,281,328,374,422,469,516,564,612,665,713,762,811,859,909][k]
    y+=j*(7.4-k*.88);hh=((30-j*.6) if k<9 else (39-j*.5)) if k<14 else 61-j*1.5
   x0=max(0,xl-5);x1=xr+6;y0=max(0,int(y-6));y1=int(y+hh+6)
   tile=l[y0:y1,x0:x1];low=tile<80
   # Select a component anchored in the expected window, ignoring detached cast shadows.
   cc,cn=ndimage.label(ndimage.binary_closing(low));opts=[]
   for ix,sl in enumerate(ndimage.find_objects(cc)):
    if not sl:continue
    yy,xx=sl;ww=xx.stop-xx.start;ht=yy.stop-yy.start
    if ww<8 or ht<10:continue
    score=(cc[sl]==ix+1).sum()-abs((xx.start+xx.stop)/2-(xl+xr)/2+x0)*4
    opts.append((score,xx,yy))
   if opts:
    _,xx,yy=max(opts,key=lambda p:p[0]);left=x0+xx.start;right=x0+xx.stop;up=y0+yy.start;down=y0+yy.stop
    left=max(left,xl-1);right=min(right,xr+1);up=max(up,int(y)-2);down=min(down,int(y+hh)+2)
    holes.append({'zone':0,'name':'Измеренное окно акцентной секции','points':rect(left,up,right-left,down-up)})
    if (j in ([0,3,4,6] if n==0 else [0,3,4])) and k<14:
     by=down+1;bh=17 if n==0 else 13-j*.3
     holes.append({'zone':0,'name':'Корзина акцентной секции','points':[[left-2,by],[right+3,by+1],[right+3,by+bh],[left-2,by+bh+1]]})
 # Dark walls have dark frames touching the wall. Locate each opening within a bounded search.
 def snapped_box(x0,y0,x1,y1,name):
  x0,y0,x1,y1=map(int,[x0,y0,x1,y1]);crop=l[max(0,y0):min(size[1],y1),max(0,x0):min(size[0],x1)]
  if not crop.size:return
  # On graphite, glass is lighter than its frame. Measured inside, then include frame thickness.
  bright=crop>94;cc,k=ndimage.label(bright);counts=np.bincount(cc.ravel());counts[0]=0
  if not k or counts.max()<30:return
  yy,xx=np.nonzero(cc==counts.argmax());left=x0+xx.min()-3;top=y0+yy.min()-3;right=x0+xx.max()+3;bottom=y0+yy.max()+3
  if right-left>90 or bottom-top>95:return
  holes.append({'zone':0,'name':name,'points':rect(left,top,right-left,bottom-top)})
 if n==0:
  for k in range(15):
   # Rows calibrated to the actual image, snapped separately for each window.
   y=93+k*57.9
   snapped_box(625,y-4,657,y+39,'Окно тёмной секции');snapped_box(672,y-4,725,y+41,'Окно тёмной секции')
   y2=188+k*52.1
   snapped_box(1571,y2-4,1613,y2+40,'Окно тёмной секции');snapped_box(1623,y2-4,1650,y2+38,'Окно тёмной секции')
 # Retail glazing on the plinth: explicit openings fitted from connected bright regions.
 glass=facade&dr&(((l>103)&(b>r-12))|((g>r+2)&(l>45)))
 glass=ndimage.binary_closing(glass,iterations=1)
 for x,y,w,h,m in component_polygons(glass,60):
  if y<(850 if n==0 else 770):continue
  if h<15 or w>75:continue
  holes.append({'zone':0,'name':'Остекление цоколя','points':rect(x-2,y-2,w+3,h+3)})
 # White condenser baskets do not have closed dark frames: measure neutral opaque bodies.
 # Their shallow bounding fields are isolated from the tall wall inset panels.
 lightbasket=facade&~acc&~dr&(l>135)&(l<215)&(abs(r-g)<8)&(abs(g-b)<8)
 for x,y,w,h,m in component_polygons(ndimage.binary_opening(lightbasket),75):
  if 24<w<70 and 7<h<27 and m.mean()>.68:
   holes.append({'zone':0,'name':'Светлая корзина','points':rect(x,y,w,h)})
 shapes.extend(holes)
 labels=Image.new('L',size);d=ImageDraw.Draw(labels)
 for s in shapes:d.polygon([tuple(p) for p in s['points']],fill=s['zone'])
 labels=np.array(labels)
 # Foreground vegetation and humans occlude lower walls; retain those pixels as protected.
 foreground=(g>r*1.08)&(g>b*1.12)&(l<205)
 foreground &= np.indices(l.shape)[0]>(890 if n==0 else 810)
 occlusion=ndimage.binary_dilation(foreground,iterations=1)
 labels[occlusion]=0
 Image.fromarray((occlusion*255).astype('uint8')).save(out/f'occlusion-{n}.png')
 protected=np.array(labels)==0
 rgba=np.zeros((*l.shape,4),np.uint8);rgba[:,:,0]=labels;rgba[:,:,3]=255
 Image.fromarray(rgba).save(out/f'mask-{n}.png')
 refs=[float(np.percentile(l[labels==z],70)) for z in range(1,5)]
 view={'width':size[0],'height':size[1],'reference':refs,'maskVersion':'geometry-v2','shapes':shapes}
 views.append(view)
 # Saturated diagnostic fill makes residual seams easy to inspect.
 colors=np.array([[0,0,0],[245,240,220],[180,63,26],[180,169,147],[50,52,58]])
 image=a.copy()
 for z in range(1,5):
  region=labels==z;shade=l[region]/refs[z-1];image[region]=np.clip(colors[z]*shade[:,None],0,255)
 Image.fromarray(image.astype('uint8')).save(qa/f'geometry-check-{n}.jpg')
 print(n,'panels',panels,'protected contours',len(holes),'painted pixels',[int((labels==z).sum()) for z in range(1,5)])
(out/'views.json').write_text(json.dumps([{k:v for k,v in s.items() if k!='shapes'} for s in views]))
(out/'geometry.json').write_text(json.dumps({'version':2,'views':views},separators=(',',':'),default=lambda x:int(x)))
