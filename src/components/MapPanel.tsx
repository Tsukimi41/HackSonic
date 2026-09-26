import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, Map as MlMap, MapMouseEvent } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Layers, MapPinned } from 'lucide-react'
import type { FieldCollection } from '../types'

interface Props { data: FieldCollection; roi:[number,number,number,number]; selectedId?:string; onSelect:(id:string)=>void }
maplibregl.setWorkerUrl(`${import.meta.env.BASE_URL}vendor/maplibre/maplibre-gl-worker.mjs`)

export function MapPanel({data,roi,selectedId,onSelect}:Props){
  const node=useRef<HTMLDivElement>(null); const mapRef=useRef<MlMap|null>(null); const onSelectRef=useRef(onSelect)
  const [ready,setReady]=useState(false); const [background,setBackground]=useState(true); const [tileWarning,setTileWarning]=useState(false)
  useEffect(()=>{onSelectRef.current=onSelect},[onSelect])
  useEffect(()=>{
    if(!node.current || mapRef.current) return
    const map=new maplibregl.Map({container:node.current,center:[(roi[0]+roi[2])/2,(roi[1]+roi[3])/2],zoom:15,
      style:{version:8,sources:{osm:{type:'raster',tiles:['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],tileSize:256,attribution:'© OpenStreetMap contributors'}},layers:[{id:'blank',type:'background',paint:{'background-color':'#edf2f1'}},{id:'osm',type:'raster',source:'osm',paint:{'raster-opacity':.8}}]},
      attributionControl:false})
    map.addControl(new maplibregl.NavigationControl({visualizePitch:false}),'top-right')
    map.addControl(new maplibregl.AttributionControl({compact:false}),'bottom-right')
    map.on('load',()=>{
      map.addSource('fields',{type:'geojson',data})
      map.addLayer({id:'field-fill',type:'fill',source:'fields',paint:{'fill-color':['match',['get','status'],'cultivation_signal','#2a9d82','fallow_candidate','#e3a12f','review_required','#d64a5b','insufficient_observation','#7b8493','#7b8493'],'fill-opacity':.58}})
      map.addLayer({id:'field-outline',type:'line',source:'fields',paint:{'line-color':'#ffffff','line-width':1}})
      map.addLayer({id:'field-selected',type:'line',source:'fields',filter:['==',['get','field_id'],''],paint:{'line-color':'#081f2c','line-width':4}})
      map.on('click','field-fill',(e:MapMouseEvent & {features?:maplibregl.MapGeoJSONFeature[]})=>{const id=e.features?.[0]?.properties?.field_id; if(id) onSelectRef.current(id)})
      map.on('mouseenter','field-fill',()=>map.getCanvas().style.cursor='pointer'); map.on('mouseleave','field-fill',()=>map.getCanvas().style.cursor='')
      map.fitBounds([[roi[0],roi[1]],[roi[2],roi[3]]],{padding:22,duration:0}); setReady(true)
    })
    let errors=0; map.on('error',e=>{ const error=(e as unknown as {error?:Error}).error; if(String(error?.message ?? '').toLowerCase().includes('tile') && ++errors>2) setTileWarning(true) })
    mapRef.current=map; return()=>{map.remove();mapRef.current=null}
  },[roi])
  useEffect(()=>{if(ready)(mapRef.current?.getSource('fields') as GeoJSONSource)?.setData(data)},[data,ready])
  useEffect(()=>{if(ready)mapRef.current?.setFilter('field-selected',['==',['get','field_id'],selectedId??''])},[selectedId,ready])
  useEffect(()=>{if(ready && mapRef.current?.getLayer('osm'))mapRef.current.setLayoutProperty('osm','visibility',background?'visible':'none')},[background,ready])
  return <section className="map-card" aria-labelledby="map-heading"><div className="panel-heading map-heading"><div><h2 id="map-heading">2025年の衛星判定</h2></div><button className="button button-ghost compact" onClick={()=>setBackground(v=>!v)}><Layers size={17}/>{background?'背景を隠す':'背景を表示'}</button></div>
    {tileWarning&&<div className="map-warning" role="status">背景地図を取得できません。圃場レイヤと一覧は引き続き利用できます。</div>}
    <div className="map-wrap"><div ref={node} className="map" aria-label="南相馬市東部の圃場判定地図"/><div className="map-count"><MapPinned size={16}/>{data.features.length}筆を表示</div></div>
    <div className="legend" aria-label="地図凡例">{[['#2a9d82','作付の兆候あり'],['#e3a12f','休耕の可能性'],['#d64a5b','要確認'],['#7b8493','観測不足']].map(([c,l])=><span key={l}><i style={{background:c}}/>{l}</span>)}</div>
  </section>
}
