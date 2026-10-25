// full-page desktop screenshot + section offsets, to plan a scene
const puppeteer=require('puppeteer-core');
(async()=>{const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--hide-scrollbars']});
const pg=await b.newPage();await pg.setViewport({width:1280,height:884});await pg.goto(process.argv[2],{waitUntil:'networkidle2'});
const H=await pg.evaluate(()=>document.documentElement.scrollHeight);for(let y=0;y<H;y+=600){await pg.evaluate(y=>scrollTo(0,y),y);await new Promise(r=>setTimeout(r,200));}
await pg.evaluate(()=>scrollTo(0,0));await new Promise(r=>setTimeout(r,800));
console.log(H, JSON.stringify(await pg.evaluate((q)=>[...document.querySelectorAll(q)].map(e=>[e.tagName+(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.split(' ')[0]:''),Math.round(e.getBoundingClientRect().top+scrollY),Math.round(e.getBoundingClientRect().height),(e.innerText||'').slice(0,40).replace(/\n/g,' ')]),process.argv[4]||'section,[id],h1,h2,footer,form,iframe')));
await pg.screenshot({path:process.argv[3],fullPage:true,type:'jpeg',quality:60});await b.close();})();
