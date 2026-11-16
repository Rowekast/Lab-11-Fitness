# IT2025C Week 11 - Week 10's app, ready to go online: a landing page you make yours, and the key in .env.
# Run:    python3 app.py      then open http://127.0.0.1:5001
# Needs:  python3 -m pip install -r requirements.txt
# The whole app is in this one file. Your pictures go in the public/ folder.

import io
import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template_string, request, jsonify

# ---------- 1. Settings ----------
load_dotenv()                                              # reads .env from this folder, if it exists
key = os.environ.get("BEARCAT_KEY", "")                    # new: the key lives in .env, not in this file

url = "https://apim-azr-ue2-bgpt-prd-ucin.azure-api.net/openai/deployments/gpt-5.4-ptu/chat/completions?api-version=2024-10-21"
instructions = (
    "You are FitBalance, a general fitness-planning assistant. Use the recent exercise history and goal "
    "provided by the user to suggest practical activities that complement what they have already done. "
    "Consider strength, cardio, mobility or flexibility, and recovery as relevant; point out what may be "
    "underrepresented and suggest a simple next session. Keep suggestions adjustable to the user's ability "
    "and avoid assuming their health status. Do not diagnose or treat medical conditions. If the history is "
    "too vague to make a useful suggestion, ask for more detail. Remind the user to stop if they feel pain "
    "and consult a qualified professional for medical concerns."
)


# ---------- 2. Read: any file -> text (Week 9) ----------
def read_any(filename, data):
    """data is the raw bytes of the file. Return the text inside it."""
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))       # treat the bytes as a file
        text = ""
        for page in reader.pages:
            text = text + page.extract_text() + "\n"
        return text
    if name.endswith(".docx"):
        import docx
        document = docx.Document(io.BytesIO(data))
        text = ""
        for paragraph in document.paragraphs:
            text = text + paragraph.text + "\n"
        return text
    return data.decode("utf-8", errors="replace")  # .txt .csv .md: the bytes already are text


# ---------- 3. Ask: send the exercise history and goal to GPT-5.4 (Week 10) ----------
def ask_files(file_texts, prompt):
    """Send the submitted exercise history and request to the model."""
    if key in ("", "PASTE-YOUR-KEY-HERE"):                # new: no key in .env, so say so instead of calling the model
        return "No key found. Copy .env.example to .env and put your key after BEARCAT_KEY="
    context = ""
    for name, text in file_texts:
        context = context + "File: " + name + "\n" + text + "\n\n"
    payload = {
        "model": "gpt-5.4-ptu",
        "messages": [{"role": "system", "content": instructions}, {"role": "user", "content": "Recent exercise history:\n" + context + "Request: " + prompt}],
        "max_completion_tokens": 2000
    }
    response = requests.post(url, headers={"api-key": key}, json=payload)
    data = response.json() if "json" in response.headers.get("Content-Type", "") else {}   # some errors are not JSON
    if "choices" not in data:
        return "The API said no (status " + str(response.status_code) + "): " + (str(data) if data else response.text[:300])
    return data["choices"][0]["message"]["content"]


# ---------- 4. The web app: three pages and a health check ----------
app = Flask(__name__, static_folder="public", static_url_path="")   # files in public/ are served from the site root


@app.route("/")
def home():
    return render_template_string(LANDING_PAGE)            # new: the first page people see


@app.route("/start")
def start():
    return render_template_string(INDEX_PAGE)              # the form (it was at / in Week 10)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "message": "FitBalance is running."})


@app.route("/about")
def about():
    return render_template_string(ABOUT_PAGE)


@app.route("/ask", methods=["POST"])
def ask():
    workout_history = request.form.get("workout_history", "").strip()
    focus = request.form.get("focus", "").strip()
    prompt = "Suggest a balanced next workout that complements this recent activity."
    if workout_history == "":
        return render_template_string(RESULT_PAGE, files=[], prompt=prompt,
                                      answer="Describe some exercises you have done recently first.")
    if focus:
        prompt += " Take this goal or preference into account: " + focus
    file_texts = [("Recent exercise history", workout_history)]
    answer = ask_files(file_texts, prompt)
    return render_template_string(RESULT_PAGE, files=["Recent exercise history"], prompt=prompt, answer=answer)


# ---------- 5. The pages: how they look (STYLE) and what they say ----------
# Change STYLE or a page, save, and refresh the browser.
# Asking BearcatGPT for help? Paste this part. Your key is in .env, not here.

STYLE = """
:root {
  --brand: #176b5b;
  --page: #f3f6f1;
  --text: #182b28;
  --muted: #5c706b;
  --accent: #dce99a;
}

* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", Arial, sans-serif;
  color: var(--text);
  background: var(--page);
  max-width: 1060px;
  margin: 0 auto;
  padding: 0 24px 48px;
  line-height: 1.6;
}
.nav {
  display: flex;
  gap: 24px;
  padding: 18px 0;
  font-size: 15px;
  font-weight: 700;
}
.nav a { color: var(--brand); text-decoration: none; }
.nav a:hover { text-decoration: underline; }
.header {
  background: var(--brand);
  color: white;
  padding: 28px 32px;
  border-radius: 18px;
  margin-bottom: 24px;
}
.header h1 { margin: 0 0 4px; line-height: 1.2; }
.header p { margin: 0; }
.card {
  background: white;
  border: 1px solid #e2e9e3;
  border-radius: 16px;
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(24, 43, 40, 0.06);
}
.steps { display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }
.step {
  flex: 1;
  min-width: 180px;
  background: #f3f6f1;
  border: 1px solid #e6ece4;
  border-radius: 12px;
  padding: 16px 18px;
}
label { display: block; font-weight: 700; margin: 12px 0 6px; }
input, textarea {
  width: 100%;
  border: 1px solid #bdcbc4;
  border-radius: 8px;
  font: inherit;
  padding: 10px 12px;
}
input:focus, textarea:focus { outline: 3px solid #dce99a; border-color: var(--brand); }
button, .button {
  display: inline-block;
  margin-top: 16px;
  background: var(--brand);
  color: white;
  border: none;
  border-radius: 9px;
  padding: 12px 20px;
  font: inherit;
  font-weight: 700;
  text-decoration: none;
}
button:hover, .button:hover { background: #105649; }
.answer { font-size: 18px; white-space: pre-wrap; border-left: 6px solid var(--brand); }
.note { color: var(--muted); font-size: 14px; }
.landing-hero {
  display: grid;
  grid-template-columns: 1fr 1.08fr;
  align-items: center;
  gap: 28px;
  padding: 24px 0 32px;
}
.hero-copy { padding: 12px 4px; }
.eyebrow {
  display: inline-block;
  color: var(--brand);
  background: #e6edd0;
  border-radius: 99px;
  padding: 5px 12px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.hero-copy h1 {
  max-width: 520px;
  margin: 16px 0;
  font-size: clamp(38px, 5vw, 58px);
  letter-spacing: -0.04em;
  line-height: 1.06;
}
.hero-copy p { max-width: 480px; color: var(--muted); font-size: 18px; }
.hero { width: 100%; border-radius: 18px; display: block; }
.section-title { margin: 0; font-size: 28px; letter-spacing: -0.02em; }
.step-number {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  margin-bottom: 10px;
  border-radius: 50%;
  color: var(--brand);
  background: var(--accent);
  font-weight: 800;
}
.step h3 { margin: 0 0 4px; }
.step p { margin: 0; color: var(--muted); }
.about-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.about-grid .card { margin-bottom: 0; }
@media (max-width: 720px) {
  body { padding: 0 16px 32px; }
  .nav { gap: 18px; flex-wrap: wrap; }
  .landing-hero { grid-template-columns: 1fr; gap: 16px; padding-top: 12px; }
  .hero-copy { padding: 8px 0; }
  .header { padding: 22px 20px; }
  .card { padding: 20px; }
  .steps, .about-grid { display: grid; grid-template-columns: 1fr; }
  .step { min-width: 0; }
  button, .button { display: block; width: 100%; text-align: center; }
}
"""

# The landing page: what the app is, who it is for, and one button to start.
LANDING_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FitBalance | Your Next Workout</title>
    <style>""" + STYLE + """</style>
  </head>
  <body>
    <nav class="nav"><a href="/">Home</a><a href="/start">Plan a workout</a><a href="/about">About</a></nav>
    <main>
      <section class="landing-hero">
        <div class="hero-copy">
          <span class="eyebrow">Your workout, in context</span>
          <h1>Make your next move a balanced one.</h1>
          <p>Log what you have been doing and get general ideas for a next workout that complements your recent activity.</p>
          <a class="button" href="/start">Plan my next workout</a>
        </div>
        <img class="hero" src="/fitness-hero.svg" alt="Illustration of a person strength training beside a balanced activity chart">
      </section>
    <div class="card">
      <h2 class="section-title">A simple way to think about your routine</h2>
      <p>FitBalance is for anyone looking for practical workout ideas that complement their recent exercise. It uses the history and optional focus you provide; it does not track activity for you.</p>
      <div class="steps">
        <div class="step"><span class="step-number">1</span><h3>Log</h3><p>Describe a few recent workouts.</p></div>
        <div class="step"><span class="step-number">2</span><h3>Add a focus</h3><p>Share a goal or preference, if you have one.</p></div>
        <div class="step"><span class="step-number">3</span><h3>Get ideas</h3><p>Review suggestions for a complementary next session.</p></div>
      </div>
    </div>
      <p class="note">General fitness ideas only, not medical advice. Adjust activities to your ability. <a href="/about">Learn about FitBalance and its limits.</a></p>
    </main>
  </body>
</html>"""

# The form. The button changes while the model reviews the exercise history.
INDEX_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Log Your Recent Exercise | FitBalance</title>
    <style>""" + STYLE + """</style>
  </head>
  <body>
    <nav class="nav"><a href="/">Home</a><a href="/start">Plan a workout</a><a href="/about">About</a></nav>
    <header class="header">
      <h1>Your Recent Exercise</h1>
      <p>Tell FitBalance what you have done lately to get ideas for a balanced next session.</p>
    </header>
    <form class="card" action="/ask" method="post"
          onsubmit="this.querySelector('button').textContent = 'Building your suggestions...';">
      <label for="workout_history">What exercises have you done recently?</label>
      <textarea id="workout_history" name="workout_history" rows="5" required
                placeholder="For example: Monday, 30-minute jog; Tuesday, upper-body weights; Wednesday, rest."></textarea>
      <label for="focus">Any goal or preference? (optional)</label>
      <input type="text" id="focus" name="focus" placeholder="For example: improve cardio or keep it low impact">
      <button type="submit">Suggest my next workout</button>
    </form>
    <p class="note">Share only what you are comfortable sending to the AI. General fitness ideas only, not medical advice. Stop if you feel pain.</p>
  </body>
</html>"""

# The answer page. {{ name }} prints a value from Python.
RESULT_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Your FitBalance Suggestions</title>
    <style>""" + STYLE + """</style>
  </head>
  <body>
    <nav class="nav"><a href="/">Home</a><a href="/start">Plan a workout</a><a href="/about">About</a></nav>
    <header class="header">
      <h1>Your FitBalance Suggestions</h1>
      <p><strong>Based on:</strong> {{ files|join(", ") }} &middot; <strong>Request:</strong> {{ prompt }}</p>
    </header>
    <div class="card answer">{{ answer }}</div>
    <a class="button" href="/start">Plan another workout</a>
  </body>
</html>"""

# Information about FitBalance and its limitations.
ABOUT_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>About FitBalance</title>
    <style>""" + STYLE + """</style>
  </head>
  <body>
    <nav class="nav"><a href="/">Home</a><a href="/start">Plan a workout</a><a href="/about">About</a></nav>
    <header class="header">
      <h1>About FitBalance</h1>
      <p>A workout-log helper for thinking about a balanced next session.</p>
    </header>
    <div class="about-grid">
      <section class="card">
        <h2>What it does</h2>
        <p>FitBalance uses the recent exercise history and optional goal or preference you enter to ask an AI model for general ideas that complement your activity.</p>
      </section>
      <section class="card">
        <h2>What it cannot do</h2>
        <p>It does not connect to a fitness tracker, keep a workout log, or know your health history. AI suggestions can be inaccurate and are not medical advice or a substitute for a qualified professional.</p>
      </section>
    </div>
    <p class="note">Only share exercise details you are comfortable sending to the AI service. Stop if an activity causes pain.</p>
    <a class="button" href="/start">Plan a workout</a>
  </body>
</html>"""


if __name__ == "__main__":
    app.run(debug=True, port=5001)   # 5001, not 5000: on a Mac, AirPlay already uses 5000


# ---------- 6. Notes ----------
# The key: copy .env.example to .env (Windows: copy .env.example .env), then put your key after BEARCAT_KEY=
#   .gitignore keeps .env out of Git and GitHub. Check with: git status
#
# Make it yours, on the landing page:
#   --brand in STYLE (your color), the <title> and <h1> (your app's name), the sentence under it,
#   the picture (put yours in public/ and change its src), "Who it is for", and the three steps.
#
# Stuck?
#   No module named ...          -> python3 -m pip install -r requirements.txt
#   No key found                 -> .env missing, still the placeholder, or not named BEARCAT_KEY; fix it, then Control+C and run python3 app.py again
#   The API said no (413, 500, or 504) -> check the service status and try a shorter exercise history
#   The picture does not show    -> is it in public/? Does src="/your-file.png" match the name exactly, capitals too?
#   Address already in use       -> another app (Week 10?) is still running: press Control+C in its terminal
#   Page looks the same after a change -> save app.py; Flask restarts by itself; then Cmd+Shift+R (Windows: Ctrl+F5)
#   Windows: use py instead of python3.
