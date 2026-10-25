const puppeteer=require('puppeteer-core');const fs=require('fs');const path=require('path');
(async()=>{const st=JSON.parse(fs.readFileSync(process.argv[2]||'states.json'));const dir=path.resolve(process.argv[3]||'caps');fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir);
const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--hide-scrollbars']});
const pg=await b.newPage();await pg.setViewport({width:1080,height:300,deviceScaleFactor:1});
await pg.goto('file://'+(process.argv[4]?path.resolve(process.argv[4]):path.join(__dirname,'caption.html')),{waitUntil:'networkidle0'});await pg.evaluate(()=>document.fonts.ready);
await pg.evaluate(()=>{document.getElementById('c').innerHTML=''});await pg.screenshot({path:path.join(dir,'blank.png'),omitBackground:true});
for(let i=0;i<st.length;i++){await pg.evaluate(h=>{document.getElementById('c').innerHTML=h},st[i].html);await pg.screenshot({path:path.join(dir,`s${String(i).padStart(4,'0')}.png`),omitBackground:true});}
await b.close();
let t=0,lines=['ffconcat version 1.0'];
for(let i=0;i<st.length;i++){const s=st[i];if(s.s>t+0.001){lines.push(`file blank.png`,`duration ${(s.s-t).toFixed(3)}`);}lines.push(`file s${String(i).padStart(4,'0')}.png`,`duration ${(s.e-s.s).toFixed(3)}`);t=s.e;}
lines.push('file blank.png','duration 1');fs.writeFileSync(path.join(dir,'list.txt'),lines.join('\n')+'\n');console.log('rendered',st.length);})();
