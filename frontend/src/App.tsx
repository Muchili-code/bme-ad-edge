import * as echarts from "echarts";
import {
  Activity,
  BarChart3,
  Brain,
  CheckCircle2,
  FileText,
  ImageIcon,
  Moon,
  Play,
  RefreshCcw,
  ShieldAlert,
  Sun,
  Tablet,
  Waves,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { apiClient } from "./api/client";
import { useBackendStatus } from "./hooks/useBackendStatus";
import { useCaseDetail } from "./hooks/useCaseDetail";
import { useCases } from "./hooks/useCases";
import type {
  BackendStatus,
  CaseDetail,
  CaseSummary,
  MetricsResponse,
  PageId,
  ReportResponse,
  RiAnalysisRunResponse,
  RiProfilesResponse,
  RoiMetric,
  SuperResolutionSimulation,
  ThemeMode,
} from "./types";

const pages: Array<{
  id: PageId;
  label: string;
  description: string;
}> = [
  { id: "cases", label: "病例选择", description: "扫描本地病例包" },
  { id: "input", label: "输入概览", description: "病例详情与预览图" },
  { id: "super-resolution", label: "局部超分展示", description: "流程展示与结果对比" },
  { id: "ri-analysis", label: "RI 分析", description: "执行本地计算并绘图" },
  { id: "report", label: "报告", description: "读取后端报告" },
];

export function App() {
  const [theme, setTheme] = useState<ThemeMode>("dark");
  const [activePage, setActivePage] = useState<PageId>("cases");
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const { status: backendStatus, refresh: refreshBackend } = useBackendStatus();
  const backendOnline = backendStatus.kind === "online";
  const { state: casesState, refresh: refreshCases } = useCases(backendOnline);

  const selectedCase = useMemo(
    () => casesState.cases.find((item) => item.case_id === selectedCaseId) ?? null,
    [casesState.cases, selectedCaseId],
  );
  const { state: caseDetailState, refresh: refreshCaseDetail } = useCaseDetail(selectedCaseId, backendOnline);

  const setPageSafely = (pageId: PageId) => {
    if (pageId !== "cases" && (!backendOnline || !selectedCase)) {
      return;
    }
    setActivePage(pageId);
  };

  const refreshAll = () => {
    void refreshBackend();
    if (backendOnline) {
      void refreshCases();
    }
  };

  return (
    <div className="app-shell" data-theme={theme}>
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <Brain size={24} />
          </div>
          <div>
            <p className="eyebrow">AD dMRI Edge Console</p>
            <h1>边缘端辅助分析工作台</h1>
          </div>
        </div>

        <div className="topbar-actions">
          <BackendBadge status={backendStatus} />
          <button className="icon-button" type="button" onClick={refreshAll} aria-label="刷新连接与病例">
            <RefreshCcw size={18} />
          </button>
          <button
            className="theme-toggle"
            type="button"
            onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
            aria-label={theme === "dark" ? "切换到浅色主题" : "切换到深色主题"}
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            <span>{theme === "dark" ? "浅色" : "深色"}</span>
          </button>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar" aria-label="页面导航">
          <div className="device-tile">
            <Tablet size={19} />
            <div>
              <strong>1024x600 Ready</strong>
              <span>触控屏优先布局</span>
            </div>
          </div>

          <nav className="page-nav">
            {pages.map((page) => {
              const disabled = page.id !== "cases" && (!backendOnline || !selectedCase);
              const active = page.id === activePage;
              return (
                <button
                  key={page.id}
                  className="nav-item"
                  type="button"
                  data-active={active}
                  disabled={disabled}
                  onClick={() => setPageSafely(page.id)}
                >
                  <span>{page.label}</span>
                  <small>{disabled ? "等待病例" : page.description}</small>
                </button>
              );
            })}
          </nav>
        </aside>

        <main className="content-panel">
          {activePage === "cases" ? (
            <CasesPage
              backendOnline={backendOnline}
              cases={casesState.cases}
              message={casesState.message}
              loading={casesState.kind === "loading"}
              selectedCase={selectedCase}
              onSelectCase={setSelectedCaseId}
              onRefresh={() => refreshCases()}
            />
          ) : activePage === "ri-analysis" ? (
            <RiAnalysisPage backendOnline={backendOnline} selectedCase={selectedCase} theme={theme} />
          ) : activePage === "report" ? (
            <ReportPage backendOnline={backendOnline} selectedCase={selectedCase} />
          ) : activePage === "input" ? (
            <InputOverviewPage
              backendOnline={backendOnline}
              selectedCase={selectedCase}
              detailState={caseDetailState}
              onRefresh={() => refreshCaseDetail()}
            />
          ) : activePage === "super-resolution" ? (
            <SuperResolutionPage
              backendOnline={backendOnline}
              selectedCase={selectedCase}
              detail={caseDetailState.detail}
              detailMessage={caseDetailState.message}
              detailReady={caseDetailState.kind === "ready"}
              onRefreshDetail={() => refreshCaseDetail()}
            />
          ) : (
            <ReservedPage page={activePage} selectedCase={selectedCase} />
          )}
        </main>
      </div>
    </div>
  );
}

function BackendBadge({ status }: { status: BackendStatus }) {
  const label = status.kind === "online" ? "在线" : status.kind === "checking" ? "检测中" : "离线";

  return (
    <div className="backend-badge" data-state={status.kind}>
      <span className="status-dot" />
      <div>
        <strong>{label}</strong>
        <small>{status.message}</small>
      </div>
    </div>
  );
}

function CasesPage({
  backendOnline,
  cases,
  message,
  loading,
  selectedCase,
  onSelectCase,
  onRefresh,
}: {
  backendOnline: boolean;
  cases: CaseSummary[];
  message: string;
  loading: boolean;
  selectedCase: CaseSummary | null;
  onSelectCase: (caseId: string | null) => void;
  onRefresh: () => void;
}) {
  return (
    <section className="page-grid" aria-labelledby="cases-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Local Case Packages</p>
          <h2 id="cases-title">病例选择</h2>
        </div>
        <button className="primary-button" type="button" onClick={onRefresh} disabled={!backendOnline || loading}>
          <RefreshCcw size={17} />
          <span>{loading ? "同步中" : "刷新病例"}</span>
        </button>
      </div>

      <div className="notice" data-disabled={!backendOnline}>
        <Activity size={18} />
        <span>{message}</span>
      </div>

      {!backendOnline ? (
        <div className="empty-state">
          <Waves size={30} />
          <h3>后端未连接</h3>
          <p>病例选择、输入概览、RI 分析和报告入口已锁定，避免进入无后端数据支撑的假流程。</p>
        </div>
      ) : (
        <div className="case-table-wrap">
          <table className="case-table">
            <thead>
              <tr>
                <th>case_id</th>
                <th>group</th>
                <th>display_name</th>
                <th>data_mode</th>
                <th>package_valid</th>
                <th>ri_analysis_done</th>
                <th>选择</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((caseItem) => {
                const selected = selectedCase?.case_id === caseItem.case_id;
                return (
                  <tr key={caseItem.case_id} data-selected={selected}>
                    <td className="mono">{caseItem.case_id}</td>
                    <td>
                      <span className={`group-chip group-${caseItem.group.toLowerCase()}`}>{caseItem.group}</span>
                    </td>
                    <td>{caseItem.display_name}</td>
                    <td>{caseItem.data_mode}</td>
                    <td>
                      <StatusPill ok={caseItem.package_valid} trueLabel="valid" falseLabel="invalid" />
                    </td>
                    <td>
                      <StatusPill ok={caseItem.ri_analysis_done} trueLabel="done" falseLabel="pending" />
                    </td>
                    <td>
                      <button
                        className="select-button"
                        type="button"
                        onClick={() => onSelectCase(selected ? null : caseItem.case_id)}
                        disabled={!caseItem.package_valid}
                      >
                        {selected ? "已选择" : "选择"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {cases.length === 0 ? (
            <div className="empty-state compact">
              <h3>暂无病例包</h3>
              <p>请确认后端能够扫描 `data/cases/` 下的标准化病例目录。</p>
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}

function InputOverviewPage({
  backendOnline,
  selectedCase,
  detailState,
  onRefresh,
}: {
  backendOnline: boolean;
  selectedCase: CaseSummary | null;
  detailState: ReturnType<typeof useCaseDetail>["state"];
  onRefresh: () => void;
}) {
  const detail = detailState.detail;
  const previewEntries = detail ? previewOrder.filter((item) => detail.preview_images[item.name]) : [];

  return (
    <section className="page-grid" aria-labelledby="input-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Case Detail</p>
          <h2 id="input-title">输入概览</h2>
        </div>
        <button
          className="primary-button"
          type="button"
          onClick={onRefresh}
          disabled={!backendOnline || !selectedCase || detailState.kind === "loading"}
        >
          <RefreshCcw size={17} />
          <span>{detailState.kind === "loading" ? "同步中" : "刷新详情"}</span>
        </button>
      </div>

      <div className="notice" data-disabled={!backendOnline || detailState.kind === "error" || !detail?.package_valid}>
        {detail?.package_valid ? <CheckCircle2 size={18} /> : <ShieldAlert size={18} />}
        <span>{detailState.message}</span>
      </div>

      {!backendOnline || !selectedCase ? (
        <LockedState title="输入概览不可用" message="请先连接后端并选择有效病例，页面不会展示无 API 支撑的预览内容。" />
      ) : detail ? (
        <>
          <div className="detail-grid">
            <InfoTile label="case_id" value={detail.case_id} mono />
            <InfoTile label="group" value={detail.group} />
            <InfoTile label="data_mode" value={detail.data_mode} />
            <InfoTile label="scan_protocol" value={detail.scan_protocol ?? "未提供"} />
            <InfoTile label="package_valid" value={detail.package_valid ? "valid" : "invalid"} />
            <InfoTile label="ri_analysis_done" value={detail.output_status.ri_analysis_done ? "done" : "pending"} />
          </div>

          <div className="preview-grid">
            {previewEntries.map((item) => (
              <PreviewFrame key={item.name} title={item.label} src={detail.preview_images[item.name]} />
            ))}
          </div>

          {previewEntries.length === 0 ? (
            <LockedState title="暂无预览图" message="后端病例详情没有返回 preview_images，页面不会使用硬编码图片代替。" compact />
          ) : null}

          <div className="integrity-grid">
            <IntegrityPanel title="缺失文件" items={detail.file_integrity.missing_files} emptyLabel="未发现缺失文件" />
            <OutputPanel detail={detail} />
          </div>
        </>
      ) : (
        <LockedState title="病例详情未载入" message="等待 GET /api/cases/{case_id} 返回病例详情。" />
      )}
    </section>
  );
}

function SuperResolutionPage({
  backendOnline,
  selectedCase,
  detail,
  detailMessage,
  detailReady,
  onRefreshDetail,
}: {
  backendOnline: boolean;
  selectedCase: CaseSummary | null;
  detail: CaseDetail | null;
  detailMessage: string;
  detailReady: boolean;
  onRefreshDetail: () => void;
}) {
  const [state, setState] = useState<
    | { kind: "idle"; result: null; message: string }
    | { kind: "running"; result: SuperResolutionSimulation | null; message: string }
    | { kind: "done"; result: SuperResolutionSimulation; message: string }
    | { kind: "error"; result: null; message: string }
  >({ kind: "idle", result: null, message: "等待启动局部超分流程展示" });

  useEffect(() => {
    setState({ kind: "idle", result: null, message: "等待启动局部超分流程展示" });
  }, [selectedCase?.case_id]);

  const canRun = backendOnline && Boolean(selectedCase) && detailReady && Boolean(detail?.package_valid);
  const lowresPatch = detail?.preview_images["lowres_dwi_patch.png"];
  const srPatch = state.result?.result_preview;

  const runSimulation = async () => {
    if (!selectedCase || !canRun) {
      return;
    }

    setState({ kind: "running", result: null, message: "正在调用 simulate-super-resolution" });

    try {
      const result = await apiClient.simulateSuperResolution(selectedCase.case_id);
      setState({ kind: "done", result, message: "局部超分流程展示已返回" });
      void onRefreshDetail();
    } catch (caught) {
      setState({
        kind: "error",
        result: null,
        message: caught instanceof Error ? caught.message : "局部超分流程展示调用失败。",
      });
    }
  };

  return (
    <section className="page-grid sr-page" aria-labelledby="sr-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Visual Demo Only</p>
          <h2 id="sr-title">局部超分流程展示</h2>
        </div>
        <button className="primary-button" type="button" onClick={runSimulation} disabled={!canRun || state.kind === "running"}>
          <Play size={17} />
          <span>{state.kind === "running" ? "调用中" : "开始展示"}</span>
        </button>
      </div>

      <div className="notice" data-disabled={!canRun || state.kind === "error"}>
        {canRun && state.kind !== "error" ? <CheckCircle2 size={18} /> : <ShieldAlert size={18} />}
        <span>{canRun ? state.message : detailMessage}</span>
      </div>

      {!backendOnline || !selectedCase ? (
        <LockedState title="演示流程已禁用" message="后端未连接或未选择病例时，不会展示假步骤或假结果。" />
      ) : !detailReady || !detail?.package_valid ? (
        <LockedState title="演示流程已禁用" message="病例详情未同步或病例包不完整，请先确认 GET /api/cases/{case_id} 返回有效数据。" />
      ) : (
        <div className="sr-layout">
          <div className="comparison-panel">
            <PreviewFrame title="低分辨 dMRI patch" src={lowresPatch} />
            <PreviewFrame title="预存超分结果对比" src={state.kind === "done" ? srPatch : undefined} />
          </div>

          <div className="flow-panel">
            <div className="flow-header">
              <div>
                <span className="field-label">mode</span>
                <strong>{state.result?.mode ?? "等待后端返回"}</strong>
              </div>
              <div>
                <span className="field-label">message</span>
                <strong>{state.result?.message ?? "点击后实际调用 POST /api/cases/{case_id}/simulate-super-resolution"}</strong>
              </div>
            </div>

            {state.result ? (
              <ol className="step-list">
                {state.result.steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            ) : (
              <LockedState title="尚未调用后端" message="这里仅在后端返回 steps 后展示流程，不预置演示步骤。" compact />
            )}
          </div>
        </div>
      )}
    </section>
  );
}

const previewOrder = [
  { name: "lowres_dwi_slice.png", label: "低分辨 dMRI 切片" },
  { name: "lowres_dwi_patch.png", label: "低分辨 dMRI patch" },
  { name: "t1_slice.png", label: "T1 代表性切片" },
  { name: "t1_patch.png", label: "T1 局部 patch" },
  { name: "sr_dwi_slice.png", label: "预存超分切片" },
  { name: "sr_dwi_patch.png", label: "预存超分 patch" },
];

function InfoTile({ label, value, mono = false }: { label: string; value: string | boolean; mono?: boolean }) {
  return (
    <div className="info-tile">
      <span>{label}</span>
      <strong className={mono ? "mono" : undefined}>{String(value)}</strong>
    </div>
  );
}

function PreviewFrame({ title, src }: { title: string; src?: string }) {
  return (
    <figure className="preview-frame">
      <figcaption>
        <ImageIcon size={16} />
        <span>{title}</span>
      </figcaption>
      {src ? (
        <img src={apiClient.previewUrl(src)} alt={title} loading="lazy" />
      ) : (
        <div className="preview-placeholder">等待后端返回预览图</div>
      )}
    </figure>
  );
}

function IntegrityPanel({ title, items, emptyLabel }: { title: string; items: string[]; emptyLabel: string }) {
  return (
    <div className="list-panel">
      <h3>{title}</h3>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item} className="mono">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p>{emptyLabel}</p>
      )}
    </div>
  );
}

function OutputPanel({ detail }: { detail: CaseDetail }) {
  return (
    <div className="list-panel">
      <h3>输出状态</h3>
      <ul>
        {Object.entries(detail.output_status.files).map(([name, file]) => (
          <li key={name}>
            <StatusPill ok={file.exists} trueLabel="exists" falseLabel="missing" />
            <span className="mono">{file.path}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function LockedState({ title, message, compact = false }: { title: string; message: string; compact?: boolean }) {
  return (
    <div className={`empty-state${compact ? " compact" : ""}`}>
      <ShieldAlert size={compact ? 22 : 30} />
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

function StatusPill({
  ok,
  trueLabel,
  falseLabel,
}: {
  ok: boolean;
  trueLabel: string;
  falseLabel: string;
}) {
  return (
    <span className="status-pill" data-ok={ok}>
      {ok ? trueLabel : falseLabel}
    </span>
  );
}

function ReservedPage({ page, selectedCase }: { page: PageId; selectedCase: CaseSummary | null }) {
  const pageLabel = pages.find((item) => item.id === page)?.label ?? "预留页面";

  return (
    <section className="reserved-page">
      <FileText size={34} />
      <h2>{pageLabel}</h2>
      <p>
        当前病例：<strong>{selectedCase?.case_id}</strong>。页面结构已预留，后续 Worker 可在此接入契约内接口。
      </p>
    </section>
  );
}

type ResultState = {
  run: RiAnalysisRunResponse | null;
  profiles: RiProfilesResponse | null;
  metrics: MetricsResponse | null;
  report: ReportResponse | null;
};

function RiAnalysisPage({
  backendOnline,
  selectedCase,
  theme,
}: {
  backendOnline: boolean;
  selectedCase: CaseSummary | null;
  theme: ThemeMode;
}) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("点击后将在后端执行本地 DTI/V1/RI 计算，并在完成后读取输出结果。");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResultState>({
    run: null,
    profiles: null,
    metrics: null,
    report: null,
  });

  useEffect(() => {
    setError(null);
    setResult({ run: null, profiles: null, metrics: null, report: null });
    setMessage("点击后将在后端执行本地 DTI/V1/RI 计算，并在完成后读取输出结果。");
  }, [selectedCase?.case_id]);

  const canRun = backendOnline && Boolean(selectedCase) && !loading;
  const profiles = backendOnline && result.profiles?.status === "completed" ? (result.profiles.profiles ?? []) : [];
  const metrics = backendOnline && result.metrics?.status === "completed" ? result.metrics.metrics : [];
  const reportReady = backendOnline && result.report?.status === "completed";

  const runAnalysis = async () => {
    if (!selectedCase) {
      return;
    }

    setLoading(true);
    setError(null);
    setMessage("正在请求后端执行 RI 分析...");

    try {
      const run = await apiClient.runRiAnalysis(selectedCase.case_id);
      if (run.status !== "completed") {
        throw new Error("RI 分析未返回 completed 状态。");
      }

      setMessage("RI 分析完成，正在读取曲线、ROI 指标和报告...");
      const [profilesResponse, metricsResponse, reportResponse] = await Promise.all([
        apiClient.getRiProfiles(selectedCase.case_id),
        apiClient.getMetrics(selectedCase.case_id),
        apiClient.getReport(selectedCase.case_id),
      ]);

      setResult({
        run,
        profiles: profilesResponse,
        metrics: metricsResponse,
        report: reportResponse,
      });
      setMessage("已读取后端输出结果。");
    } catch (caught) {
      setResult({ run: null, profiles: null, metrics: null, report: null });
      setError(caught instanceof Error ? caught.message : "RI 分析请求失败。");
      setMessage("未显示任何缓存或假结果，请检查后端与病例包。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page-grid analysis-page" aria-labelledby="ri-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">RI Depth Profiles</p>
          <h2 id="ri-title">RI 分析</h2>
        </div>
        <button className="primary-button analysis-run-button" type="button" onClick={runAnalysis} disabled={!canRun}>
          <Play size={17} />
          <span>{loading ? "分析中" : "RI 分析"}</span>
        </button>
      </div>

      <div className="notice" data-disabled={!backendOnline || Boolean(error)}>
        {error ? <ShieldAlert size={18} /> : <Activity size={18} />}
        <span>
          {selectedCase ? `${selectedCase.case_id}：${error ?? message}` : "请先在病例选择页选择有效病例。"}
        </span>
      </div>

      <div className="analysis-layout">
        <div className="chart-card primary-chart">
          <div className="card-heading">
            <div>
              <p className="eyebrow">11-Depth Sampling</p>
              <h3>RI 深度曲线</h3>
            </div>
            <span className="count-chip">{profiles.length} ROI</span>
          </div>
          {profiles.length > 0 ? (
            <RiDepthChart profiles={profiles} theme={theme} />
          ) : (
            <ChartEmpty text={result.profiles?.message ?? "等待后端生成 RI 曲线。"} />
          )}
        </div>

        <div className="chart-card metrics-chart">
          <div className="card-heading">
            <div>
              <p className="eyebrow">ROI Metrics</p>
              <h3>ROI 指标</h3>
            </div>
            <span className="count-chip">{metrics.length} 项</span>
          </div>
          {metrics.length > 0 ? <MetricsChart metrics={metrics} theme={theme} /> : <ChartEmpty text="等待后端生成 ROI 指标。" />}
        </div>

        <div className="metric-list">
          {metrics.length > 0 ? (
            metrics.map((metric) => (
              <article className="metric-row" key={`${metric.roi_id}-${metric.hemisphere}`}>
                <div>
                  <strong>{metric.roi_name}</strong>
                  <span>
                    {metric.network} · {metric.hemisphere}
                  </span>
                </div>
                <div className="metric-values">
                  <span>{metric.ri_skewness.toFixed(3)}</span>
                  <span>{metric.ri_maximum.toFixed(3)}</span>
                  <RiskPill risk={metric.risk_level} />
                </div>
              </article>
            ))
          ) : (
            <div className="empty-state compact">
              <BarChart3 size={26} />
              <h3>暂无 ROI 指标</h3>
              <p>只有后端返回 completed 结果后，这里才展示 metrics API 的数据。</p>
            </div>
          )}
        </div>
      </div>

      <div className="result-strip">
        <span>计算状态：{result.run?.status ?? "未开始"}</span>
        <span>耗时：{typeof result.run?.elapsed_ms === "number" ? `${result.run.elapsed_ms} ms` : "等待后端返回"}</span>
        <span>报告：{reportReady ? result.report?.title ?? "已生成" : result.report?.message ?? "等待生成"}</span>
      </div>
    </section>
  );
}

function RiDepthChart({ profiles, theme }: { profiles: NonNullable<RiProfilesResponse["profiles"]>; theme: ThemeMode }) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const palette = getChartPalette(theme);

  useEffect(() => {
    if (!chartRef.current) {
      return undefined;
    }

    const chart = echarts.init(chartRef.current);
    const firstDepth = profiles[0]?.depth_percent ?? [];
    chart.setOption({
      color: palette.lines,
      animationDuration: 420,
      tooltip: { trigger: "axis", backgroundColor: palette.tooltipBg, borderColor: palette.grid, textStyle: { color: palette.text } },
      legend: { top: 0, textStyle: { color: palette.muted } },
      grid: { left: 42, right: 22, top: 42, bottom: 36 },
      xAxis: {
        type: "category",
        name: "depth %",
        data: firstDepth,
        axisLine: { lineStyle: { color: palette.grid } },
        axisLabel: { color: palette.muted },
        nameTextStyle: { color: palette.muted },
      },
      yAxis: {
        type: "value",
        name: "RI",
        axisLabel: { color: palette.muted },
        nameTextStyle: { color: palette.muted },
        splitLine: { lineStyle: { color: palette.grid } },
      },
      series: profiles.map((profile) => ({
        name: profile.roi_name,
        type: "line",
        smooth: true,
        symbolSize: 6,
        data: profile.ri_values,
      })),
    });

    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [palette.grid, palette.lines, palette.muted, palette.text, palette.tooltipBg, profiles]);

  return <div className="echart" ref={chartRef} aria-label="RI 深度曲线图" />;
}

function MetricsChart({ metrics, theme }: { metrics: RoiMetric[]; theme: ThemeMode }) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const palette = getChartPalette(theme);

  useEffect(() => {
    if (!chartRef.current) {
      return undefined;
    }

    const chart = echarts.init(chartRef.current);
    chart.setOption({
      color: [palette.primary, palette.warning],
      tooltip: { trigger: "axis", backgroundColor: palette.tooltipBg, borderColor: palette.grid, textStyle: { color: palette.text } },
      legend: { top: 0, textStyle: { color: palette.muted } },
      grid: { left: 44, right: 16, top: 42, bottom: 70 },
      xAxis: {
        type: "category",
        data: metrics.map((metric) => metric.roi_name),
        axisLine: { lineStyle: { color: palette.grid } },
        axisLabel: { color: palette.muted, interval: 0, rotate: 28 },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: palette.muted },
        splitLine: { lineStyle: { color: palette.grid } },
      },
      series: [
        {
          name: "RI Skewness",
          type: "bar",
          data: metrics.map((metric) => metric.ri_skewness),
        },
        {
          name: "RI Maximum",
          type: "bar",
          data: metrics.map((metric) => metric.ri_maximum),
        },
      ],
    });

    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [metrics, palette.grid, palette.muted, palette.primary, palette.text, palette.tooltipBg, palette.warning]);

  return <div className="echart" ref={chartRef} aria-label="ROI 指标图" />;
}

function ReportPage({ backendOnline, selectedCase }: { backendOnline: boolean; selectedCase: CaseSummary | null }) {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadReport = async () => {
    if (!selectedCase) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getReport(selectedCase.case_id);
      setReport(response);
    } catch (caught) {
      setReport(null);
      setError(caught instanceof Error ? caught.message : "报告读取失败。");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setReport(null);
    setError(null);
    if (backendOnline && selectedCase) {
      void loadReport();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline, selectedCase?.case_id]);

  const reportReady = backendOnline && report?.status === "completed";

  return (
    <section className="page-grid report-page" aria-labelledby="report-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Generated Report</p>
          <h2 id="report-title">报告</h2>
        </div>
        <button className="primary-button" type="button" onClick={loadReport} disabled={!backendOnline || !selectedCase || loading}>
          <RefreshCcw size={17} />
          <span>{loading ? "读取中" : "刷新报告"}</span>
        </button>
      </div>

      <div className="notice" data-disabled={!backendOnline || Boolean(error) || report?.status === "not_completed"}>
        {error || !reportReady ? <ShieldAlert size={18} /> : <FileText size={18} />}
        <span>
          {!backendOnline
            ? "后端未连接，报告页不会展示缓存或假报告。"
            : error ?? report?.message ?? "报告内容来自后端 report API。"}
        </span>
      </div>

      {!reportReady ? (
        <div className="empty-state report-empty">
          <FileText size={34} />
          <h3>报告尚未生成</h3>
          <p>{report?.message ?? "请先完成 RI 分析；如果后端停止或 report.json 缺失，本页不会生成替代结论。"}</p>
        </div>
      ) : (
        <article className="report-document">
          <p className="eyebrow">Case {report.case_id}</p>
          <h3>{typeof report.title === "string" ? report.title : "边缘端 RI 皮层柱辅助分析报告"}</h3>
          {typeof report.summary === "string" ? <p className="report-summary">{report.summary}</p> : null}
          <ReportFields report={report} />
          {typeof report.disclaimer === "string" ? <p className="report-disclaimer">{report.disclaimer}</p> : null}
        </article>
      )}
    </section>
  );
}

function ReportFields({ report }: { report: ReportResponse }) {
  const hiddenFields = new Set(["case_id", "status", "title", "summary", "disclaimer"]);
  const entries = Object.entries(report).filter(([field]) => !hiddenFields.has(field));

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="report-fields">
      {entries.map(([field, value]) => (
        <section className="report-field" key={field}>
          <h4>{field.replace(/_/g, " ")}</h4>
          {Array.isArray(value) ? (
            <ul>
              {value.map((item, index) => (
                <li key={`${field}-${index}`}>{renderReportValue(item)}</li>
              ))}
            </ul>
          ) : (
            <p>{renderReportValue(value)}</p>
          )}
        </section>
      ))}
    </div>
  );
}

function renderReportValue(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (value == null) {
    return "";
  }
  return JSON.stringify(value);
}

function RiskPill({ risk }: { risk: string }) {
  return (
    <span className="risk-pill" data-risk={risk.toLowerCase()}>
      {risk}
    </span>
  );
}

function ChartEmpty({ text }: { text: string }) {
  return (
    <div className="chart-empty">
      <Waves size={28} />
      <span>{text}</span>
    </div>
  );
}

function getChartPalette(theme: ThemeMode) {
  if (theme === "light") {
    return {
      primary: "#0056d2",
      warning: "#f06d45",
      text: "#27313f",
      muted: "#5f6f82",
      grid: "rgba(27, 39, 58, 0.14)",
      tooltipBg: "rgba(255, 255, 255, 0.96)",
      lines: ["#0056d2", "#2fbf91", "#f06d45", "#6d5dfc", "#00a6a6", "#d9485f"],
    };
  }

  return {
    primary: "#25d6c9",
    warning: "#ff9a6a",
    text: "#f5f7fb",
    muted: "#abb6c7",
    grid: "rgba(255, 255, 255, 0.14)",
    tooltipBg: "rgba(18, 19, 26, 0.94)",
    lines: ["#25d6c9", "#8f68ff", "#ff9a6a", "#5be6a1", "#67b7ff", "#ff6f86"],
  };
}
