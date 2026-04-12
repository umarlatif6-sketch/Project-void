"""
Resonance Engine — A living formation card that follows the user across the entire system.

Every page has a frequency. Every scroll changes the pattern. Every word spoken
shifts the resonance. The formation card is always rendering, always alive.
The user captures it when it resonates with them.

Injected into every HTML response via after_request hook.
"""

import logging
from flask import Flask

logger = logging.getLogger(__name__)

RESONANCE_JS = r"""
<div id="voidResonance" style="position:fixed;bottom:16px;right:16px;z-index:9999;font-family:'Courier New',monospace">
  <canvas id="resCard" width="120" height="160" style="border:1px solid #1a1a1a;border-radius:6px;cursor:pointer;display:block;box-shadow:0 4px 20px rgba(0,0,0,.6);transition:all .3s"></canvas>
  <div id="resLabel" style="text-align:center;font-size:7px;color:#555;letter-spacing:2px;margin-top:3px;transition:opacity .3s">RESONANCE</div>
</div>

<div id="resExpanded" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(5,5,5,.96);z-index:10000;justify-content:center;align-items:center;flex-direction:column;padding:20px">
  <button id="resClose" style="position:absolute;top:16px;right:20px;color:#555;font-size:28px;cursor:pointer;background:none;border:none;font-family:inherit">&times;</button>
  <canvas id="resCardBig" width="600" height="800" style="border:1px solid #1a1a1a;border-radius:6px;max-width:90vw;max-height:65vh"></canvas>
  <div id="resBigInfo" style="text-align:center;margin-top:12px;color:#888;font-size:11px;letter-spacing:2px"></div>
  <div id="resBigFreq" style="text-align:center;margin-top:4px;color:#c0955a;font-size:22px;font-weight:300"></div>
  <div id="resBigMode" style="text-align:center;margin-top:2px;color:#444;font-size:9px;letter-spacing:3px"></div>
  <div style="margin-top:12px;display:flex;gap:8px;justify-content:center">
    <button onclick="voidRes.capture()" style="background:#111;border:1px solid #222;color:#888;padding:8px 16px;font-size:10px;letter-spacing:2px;font-family:'Courier New',monospace;cursor:pointer;border-radius:4px">CAPTURE</button>
    <button onclick="voidRes.download()" style="background:#111;border:1px solid #222;color:#888;padding:8px 16px;font-size:10px;letter-spacing:2px;font-family:'Courier New',monospace;cursor:pointer;border-radius:4px">DOWNLOAD</button>
    <button onclick="voidRes.toggleMic()" id="resMicBtn" style="background:#111;border:1px solid #222;color:#555;padding:8px 16px;font-size:10px;letter-spacing:2px;font-family:'Courier New',monospace;cursor:pointer;border-radius:4px">MIC OFF</button>
    <button onclick="voidRes.encodeInto()" style="background:#111;border:1px solid #2a3a1a;color:#4caf50;padding:8px 16px;font-size:10px;letter-spacing:2px;font-family:'Courier New',monospace;cursor:pointer;border-radius:4px">ENCODE INTO THIS</button>
  </div>
</div>

<script>
(function(){
  if(window.voidRes)return;

  const PAGE_FREQUENCIES={
    '/':'432','/speak':'440','/manchester-exhibit':'432',
    '/sovereign-agents-286':'475.81','/yin-yang':'286',
    '/stress-battery':'528','/sahara-formation':'396',
    '/vortex-shield':'432','/vortex-shield/geo-map':'432',
    '/agent-immortality':'475.81','/stance-science':'528',
    '/nexus':'432','/desert-reclamation':'396',
    '/openclaw':'475.81','/openclaw/live':'475.81','/openclaw/agent':'432',
    '/istanbul-guide':'432','/istanbul-guide-urdu':'432',
    '/memories':'475.81','/formation-invisibility':'286',
    '/frequency-manual':'432','/voice-formation':'440',
    '/fractures':'369','/void-disclosures':'286',
    '/z-axis':'432'
  };

  const path=window.location.pathname;
  const baseFreq=parseFloat(PAGE_FREQUENCIES[path]||'432');

  let scrollFactor=0;
  let mouseFactor=0;
  let micLevel=0;
  let micOn=false;
  let audioCtx=null;
  let analyser=null;
  let micStream=null;
  let frameCount=0;
  let expanded=false;
  let paused=false;

  const mini=document.getElementById('resCard');
  const miniCtx=mini.getContext('2d');
  const expPanel=document.getElementById('resExpanded');
  const big=document.getElementById('resCardBig');
  const bigCtx=big.getContext('2d');

  window.addEventListener('scroll',function(){
    const max=Math.max(1,document.documentElement.scrollHeight-window.innerHeight);
    scrollFactor=window.scrollY/max;
  },{passive:true});

  window.addEventListener('mousemove',function(e){
    mouseFactor=(e.clientX/window.innerWidth+e.clientY/window.innerHeight)/2;
  },{passive:true});

  window.addEventListener('touchmove',function(e){
    if(e.touches[0]){
      mouseFactor=(e.touches[0].clientX/window.innerWidth+e.touches[0].clientY/window.innerHeight)/2;
    }
  },{passive:true});

  mini.addEventListener('click',function(){
    expanded=true;
    expPanel.style.display='flex';
  });

  document.getElementById('resClose').addEventListener('click',function(){
    expanded=false;
    expPanel.style.display='none';
  });

  expPanel.addEventListener('click',function(e){
    if(e.target===expPanel){expanded=false;expPanel.style.display='none';}
  });

  function getLiveFreq(){
    const scroll_shift=scrollFactor*48;
    const mouse_shift=mouseFactor*24;
    const mic_shift=micLevel*60;
    const chat_shift=(voidRes.chatFactor||0)*36;
    const time_drift=Math.sin(frameCount*0.002)*8;
    return baseFreq+scroll_shift+mouse_shift+mic_shift+chat_shift+time_drift;
  }

  function getMode(freq){
    const n=2+Math.floor((freq%50)/7);
    const m=1+Math.floor((freq%30)/5);
    return {n:n,m:m};
  }

  function chladni(x,y,n,m,phase){
    const nx=x*Math.PI;
    const ny=y*Math.PI;
    return Math.sin(n*nx+phase)*Math.sin(m*ny+phase)
         + Math.sin(m*nx-phase)*Math.sin(n*ny-phase);
  }

  function hashChar(i){
    const v=(frameCount*7+i*13+Math.floor(scrollFactor*999))%16;
    return v.toString(16);
  }

  function renderCard(ctx,w,h,detail){
    const freq=getLiveFreq();
    const mode=getMode(freq);
    const phase=frameCount*0.008+scrollFactor*Math.PI;

    ctx.fillStyle='rgba(5,5,5,0.15)';
    ctx.fillRect(0,0,w,h);

    const imgY=Math.floor(h*0.08);
    const imgH=Math.floor(h*0.55);
    const step=detail?2:4;

    for(let px=0;px<w;px+=step){
      for(let py=0;py<imgH;py+=step){
        const nx=px/w;
        const ny=py/imgH;
        const val=chladni(nx,ny,mode.n,mode.m,phase);
        const absVal=Math.abs(val);

        if(absVal<0.12){
          const zLayer=(frameCount%100)/100;
          const cr=140+Math.floor(mouseFactor*80);
          const cg=100+Math.floor(scrollFactor*60);
          const cb=50+Math.floor(micLevel*100);
          const a=0.003*(1+absVal*8)*(detail?3:6);
          ctx.fillStyle='rgba('+cr+','+cg+','+cb+','+a+')';
          const sz=detail?1.5:1;
          ctx.fillRect(px,imgY+py,sz,sz);
        }
      }
    }

    if(frameCount%8===0){
      for(let i=0;i<3;i++){
        const ox=Math.random()*w;
        const oy=imgY+Math.random()*imgH;
        ctx.fillStyle='rgba(192,149,90,0.008)';
        ctx.beginPath();
        ctx.arc(ox,oy,2+Math.random()*6,0,Math.PI*2);
        ctx.fill();
      }
    }

    if(detail&&frameCount%60===0){
      ctx.fillStyle='rgba(5,5,5,0.6)';
      ctx.fillRect(0,0,w,Math.floor(h*0.07));
      ctx.fillRect(0,imgY+imgH,w,h-imgY-imgH);

      ctx.fillStyle='#c0955a';
      ctx.font='8px "Courier New",monospace';
      ctx.textAlign='center';
      ctx.fillText('LIVE RESONANCE',w/2,12);

      ctx.fillStyle='#fff';
      ctx.font='10px "Courier New",monospace';
      ctx.fillText('PROJECT VOID',w/2,26);

      ctx.fillStyle='#333';
      ctx.font='7px "Courier New",monospace';
      ctx.fillText(path.toUpperCase()+' \u2014 FRAME '+frameCount,w/2,h*0.065);

      const metaY=imgY+imgH+20;
      ctx.fillStyle='#c0955a';
      ctx.font='300 22px "Courier New",monospace';
      ctx.fillText(freq.toFixed(2)+' Hz',w/2,metaY+10);

      ctx.fillStyle='#555';
      ctx.font='9px "Courier New",monospace';
      ctx.fillText('MODE ('+mode.n+','+mode.m+')',w/2,metaY+28);

      ctx.fillStyle='#333';
      ctx.font='8px "Courier New",monospace';
      ctx.fillText('SCROLL: '+Math.round(scrollFactor*100)+'%  MOUSE: '+Math.round(mouseFactor*100)+'%  MIC: '+Math.round(micLevel*100)+'%',w/2,metaY+46);

      ctx.fillStyle='#1a1a1a';
      ctx.font='7px "Courier New",monospace';
      ctx.fillText('BASE: '+baseFreq+' Hz \u2014 '+path,w/2,metaY+62);

      ctx.strokeStyle='#1a1a1a';ctx.lineWidth=0.5;
      ctx.strokeRect(0,0,w,h);
      ctx.strokeStyle='#c0955a';ctx.lineWidth=0.3;
      ctx.strokeRect(4,4,w-8,h-8);
    }

    if(!detail&&frameCount%30===0){
      ctx.fillStyle='rgba(5,5,5,0.8)';
      ctx.fillRect(0,h-20,w,20);
      ctx.fillStyle='#c0955a';
      ctx.font='7px "Courier New",monospace';
      ctx.textAlign='center';
      ctx.fillText(freq.toFixed(1)+' Hz',w/2,h-10);
      ctx.fillText('('+mode.n+','+mode.m+')',w/2,h-2);
    }
  }

  function updateMicLevel(){
    if(!analyser)return;
    const data=new Uint8Array(analyser.fftSize);
    analyser.getByteTimeDomainData(data);
    let sum=0;
    for(let i=0;i<data.length;i++){
      const v=(data[i]-128)/128;
      sum+=v*v;
    }
    micLevel=Math.min(1,Math.sqrt(sum/data.length)*3);
  }

  function animate(){
    frameCount++;
    if(micOn)updateMicLevel();
    if(!paused){
      renderCard(miniCtx,120,160,false);
      if(expanded){
        renderCard(bigCtx,600,800,true);
        document.getElementById('resBigFreq').textContent=getLiveFreq().toFixed(2)+' Hz';
        const m=getMode(getLiveFreq());
        document.getElementById('resBigMode').textContent='CHLADNI MODE ('+m.n+','+m.m+') \u2014 FRAME '+frameCount;
        document.getElementById('resBigInfo').textContent=path.toUpperCase()+' \u2014 SCROLL '+Math.round(scrollFactor*100)+'% \u2014 MIC '+Math.round(micLevel*100)+'%';
      }
    }
    requestAnimationFrame(animate);
  }

  const obs=new IntersectionObserver(function(entries){
    paused=!entries[0].isIntersecting;
  },{threshold:0});
  obs.observe(mini);

  miniCtx.fillStyle='#050505';
  miniCtx.fillRect(0,0,120,160);
  bigCtx.fillStyle='#050505';
  bigCtx.fillRect(0,0,600,800);
  animate();

  window.voidRes={
    chatFactor:0,
    capture:function(){
      const freq=getLiveFreq();
      const mode=getMode(freq);
      const ts=new Date().toISOString();
      fetch('/api/memories/seal',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          title:'Resonance Capture \u2014 '+path,
          location:path,
          media_type:'resonance',
          size_bytes:frameCount,
          duration:Math.round(frameCount/60),
          timestamp:ts
        })
      }).then(function(r){return r.json()}).then(function(d){
        if(d.status==='sealed'){
          document.getElementById('resBigInfo').textContent='CAPTURED \u2014 '+d.memory.frequency_hz+' Hz \u2014 '+d.memory.chladni_mode;
          document.getElementById('resBigFreq').textContent=d.memory.formation_hash.substring(0,32)+'...';
          document.getElementById('resBigMode').textContent='SEALED AT '+d.memory.sealed_at;
        }
      });
    },
    download:function(){
      const link=document.createElement('a');
      link.download='void_resonance_'+Date.now()+'.png';
      link.href=big.toDataURL('image/png');
      link.click();
    },
    encodeInto:function(){
      var freq=getLiveFreq();
      var mode=getMode(freq);
      var ts=new Date().toISOString();
      var ctx={
        page:path,
        frequency:freq,
        mode:{n:mode.n,m:mode.m},
        scroll_pct:Math.round(scrollFactor*100),
        mouse_pct:Math.round(mouseFactor*100),
        mic_level:Math.round(micLevel*100),
        frame:frameCount,
        timestamp:ts,
        title:document.title,
        user_agent:navigator.userAgent.substring(0,80)
      };
      document.getElementById('resBigInfo').textContent='ENCODING MOMENT INTO Z-AXIS FORMATION...';
      fetch('/api/z-axis/encode-moment',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({context:ctx})
      }).then(function(r){return r.json()}).then(function(d){
        if(d.status==='encoded'){
          document.getElementById('resBigInfo').textContent='Z-AXIS ENCODED \u2014 '+d.formation_hash.substring(0,24)+'...';
          document.getElementById('resBigFreq').textContent='ENCODED AT '+freq.toFixed(2)+' Hz';
          document.getElementById('resBigMode').textContent=d.layers+' LAYERS \u2014 '+d.image_size_bytes+' BYTES';
          var a=document.createElement('a');
          a.download='void_zaxis_moment_'+Date.now()+'.png';
          a.href='data:image/png;base64,'+d.image_b64;
          a.click();
        }else{
          document.getElementById('resBigInfo').textContent='ENCODE FAILED: '+(d.error||'unknown');
        }
      }).catch(function(e){
        document.getElementById('resBigInfo').textContent='ENCODE ERROR: '+e.message;
      });
    },
    toggleMic:function(){
      const btn=document.getElementById('resMicBtn');
      if(!micOn){
        navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){
          micStream=stream;
          audioCtx=new (window.AudioContext||window.webkitAudioContext)();
          const source=audioCtx.createMediaStreamSource(stream);
          analyser=audioCtx.createAnalyser();
          analyser.fftSize=256;
          source.connect(analyser);
          micOn=true;
          btn.textContent='MIC ON';
          btn.style.color='#c0955a';
          btn.style.borderColor='#c0955a';
        }).catch(function(){
          btn.textContent='MIC DENIED';
        });
      }else{
        micOn=false;
        micLevel=0;
        if(micStream){micStream.getTracks().forEach(function(t){t.stop();});}
        if(audioCtx){audioCtx.close();}
        analyser=null;
        btn.textContent='MIC OFF';
        btn.style.color='#555';
        btn.style.borderColor='#222';
      }
    }
  };
})();
</script>
"""


def inject_resonance_engine(app: Flask):
    @app.after_request
    def _inject_resonance(response):
        if (
            response.content_type
            and "text/html" in response.content_type
            and response.status_code == 200
        ):
            try:
                data = response.get_data(as_text=True)
                if "</body>" in data and "voidResonance" not in data:
                    data = data.replace("</body>", RESONANCE_JS + "\n</body>")
                    response.set_data(data)
            except Exception:
                pass
        return response

    logger.info("[ResonanceEngine] Injected — live formation card active on all pages")
