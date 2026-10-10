const fs=require('fs'),vm=require('vm'),assert=require('assert');
class CanvasContext{
 constructor(canvas){this.c=canvas;this.globalCompositeOperation='source-over';}
 beginPath(){this.points=[];}moveTo(x,y){this.points.push([x,y]);}lineTo(x,y){this.points.push([x,y]);}closePath(){}
 fill(){this.raw??=new Uint8ClampedArray(this.c.width*this.c.height*4);const red=Number(this.fillStyle.match(/\d+/)[0]);for(let y=0;y<this.c.height;y++)for(let x=0;x<this.c.width;x++){let inside=false;const p=this.points;for(let i=0,j=p.length-1;i<p.length;j=i++)if(((p[i][1]>y+.5)!==(p[j][1]>y+.5))&&x+.5<(p[j][0]-p[i][0])*(y+.5-p[i][1])/(p[j][1]-p[i][1])+p[i][0])inside=!inside;if(inside){const k=(y*this.c.width+x)*4;this.raw[k]=this.globalCompositeOperation==='destination-out'?0:red;this.raw[k+3]=this.globalCompositeOperation==='destination-out'?0:255;}}}
 getImageData(){return {data:this.raw||new Uint8ClampedArray(this.c.width*this.c.height*4)};}
}
class E{constructor(){this.value='';this.style={};this.children=[];this.attributes={};this.classList={toggle(){},add(){},remove(){}};}set innerHTML(v){this.html=v;}querySelector(){return new E();}querySelectorAll(){return [];}replaceChildren(...c){this.children=c;}append(...c){this.children.push(...c);}setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k]??null;}getContext(){return this.context??=new CanvasContext(this);}getBoundingClientRect(){return {width:1024,height:572,left:0,top:0};}setPointerCapture(){}scrollTo(){}}
const els={},storage={};const sandbox={document:{getElementById:id=>els[id]??=new E(),createElement:()=>new E(),createElementNS:()=>new E(),addEventListener(){}},localStorage:{getItem:k=>storage[k]??null,setItem:(k,v)=>storage[k]=v},requestAnimationFrame:()=>1,cancelAnimationFrame(){},setTimeout(){},clearTimeout(){},console,Uint8Array,Uint8ClampedArray,Map};
vm.createContext(sandbox);vm.runInContext(['dist/palette.js','dist/app.js','dist/editor.js'].map(p=>fs.readFileSync(p,'utf8').replace('showPresets(PRESETS);renderSaved();update();init();','')).join('\n'),sandbox);
sandbox.geometry=JSON.parse(fs.readFileSync('dist/assets/geometry.json','utf8'));
vm.runInContext(`
for(const v of geometry.views)if(!validGeometry(v.shapes,v.width,v.height))throw Error('Real geometry invalid');
if(validGeometry([{zone:9,name:'bad',points:[[0,0],[3,0],[3,3]]}],8,8))throw Error('Invalid zone accepted');
if(validStrokes([{zone:0,radius:2,points:[null]}],8,8))throw Error('Bad point accepted');
const wall={zone:2,name:'wall',points:[[0,0],[8,0],[8,8],[0,8]]};
const window={zone:0,name:'window',points:[[2,2],[6,2],[6,6],[2,6]]};
const m=rasterizeShapes([wall,window],8,8);if(m[0]!==2||m[3*8+3]!==0)throw Error('Window protection failed');
strokeToMask(m,{zone:4,radius:1,points:[[3,3]]},8,8);if(m[27]!==4||m[0]!==2)throw Error('Brush failed');
if(!pointInPolygon({x:4,y:4},wall.points)||pointInPolygon({x:9,y:9},wall.points))throw Error('Selection hit test failed');
state.ready=true;state.view=0;$('contour-filter').value='all';
for(let i=0;i<2;i++)data[i]={width:8,height:8,shapes:clone([wall,window]),baseShapes:clone([wall,window]),strokes:[],mask:rasterizeShapes([wall,window],8,8),occlusion:new Uint8Array(64)};
for(const d of data)d.baseMask=d.mask.slice();
edit.draft={zone:0,name:'manual cut',points:[[0,0],[2,0],[2,2],[0,2]]};$('polygon-finish').onclick();
if(data[0].mask[0]!==0||data[1].mask[0]!==2)throw Error('View isolation failed');
$('geometry-undo').onclick();if(data[0].mask[0]!==2||data[0].shapes.length!==2)throw Error('Undo failed');
data[0].strokes=[{zone:1,radius:1,points:[[3,3]]}];rebuildMask();saveGeometry();
data[0].shapes=[];data[0].strokes=[];setupEditor();if(data[0].mask[27]!==1||data[0].shapes.length!==2)throw Error('Reload failed');
$('mask-reset').onclick();if(data[0].mask[27]!==0||data[0].strokes.length!==0)throw Error('Reset failed');
setZoom(50);if(edit.zoom!==8)throw Error('Zoom limit failed');setZoom(.1);if(edit.zoom!==1)throw Error('Zoom fit failed');
console.log('Geometry schema, window protection, selection, brush, per-view edits, undo, persistence, reset and zoom passed.');
`,sandbox);
