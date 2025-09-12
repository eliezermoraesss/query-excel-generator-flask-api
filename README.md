# 📌 Gerador de Queries SQL - Flask

Este projeto foi desenvolvido para **automatizar um processo manual e oneroso** de geração de queries SQL a partir de planilhas Excel.  
Antes, era necessário abrir a planilha e utilizar fórmulas (`CONCAT`, `TEXT`) manualmente.  
Agora, com esta aplicação Flask, é possível enviar um arquivo Excel e gerar automaticamente as queries para atualização de registros no banco de dados.

---

## 🚀 Tecnologias Utilizadas
- [Python 3](https://www.python.org/)
- [Flask](https://flask.palletsprojects.com/)
- [Pandas](https://pandas.pydata.org/)
- [Werkzeug](https://werkzeug.palletsprojects.com/)
- [Bootstrap 5](https://getbootstrap.com/) (para a interface)

---

## 📂 Estrutura do Projeto

```bash
flask_queries/
│── templates/
│   ├── index.html      # Página inicial para upload do Excel
│   ├── result.html     # Página de exibição das queries geradas
│── app.py              # Aplicação Flask principal
│── requirements.txt    # Dependências do projeto
│── .gitignore
```

---

## ⚙️ Funcionalidades
✅ Upload de arquivos `.xls` ou `.xlsx`  
✅ Mapeamento automático de colunas da planilha para campos do banco  
✅ Geração de queries SQL `UPDATE` com formatação correta de datas (`TO_DATE`)  
✅ Botão para **copiar** todas as queries geradas  
✅ Opção para **download** de arquivo `.sql`  
✅ Interface simples e responsiva com Bootstrap  

---

## 📌 Endpoints

### `GET /`
Retorna a página inicial com o formulário para upload.

### `POST /upload`
Recebe o arquivo Excel, processa os dados e gera as queries SQL.

### `GET /download`
Permite baixar um arquivo `.sql` contendo todas as queries geradas.

---

## 📊 Exemplo de Query Gerada

```sql
UPDATE TGFCAB
SET STATUSNFE = 'A',
    DTNEG = TO_DATE('28/08/2025', 'dd/mm/yyyy'),
    DTFATUR = TO_DATE('28/08/2025 17:55:25', 'dd/mm/yyyy HH24:MI:SS'),
    DTMOV = TO_DATE('28/08/2025', 'dd/mm/yyyy'),
    DTENTSAI = TO_DATE('28/08/2025', 'dd/mm/yyyy'),
    AD_DHINC = TO_DATE('28/08/2025 17:55:25', 'dd/mm/yyyy HH24:MI:SS'),
    AD_DHCONFIRMACAO = TO_DATE('28/08/2025 17:55:25', 'dd/mm/yyyy HH24:MI:SS'),
    SERIENOTA = 4,
    CHAVENFE = '35250864580707000288550040000008231862779265'
WHERE NUNOTA = 7992650;
```

---

## 📦 Instalação e Uso

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/flask_queries.git
   cd flask_queries
   ```

2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute a aplicação:
   ```bash
   python app.py
   ```

5. Acesse no navegador:
   ```
   http://localhost:5000
   ```

---

## 📝 Licença
Este projeto foi desenvolvido para uso interno e educacional.  
Sinta-se à vontade para adaptá-lo conforme necessário. 🚀
