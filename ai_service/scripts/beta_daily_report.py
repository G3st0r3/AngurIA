from datetime import datetime
from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"

sys.path.insert(0, str(BASE_DIR))

from beta_monitor import (  # noqa: E402
    load_beta_activity,
    load_beta_friends,
    load_summary,
)


def main():
    now = datetime.now()

    summary = load_summary()
    activity = load_beta_activity()
    friends = load_beta_friends()

    today = (
        activity.get("daily", [{}])[0]
        if activity.get("daily")
        else {}
    )

    visitors_7d = activity.get("visitors7d", 0)
    analyses_7d = activity.get("analyses7d", 0)

    conversion_7d = (
        round(
            analyses_7d / visitors_7d * 100,
            1,
        )
        if visitors_7d
        else 0
    )

    if today.get("visits", 0) == 0:
        today_summary = "Nessuna nuova visita oggi."
    else:
        today_summary = (
            f"Oggi {today.get('visits', 0)} visite, "
            f"{today.get('analyses', 0)} analisi."
        )

    prediction_summary = (
        f"Errore medio {summary.get('avgPredictionError', 0):.1f} punti; "
        f"sovrastime {summary.get('overestimatedPredictions', 0)}, "
        f"sottostime {summary.get('underestimatedPredictions', 0)}."
    )

    report = f"""
🍉 ANGURIA BETA DAILY REPORT
========================================

Data: {now.strftime("%d/%m/%Y %H:%M")}

SINTESI
----------------------------------------
{today_summary}
Ultimi 7 giorni: {visitors_7d} visitatori, {analyses_7d} analisi.
Conversione visita → analisi: {conversion_7d}%.
{prediction_summary}

OGGI
----------------------------------------
Visite: {today.get("visits", 0)}
Visitatori: {today.get("visitors", 0)}
Analisi: {today.get("analyses", 0)}
Feedback: {today.get("feedback", 0)}

ATTIVITÀ
----------------------------------------
Visite ultime 24h: {activity.get("visits24h", 0)}
Visitatori ultimi 7 giorni: {activity.get("visitors7d", 0)}
Analisi ultimi 7 giorni: {activity.get("analyses7d", 0)}
Feedback ultimi 7 giorni: {activity.get("feedback7d", 0)}

BETA
----------------------------------------
Beta Friends: {summary.get("betaFriends", 0)}
Analisi totali: {summary.get("analysesTotal", 0)}
Feedback completati: {summary.get("feedbackCompleted", 0)}
Completion rate: {summary.get("completionRate", 0)}%

QUALITÀ PREVISIONI
----------------------------------------
Score medio: {summary.get("avgScore", 0):.1f}
Qualità reale media: {summary.get("avgRealQuality", 0):.1f}
Errore medio: {summary.get("avgPredictionError", 0):.1f}

Previsioni accurate: {summary.get("accuratePredictions", 0)}
Sovrastimate: {summary.get("overestimatedPredictions", 0)}
Sottostimate: {summary.get("underestimatedPredictions", 0)}

TESTER ATTIVI
----------------------------------------
"""

    for friend in friends:
        report += (
            f"{friend.get('betaFriendId', '—')} | "
            f"analisi {friend.get('analyses', 0)} | "
            f"feedback {friend.get('feedback', 0)} | "
            f"ultima attività "
            f"{friend.get('lastActivity', '—')}\n"
        )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = (
        REPORTS_DIR
        / f"beta_daily_{now.strftime('%Y%m%d')}.txt"
    )

    output.write_text(
        report.strip() + "\n",
        encoding="utf-8",
    )

    print(report.strip())
    print()
    print("✅ Report salvato:")
    print(output)


if __name__ == "__main__":
    main()
