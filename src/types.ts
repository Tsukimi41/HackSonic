import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson'

export type Status = 'cultivation_signal' | 'fallow_candidate' | 'review_required' | 'insufficient_observation'
export type Subtype = 'paddy_signal' | 'upland_crop_signal' | 'mixed_or_unknown' | 'not_evaluated'
export type ChangeType = 'paddy_to_upland_candidate' | 'upland_to_paddy_candidate' | 'cultivated_to_fallow_candidate' | 'fallow_to_cultivated_candidate' | 'stable' | 'change_uncertain'

export interface PriorityParts { declaration: number; status: number; change: number; evidence_uncertainty: number; area: number }
export interface FieldProperties {
  field_id: string; source_polygon_id: string | null; field_id_method: string; municipality: string; area_ha: number
  declared_crop: string | null; declared_status: string | null; declaration_source: 'synthetic_demo'; is_synthetic_declaration: true
  baseline_year: number; target_year: number; baseline_status: Status; status: Status
  baseline_confidence: number | null; confidence: number | null; reason_codes: string[]
  baseline_subtype: Subtype; cultivation_subtype: Subtype; subtype_confidence: number | null; subtype_reason_codes: string[]
  change_type: ChangeType; change_confidence: number | null; change_reason_codes: string[]; declaration_match: 'match' | 'mismatch' | 'not_comparable' | 'unavailable'
  auto_candidate: boolean; priority_score: number; priority_components: PriorityParts
  reference_label: string | null; evidence_strength: string | null; evidence_sources: string[]; evidence_dates: string[]; review_status: string
  polygon_vintage: number; valid_s2_count: number; valid_s1_count: number; observation_quality: number; quality_flags: string[]
  ndvi_max: number | null; ndvi_amplitude: number | null; ndvi_may: number | null; ndvi_aug: number | null; vh_may_db: number | null; vh_aug_db: number | null
  centroid_lat: number; centroid_lon: number; source_land_type?: number
}
export type FieldFeature = Feature<Polygon | MultiPolygon, FieldProperties>
export type FieldCollection = FeatureCollection<Polygon | MultiPolygon, FieldProperties>

export interface Observation { date: string; ndvi: number | null; vh_db: number | null; vv_db: number | null; valid_s1: boolean; valid_s2: boolean; valid_ratio: number }
export interface YearSeries { observations: Observation[]; features: Record<string, number | boolean | null> }
export interface Timeseries { fields: Record<string, Record<string, YearSeries>> }
export interface Manifest {
  datasetVersion: string; generatedAt: string; regionLabel: string; roi: [number, number, number, number]
  baselineYear: number; targetYear: number; polygonVintage: number; fieldCount: number; methodVersion: string
  relativeOrbitNumberStart: number; orbitPass: string; dataMode: string; notices: string[]
  thresholds: { sarFloodDropDb: number; ndviGrowthRise: number; ndviPeak: number; ndviHarvestDrop: number }
}
export interface Methodology {
  thresholds: Record<string, number>; requiredObservations: Record<string, number>; fieldAggregation: Record<string, number>
  sensitivity: Array<{ parameter: string; value: number | null; changed_fields: number; status_counts: Record<Status, number> }>
  reasonLabels: Record<string, string>
}
