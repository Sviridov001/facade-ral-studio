const fs=require('fs'),vm=require('vm'),assert=require('assert');
class E{constructor(){this.value='';this.checked=false;this.style={};this.children=[];this.classList={add(){},remove(){},toggle(){}};}set innerHTML(v){this.html=v;}get innerHTML(){return this.html;}querySelector(){return new E();}querySelectorAll(){return [];}replaceChildren(...c){this.children=c;}append(...c){this.children.push(...c);}setAttribute(){}getContext(){return {};}getBoundingClientRect(){return {width:1024,height:572,left:0,top:0};}}
const els={};const sandbox={document:{getElementById:id=>els[id]||(els[id]=new E()),createElement:()=>new E()},localStorage:{getItem(){return null;},setItem(){}},requestAnimationFrame(){return 1;},cancelAnimationFrame(){},setTimeout(){},clearTimeout(){},console,Uint8ClampedArray,Uint8Array,Map};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync('dist/palette.js','utf8')+'\n'+fs.readFileSync('dist/app.js','utf8').replace('showPresets(PRESETS);renderSaved();update();init();',''),sandbox);
vm.runInContext(`
if(new Set(RAL.map(c=>c.code)).size!==RAL.length)throw Error('Duplicate codes');
if(RAL.some(c=>!/^#[0-9A-F]{6}$/.test(c.hex)))throw Error('Invalid colors');
for(const anchor of RAL)for(const mode of ['tonal','analog','contrast']){const ps=generateHarmonies(anchor.code,mode);if(ps.length!==4||ps.some(p=>p.codes.length!==4||p.codes.some(c=>!paletteByCode[c])||!p.codes.includes(anchor.code)))throw Error('Harmony error');}
const src=new Uint8ClampedArray([200,200,200,255,100,100,100,255,50,50,50,255]);
const unchanged=transformPixels(src,new Uint8Array([1,2,0]),[null,null,null,null],[200,100,100,50]);
if(src.some((v,i)=>v!==unchanged[i]))throw Error('Original changed');
const recolored=transformPixels(src,new Uint8Array([1,2,0]),[{code:'1019',light:0},null,null,null],[200,100,100,50]);
if(recolored[0]!==164||recolored[1]!==143||recolored[2]!==122)throw Error('Recolor failed');
if(recolored.slice(4).some((v,i)=>v!==src[i+4]))throw Error('Unselected pixel changed');
const c=colorRGB({code:'6009',light:50});if(c.some(v=>v<140))throw Error('Lightening failed');
$('family').value='all';$('harmony-mode').value='tonal';update();
presetButton(PRESETS[0]).onclick();if(state.colors[1].code!=='1019')throw Error('Preset failed');
$('save').onclick();if(saved.length!==1)throw Error('Save failed');
$('reset').onclick();if(state.colors.some(Boolean))throw Error('Reset failed');
$('search').value='6009';renderSwatches();if($('swatches').children.length!==1)throw Error('Search failed');
$('views').onclick({target:{closest(){return {dataset:{view:'1'}};}}});if(state.view!==1)throw Error('Switch failed');
console.log(RAL.length+' RAL colors; all harmony modes, pixel invariants, lightening, presets, search, saved variants and reset passed.');
`,sandbox);
const html=fs.readFileSync('dist/index.html','utf8');for(const m of html.matchAll(/(?:src|href)="([^"#]+)"/g)){if(!m[1].startsWith('http')&&m[1]!=='./')assert(fs.existsSync('dist/'+m[1].split('?')[0]),m[1]+' missing');}
console.log('Static links passed.');
