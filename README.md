
🧠 AI CV Matcher – Streamlit UI

Toto je frontendová aplikace (MVP) pro projekt **AI CV Matcher**.
Aplikace umožňuje HR a hiring manažerům rychle porovnávat více CV s jedním Job Description a získat:

- Strukturovaná data z CV (jméno, zkušenosti, technologie…)
- AI generované shrnutí kandidáta
- Match score podle požadavků pozice
- Porovnávací tabulku s automatickým zvýrazněním nejlepšího kandidáta
- Detailní pohled na kandidáta

Backend (FastAPI) běží na Render.com a je volán přes REST API.

✅ Funkce UI

- 📄 Nahrání více CV naráz (PDF / DOCX)
- ✏️ Vložení Job Description
- 🔍 Volání backendu `/parse` pro každý CV soubor
- ⚙️ AI extrakce dat a vyhodnocení match skóre
- 📊 Porovnávací tabulka (highlight nejlepšího kandidáta)
- 🧩 Detail kandidáta (technologie, jazyky, shrnutí…)
- 📦 Zobrazení raw JSON dat

✅ Backend API

Aplikace komunikuje s backendem běžícím na Renderu:
POST https://cv-parser-aewt.onrender.com/parse

Parametry:
- file: PDF nebo DOCX
- jd: text Job Description

Backend vrací JSON.

✅ Lokální spuštění

```
pip install -r requirements.txt
streamlit run app.py
```

✅ Struktura projektu

cv-matcher-ui/
 ├── app.py
 ├── requirements.txt
 └── .streamlit/config.toml

✅ Použité technologie

- Streamlit
- Requests
- Pandas
- FastAPI backend
- OpenAI GPT‑4.1

✅ Licenční ujednání

Tento projekt je určen pro interní testování.

✅ Autor

Michael Zelinka – 2026

<img width="432" height="628" alt="image" src="https://github.com/user-attachments/assets/b124137a-c69c-43a2-afd6-782fabbd3df7" />
