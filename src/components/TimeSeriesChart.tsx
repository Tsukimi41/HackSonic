import type { Observation } from '../types'

interface Props { title:string; unit:string; rows:Observation[]; value:'ndvi'|'vh_db'; domain:[number,number]; color:string; threshold?:number }
export function TimeSeriesChart({title,unit,rows,value,domain,color,threshold}:Props){
  const w=520,h=190,p={l:42,r:12,t:24,b:34}; const valid=rows.map((r,i)=>({x:p.l+i*(w-p.l-p.r)/(rows.length-1),y:r[value]==null?null:p.t+(domain[1]-r[value]!)*(h-p.t-p.b)/(domain[1]-domain[0]),row:r}))
  let path=''; let pen=false; valid.forEach(v=>{if(v.y==null){pen=false;return} path+=`${pen?'L':'M'}${v.x.toFixed(1)},${v.y.toFixed(1)} `;pen=true})
  const ty=threshold==null?null:p.t+(domain[1]-threshold)*(h-p.t-p.b)/(domain[1]-domain[0])
  return <figure className="chart"><figcaption><strong>{title}</strong><span>{unit}</span></figcaption><svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${title}の時系列グラフ`}>
    {[0,.5,1].map(fr=>{const y=p.t+fr*(h-p.t-p.b);const val=domain[1]-fr*(domain[1]-domain[0]);return <g key={fr}><line x1={p.l} x2={w-p.r} y1={y} y2={y} className="grid"/><text x={p.l-7} y={y+4} textAnchor="end">{val.toFixed(value==='ndvi'?1:0)}</text></g>})}
    {ty!=null&&<g><line x1={p.l} x2={w-p.r} y1={ty} y2={ty} className="threshold"/><text x={w-p.r-2} y={ty-5} textAnchor="end" className="threshold-label">基準 {threshold}</text></g>}
    <path d={path} fill="none" stroke={color} strokeWidth="3" strokeLinejoin="round"/>
    {valid.map((v,i)=>v.y==null?<path key={i} d={`M${v.x-4},${h-p.b-4}l8,8m0,-8l-8,8`} className="missing"/>:<circle key={i} cx={v.x} cy={v.y} r="4" fill={color}><title>{v.row.date}: {v.row[value]}</title></circle>)}
    {valid.map((v,i)=>i%2===0&&<text key={v.row.date} x={v.x} y={h-12} textAnchor="middle">{Number(v.row.date.slice(5,7))}月</text>)}
  </svg><p className="chart-note">× は欠測。欠測を0として補完していません。</p></figure>
}
