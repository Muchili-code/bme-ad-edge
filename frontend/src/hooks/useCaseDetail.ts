import { useCallback, useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { CaseDetail } from "../types";

type CaseDetailState =
  | { kind: "idle"; detail: null; message: string }
  | { kind: "loading"; detail: CaseDetail | null; message: string }
  | { kind: "ready"; detail: CaseDetail; message: string }
  | { kind: "unavailable"; detail: null; message: string }
  | { kind: "error"; detail: null; message: string };

export function useCaseDetail(caseId: string | null, enabled: boolean) {
  const [state, setState] = useState<CaseDetailState>({
    kind: "idle",
    detail: null,
    message: "等待选择病例",
  });

  const refresh = useCallback(
    async (signal?: AbortSignal) => {
      if (!enabled) {
        setState({
          kind: "unavailable",
          detail: null,
          message: "后端未连接，病例详情不可用",
        });
        return;
      }

      if (!caseId) {
        setState({
          kind: "idle",
          detail: null,
          message: "等待选择病例",
        });
        return;
      }

      setState((current) => ({
        kind: "loading",
        detail: current.detail,
        message: "正在读取病例详情",
      }));

      try {
        const detail = await apiClient.getCase(caseId, { signal });
        setState({
          kind: "ready",
          detail,
          message: detail.package_valid ? "病例详情已同步" : "病例包不完整，后续演示已锁定",
        });
      } catch {
        setState({
          kind: "error",
          detail: null,
          message: "病例详情读取失败，请确认后端服务与病例 ID",
        });
      }
    },
    [caseId, enabled],
  );

  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);

  return { state, refresh };
}
