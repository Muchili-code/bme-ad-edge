import type {
  BackendHealth,
  CaseDetail,
  CasesResponse,
  MetricsResponse,
  ReportResponse,
  RiAnalysisRunResponse,
  RiProfilesResponse,
  SuperResolutionSimulation,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

type RequestOptions = {
  signal?: AbortSignal;
};

type RequestMethod = "GET" | "POST";

async function requestJson<T>(
  path: string,
  options: RequestOptions & { method?: RequestMethod } = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      Accept: "application/json",
    },
    signal: options.signal,
  });

  if (!response.ok) {
    let message = `API ${path} failed with HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown; message?: unknown };
      const detail = typeof body.detail === "string" ? body.detail : body.message;
      if (typeof detail === "string" && detail.length > 0) {
        message = detail;
      }
    } catch {
      // Keep the HTTP status message when the backend does not return JSON.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  getHealth(options?: RequestOptions) {
    return requestJson<BackendHealth>("/api/health", options);
  },

  getCases(options?: RequestOptions) {
    return requestJson<CasesResponse>("/api/cases", options);
  },

  getCase(caseId: string, options?: RequestOptions) {
    return requestJson<CaseDetail>(`/api/cases/${encodeURIComponent(caseId)}`, options);
  },

  simulateSuperResolution(caseId: string, options?: RequestOptions) {
    return requestJson<SuperResolutionSimulation>(
      `/api/cases/${encodeURIComponent(caseId)}/simulate-super-resolution`,
      {
        ...options,
        method: "POST",
      },
    );
  },

  runRiAnalysis(caseId: string, options?: RequestOptions) {
    return requestJson<RiAnalysisRunResponse>(`/api/cases/${encodeURIComponent(caseId)}/run-ri-analysis`, {
      ...options,
      method: "POST",
    });
  },

  getRiProfiles(caseId: string, options?: RequestOptions) {
    return requestJson<RiProfilesResponse>(`/api/cases/${encodeURIComponent(caseId)}/ri-profiles`, options);
  },

  getMetrics(caseId: string, options?: RequestOptions) {
    return requestJson<MetricsResponse>(`/api/cases/${encodeURIComponent(caseId)}/metrics`, options);
  },

  getReport(caseId: string, options?: RequestOptions) {
    return requestJson<ReportResponse>(`/api/cases/${encodeURIComponent(caseId)}/report`, options);
  },

  previewUrl(path: string) {
    return `${API_BASE_URL}${path}`;
  },
};
