import io

import pandas as pd
from flask import Flask, render_template, request, session, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "laranja"  # necessário para session

# limite de upload: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"xls", "xlsx"}

# dicionário de mapeamento (já em uppercase para comparação)
mapping = {
    "DT. NEG.": "DTNEG",
    "DT. ENTRADA/SAÍDA": "DTENTSAI",
    "DT. DO MOVIMENTO": "DTMOV",
    "DT. CONFIRMAÇÃO": "AD_DHCONFIRMACAO",
    "DT. DO FATURAMENTO": "DTFATUR",
    "DATA INCLUSÃO": "AD_DHINC",
    "SERIE": "SERIENOTA",
    "CHAVE NF": "CHAVENFE",
    "NRO. ÚNICO": "NUNOTA",
    "CENTRO RESULTADO": "CODCENCUS",
    "VENDEDOR": "CODVEND",
    "STATUS NF-E": "STATUSNFE"
}

# campos que precisam de TO_DATE
date_fields = {
    "DTNEG": "dd/mm/yyyy",
    "DTENTSAI": "dd/mm/yyyy",
    "DTMOV": "dd/mm/yyyy",
    "AD_DHCONFIRMACAO": "dd/mm/yyyy HH24:MI:SS",
    "DTFATUR": "dd/mm/yyyy HH24:MI:SS",
    "AD_DHINC": "dd/mm/yyyy HH24:MI:SS",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.errorhandler(413)
def too_large(e):
    return "Arquivo muito grande! Máximo permitido é 10 MB", 413


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file or file.filename == "":
        return "Nenhum arquivo enviado", 400

    if not allowed_file(file.filename):
        return "Formato inválido! Envie apenas arquivos .xls ou .xlsx", 400

    filename = secure_filename(file.filename)

    try:
        df = pd.read_excel(file)
    except Exception as e:
        return f"Erro ao ler o arquivo Excel: {e}", 400

    # normaliza colunas
    normalized_columns = [c.strip().upper() for c in df.columns]

    # verifica se pelo menos uma coluna do mapping + NUNOTA existem
    if "NRO. ÚNICO" not in normalized_columns:
        return "Arquivo fora do padrão necessário (coluna Nro. Único ausente)", 400

    valid_cols = [c for c in normalized_columns if c in mapping]
    if len(valid_cols) <= 1:  # só NUNOTA não basta
        return "Arquivo fora do padrão necessário (colunas insuficientes)", 400

    queries = []
    for _, row in df.iterrows():
        set_clauses = []
        nunota_value = None

        for col in df.columns:
            normalized = col.strip().upper()
            if normalized in mapping:
                field = mapping[normalized]
                value = row[col]

                if pd.isna(value):
                    continue

                # pega o NUNOTA só para o WHERE
                if field == "NUNOTA":
                    nunota_value = int(value)
                    continue

                # campos de data
                if field in date_fields:
                    clause = f"{field} = TO_DATE('{value}', '{date_fields[field]}')"
                # campos de texto
                elif isinstance(value, str):
                    if value.upper().strip() == "APROVADA":
                        value = "A"
                    clause = f"{field} = '{value}'"
                # numéricos
                else:
                    clause = f"{field} = {value}"

                set_clauses.append(clause)

        if nunota_value is None:
            continue

        query = f"UPDATE TGFCAB SET {', '.join(set_clauses)} WHERE NUNOTA = {nunota_value};"
        queries.append(query)

    if not queries:
        return "Arquivo fora do padrão necessário (nenhuma query gerada)", 400

    session["sql_file"] = "\n".join(queries)

    return render_template("result.html", queries=queries)


@app.route("/download")
def download_sql():
    sql_file = session.get("sql_file", "")
    if not sql_file:
        return "Nenhuma query disponível para download", 400

    return send_file(
        io.BytesIO(sql_file.encode("utf-8")),
        as_attachment=True,
        download_name="queries.sql",
        mimetype="text/sql",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
