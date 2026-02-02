import io

import pandas as pd
from flask import Flask, render_template, request, session, send_file

app = Flask(__name__)
app.secret_key = "query-generator-super-secret-key"

# limite de upload: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"xls", "xlsx"}

mapping_fiscal = {
    "DT. NEG.": "DTNEG",
    "DT. ENTRADA/SAÍDA": "DTENTSAI",
    "DT. DO MOVIMENTO": "DTMOV",
    "DT. CONFIRMAÇÃO": "AD_DHCONFIRMACAO",
    "DT. DO FATURAMENTO": "DTFATUR",
    "DATA INCLUSÃO": "AD_DHINC",
    "SERIE": "SERIENOTA",
    "SERIE DA NOTA": "SERIENOTA",
    "SÉRIE DA NOTA": "SERIENOTA",
    "CHAVE NF": "CHAVENFE",
    "CHAVE NF-E": "CHAVENFE",
    "CHAVE NFE": "CHAVENFE",
    "CHVE NFE": "CHAVENFE",
    "CHAVE ACESSO": "CHAVENFE",
    "CHAVES ACESSO": "CHAVENFE",
    "CHAVE DE ACESSO": "CHAVENFE",
    "CHAVES DE ACESSO": "CHAVENFE",
    "NRO. ÚNICO": "NUNOTA",
    "CENTRO RESULTADO": "CODCENCUS",
    "VENDEDOR": "CODVEND",
    "STATUS NF-E": "STATUSNFE",
    "STATUS NFE": "STATUSNFE",
    "STATUS": "STATUSNFE",
}

mapping_invest = {
    "EMPRESA": {"field": "CODEMP", "key": True},
    "CODIGO": {"field": "CODPROD", "key": True},
    "DEMANDA": {"field": "DEMANDA"},
    "MINIMO": {"field": "ESTMIN"},
    "MAXIMO": {"field": "ESTMAX"},
    "DIA ESTOQUE": {"field": "DIASEST"},
    "DIAS ESTOQUE": {"field": "DIASEST"},
    "MULTIPLO TRF": {"field": "AGRUPTRANSFMIX"},
    "INVESTIMENTO": {"field": "AD_INVESTIMENTO", "fixed": "'S'"}
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

def format_date(value, field):
    formato = date_fields[field]
    if hasattr(value, "strftime"):
        if formato == "dd/mm/yyyy":
            formatted = value.strftime("%d/%m/%Y")
            return f"{field} = TO_DATE('{formatted}', 'dd/mm/yyyy')"
        else:  # data + hora
            formatted = value.strftime("%d/%m/%Y %H:%M:%S")
            return f"{field} = TO_DATE('{formatted}', 'dd/mm/yyyy HH24:MI:SS')"
    else:
        return f"{field} = TO_DATE('{value}', '{formato}')"

@app.route("/")
def index():
    return render_template("index.html")

@app.errorhandler(413)
def too_large(e):
    return "Arquivo muito grande! Máximo permitido é 10 MB", 413

def gerar_query_investimento(df, file):
    all_queries = []
    df.columns = [c.strip().upper() for c in df.columns]

    all_queries.append(f"-- Arquivo: {file.filename}")

    for _, row in df.iterrows():
        insert_fields = []
        insert_values = []
        update_clauses = []
        where_clauses = []

        for col, config in mapping_invest.items():
            if col not in df.columns:
                continue

            field = config["field"]
            value = row[col]

            if pd.isna(value):
                continue

            if "fixed" in config:
                insert_fields.append(field)
                insert_values.append(config["fixed"])
                update_clauses.append(f"{field} = {config['fixed']}")
                continue

            if isinstance(value, (int, float)):
                sql_value = int(value)
            else:
                sql_value = f"'{value}'"

            if config.get("key"):
                where_clauses.append(f"{field} = {sql_value}")
                insert_fields.append(field)
                insert_values.append(sql_value)
            else:
                insert_fields.append(field)
                insert_values.append(sql_value)
                update_clauses.append(f"{field} = {sql_value}")

        if not where_clauses:
            continue

        insert_sql = (
            f"INSERT INTO AD_MIXPRO ({', '.join(insert_fields)}) "
            f"VALUES ({', '.join(map(str, insert_values))});"
        )

        update_sql = (
            f"UPDATE AD_MIXPRO SET {', '.join(update_clauses)} "
            f"WHERE {' AND '.join(where_clauses)};"
        )

        all_queries.append(insert_sql)
        all_queries.append(update_sql)

    return all_queries



def gerar_query_fiscal(df, file):
    all_queries = []

    queries = []
    for _, row in df.iterrows():
        set_clauses = []
        nunota_value = None

        for col in df.columns:
            normalized = col.strip().upper()
            if normalized in mapping_fiscal:
                field = mapping_fiscal[normalized]
                value = row[col]

                if pd.isna(value):
                    continue

                if field == "NUNOTA":
                    nunota_value = int(value)
                    continue

                if field in date_fields:
                    clause = format_date(value, field)
                elif isinstance(value, str):
                    if value.upper().strip() == "APROVADA":
                        value = "A"
                    clause = f"{field} = '{value}'"
                else:
                    clause = f"{field} = {value}"

                set_clauses.append(clause)

        if nunota_value is None:
            continue

        query = f"UPDATE TGFCAB SET {', '.join(set_clauses)} WHERE NUNOTA = {nunota_value};"
        queries.append(query)

    if queries:
        all_queries.append(f"-- Arquivo: {file.filename}")
        all_queries.extend(queries)

    return all_queries

@app.route("/query-generator/flask_queries/upload", methods=["POST"])
def upload():
    files = request.files.getlist("file")  # vários arquivos
    if not files or files[0].filename == "":
        return "Nenhum arquivo enviado", 400

    all_queries = []

    for file in files:
        if not allowed_file(file.filename):
            return f"Formato inválido no arquivo {file.filename}! Envie apenas .xls ou .xlsx", 400

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return f"Erro ao ler o arquivo {file.filename}: {e}", 400

        # normaliza colunas
        normalized_columns = [c.strip().upper() for c in df.columns]

        if "NRO. ÚNICO" in normalized_columns:
            tipo_operacao = 'fiscal'
            mapping = mapping_fiscal
        elif "INVESTIMENTO" in normalized_columns:
            tipo_operacao = 'investimento'
            mapping = mapping_invest
        else:
            return f"Arquivo {file.filename} fora do padrão necessário", 400

        valid_cols = [c for c in normalized_columns if c in mapping]
        if len(valid_cols) <= 1:
            return f"Arquivo {file.filename} fora do padrão necessário (colunas insuficientes)", 400

        if tipo_operacao == 'fiscal':
            all_queries = gerar_query_fiscal(df, file)
        elif tipo_operacao == 'investimento':
            all_queries = gerar_query_investimento(df, file)

        if not all_queries:
            return "Nenhuma query gerada", 400

        session["sql_file"] = "\n".join(all_queries)

    return render_template("result.html", queries=all_queries)

@app.route("/query-generator/flask_queries/download")
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
    app.run(host="0.0.0.0", port=5002)
