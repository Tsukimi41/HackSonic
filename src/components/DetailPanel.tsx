import { AlertTriangle, ArrowRight, CheckCircle2, ClipboardPlus, Database, Eye, Satellite, X } from 'lucide-react'
import { CHANGE, CROP, DECLARED_STATUS, MATCH, QUALITY, STATUS, SUBTYPE } from '../labels'
import type { FieldProperties, Manifest, Methodology, YearSeries } from '../types'
import { TimeSeriesChart } from './TimeSeriesChart'

interface Props { field?:FieldProperties; series?:Record<string,YearSeries>; methodology:Methodology; manifest:Manifest; inCandidates:boolean; onToggle:()=>void; onClose?:()=>void }
const pct=(v:number|null)=>v==null?'算出不可':`${Math.round(v*100)}%`
const metric=(label:string,value:string,help?:string)=><div className="metric"><span>{label}</span><strong>{value}</strong>{help&&<small>{help}</small>}</div>
export function DetailPanel({field,series,methodology,manifest,inCandidates,onToggle,onClose}:Props){
  if(!field)return <aside className="detail-card empty-detail"><Satellite size={36}/><h2>圃場を選択してください</h2><p>地図または一覧から圃場を選ぶと、判定根拠と時系列を確認できます。</p></aside>
  const status=STATUS[field.status]; const reasons=field.reason_codes.map(c=>methodology.reasonLabels[c]??c)
  const s2024=series?.['2024']; const s2025=series?.['2025']
  return <aside className="detail-card" aria-labelledby="detail-title">
    <div className="detail-top"><div><span className="eyebrow">選択中の圃場</span><h2 id="detail-title">{field.field_id.replace('maff-2026-','圃場 ')}</h2></div>{onClose&&<button className="icon-button" onClick={onClose} aria-label="詳細を閉じる"><X/></button>}</div>
    <div className="status-hero" style={{borderLeftColor:status.color}}><div><span className={`status-pill ${status.tone}`}>{status.label}</span><p>{reasons[0]}</p></div><div className="confidence"><strong>{pct(field.confidence)}</strong><span>証拠の強さ</span></div></div>
    <p className="caution"><AlertTriangle size={17}/>衛星解析だけでは確定できません。交付金等の判断には所定の確認が必要です。</p>
    <section className="detail-section"><div className="section-title"><h3>申告との照合</h3><span className="demo-tag">デモ用架空データ</span></div>
      <div className="compare-row"><div><span>架空申告</span><strong>{CROP[field.declared_crop??'']??'—'}・{DECLARED_STATUS[field.declared_status??'']??'—'}</strong></div><ArrowRight/><div><span>照合結果</span><strong className={`match-${field.declaration_match}`}>{MATCH[field.declaration_match]}</strong></div></div>
      <p className="fine-print">実在する営農計画書ではなく、照合操作を示すため固定seedで生成しています。</p>
    </section>
    <section className="detail-section"><h3>判定の理由</h3><ul className="reason-list">{reasons.map((r,i)=><li key={`${r}-${i}`}><CheckCircle2 size={18}/>{r}</li>)}</ul>
      <div className="subtype"><span>実験的な参考情報</span><strong>{SUBTYPE[field.cultivation_subtype]}</strong>{field.subtype_confidence!=null&&<small>補助判定の証拠 {pct(field.subtype_confidence)}</small>}</div>
    </section>
    <section className="detail-section"><h3>2024 → 2025 比較</h3><div className="year-cards"><div><span>2024 基準年</span><strong>{STATUS[field.baseline_status].label}</strong><small>{pct(field.baseline_confidence)}</small></div><ArrowRight/><div><span>2025 対象年</span><strong>{STATUS[field.status].label}</strong><small>{pct(field.confidence)}</small></div></div><p className="change-label">{CHANGE[field.change_type]}</p></section>
    {s2025&&<section className="detail-section charts"><h3>衛星時系列</h3><div className="chart-tabs-note"><Satellite size={17}/>実線: 2025年。{manifest.dataMode.startsWith('actual_sentinel_observations')?'Sentinel実観測の筆内中央値です。':'値は実演用の模擬観測です。'}</div><TimeSeriesChart title="NDVI（植生の活発さ）" unit="指数" rows={s2025.observations} value="ndvi" domain={[0,1]} color="#17806d" threshold={.5}/><TimeSeriesChart title="Sentinel-1 VH" unit="dB" rows={s2025.observations} value="vh_db" domain={[-25,-5]} color="#185b87" threshold={-19}/>
      <details><summary>2024年の時系列も表示</summary>{s2024&&<><TimeSeriesChart title="2024 NDVI" unit="指数" rows={s2024.observations} value="ndvi" domain={[0,1]} color="#6c7a89" threshold={.5}/><TimeSeriesChart title="2024 VH" unit="dB" rows={s2024.observations} value="vh_db" domain={[-25,-5]} color="#6c7a89" threshold={-19}/></>}</details></section>}
    <section className="detail-section"><h3>主な指標</h3><div className="metric-grid">{metric('面積',`${field.area_ha.toFixed(4)} ha`)}{metric('NDVIピーク',field.ndvi_max?.toFixed(2)??'—')}{metric('NDVI振幅',field.ndvi_amplitude?.toFixed(2)??'—')}{metric('5月 VH',field.vh_may_db==null?'—':`${field.vh_may_db.toFixed(1)} dB`)}{metric('光学観測',`${field.valid_s2_count}回`)}{metric('SAR観測',`${field.valid_s1_count}回`)}</div></section>
    <section className="detail-section"><h3>観測品質と検証</h3><div className="quality-score"><Database/><div><strong>{pct(field.observation_quality)}</strong><span>観測品質（精度確率ではありません）</span></div></div><ul className="flag-list">{field.quality_flags.map(flag=><li key={flag}>{QUALITY[flag]??flag}</li>)}</ul><div className="evidence"><Eye size={18}/><div><strong>独立目視検証: 未実施</strong><span>参考ラベル・精度値は付与していません</span></div></div><p className="fine-print">解析年 2024–2025／筆ポリゴン公開年 {field.polygon_vintage}</p></section>
    <button className={`button full ${inCandidates?'button-secondary':'button-primary'}`} onClick={onToggle}><ClipboardPlus size={19}/>{inCandidates?'現地確認リストから削除':'現地確認候補に追加'}</button>
  </aside>
}
