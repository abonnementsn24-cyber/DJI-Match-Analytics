import { api, ApiError } from "@/lib/api";
import { API_BASE_URL } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  let status: Awaited<ReturnType<typeof api.systemStatus>> | null = null;
  let error: string | null = null;

  try {
    status = await api.systemStatus();
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Erreur lors du chargement du statut.";
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Paramètres</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Statut du système. La synchronisation des données réelles et l&apos;entraînement du modèle ML se pilotent
          via la CLI ou les endpoints d&apos;administration protégés — jamais depuis le navigateur, pour ne jamais
          exposer de clé d&apos;API côté client.
        </p>
      </div>

      {error && <div className="card border-loss/40 bg-loss/10 p-4 text-sm text-loss">{error}</div>}

      {status && (
        <div className="card divide-y divide-line p-0">
          <Row label="API" value={API_BASE_URL} />
          <Row label="Mode" value={status.demo_mode ? "Démo (données fictives)" : "Données réelles"} />
          <Row label="Compétitions" value={String(status.competitions_count)} />
          <Row label="Matchs totaux" value={String(status.matches_count)} />
          <Row label="Matchs terminés" value={String(status.finished_matches_count)} />
          <Row label="Matchs démo" value={String(status.demo_matches_count)} />
          <Row label="Matchs réels" value={String(status.real_matches_count)} />
          <Row label="Modèle ML entraîné" value={status.ml_model_available ? "Oui" : "Non"} />
        </div>
      )}

      <div className="card p-4 text-sm text-text-secondary">
        <h2 className="mb-2 font-semibold text-text">Passer en données réelles</h2>
        <ol className="list-decimal space-y-1 pl-5">
          <li>
            Créez une clé gratuite sur{" "}
            <a href="https://www.football-data.org/" className="text-accent underline" target="_blank" rel="noreferrer">
              football-data.org
            </a>
            .
          </li>
          <li>
            Définissez <code className="rounded bg-surface-2 px-1">FOOTBALL_DATA_API_KEY</code> côté backend.
          </li>
          <li>
            Lancez <code className="rounded bg-surface-2 px-1">python -m app.cli discover</code> puis{" "}
            <code className="rounded bg-surface-2 px-1">sync PL 2025</code>.
          </li>
        </ol>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between px-4 py-3 text-sm">
      <span className="text-text-secondary">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
