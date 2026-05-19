import { useCallback, useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { CaseSummary } from "../types";

type CasesState =
  | { kind: "idle"; cases: CaseSummary[]; message: string }
  | { kind: "loading"; cases: CaseSummary[]; message: string }
  | { kind: "ready"; cases: CaseSummary[]; message: string }
  | { kind: "unavailable"; cases: CaseSummary[]; message: string }
  | { kind: "error"; cases: CaseSummary[]; message: string };

export function useCases(enabled: boolean) {
  const [state, setState] = useState<CasesState>({
    kind: "idle",
    cases: [],
    message: "等待后端连接",
  });

  const refresh = useCallback(
    async (signal?: AbortSignal) => {
      if (!enabled) {
        setState({
          kind: "unavailable",
          cases: [],
          message: "后端未连接，病例选择不可用",
        });
        return;
      }

      setState((current) => ({
        kind: "loading",
        cases: current.cases,
        message: "正在读取病例列表",
      }));

      try {
        const response = await apiClient.getCases({ signal });
        setState({
          kind: "ready",
          cases: response.cases,
          message: response.cases.length > 0 ? "病例列表已同步" : "未发现可用病例包",
        });
      } catch {
        setState({
          kind: "error",
          cases: [],
          message: "病例列表读取失败，请确认后端服务与病例目录",
        });
      }
    },
    [enabled],
  );

  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);

  return { state, refresh };
}
