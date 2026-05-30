from flask import Flask
import pandas as pd

app = Flask(__name__)

HISTORY_FILE = "funding_history.csv"


@app.route("/")
def dashboard():

    try:

        df = pd.read_csv(HISTORY_FILE)

    except Exception as e:

        return f"""
        <html>
        <body style="
            background:#0f1117;
            color:white;
            font-family:Arial;
            padding:40px;
        ">
            <h1>Dashboard Error</h1>

            <pre>{str(e)}</pre>

            <p>Run funding_agent.py first</p>
        </body>
        </html>
        """

    if df.empty:

        return """
        <html>
        <body style="
            background:#0f1117;
            color:white;
            font-family:Arial;
            padding:40px;
        ">
            <h1>No funding data yet</h1>
        </body>
        </html>
        """

    table_html = df.to_html(index=False)

    return f"""
    <html>

    <head>

        <title>Funding Dashboard</title>

        <style>

            body {{
                background: #0f1117;
                color: white;
                font-family: Arial;
                padding: 30px;
            }}

            h1 {{
                color: #00ff99;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: #111827;
            }}

            th {{
                background: #1f2937;
                padding: 12px;
                color: #00ff99;
            }}

            td {{
                padding: 10px;
                border-bottom: 1px solid #333;
                text-align: center;
            }}

            tr:hover {{
                background: #1a1a1a;
            }}

        </style>

    </head>

    <body>

        <h1>Hyperliquid Funding Dashboard</h1>

        {table_html}

    </body>

    </html>
    """


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8050,
        debug=False
    )