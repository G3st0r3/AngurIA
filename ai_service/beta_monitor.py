import html
import os
from typing import Any, Dict, List

import psycopg
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "",
).strip()


app = FastAPI(
    title="AngurIA Beta Friends Monitor",
    version="0.1.0",
)


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL non configurato"
        )

    return psycopg.connect(DATABASE_URL)


def load_summary() -> Dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) FILTER (
                        WHERE NULLIF(
                            payload->>'betaFriendId',
                            ''
                        ) IS NOT NULL
                    ) AS beta_analyses,

                    COUNT(
                        DISTINCT NULLIF(
                            payload->>'betaFriendId',
                            ''
                        )
                    ) AS beta_friends,

                    COUNT(*) FILTER (
                        WHERE
                            NULLIF(
                                payload->>'betaFriendId',
                                ''
                            ) IS NOT NULL
                            AND status = 'feedback_completed'
                    ) AS beta_feedback,

                    AVG(
                        CASE
                            WHEN
                                NULLIF(
                                    payload->>'betaFriendId',
                                    ''
                                ) IS NOT NULL
                                AND payload->>'score'
                                    ~ '^[0-9]+([.][0-9]+)?$'
                            THEN
                                (payload->>'score')::numeric
                        END
                    ) AS avg_score,

                    AVG(
                        CASE
                            WHEN
                                NULLIF(
                                    payload->>'betaFriendId',
                                    ''
                                ) IS NOT NULL
                                AND payload->>'realQualityScore'
                                    ~ '^[0-9]+([.][0-9]+)?$'
                            THEN
                                (
                                    payload
                                    ->>'realQualityScore'
                                )::numeric
                        END
                    ) AS avg_real_quality,

                    AVG(
                        CASE
                            WHEN
                                NULLIF(
                                    payload->>'betaFriendId',
                                    ''
                                ) IS NOT NULL
                                AND payload->>'predictionError'
                                    ~ '^[0-9]+([.][0-9]+)?$'
                            THEN
                                (
                                    payload
                                    ->>'predictionError'
                                )::numeric
                        END
                    ) AS avg_prediction_error,

                    COUNT(*) FILTER (
                        WHERE NULLIF(
                            payload->>'betaFriendId',
                            ''
                        ) IS NULL
                    ) AS historical_analyses,

                    COUNT(*) FILTER (
                        WHERE
                            NULLIF(
                                payload->>'betaFriendId',
                                ''
                            ) IS NULL
                            AND status = 'feedback_completed'
                    ) AS historical_feedback

                FROM analyses
                """
            )

            row = cursor.fetchone()

    beta_analyses = int(row[0] or 0)
    beta_friends = int(row[1] or 0)
    beta_feedback = int(row[2] or 0)

    completion_rate = (
        beta_feedback / beta_analyses * 100
        if beta_analyses
        else 0
    )

    return {
        "analysesTotal": beta_analyses,
        "betaFriends": beta_friends,
        "feedbackCompleted": beta_feedback,
        "completionRate": completion_rate,
        "avgScore": float(row[3] or 0),
        "avgRealQuality": float(row[4] or 0),
        "avgPredictionError": float(row[5] or 0),
        "historicalAnalyses": int(row[6] or 0),
        "historicalFeedback": int(row[7] or 0),
    }

def load_beta_friends() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE(
                        NULLIF(
                            payload->>'betaFriendId',
                            ''
                        ),
                        'SENZA_ID'
                    ) AS beta_friend_id,

                    COUNT(*) AS analyses,

                    COUNT(*) FILTER (
                        WHERE status = 'feedback_completed'
                    ) AS feedback,

                    AVG(
                        CASE
                            WHEN payload->>'score'
                                ~ '^[0-9]+([.][0-9]+)?$'
                            THEN
                                (payload->>'score')::numeric
                        END
                    ) AS avg_score,

                    AVG(
                        CASE
                            WHEN payload->>'predictionError'
                                ~ '^[0-9]+([.][0-9]+)?$'
                            THEN
                                (
                                    payload
                                    ->>'predictionError'
                                )::numeric
                        END
                    ) AS avg_error,

                    MAX(updated_at)
                        AS last_activity

                FROM analyses

                WHERE NULLIF(
                    payload->>'betaFriendId',
                    ''
                ) IS NOT NULL

                GROUP BY 1

                ORDER BY
                    last_activity DESC
                """
            )

            rows = cursor.fetchall()

    result = []

    for row in rows:
        analyses = int(row[1] or 0)
        feedback = int(row[2] or 0)

        completion = (
            feedback / analyses * 100
            if analyses
            else 0
        )

        result.append(
            {
                "betaFriendId": row[0],
                "analyses": analyses,
                "feedback": feedback,
                "completion": completion,
                "avgScore": float(row[3] or 0),
                "avgError": float(row[4] or 0),
                "lastActivity": (
                    row[5].strftime(
                        "%d/%m/%Y %H:%M"
                    )
                    if row[5]
                    else "-"
                ),
            }
        )

    return result


def metric_card(
    title: str,
    value: str,
    subtitle: str = "",
) -> str:
    return f"""
        <div class="metric-card">
            <div class="metric-title">
                {html.escape(title)}
            </div>

            <div class="metric-value">
                {html.escape(value)}
            </div>

            <div class="metric-subtitle">
                {html.escape(subtitle)}
            </div>
        </div>
    """


@app.get(
    "/health",
)
def health():
    return {
        "service":
            "AngurIA Beta Friends Monitor",
        "status": "online",
        "databaseConfigured":
            bool(DATABASE_URL),
    }


@app.get(
    "/",
    response_class=HTMLResponse,
)
def dashboard():
    if not DATABASE_URL:
        return HTMLResponse(
            """
            <h1>🍉 AngurIA Beta Monitor</h1>
            <p>
                DATABASE_URL non configurato.
            </p>
            """,
            status_code=503,
        )

    try:
        summary = load_summary()
        friends = load_beta_friends()

    except Exception as error:
        safe_error = html.escape(
            str(error)
        )

        return HTMLResponse(
            f"""
            <h1>🍉 AngurIA Beta Monitor</h1>
            <p>
                Errore database:
                {safe_error}
            </p>
            """,
            status_code=500,
        )

    cards = "".join(
    [
        metric_card(
            "Beta Friend unici",
            str(
                summary[
                    "betaFriends"
                ]
            ),
            "Tester identificati",
        ),
        metric_card(
            "Analisi totali",
            str(
                summary[
                    "analysesTotal"
                ]
            ),
            "Previsioni salvate",
        ),
        metric_card(
            "Feedback completi",
            str(
                summary[
                    "feedbackCompleted"
                ]
            ),
            "Angurie aperte e valutate",
        ),
        metric_card(
            "Completion rate",
            (
                f"{summary['completionRate']:.1f}%"
            ),
            "Analisi con risultato reale",
        ),
        metric_card(
            "Score medio",
            (
                f"{summary['avgScore']:.1f}"
            ),
            "Previsione AngurIA /100",
        ),
        metric_card(
            "Qualità reale media",
            (
                f"{summary['avgRealQuality']:.1f}"
            ),
            "Feedback reale /100",
        ),
        metric_card(
            "Errore medio",
            (
                f"{summary['avgPredictionError']:.1f}"
            ),
            "Differenza previsione/realtà",
        ),
    ]
    )

    historical_html = f"""
        <div class="table-card historical-card">
            <h2>📦 Storico pre-Beta</h2>

            <p>
                Questi dati provengono dai test effettuati
                prima dell'introduzione del Beta Friend ID
                e non influenzano le metriche della Beta.
            </p>

            <div class="historical-values">
                <strong>
                    {summary['historicalAnalyses']}
                </strong>
                analisi storiche
                &nbsp; • &nbsp;
                <strong>
                    {summary['historicalFeedback']}
                </strong>
                feedback completati
            </div>
        </div>
    """

    table_rows = []

    for friend in friends:
        beta_id = html.escape(
            str(
                friend[
                    "betaFriendId"
                ]
            )
        )

        table_rows.append(
            f"""
            <tr>
                <td>
                    <strong>
                        {beta_id}
                    </strong>
                </td>

                <td>
                    {friend['analyses']}
                </td>

                <td>
                    {friend['feedback']}
                </td>

                <td>
                    {friend['completion']:.1f}%
                </td>

                <td>
                    {friend['avgScore']:.1f}
                </td>

                <td>
                    {friend['avgError']:.1f}
                </td>

                <td>
                    {friend['lastActivity']}
                </td>
            </tr>
            """
        )

    rows_html = "\n".join(
        table_rows
    )

    return HTMLResponse(
        f"""
<!DOCTYPE html>
<html lang="it">

<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>
        AngurIA Beta Friends Monitor
    </title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: #f4f8f3;
            color: #263238;
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 32px 20px 60px;
        }}

        h1 {{
            color: #2e7d32;
            margin-bottom: 4px;
        }}

        .subtitle {{
            color: #607d8b;
            margin-bottom: 28px;
        }}

        .metrics {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(190px, 1fr)
                );
            gap: 16px;
            margin-bottom: 32px;
        }}

        .metric-card {{
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow:
                0 3px 14px
                rgba(0, 0, 0, 0.06);
        }}

        .metric-title {{
            color: #607d8b;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .metric-value {{
            margin: 8px 0;
            color: #2e7d32;
            font-size: 32px;
            font-weight: 800;
        }}

        .metric-subtitle {{
            color: #90a4ae;
            font-size: 12px;
        }}

        .table-card {{
            background: white;
            border-radius: 16px;
            padding: 20px;
            overflow-x: auto;
            box-shadow:
                0 3px 14px
                rgba(0, 0, 0, 0.06);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 760px;
        }}

        th {{
            text-align: left;
            color: #607d8b;
            font-size: 12px;
            text-transform: uppercase;
            padding: 12px;
            border-bottom:
                2px solid #edf2ed;
        }}

        td {{
            padding: 14px 12px;
            border-bottom:
                1px solid #edf2ed;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        .footer {{
            margin-top: 20px;
            text-align: center;
            color: #90a4ae;
            font-size: 12px;
        }}
    </style>
</head>

<body>

    <div class="container">

        <h1>
            🍉 AngurIA Beta Friends
        </h1>

        <div class="subtitle">
            Monitor sperimentale della Beta
        </div>

        <div class="metrics">
            {cards}
        </div>

        <div class="table-card">

            <h2>
                Beta Friends
            </h2>

            <table>

                <thead>
                    <tr>
                        <th>Tester</th>
                        <th>Analisi</th>
                        <th>Feedback</th>
                        <th>Completion</th>
                        <th>Score medio</th>
                        <th>Errore medio</th>
                        <th>Ultima attività</th>
                    </tr>
                </thead>

                <tbody>
                    {rows_html}
                </tbody>

            </table>

        </div>
        {historical_html}
        <div class="footer">
            AngurIA Beta Monitor •
            dati aggiornati al caricamento della pagina
        </div>

    </div>

</body>
</html>
        """
    )