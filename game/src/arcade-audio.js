/* Original Pocket Reel opening: no external audio, sample requests, timers or context creation. */
const arcadeAudio = (() => {
  const R=18000, TAU=2*Math.PI, LOOP=25.6, N=Math.round(R*LOOP);
  const db=x=>Math.max(0,Math.min(1,Number.isFinite(x)?x:0));
  const hz=n=>440*2**((n-69)/12);
  const table=Float64Array.from({length:16384},(_,i)=>Math.sin(TAU*i/16384));
  const sin=r=>table[(r*(16384/TAU))&16383];
  const cos=r=>sin(r+Math.PI*.5);
  const seed=(n)=>{let x=(n+0x65ca3a73)|0;x=Math.imul(x^(x>>>16),0x21f0aaad);x=Math.imul(x^(x>>>15),0x735a2d97);return ((x^(x>>>15))>>>0)/2147483648-1};
  const out=(n=N)=>[new Float32Array(n),new Float32Array(n)];
  const levels={music:.34,nature:.29,cue:.42};
  function trim(a,peak){let seen=0;for(const c of a)for(let i=0;i<c.length;i++)seen=Math.max(seen,Math.abs(c[i]));
    if(seen>0)for(const c of a)for(let i=0,scale=peak/seen;i<c.length;i++)c[i]*=scale;return a;}
  function pour(a,t,s,pan=0,wet=.10){
    const [l,r]=a,N=l.length,i0=Math.round(t*R),gL=Math.sqrt(.5-.5*pan),gR=Math.sqrt(.5+.5*pan);
    const dl=Math.round(.081*R),dr=Math.round(.118*R),d2=Math.round(.196*R);
    for(let i=0;i<s.length;i++){
      const j=(i+i0)%N,v=s[i];l[j]+=v*gL;r[j]+=v*gR;
      l[(j+dl)%N]+=v*wet*gR*.61;
      r[(j+dr)%N]+=v*wet*gL*.68;
      l[(j+d2)%N]+=v*wet*gL*.22;
      r[(j+d2+193)%N]+=v*wet*gR*.24;
    }
  }
  function felt(note,dur,amp,kind=0){
    const a=new Float32Array(Math.round(dur*R)), f=hz(note), w=TAU*f/R;
    const det=(kind===2?.0038:.00155), med=kind===2?1.6:kind===1?4.8:2.5, attack=kind===2?.035:kind===1?.006:.009;
    const f1=Math.exp(-1/(R*attack)),f2=Math.exp(-med/R),f3=Math.exp(-(kind===1?8:4.3)/R),
      f4=Math.exp(-2.8/R),f5=Math.exp(-7/R),f6=Math.exp(-40/R),fin=.09*R;
    let phase=0, flutter=0, click=0,e1=1,e2=1,m=kind===1?.99:kind===2?.02:1.55,e4=1,e5=.065,e6=.045;
    for(let i=0;i<a.length;i++){
      const e=amp*(1-e1)*e2*Math.min(1,(a.length-i)/fin);
      phase+=w*(1+(kind===2?.0014:.0008)*sin(flutter));flutter+=TAU*4.2/R;
      click=.58*click+.42*seed(i+note*324);
      const cavity=(kind===2?.09:.158)*sin(phase*3.004);
      a[i]=e*(.64*sin(phase+m*sin(2*phase))+.21*sin(phase*(1+det))+
        cavity*e4+e5*sin(phase*5.01)+e6*click);
      e1*=f1;e2*=f2;m*=f3;e4*=f4;e5*=f5;e6*=f6;
    }
    return a;
  }
  function stringPad(note,d,amp,offset){
    const a=new Float32Array(Math.round(d*R)),w=TAU*hz(note)/R,trem=TAU*(.27+offset*.018)/R;
    const step2=w*(1.002+offset*.00043), ain=R*.46,aout=R*.63;
    let ph=.87+offset*.61,second=ph*1.17;
    for(let i=0;i<a.length;i++){
      const rise=Math.min(1,i/ain), fall=Math.min(1,(a.length-i)/aout);
      const e=rise*rise*fall*fall*(.89+.11*sin(trem*i+offset));
      ph+=w; second+=step2;
      const bow=.39*sin(ph)+.27*sin(second)+.125*sin(ph*2+.29)+.109*sin(second*3)+.049*sin(ph*4.002);
      a[i]=amp*e*bow;
    }
    return a;
  }
  function makeScore(){
    // Eight original four-beat bars, 75 bpm. Sparse blues-free lakeside harmonic bed, not a borrowed song.
    const a=out(), chords=[
      [52,55,59,62,67],[48,55,59,62,64],[43,54,57,59,64],[50,54,57,60,64],
      [52,55,59,62,66],[45,55,59,60,64],[48,55,59,62,67],[47,54,57,62,66]];
    const melody=[
      [[.45,71],[1.36,74],[2.23,76],[3.03,79]],[[.43,76],[1.67,74],[2.98,71]],
      [[.27,69],[1.36,71],[2.64,74]],[[.71,71],[1.90,69],[3.00,66]],
      [[.36,71],[1.36,74],[2.37,78],[3.17,76]],[[.52,76],[1.92,72],[2.66,71]],
      [[.41,67],[1.52,71],[2.63,74],[3.12,79]],[[.59,78],[1.61,74],[3.01,71]]];
    for(let b=0;b<8;b++){
      const t=3.2*b,c=chords[b];
      for(let k=1;k<c.length;k++)pour(a,t-.30+LOOP,stringPad(c[k],4.02,.026,k),[-.6,.42,-.28,.57][k-1],.14);
      pour(a,t+.035,felt(c[0]-12,2.7,.14,2),-.08,.033);
      if(b%3!==1)pour(a,t+2.02,felt(c[0],1.32,.049,2),.11,.05);
      for(let k=1;k<c.length;k++)pour(a,t+.09+k*.078,felt(c[k],2.50,.054,0),-.43+k*.235,.16);
      for(const [bt,n] of melody[b])pour(a,t+bt*.8,felt(n,1.55,.125,1),.17,.21);
    }
    return trim(a,.53);
  }
  function makeNature(){
    const a=out();
    let foam1=0,foam2=0,warm=0,air=0,low=0;
    for(let i=-R;i<N;i++){
      const j=(i+N)%N, p=TAU*j/N;
      const x=seed(j+1062),y=seed(j+54139);
      foam1=.69*foam1+.31*x;foam2=.77*foam2+.23*y;warm=.956*warm+.044*(x+y);
      low=.997*low+.003*(x+y);
      air=.981*air+.019*y;
      if(i<0)continue;
      const a1=.5+.5*sin(9*p+.30*sin(2*p)),a2=.5+.5*sin(7*p+1.25+.52*cos(3*p));
      const wave=.34+.47*a1*a1,swell=.31+.37*a2*a2*a2;
      const lap=(foam1-.79*warm)*.106*wave+(warm-low)*.188*swell;
      const breeze=(air-.28*low)*(.053+.012*sin(2*p));
      a[0][i]=lap+breeze+(foam2+.3*warm)*.028*swell;
      a[1][i]=lap*.79+breeze+(foam2-.5*air)*.065*swell;
    }
    const bird=(f,d,drop,amp,seq)=>{
      const a=new Float32Array(Math.round(R*d)); let p=0;
      for(let i=0;i<a.length;i++){
        const t=i/R,q=t/d;
        const slur=f*(1+.15*Math.sin(Math.PI*q)-drop*q*q+.021*Math.sin(TAU*q*2.1+seq));
        p+=TAU*slur/R;
        const gate=Math.pow(Math.sin(Math.PI*q),1.7)*(.85+.15*Math.sin((90+seq*8)*Math.PI*t));
        a[i]=amp*gate*(.82*Math.sin(p)+.12*Math.sin(p*2+.23)+.039*seed(i+seq*866));
      }
      return a;
    };
    for(const [base,pitch,pan,num] of [[2.45,1740,-.70,3],[8.62,1252,.51,2],[15.04,1810,-.43,3],[20.22,1388,.64,2]]){
      for(let k=0;k<num;k++){
        const duration=[.16,.207,.142][k], timing=[0,.28,.61][k];
        pour(a,base+timing,bird(pitch+[0,132,-87][k],duration,.25+k*.073,.034,k),pan,.16);
      }
    }
    // A tiny shore-wash join, so random adjacent samples do not become a loop-edge click.
    for(const c of a){
      const w=Math.round(.008*R), mid=(c[0]+c[N-1])*.5;
      for(let j=0;j<w;j++){
        const alpha=.5+.5*cos(Math.PI*j/w), k=N-1-j;
        c[j]+=(mid-c[j])*alpha;c[k]+=(mid-c[k])*alpha;
      }
    }
    return trim(a,.34);
  }
  function makeCue(){
    // Original three-note ascending sixth-and-third gesture, velvet attack, no square waves.
    const a=out(Math.round(.96*R));
    for(const [t,n,k] of [[.016,57,0],[.079,65,1],[.139,69,0],[.151,72,1]]){
      const p=felt(n,.555,.142,k);
      const d=Math.floor(t*R),pan=(k?-.27:.22),gL=Math.sqrt(.5-.5*pan),gR=Math.sqrt(.5+.5*pan);
      for(let i=0;i<p.length;i++){
        a[0][i+d]+=p[i]*gL;a[1][i+d]+=p[i]*gR;
        a[0][i+d+519]+=p[i]*.094;a[1][i+d+794]+=p[i]*.077;
      }
    }
    let z=0;
    for(let i=0;i<Math.floor(.12*R);i++){
      z=.72*z+.28*seed(i+931);const t=i/R, v=.078*(1-Math.exp(-t/.003))*Math.exp(-t/.027)*z*(1-t/.12);
      a[0][i]+=v;a[1][i]+=v*.9;
    }
    return trim(a,.69);
  }
  const built=new WeakMap();
  let run=null, select={master:0,music:0,effects:0};
  function atGain(n,target,time,fade){
    const g=n.gain;
    if(typeof g.cancelAndHoldAtTime==='function')g.cancelAndHoldAtTime(time);
    else{const v=g.value;g.cancelScheduledValues(time);g.setValueAtTime(v,time);}
    if(fade)g.linearRampToValueAtTime(target,time+fade);
    else g.setValueAtTime(target,time);
  }
  function wire(s,buffer,loop,name){
    const ctx=s.context, v=ctx.createBufferSource(),g=ctx.createGain();
    v.buffer=buffer;v.loop=loop;g.gain.value=0;v.connect(g);g.connect(s.output);
    const record={v,g,name};
    s.voices.add(record);
    v.onended=()=>{
      // Never clear a restarted session because an old source's handler runs late.
      detach(s,record);
      if(run===s&&!s.voices.size)run=null;
    };
    return record;
  }
  function detach(s,o){
    try{o.v.disconnect();}catch{}
    try{o.g.disconnect();}catch{}
    s.voices.delete(o);
    o.v.onended=null;
  }
  function stop(){
    const s=run;run=null;if(!s)return;
    for(const o of [...s.voices]){
      try{o.v.stop();}catch{}
      detach(s,o);
    }
  }
  function mix({master=select.master,music=select.music,effects=select.effects}={}){
    select={master:db(master),music:db(music),effects:db(effects)};
    const s=run;if(!s)return;
    const t=s.context.currentTime;
    for(const o of s.voices){
      if(s.launching&&o.name!=='cue'){
        if(select.master===0||(o.name==='music'?select.music:select.effects)===0)atGain(o.g,0,t,.012);
        continue;
      }
      const fld=o.name==='music'?'music':'effects';
      atGain(o.g,select.master*select[fld]*levels[o.name],t,.045);
    }
  }
  function getBuffers(context){
    let b=built.get(context);
    if(!b){
      b={};built.set(context,b);
      for(const [key,pcm] of [['music',makeScore()],['nature',makeNature()],['cue',makeCue()]]){
        const buf=context.createBuffer(2,pcm[0].length,R);
        pcm.forEach((x,i)=>buf.getChannelData(i).set(x)); b[key]=buf;
      }
    }
    return b;
  }
  function start({context,output,master,music,effects}={}){
    if(!context||context.state!=='running'||!output)return false;
    if(run&&run.context===context&&run.output===output){
      if(run.launching)return false;
      mix({master,music,effects});return true;
    }
    stop();
    try{
      const b=getBuffers(context),s={context,output,voices:new Set(),launching:false,b};
      run=s;
      const t=context.currentTime+.012;
      const loops=[wire(s,b.music,true,'music'),wire(s,b.nature,true,'nature')];
      mix({master,music,effects});
      for(const o of loops)o.v.start(t);
      return true;
    }catch{built.delete(context);stop();return false;}
  }
  function launch(){
    const s=run;
    if(!s||s.launching||s.context.state!=='running')return false;
    s.launching=true;
    const t=s.context.currentTime;
    for(const o of s.voices){atGain(o.g,0,t,.16);try{o.v.stop(t+.168);}catch{detach(s,o);}}
    if(!select.master||!select.effects)return false;
    try{
      const cue=wire(s,s.b.cue,false,'cue');
      atGain(cue.g,select.master*select.effects*levels.cue,t,0);
      cue.v.start(t+.005);
      return true;
    }catch{stop();return false;}
  }
  return Object.freeze({start,mix,launch,stop,get active(){return !!run},
    // Same pure synthesis for the private deterministic WAV receipt; never runs until invoked.
    render:()=>({score:makeScore(),nature:makeNature(),cue:makeCue(),rate:R,levels:{...levels},loopSeconds:LOOP})});
})();
