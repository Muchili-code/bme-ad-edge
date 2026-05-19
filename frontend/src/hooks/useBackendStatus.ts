import { useCallback, useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { BackendStatus } from "../types";

export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatus>({
    kind: "checking",
    message: "正在连接本地后端",
  });

  const refresh = useCallback(async (signal?: AbortSignal) => {
    setStatus({ kind: "checking", message: "正在连接本地后端" });

    try {
      const health = await apiClient.getHealth({ signal });
      setStatus({
        kind: "online",
        health,
        message: health.case_root_exists ? "后端在线，病例目录可用" : "后端在线，病例目录未就绪",
      });
    } catch {
      setStatus({
        kind: "offline",
        message: "后端离线，病例与后续流程不可用",
      });
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);

  return { status, refresh };
}
