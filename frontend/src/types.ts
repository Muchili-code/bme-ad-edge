export type ThemeMode = "light" | "dark";

export type BackendHealth = {
  status: "ok";
  service: string;
  case_root_exists: boolean;
};

export type CaseGroup = "HC" | "MCI" | "AD" | string;

export type DataMode = "mock" | "real" | string;

export type CaseSummary = {
  case_id: string;
  group: CaseGroup;
  display_name: string;
  data_mode: DataMode;
  package_valid: boolean;
  ri_analysis_done: boolean;
};

export type CasesResponse = {
  cases: CaseSummary[];
};

export type FileIntegrity = {
  package_valid: boolean;
  missing_files: string[];
  missing_by_section: Record<string, string[]>;
  present_by_section: Record<string, string[]>;
};

export type OutputStatus = {
  ri_analysis_done: boolean;
  files: Record<
    string,
    {
      exists: boolean;
      path: string;
    }
  >;
};

export type CaseDetail = CaseSummary & {
  description?: string | null;
  scan_protocol?: string | null;
  processing_status: Record<string, boolean | string | number | null>;
  file_integrity: FileIntegrity;
  preview_images: Record<string, string>;
  output_status: OutputStatus;
};

export type SuperResolutionSimulation = {
  case_id: string;
  mode: string;
  message: string;
  steps: string[];
  result_preview: string;
};

export type RiAnalysisRunResponse = {
  case_id: string;
  status: "completed" | string;
  elapsed_ms?: number;
  generated_files?: string[];
};

export type RiProfile = {
  roi_id: string;
  roi_name: string;
  depth_percent: number[];
  ri_values: number[];
};

export type RiProfilesResponse = {
  case_id: string;
  status?: "completed" | "not_completed" | string;
  message?: string;
  profiles?: RiProfile[];
};

export type RoiMetric = {
  case_id: string;
  group: string;
  roi_id: string;
  roi_name: string;
  network: string;
  hemisphere: string;
  ri_skewness: number;
  ri_maximum: number;
  risk_level: string;
  pattern: string;
};

export type MetricsResponse = {
  case_id: string;
  status: "completed" | "not_completed" | string;
  message?: string;
  metrics: RoiMetric[];
};

export type ReportResponse = {
  case_id: string;
  status?: "completed" | "not_completed" | string;
  message?: string;
  title?: string;
  summary?: string;
  disclaimer?: string;
  [field: string]: unknown;
};

export type BackendStatus =
  | {
      kind: "checking";
      message: string;
    }
  | {
      kind: "online";
      health: BackendHealth;
      message: string;
    }
  | {
      kind: "offline";
      message: string;
    };

export type PageId = "cases" | "input" | "super-resolution" | "ri-analysis" | "report";
