import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
const source = (await fs.readFile(new URL('../src/components/SecureVideoPlayer.vue', import.meta.url), 'utf8')).match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm, '')

function harness({native=false, request}={}) {
  let unmount, change, current=1000, calls=0
  const timers=new Map()
  const player={currentTime:0,paused:true,src:'',canPlayType:()=>native?'maybe':'',load(){},pause(){this.paused=true},removeAttribute(){this.src=''},play(){this.paused=false;return Promise.resolve()}}
  const prefix='https://media.example.com/videos/hls/11111111-1111-4111-8111-111111111111/22222222-2222-4222-8222-222222222222/'
  const data=()=>{calls++;return {play_url:prefix+'master.m3u8?token=token'+calls,token:'token'+calls,expires_at:current+300,expires_in:300,refresh_after:240}}
  class MockHls {
    static isSupported(){return true}
    static Events={MANIFEST_PARSED:'manifest',ERROR:'error'}
    static ErrorTypes={MEDIA_ERROR:'media'}
    constructor(config){this.config=config;this.handlers={};this.sources=[]}
    attachMedia(v){this.media=v}
    loadSource(url){this.sources.push(url)}
    startLoad(position){this.position=position}
    on(event, handler){this.handlers[event]=handler}
    recoverMediaError(){this.recovered=true}
    destroy(){this.destroyed=true}
  }
  const getAuth=request || (async()=>data())
  const api=new Function('defineProps','ref','watch','onBeforeUnmount','nextTick','Hls','getPlayAuthorization','document','setTimeout','clearTimeout','Date', source+`
    return {video,loading,started,error,playVideo,renewAuthorization,nativeError,resumeAfterSleep,getHls:()=>hls,getAuth:()=>authorization};
  `)(()=>({lessonId:1}),value=>({value}),(_,fn)=>{change=fn},fn=>{unmount=fn},()=>Promise.resolve(),MockHls,getAuth,{visibilityState:'visible',addEventListener(){},removeEventListener(){}},(fn,ms)=>{const key=Symbol();timers.set(key,{fn,ms});return key},key=>timers.delete(key),{now:()=>current*1000})
  api.video.value=player
  return {api,player,timers,prefix,MockHls,data,get calls(){return calls},advance(seconds){current+=seconds},unmount(){unmount()},change(){change()}}
}

test('initial HLS authorization and request-scoped renewal update the segment token', async()=>{
  const h=harness()
  await h.api.playVideo()
  const engine=h.api.getHls()
  assert.equal(h.calls,1)
  assert.equal([...h.timers.values()][0].ms,240000)
  let opened
  const xhr={open(...args){opened=args}}
  await engine.config.xhrSetup(xhr,h.prefix+'360p/segment_00000.ts?token=token1')
  assert.match(opened[1],/token=token1/)
  h.advance(280)
  await engine.config.xhrSetup(xhr,h.prefix+'360p/segment_00001.ts?token=token1')
  assert.equal(h.calls,2)
  assert.match(opened[1],/token=token2/)
  assert.equal(xhr.withCredentials,false)
  await assert.rejects(engine.config.xhrSetup(xhr,'https://evil.example/a.ts'))
  h.unmount()
  assert.equal(h.timers.size,0)
})

test('authorization revoked at renewal stops media and shows permission error',async()=>{
  let calls=0, h
  h=harness({request:async()=>{
    if(calls++)throw {response:{status:403}}
    return h.data()
  }})
  await h.api.playVideo()
  const engine=h.api.getHls()
  await assert.rejects(h.api.renewAuthorization())
  assert.equal(engine.destroyed,true)
  assert.equal(h.api.started.value,false)
  assert.equal(h.api.getAuth(),null)
  assert.match(h.api.error.value,/课程权限/)
  assert.equal(h.timers.size,0)
})

test('native HLS refresh restores position and paused state',async()=>{
  const h=harness({native:true})
  await h.api.playVideo()
  assert.equal(h.api.getHls(),null)
  h.player.onloadedmetadata()
  assert.equal(h.player.paused,false)
  h.player.currentTime=95
  h.player.paused=true
  await h.api.renewAuthorization()
  assert.match(h.player.src,/token2/)
  h.player.currentTime=0
  h.player.onloadedmetadata()
  assert.equal(h.player.currentTime,95)
  assert.equal(h.player.paused,true)
})

test('unmount cancels late authorization and does not restart playback',async()=>{
  let resolve, h
  h=harness({request:()=>new Promise(r=>{resolve=r})})
  const running=h.api.playVideo()
  h.unmount()
  resolve(h.data())
  await running
  assert.equal(h.api.getHls(),null)
  assert.equal(h.timers.size,0)
})

test('fatal network error stops without unbounded startLoad retry',async()=>{
  const h=harness()
  await h.api.playVideo()
  const engine=h.api.getHls()
  engine.handlers.error(null,{fatal:true,type:'network'})
  assert.equal(engine.destroyed,true)
  assert.equal(h.api.started.value,false)
  assert.equal(h.timers.size,0)
})

test('course change clears old media and renewal timer',async()=>{
  const h=harness()
  await h.api.playVideo()
  const engine=h.api.getHls()
  h.change()
  assert.equal(engine.destroyed,true)
  assert.equal(h.api.getAuth(),null)
  assert.equal(h.api.started.value,false)
  assert.equal(h.timers.size,0)
})
