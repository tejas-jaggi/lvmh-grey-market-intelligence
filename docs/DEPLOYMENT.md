# Deployment Checklist

Use this checklist to publish the prototype as a portfolio project.

## 1. Create the GitHub Repository

From the project folder:

```powershell
git init
git add .
git commit -m "Initial LVMH grey market intelligence prototype"
```

Then create a new GitHub repository named:

```text
lvmh-grey-market-intelligence
```

Connect your local repo to GitHub:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/lvmh-grey-market-intelligence.git
git push -u origin main
```

Before pushing, confirm these files are not staged:

```powershell
git status --short
```

The `.gitignore` should keep local files such as `.venv`, `.tmp`, `.deps`, logs, and SQLite databases out of GitHub.

## 2. Deploy on Render

1. Go to `https://render.com`.
2. Sign in with GitHub.
3. Click `New`.
4. Choose `Blueprint`.
5. Select the `lvmh-grey-market-intelligence` repository.
6. Render should detect `render.yaml`.
7. Confirm the service name: `lvmh-grey-market-intelligence`.
8. Confirm the instance type is `Free`.
9. Click `Apply` or `Create Web Service`.

Render will use:

```text
Build Command: pip install -r requirements.txt -r requirements-deploy.txt
Start Command: gunicorn app:app --bind 0.0.0.0:$PORT
Python: 3.12.7
```

Optional eBay live connector environment variables:

```text
EBAY_CLIENT_ID
EBAY_CLIENT_SECRET
EBAY_MARKETPLACE_ID=EBAY_US
EBAY_ENV=production
```

If the eBay variables are not set, the app keeps the Marketplace Monitor import workflow available through the bundled fixture dataset.

## 3. Smoke Test the Live App

After Render finishes deployment, open the public URL and test:

```text
https://lvmh-grey-market-intelligence.onrender.com
/
/listings
/distributors
/analytics
/api/health
```

Click `Run Scan` on the dashboard and confirm the scan panel updates.
Open Marketplace Monitor, click `eBay Import`, and confirm the table refreshes with eBay-sourced rows. Without eBay credentials this should run in fixture mode.

Current live URL:

```text
https://lvmh-grey-market-intelligence.onrender.com
```

## 4. Add the Link to Your Portfolio

Use this description:

```text
AI-assisted grey market intelligence prototype for luxury brand protection. Built with Flask, SQLAlchemy, scikit-learn, Chart.js, and D3. Includes listing anomaly scoring, distributor risk scoring, evidence trails, seller network detection, eBay listing ingestion, and allocation scenario modeling.
```

Suggested LinkedIn/GitHub headline:

```text
Built an explainable AI prototype for luxury grey-market diversion intelligence.
```

## 5. Render Free Tier Notes

Free Render web services can spin down after inactivity, so the first request may take around a minute to load. The local SQLite database is also ephemeral on redeploy/restart. This prototype handles that by reseeding synthetic demo data automatically when the database is missing.
