# ORYX Standalone Migration

Use this procedure to split ORYX into its own operational company repository.

## 1) Extract ORYX Files
Run from the Project VOID root:

```bash
bash .oryx/scripts/extract_oryx.sh ../oryx-standalone
```

## 2) Initialize Standalone Repository
```bash
cd ../oryx-standalone
git init
git add .
git commit -m "Initial ORYX standalone import"
```

## 3) Wire Runtime
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 4) Open Creator Editor
- Backend API: http://127.0.0.1:5000
- Editor UI: http://127.0.0.1:5000/editor

## 5) Keep Optional Link to Project VOID
- Keep integration mode as optional in world creation.
- Add explicit import/export adapters later if cross-system sync is needed.