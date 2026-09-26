import { STATUS } from './labels'
import type { FieldProperties, Manifest } from './types'

const COLUMNS = ['exported_at_jst','dataset_version','field_id','municipality','centroid_lat','centroid_lon','area_ha','declared_crop','declared_status','declaration_match','status','status_label','confidence','observation_quality','priority_score','priority_rank','priority_components','change_type','reason_codes','quality_flags','valid_s2_count','valid_s1_count','polygon_vintage'] as const
const PART_ORDER = ['declaration', 'status', 'change', 'evidence_uncertainty', 'area'] as const
const safe = (value: unknown) => {
  let text = value == null ? '' : String(value)
  if (/^[=+\-@]/.test(text)) text = `'${text}`
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}
export type CandidatePreference = 'cultivation_signal' | 'review_required' | 'insufficient_observation'
const matchRank = (field: FieldProperties) => field.declaration_match === 'match' ? 0 : field.declaration_match === 'mismatch' ? 1 : 2
export const sortedCandidates = (fields: FieldProperties[], preferred?: CandidatePreference) => [...fields].sort((a,b) => {
  if (preferred) {
    const statusRank=(a.status===preferred?0:1)-(b.status===preferred?0:1)
    if (statusRank!==0) return statusRank
    const declarationRank=matchRank(a)-matchRank(b)
    if (declarationRank!==0) return declarationRank
  }
  return b.priority_score-a.priority_score || b.area_ha-a.area_ha || a.field_id.localeCompare(b.field_id)
})

export function buildCandidateCsv(fields: FieldProperties[], manifest: Manifest, exportedAt = new Date()): string {
  const sorted = sortedCandidates(fields)
  const when = new Intl.DateTimeFormat('sv-SE', { timeZone:'Asia/Tokyo', dateStyle:'short', timeStyle:'medium' }).format(exportedAt).replace(' ', 'T') + '+09:00'
  const rows = sorted.map((f, index) => {
    const values: Record<(typeof COLUMNS)[number], unknown> = {
      exported_at_jst: when, dataset_version: manifest.datasetVersion, field_id:f.field_id, municipality:f.municipality,
      centroid_lat:f.centroid_lat.toFixed(6), centroid_lon:f.centroid_lon.toFixed(6), area_ha:f.area_ha.toFixed(4),
      declared_crop:f.declared_crop, declared_status:f.declared_status, declaration_match:f.declaration_match, status:f.status,
      status_label:STATUS[f.status].label, confidence:f.confidence?.toFixed(2) ?? '', observation_quality:f.observation_quality.toFixed(2),
      priority_score:f.priority_score.toFixed(2), priority_rank:index+1,
      priority_components:PART_ORDER.map(k=>`${k}:${f.priority_components[k].toFixed(2)}`).join(';'), change_type:f.change_type,
      reason_codes:f.reason_codes.join(';'), quality_flags:f.quality_flags.join(';'), valid_s2_count:f.valid_s2_count,
      valid_s1_count:f.valid_s1_count, polygon_vintage:f.polygon_vintage,
    }
    return COLUMNS.map(key=>safe(values[key])).join(',')
  })
  return '\uFEFF' + [COLUMNS.join(','), ...rows].join('\r\n') + '\r\n'
}

export function csvFilename(now = new Date()) {
  const parts = new Intl.DateTimeFormat('ja-JP', { timeZone:'Asia/Tokyo', year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23' }).formatToParts(now)
  const get=(type:string)=>parts.find(p=>p.type===type)?.value ?? ''
  return `soramamori_inspection_candidates_2025_${get('year')}${get('month')}${get('day')}-${get('hour')}${get('minute')}JST.csv`
}
