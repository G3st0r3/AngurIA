import json
from pathlib import Path
from statistics import mean


BASE_DIR = Path(__file__).resolve().parent.parent

HISTORY_DIR = (
    BASE_DIR
    / "datasets"
    / "watermelon"
    / "analysis_history"
)

REPORTS_DIR = BASE_DIR / "reports"
REPORT_PATH = REPORTS_DIR / "beta_report.html"


def load_analyses():
    analyses = []

    if not HISTORY_DIR.exists():
        return analyses

    for path in sorted(
        HISTORY_DIR.glob("ANALYSIS_*.json")
    ):
        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            analyses.append(data)

        except Exception as error:
            print(
                f"⚠️ Impossibile leggere "
                f"{path.name}: {error}"
            )

    return analyses


def safe_mean(values):
    valid = [
        value
        for value in values
        if isinstance(value, (int, float))
    ]

    if not valid:
        return None

    return round(mean(valid), 1)


def format_value(value, suffix=""):
    if value is None:
        return "—"

    return f"{value}{suffix}"


def build_report(analyses):
    total = len(analyses)

    completed = [
        item
        for item in analyses
        if item.get("status")
        == "feedback_completed"
    ]

    completed_count = len(completed)

    predicted_scores = [
        item.get("score")
        for item in analyses
    ]

    real_scores = [
        item.get("realQualityScore")
        for item in completed
    ]

    prediction_errors = [
        item.get("predictionError")
        for item in completed
    ]

    avg_predicted = safe_mean(
        predicted_scores
    )

    avg_real = safe_mean(
        real_scores
    )

    avg_error = safe_mean(
        prediction_errors
    )

    feedback_rate = (
        round(
            completed_count
            / total
            * 100,
            1,
        )
        if total
        else 0
    )

    rows = []

    ordered = sorted(
        analyses,
        key=lambda item:
            item.get("createdAt", ""),
        reverse=True,
    )

    for item in ordered:
        feedback = item.get("feedback") or {}

        status = item.get(
            "status",
            "analysis_only",
        )

        if status == "feedback_completed":
            status_text = "✅ Completo"
        else:
            status_text = "⏳ In attesa"

        rows.append(
            f"""
            <tr>
                <td>
                    {item.get("id", "—")}
                </td>

                <td>
                    {format_value(
                        item.get("score"),
                        "/100",
                    )}
                </td>

                <td>
                    {format_value(
                        item.get(
                            "realQualityScore"
                        ),
                        "/100",
                    )}
                </td>

                <td>
                    {format_value(
                        item.get(
                            "predictionError"
                        ),
                        " pt",
                    )}
                </td>

                <td>
                    {format_value(
                        feedback.get(
                            "sweetness"
                        )
                    )}
                </td>

                <td>
                    {format_value(
                        feedback.get(
                            "crunchiness"
                        )
                    )}
                </td>

                <td>
                    {format_value(
                        feedback.get(
                            "juiciness"
                        )
                    )}
                </td>

                <td>
                    {format_value(
                        feedback.get(
                            "mealiness"
                        )
                    )}
                </td>

                <td>
                    {format_value(
                        feedback.get("brix")
                    )}
                </td>

                <td>
                    {status_text}
                </td>
            </tr>
            """
        )

    rows_html = "\n".join(rows)

    html = f"""
<!DOCTYPE html>

<html lang="it">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
    AngurIA Beta Report
</title>

<style>

body {{
    margin: 0;
    padding: 30px;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background: #f4f8f3;
    color: #223322;
}}

.container {{
    max-width: 1400px;
    margin: auto;
}}

h1 {{
    margin-bottom: 4px;
    color: #2e7d32;
}}

.subtitle {{
    color: #687568;
    margin-bottom: 28px;
}}

.cards {{
    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(180px, 1fr)
        );

    gap: 16px;

    margin-bottom: 30px;
}}

.card {{
    background: white;
    border-radius: 18px;
    padding: 20px;

    box-shadow:
        0 5px 18px
        rgba(0, 0, 0, 0.05);
}}

.card-label {{
    color: #718071;
    font-size: 13px;
}}

.card-value {{
    margin-top: 8px;

    font-size: 30px;
    font-weight: 800;

    color: #2e7d32;
}}

.table-box {{
    overflow-x: auto;

    background: white;

    border-radius: 18px;

    box-shadow:
        0 5px 18px
        rgba(0, 0, 0, 0.05);
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    padding: 13px 14px;
    text-align: left;
    border-bottom:
        1px solid #edf1ed;
    white-space: nowrap;
}}

th {{
    background: #eaf4e8;
    color: #2e7d32;
}}

tr:hover {{
    background: #f8fbf7;
}}

.note {{
    margin-top: 18px;

    color: #728072;

    font-size: 13px;
}}

</style>

</head>

<body>

<div class="container">

<h1>
    🍉 AngurIA Beta Report
</h1>

<div class="subtitle">
    Stato del dataset reale e precisione sperimentale
</div>

<div class="cards">

    <div class="card">
        <div class="card-label">
            Analisi totali
        </div>
        <div class="card-value">
            {total}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Feedback completi
        </div>
        <div class="card-value">
            {completed_count}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Tasso feedback
        </div>
        <div class="card-value">
            {feedback_rate}%
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Score previsto medio
        </div>
        <div class="card-value">
            {format_value(
                avg_predicted,
                "/100",
            )}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Qualità reale media
        </div>
        <div class="card-value">
            {format_value(
                avg_real,
                "/100",
            )}
        </div>
    </div>

    <div class="card">
        <div class="card-label">
            Errore medio previsione
        </div>
        <div class="card-value">
            {format_value(
                avg_error,
                " pt",
            )}
        </div>
    </div>

</div>

<div class="table-box">

<table>

<thead>

<tr>
    <th>Analisi</th>
    <th>Previsto</th>
    <th>Reale</th>
    <th>Errore</th>
    <th>Dolcezza</th>
    <th>Croccantezza</th>
    <th>Succosità</th>
    <th>Farinosità</th>
    <th>Brix</th>
    <th>Stato</th>
</tr>

</thead>

<tbody>

{rows_html}

</tbody>

</table>

</div>

<div class="note">
    AngurIA Beta Report —
    metriche sperimentali basate
    sui feedback reali disponibili.
</div>

</div>

</body>

</html>
"""

    return html


def main():
    analyses = load_analyses()

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    html = build_report(
        analyses
    )

    REPORT_PATH.write_text(
        html,
        encoding="utf-8",
    )

    print()
    print(
        "# 🍉 ANGURIA BETA REPORT"
    )
    print()
    print(
        f"Analisi lette : "
        f"{len(analyses)}"
    )
    print(
        f"Report creato : "
        f"{REPORT_PATH}"
    )
    print()


if __name__ == "__main__":
    main()