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



def load_friend_analyses(beta_friend_id: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    created_at,
                    updated_at,
                    payload->>'score' AS score,
                    payload->>'realQualityScore' AS real_quality,
                    payload->>'predictionError' AS prediction_error,
                    COALESCE(status, '') AS status
                FROM analyses
                WHERE payload->>'betaFriendId' = %s
                ORDER BY created_at DESC
                """,
                (beta_friend_id,),
            )

            rows = cursor.fetchall()

    result = []

    for row in rows:
        result.append(
            {
                "id": row[0],
                "createdAt": (
                    row[1].strftime("%d/%m/%Y %H:%M")
                    if row[1]
                    else "-"
                ),
                "updatedAt": (
                    row[2].strftime("%d/%m/%Y %H:%M")
                    if row[2]
                    else "-"
                ),
                "score": row[3] or "-",
                "realQuality": row[4] or "-",
                "predictionError": row[5] or "-",
                "status": row[6] or "-",
            }
        )

    return result



def load_analysis_detail(analysis_id: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    created_at,
                    updated_at,
                    status,
                    payload
                FROM analyses
                WHERE id = %s
                """,
                (analysis_id,),
            )

            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "createdAt": (
            row[1].strftime("%d/%m/%Y %H:%M")
            if row[1]
            else "-"
        ),
        "updatedAt": (
            row[2].strftime("%d/%m/%Y %H:%M")
            if row[2]
            else "-"
        ),
        "status": row[3] or "-",
        "payload": row[4] or {},
    }



def load_high_error_analyses(limit: int = 10):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    payload->>'betaFriendId' AS beta_friend_id,
                    payload->>'score' AS score,
                    payload->>'realQualityScore' AS real_quality,
                    payload->>'predictionError' AS prediction_error,
                    created_at
                FROM analyses
                WHERE
                    NULLIF(
                        payload->>'betaFriendId',
                        ''
                    ) IS NOT NULL
                    AND status = 'feedback_completed'
                    AND payload->>'predictionError'
                        ~ '^[0-9]+([.][0-9]+)?$'
                ORDER BY
                    (payload->>'predictionError')::numeric DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()

    result = []

    for row in rows:
        result.append(
            {
                "id": row[0],
                "betaFriendId": row[1] or "-",
                "score": row[2] or "-",
                "realQuality": row[3] or "-",
                "predictionError": row[4] or "-",
                "createdAt": (
                    row[5].strftime("%d/%m/%Y %H:%M")
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
    "/analysis/{analysis_id}",
    response_class=HTMLResponse,
)
def analysis_detail(analysis_id: str):
    if not DATABASE_URL:
        return HTMLResponse(
            "<h1>DATABASE_URL non configurato</h1>",
            status_code=503,
        )

    try:
        item = load_analysis_detail(analysis_id)
    except Exception as error:
        return HTMLResponse(
            f"<h1>Errore database</h1><p>{html.escape(str(error))}</p>",
            status_code=500,
        )

    if item is None:
        return HTMLResponse(
            "<h1>Analisi non trovata</h1>",
            status_code=404,
        )

    payload = item["payload"]

    beta_friend_id = html.escape(
        str(payload.get("betaFriendId") or "-")
    )

    score = payload.get("score", "-")
    real_quality = payload.get("realQualityScore", "-")
    prediction_error = payload.get("predictionError", "-")
    advice = html.escape(str(payload.get("advice") or "-"))

    features = payload.get("features") or {}
    detector = payload.get("detector") or {}
    feedback = payload.get("feedback") or {}

    reasons = payload.get("reasons") or []
    warnings = payload.get("warnings") or []

    reasons_html = "".join(
        f"<li>{html.escape(str(value))}</li>"
        for value in reasons
    ) or "<li>-</li>"

    warnings_html = "".join(
        f"<li>{html.escape(str(value))}</li>"
        for value in warnings
    ) or "<li>-</li>"

    feature_rows = "".join(
        f"""
        <tr>
            <td>{html.escape(str(key))}</td>
            <td>{html.escape(str(value or '-'))}</td>
        </tr>
        """
        for key, value in features.items()
    )

    feedback_rows = "".join(
        f"""
        <tr>
            <td>{html.escape(str(key))}</td>
            <td>{html.escape(str(value if value is not None else '-'))}</td>
        </tr>
        """
        for key, value in feedback.items()
    ) or """
        <tr>
            <td colspan="2">Nessun feedback disponibile</td>
        </tr>
    """

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

    <title>Dettaglio analisi AngurIA</title>

    <style>
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
            max-width: 1100px;
            margin: 0 auto;
            padding: 32px 20px 60px;
        }}

        h1, h2 {{
            color: #2e7d32;
        }}

        a {{
            color: #2e7d32;
            text-decoration: none;
            font-weight: 600;
        }}

        .back {{
            display: inline-block;
            margin-bottom: 20px;
        }}

        .grid {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .card {{
            background: white;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow:
                0 3px 14px
                rgba(0, 0, 0, 0.06);
        }}

        .metric {{
            font-size: 30px;
            font-weight: 800;
            color: #2e7d32;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        td, th {{
            padding: 10px;
            border-bottom: 1px solid #edf2ed;
            text-align: left;
        }}

        .muted {{
            color: #78909c;
            font-size: 13px;
        }}
    </style>
</head>

<body>
    <div class="container">

        <a class="back" href="/tester/{beta_friend_id}">
            ← Torna al tester
        </a>

        <h1>🍉 Dettaglio analisi</h1>

        <div class="muted">
            {html.escape(str(item['id']))}
            • {item['createdAt']}
            • {html.escape(str(item['status']))}
        </div>

        <div class="grid">

            <div class="card">
                <div>AngurIA Score</div>
                <div class="metric">{score}</div>
            </div>

            <div class="card">
                <div>Qualità reale</div>
                <div class="metric">{real_quality}</div>
            </div>

            <div class="card">
                <div>Errore previsione</div>
                <div class="metric">{prediction_error}</div>
            </div>

            <div class="card">
                <div>Beta Friend</div>
                <div class="metric" style="font-size:22px;">
                    {beta_friend_id}
                </div>
            </div>

        </div>

        <div class="card">
            <h2>Verdetto AngurIA</h2>
            <p>{advice}</p>
        </div>

        <div class="card">
            <h2>Caratteristiche osservate</h2>
            <table>
                <tbody>
                    {feature_rows}
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>Detector</h2>
            <table>
                <tbody>
                    <tr>
                        <td>Rilevato</td>
                        <td>{html.escape(str(detector.get('found', '-')))}</td>
                    </tr>
                    <tr>
                        <td>Confidenza</td>
                        <td>{html.escape(str(detector.get('confidence', '-')))}</td>
                    </tr>
                    <tr>
                        <td>Label</td>
                        <td>{html.escape(str(detector.get('label', '-')))}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>Punti favorevoli</h2>
            <ul>
                {reasons_html}
            </ul>
        </div>

        <div class="card">
            <h2>Avvertenze</h2>
            <ul>
                {warnings_html}
            </ul>
        </div>

        <div class="card">
            <h2>Com'è davvero?</h2>

            <table>
                <tbody>
                    {feedback_rows}
                </tbody>
            </table>
        </div>

    </div>
</body>
</html>
        """
    )



@app.get(
    "/tester/{beta_friend_id}",
    response_class=HTMLResponse,
)
def tester_detail(beta_friend_id: str):
    if not DATABASE_URL:
        return HTMLResponse(
            "<h1>DATABASE_URL non configurato</h1>",
            status_code=503,
        )

    try:
        analyses = load_friend_analyses(beta_friend_id)
    except Exception as error:
        return HTMLResponse(
            f"<h1>Errore database</h1><p>{html.escape(str(error))}</p>",
            status_code=500,
        )

    rows = []

    for item in analyses:
        rows.append(
            f"""
            <tr>
                <td>
                    <a href="/analysis/{html.escape(str(item['id']))}">
                        {html.escape(str(item['id']))}
                    </a>
                </td>
                <td>{item['createdAt']}</td>
                <td>{item['score']}</td>
                <td>{item['realQuality']}</td>
                <td>{item['predictionError']}</td>
                <td>{html.escape(str(item['status']))}</td>
            </tr>
            """
        )

    rows_html = "\n".join(rows)

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
    <title>AngurIA Beta Friend</title>

    <style>
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
            max-width: 1100px;
            margin: 0 auto;
            padding: 32px 20px 60px;
        }}

        a {{
            color: #2e7d32;
            text-decoration: none;
            font-weight: 600;
        }}

        h1 {{
            color: #2e7d32;
        }}

        .card {{
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow:
                0 3px 14px
                rgba(0, 0, 0, 0.06);
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 760px;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #edf2ed;
        }}

        th {{
            color: #607d8b;
            font-size: 12px;
            text-transform: uppercase;
        }}

        .back {{
            margin-bottom: 20px;
            display: inline-block;
        }}
    </style>
</head>

<body>
    <div class="container">

        <a
            class="back"
            href="/"
        >
            ← Torna al monitor
        </a>

        <h1>
            🍉 Beta Friend {html.escape(beta_friend_id)}
        </h1>

        <p>
            Analisi registrate: <strong>{len(analyses)}</strong>
        </p>

        <div class="card">

            <table>
                <thead>
                    <tr>
                        <th>Analisi</th>
                        <th>Data</th>
                        <th>Score</th>
                        <th>Qualità reale</th>
                        <th>Errore</th>
                        <th>Stato</th>
                    </tr>
                </thead>

                <tbody>
                    {rows_html}
                </tbody>
            </table>

        </div>
    </div>
</body>
</html>
        """
    )



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
        high_errors = load_high_error_analyses()

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
                        <a href="/tester/{beta_id}">
                            {beta_id}
                        </a>
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


    diagnostic_rows = []

    for item in high_errors:
        diagnostic_rows.append(
            f"""
            <tr>
                <td>
                    <a href="/analysis/{html.escape(str(item['id']))}">
                        {html.escape(str(item['id']))}
                    </a>
                </td>

                <td>
                    {html.escape(str(item['betaFriendId']))}
                </td>

                <td>{item['score']}</td>

                <td>{item['realQuality']}</td>

                <td>
                    <strong>{item['predictionError']}</strong>
                </td>

                <td>{item['createdAt']}</td>
            </tr>
            """
        )

    diagnostic_rows_html = (
        "\n".join(diagnostic_rows)
        if diagnostic_rows
        else """
            <tr>
                <td colspan="6">
                    Nessuna analisi con feedback disponibile.
                </td>
            </tr>
        """
    )

    diagnostic_html = f"""
        <div class="table-card">
            <h2>🔬 Analisi con errore più alto</h2>

            <p>
                Casi Beta ordinati dalla maggiore
                differenza tra previsione AngurIA
                e qualità reale.
            </p>

            <table>
                <thead>
                    <tr>
                        <th>Analisi</th>
                        <th>Tester</th>
                        <th>AngurIA</th>
                        <th>Reale</th>
                        <th>Errore</th>
                        <th>Data</th>
                    </tr>
                </thead>

                <tbody>
                    {diagnostic_rows_html}
                </tbody>
            </table>
        </div>
    """

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
        {diagnostic_html}

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