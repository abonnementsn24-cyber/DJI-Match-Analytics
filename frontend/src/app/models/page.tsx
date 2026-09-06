import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { MODEL_LABELS, pct } from "@/lib/format";
import { PerformanceChart } from "@/components/charts/PerformanceChart";
import { CalibrationChart } from "@/components/charts/CalibrationChart";
import { ConfusionMatrix } from "@/components/ConfusionMatrix";

export const dynamic = "force-dynamic";

export default async function ModelsPage({ searchParams }: PageProps<"/models">) {
  const params = await searchParams;

  let error: string | null = null;
  let models: Awaited<ReturnType<typeof api.models>> = [];
  let metrics: Awaited<ReturnType<typeof api.modelsMetrics>> = {};
  let backtest: Awaited<ReturnType<typeof api.backtesting>> | null = null;

  try {
    [models, metrics, backtest] = await Promise.all([api.models(), api.modelsMetrics(), api.backtesting()]);
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Erreur lors du chargement du Model Lab.";
  }

  const selected = typeof params.model === "string" ? params.model : models[0]?.name ?? "ensemble";
  const selectedMetrics = metrics[selected];
  const selectedBacktest = backtest?.models?.[selected];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Model Lab</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Comparaison objective des modèles — précision, Brier score, log loss et calibration mesurés par backtesting
          chronologique.
        </p>
      </div>

      {error && <div className="card border-loss/40 bg-loss/10 p-4 text-sm text-loss">{error}</div>}

      {backtest?.best_model && (
        <div className="card border-accent/40 bg-accent/10 p-4 text-sm text-accent">
          Modèle le mieux calibré actuellement : <strong>{MODEL_LABELS[backtest.best_model]}</strong> (Brier score le
          plus bas sur l&apos;historique disponible).
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {models.map((m) => (
          <Link
            key={m.name}
            href={`/models?model=${m.name}`}
            className={`card card-hover p-4 ${selected === m.name ? "border-accent" : ""}`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold">{m.label}</span>
              {backtest?.best_model === m.name && (
                <span className="rounded-full bg-win/15 px-2 py-0.5 text-[10px] text-win">Recommandé</span>
              )}
            </div>
            <p className="mt-1 text-xs text-text-secondary">{m.variables.join(" · ")}</p>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
              <div>
                <div className="font-bold">{m.matches_evaluated}</div>
                <div className="text-text-secondary">Matchs</div>
              </div>
              <div>
                <div className="font-bold">{m.accuracy !== null ? pct(m.accuracy) : "—"}</div>
                <div className="text-text-secondary">Accuracy</div>
              </div>
              <div>
                <div className="font-bold">{m.brier_score ?? "—"}</div>
                <div className="text-text-secondary">Brier</div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {selectedMetrics && (
        <>
          <div className="card p-6">
            <h2 className="mb-2 text-lg font-semibold">Performance dans le temps — {MODEL_LABELS[selected]}</h2>
            <PerformanceChart data={selectedMetrics.monthly} />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="card p-6">
              <h2 className="mb-2 text-lg font-semibold">Calibration</h2>
              <CalibrationChart data={selectedBacktest?.calibration_curve ?? []} />
            </div>
            <div className="card p-6">
              <h2 className="mb-4 text-lg font-semibold">Matrice de confusion</h2>
              {selectedBacktest?.classification ? (
                <ConfusionMatrix report={selectedBacktest.classification} />
              ) : (
                <p className="text-sm text-text-secondary">Pas assez de matchs évalués.</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
