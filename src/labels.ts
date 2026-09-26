import type { ChangeType, Status, Subtype } from './types'

export const STATUS: Record<Status, { label: string; short: string; color: string; tone: string }> = {
  cultivation_signal: { label: '作付の兆候あり', short: '作付兆候', color: '#17806d', tone: 'green' },
  fallow_candidate: { label: '休耕の可能性', short: '休耕可能性', color: '#b45f06', tone: 'amber' },
  review_required: { label: '要確認', short: '要確認', color: '#b42335', tone: 'red' },
  insufficient_observation: { label: '観測不足', short: '観測不足', color: '#667085', tone: 'gray' },
}
export const SUBTYPE: Record<Subtype, string> = {
  paddy_signal: '水田兆候', upland_crop_signal: '畑作兆候', mixed_or_unknown: '種別要確認', not_evaluated: '補助判定なし',
}
export const CHANGE: Record<ChangeType, string> = {
  paddy_to_upland_candidate: '水田兆候 → 畑作兆候', upland_to_paddy_candidate: '畑作兆候 → 水田兆候',
  cultivated_to_fallow_candidate: '作付兆候 → 休耕可能性', fallow_to_cultivated_candidate: '休耕可能性 → 作付兆候',
  stable: '大きな変化なし', change_uncertain: '変化判定不能',
}
export const MATCH: Record<string, string> = { match: '一致', mismatch: '不一致', not_comparable: '比較不能', unavailable: '申告なし' }
export const CROP: Record<string, string> = { paddy_rice: '水稲', upland_crop: '畑作物', other_crop: 'その他作物', not_declared: '申告なし', unknown: '不明' }
export const DECLARED_STATUS: Record<string, string> = { planned_cultivation: '作付予定', planned_fallow: '休耕予定', not_submitted: '未提出', unknown: '不明' }
export const QUALITY: Record<string, string> = {
  BOUNDARY_VINTAGE_DIFFERENCE: '観測年と境界公開年が異なります', SMALL_FIELD_SEVERE: '0.05 ha未満の小区画です',
  SMALL_FIELD_WARNING: '0.10 ha未満の小区画です', SMALL_FIELD_MIXED_PIXEL: '周辺画素が混ざる可能性があります',
  HARVEST_WINDOW_INCOMPLETE: '収穫確認期の観測が不足しています', CLOUD_LIMITED: '雲により光学観測が限られます',
}
