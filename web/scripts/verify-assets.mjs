/** Browser integration QA: real GLBs, skin deformation, repeatable seek. */
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const out=resolve('../build/preview/asset_qa'); mkdirSync(out,{recursive:true});
const server=spawn('npm',['run','dev','--','--host','127.0.0.1','--port','5184','--strictPort'],{stdio:'ignore'});
let browser;
try {
  let ready=false;
  for(let i=0;i<100;i++){try{if((await fetch('http://127.0.0.1:5184')).ok){ready=true;break;}}catch{} await new Promise(r=>setTimeout(r,100));}
  if(!ready) throw Error('Vite unavailable');
  browser=await chromium.launch({executablePath:process.env.CHROME_BIN??'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
  const page=await browser.newPage({viewport:{width:1280,height:720}}); const errors=[];
  page.on('pageerror',e=>errors.push(String(e))); page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.route('**/favicon.ico',route=>route.fulfill({status:204}));
  await page.goto('http://127.0.0.1:5184',{waitUntil:'networkidle'}); await page.waitForFunction(()=>window.dinosaurRuntime);
  const result=await page.evaluate(async()=>{
    const THREE=await import('/node_modules/three/build/three.module.js');
    const r=window.dinosaurRuntime; r.pause(); r.seek(0);
    const actors=[...r.actors.values()]; const report={actors:[],clips:[],determinism:{},clipFrames:[]};
    if(actors.length!==10) throw Error('Expected ten actors');
    for(const a of actors){let skins=0;a.traverse(o=>{if(o.isSkinnedMesh)skins++;});if(!skins||a.userData.isPlaceholder)throw Error('Placeholder '+a.name);report.actors.push({id:a.name,skins});}
    if(r.scene.getObjectByName('__placeholder_world__').visible)throw Error('Placeholder environment remains visible');
    for(const species of ['velociraptor','triceratops','tyrannosaurus_rex']){
      const a=actors.find(a=>a.userData.species===species); const c=r.controllers.get(a.name);
      const sample=()=>{r.scene.updateMatrixWorld(true);const values=[];a.traverse(o=>{if(o.isSkinnedMesh){o.skeleton.update();for(let i=0;i<o.geometry.attributes.position.count;i+=37){const v=new THREE.Vector3().fromBufferAttribute(o.geometry.attributes.position,i);o.applyBoneTransform(i,v);values.push(v.x,v.y,v.z);}}});return values;};
      for(const clip of c.embeddedAnimations){
        c.reset();c.setState(clip.name.split('_').at(-1),clip.name);c.update(.1);if(c.activeAction.getClip().name!==clip.name)throw Error('Wrong resolved clip: '+clip.name);const before=sample();
        for(const other of actors)other.visible=other===a;
        const size=species==='velociraptor'?1.5:species==='triceratops'?4.5:5;
        r.camera.position.copy(a.position).add(new THREE.Vector3(size*1.7,size*.75,size*1.5));
        r.camera.setFocalLength(38);r.camera.lookAt(a.position.clone().add(new THREE.Vector3(0,size*.35,0)));r.camera.updateProjectionMatrix();
        report.clipFrames.push({name:clip.name+'_a',data:r.captureDataUrl()});
        c.update(.3);const after=sample();report.clipFrames.push({name:clip.name+'_b',data:r.captureDataUrl()});
        for(const other of actors)other.visible=true;
        const delta=Math.max(...before.map((x,i)=>Math.abs(x-after[i])));
        if(a.userData.animationMissing||delta<.0001)throw Error('No skin deformation for '+clip.name);
        report.clips.push({actor:a.name,clip:clip.name,duration:clip.duration,max_sampled_vertex_delta:delta});
      }
    }
    r.seek(31);
    const prey=actors.find(a=>a.userData.species==='triceratops');
    report.attackClearances=actors.filter(a=>a.userData.species==='velociraptor').map(a=>({id:a.name,distance:a.position.distanceTo(prey.position),minimum:a.userData.bodyClearance+prey.userData.bodyClearance}));
    if(report.attackClearances.some(a=>a.distance<a.minimum-.01))throw Error('Pack intersects prey body clearance');
    r.seek(50);const first=JSON.stringify(r.snapshot().actors);const pixels=r.captureDataUrl();r.seek(15);r.seek(50);
    report.determinism={actors:first===JSON.stringify(r.snapshot().actors),pixels:pixels===r.captureDataUrl()};
    if(!report.determinism.actors||!report.determinism.pixels)throw Error('Seek is not deterministic');
    report.render=r.renderer.info.render;return report;
  });
  for(const t of [8.3,8.6,22.3,22.7,40.2,40.5,125.3,125.6,131.3,131.7,137.4,137.8]){
    const data=await page.evaluate(t=>{window.dinosaurRuntime.renderFrameAt(t);return window.dinosaurRuntime.captureDataUrl();},t);
    writeFileSync(resolve(out,`time_${t.toFixed(1)}.png`),Buffer.from(data.split(',')[1],'base64'));
  }
  for(const frame of result.clipFrames)writeFileSync(resolve(out,frame.name+'.png'),Buffer.from(frame.data.split(',')[1],'base64'));
  delete result.clipFrames;
  result.errors=errors;writeFileSync(resolve(out,'verification.json'),JSON.stringify(result,null,2));
  if(errors.length)throw Error(errors.join('\n'));console.log(JSON.stringify(result,null,2));
} finally {await browser?.close();server.kill('SIGTERM');}
