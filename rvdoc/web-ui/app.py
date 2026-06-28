"""
Simple Flask web UI for RVDoc

Provides the same functionality as the terminal version but accessible
via a web browser.  Run with:
    python -m flask run
or simply:
    python app.py

The app stores the PDI inspection results in the user session and
writes the final report to the same `reports/` directory as the CLI.
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
# A secret key is required for the session – in a real deployment you would
# generate a strong random value.  For local use a static key is fine.
app.secret_key = "rvdoc-secret-key"

# ---------------------------------------------------------------------------
# Helper – ensure the reports folder exists
# ---------------------------------------------------------------------------
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Data structures – mirrors the CLI version
# ---------------------------------------------------------------------------
CATEGORIES = [
    "⚙️ Landing Gear",
    "⚡ Electrical",
    "↔️ Slide-Outs",
    "❄️ Air Conditioning — Dometic, Coleman, Advent Air rooftop units",
    "💧 Plumbing",
    "🔥 Propane/Gas",
    "🔋 Generator",
    "🏕️ Awning",
    "🚿 Water Heater — Suburban, Atwood",
    "🌡️ Furnace — Suburban, Atwood",
    "🔧 Other System",
]

PDI_CHECKLIST = {
    "Exterior": ["Seals & Roof inspect", "Compartment doors & locks", "Running lights & Tires"],
    "Electrical": ["Shore power hookup", "Battery voltage/Converter", "12V and 120V outlets"],
    "Plumbing": ["Water pump operational", "Fresh/Waste tank valves", "Faucets, Toilet, Water Heater"],
    "Appliances": ["Furnace cycling", "Air Conditioning cooling", "Refrigerator & Microwave"],
    "LP System": ["Regulator pressure drop test", "LP Detector functional", "Gas appliances ignite"],
    "Slides & Awnings": ["Slide-out full cycle/seals", "Awning extend/retract & lights"],
    "Chassis/Hitch": ["Landing gear / Jacks / Auto level", "Kingpin/Coupler & safety chains"],
    "Interior": ["All lights & ceiling fans", "Windows, doors, and cabinet latches"],
}

# ---------------------------------------------------------------------------
# Routes – main menu
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# ---------------------------------------------------------------------------
# Diagnostic mode – simple placeholder
# ---------------------------------------------------------------------------
@app.route('/diagnostic', methods=['GET', 'POST'])
def diagnostic():
    if request.method == 'POST':
        # In the CLI version this just echoes a placeholder.  Here we store the
        # chosen category so the page can display a tiny acknowledgement.
        choice = request.form.get('category')
        flash(f"Diagnostic placeholder for {choice} – AI assistance not yet implemented.")
        return redirect(url_for('diagnostic'))
    return render_template('diagnostic.html', categories=CATEGORIES)

# ---------------------------------------------------------------------------
# PDI mode – guided inspection
# ---------------------------------------------------------------------------
@app.route('/pdi', methods=['GET', 'POST'])
def pdi():
    if 'pdi_report' not in session:
        # Initialise an empty report dictionary on first visit
        session['pdi_report'] = {}

    if request.method == 'POST':
        section = request.form['section']
        item = request.form['item']
        status = request.form['status']
        # Normalise the status to the same symbols used in the CLI version
        mapping = {'p': 'PASS ✅', 'f': 'FAIL ❌', 's': 'SKIPPED 🟡'}
        report = session['pdi_report']
        report.setdefault(section, {})[item] = mapping[status]
        session['pdi_report'] = report
        flash(f"Recorded {item}: {mapping[status]}")
        # Stay on the same page so the user can continue the checklist
        return redirect(url_for('pdi'))

    # Determine the next unfinished section/item
    for sec, items in PDI_CHECKLIST.items():
        for itm in items:
            if sec not in session['pdi_report'] or itm not in session['pdi_report'][sec]:
                next_section, next_item = sec, itm
                break
        else:
            continue
        break
    else:
        # All items completed – show summary and allow saving the report
        return redirect(url_for('pdi_summary'))

    return render_template(
        'pdi.html',
        section=next_section,
        item=next_item,
    )

# ---------------------------------------------------------------------------
# PDI summary – show the collected results and write the text file
# ---------------------------------------------------------------------------
@app.route('/pdi/summary', methods=['GET', 'POST'])
def pdi_summary():
    report = session.get('pdi_report', {})
    if request.method == 'POST':
        # Save the report to disk
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"PDI_Report_{timestamp}.txt"
        path = os.path.join(REPORTS_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"=== RVDoc PDI REPORT: {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n\n")
            for sec, results in report.items():
                f.write(f"--- {sec.upper()} ---\n")
                for itm, res in results.items():
                    f.write(f"  {res} : {itm}\n")
                f.write("\n")
        flash(f"Report saved to {path}")
        # Clear the session so a new inspection can start fresh
        session.pop('pdi_report', None)
        return redirect(url_for('index'))
    return render_template('summary.html', report=report)

# ---------------------------------------------------------------------------
# Run the app – `python app.py` works out‑of‑the‑box
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # Flask's built‑in server is fine for local use.
    # Listen on all interfaces so other devices (e.g., your phone) can reach it.
    app.run(host='0.0.0.0', port=5000, debug=True)
