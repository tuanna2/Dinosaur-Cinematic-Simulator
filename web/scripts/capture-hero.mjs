/** Repeatable diagnostic views of the actual master in the existing runtime. */
import {chromium} from 'playwright-core';
import {spawn} from 'node:child_process';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const out=resolve('../build/preview',process.env.HERO_OUTPUT??'trex_quality');mkdirSync(out,{recursive:true});
const server=spawn('npm',['run','dev','--','--host','127.0.0.1','--port','5190','--strictPort'],{stdio:'ignore'});let browser;
try{
 for(let i=0;i<150;i++){try{if((await fetch('http://127.0.0.1:5190')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 browser=await chromium.launch({executablePath:process.env.CHROME_BIN??'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1600,height:900}});await page.route('**/favicon.ico',r=>r.fulfill({status:204}));const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:5190',{waitUntil:'networkidle'});await page.waitForFunction(()=>window.dinosaurRuntime);
 const views=[['silhouette','anim_trex_walk',.15,false],['stride','anim_trex_walk',.7,false],['roar','anim_trex_roar',1.1,false],['head','anim_trex_roar',1.1,true]];
 for(const [name,clip,t,close] of views){
  const data=await page.evaluate(({clip,t,close})=>{
   const r=window.dinosaurRuntime;r.pause();r.seek(0);const a=r.actors.get('trex_01');for(const other of r.actors.values())other.visible=other===a;
   a.position.set(0,0,0);a.rotation.set(0,0,0);const c=r.controllers.get(a.name);c.reset();c.setState(clip.endsWith('roar')?'roar':'walk',clip);c.update(t);r.scene.updateMatrixWorld(true);
   if(close){r.camera.position.set(-5.3,3.85,6.5);r.camera.lookAt(0,3.3,2.75);r.camera.setFocalLength(48);}else{r.camera.position.set(-10,4.2,11.5);r.camera.lookAt(0,1.8,-.8);r.camera.setFocalLength(40);}
   r.camera.updateProjectionMatrix();return r.captureDataUrl();
  },{clip,t,close});
  writeFileSync(resolve(out,name+'.png'),Buffer.from(data.split(',')[1],'base64'));console.log('CAPTURED '+name);
 }
 if(errors.length)throw Error(errors.join('\n'));
}finally{await browser?.close();server.kill('SIGTERM');}
