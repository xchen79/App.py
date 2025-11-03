import os
import re
import csv
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g, send_file, redirect, url_for
import requests
import openai
app = Flask(__name__)
journal_entries = []
next_id = 1

OPENAI_API_Key = os.environ.get("OpenAI_API_Key")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # change if you want
if not OPENAI_API_Key:
    raise RuntimeError("Set the OPENAI_API_KEY environment variable.")
openai.api_key = OPENAI_API_Key

DATABASE = os.path.join(os.path.dirname(__file__), "chat.db")

app = Flask(__name__, static_folder="static", template_folder="templates")

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Run once at startup
init_db()
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def insert_message(username, role, content):
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (username, role, content) VALUES (?, ?, ?)",
        (username, role, content)
    )
    conn.commit()
    conn.close()

def fetch_recent_for_user(username, limit=20):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM messages WHERE username=? ORDER BY id DESC LIMIT ?",
        (username, limit),
    )
    rows = cur.fetchall()
    # return oldest-first
    return list(reversed([dict(r) for r in rows]))

# --- OpenAI call and parsing metadata ---
def call_openai_and_extract_metadata(username, user_message, mock=False):
    if mock:
        reply = (
            f"Nice observation — keep focusing on your stance and contact point. You're doing well, {username}! "
            "Try taking a slightly wider base on your forehand and keep the racquet head steady.\n\n"
            '{"labels":["forehand_stance","contact_point"], "confidence":0.73, "sentiment":"encouraging"}'
        )
        return reply, {"labels": ["forehand_stance", "contact_point"], "confidence": 0.73, "sentiment": "encouraging"}
    system_prompt = (
        "You are a supportive tennis coach and mental-performance assistant. "
        "Keep language explicitly encouraging, brief actionable tips, and focus on tennis technique and mindset. "
        "Do NOT give medical or legal advice. If the user expresses self-harm or severe distress, "
        "acknowledge and provide crisis resources (but do NOT attempt clinical therapy). "
        "After your natural-language reply, append a JSON object on its own line (in triple-backticks or raw) containing "
        "the metadata with keys: labels (list of short tags for technique/sentiment), confidence (0-1), sentiment (one word). "
        "Example at the end: {\"labels\": [\"forehand_contact\"], \"confidence\": 0.81, \"sentiment\":\"encouraging\"} "
        "This JSON must be the last content in the assistant message."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=messages,
        max_tokens=350,
        temperature=0.7,
    )

    assistant_text = resp["choices"][0]["message"]["content"].strip()

    # Try to find trailing JSON block
    metadata = None
    # look for JSON at the end of the assistant_text
    json_match = re.search(r'({\s*"labels"[\s\S]*})\s*$', assistant_text)
    if not json_match:
        # try code block style
        json_match = re.search(r'```(?:json)?\s*({[\s\S]*})\s*```', assistant_text, re.IGNORECASE)

    if json_match:
        json_text = json_match.group(1)
        try:
            metadata = json.loads(json_text)
            # remove the JSON block from the reply text
            assistant_text = assistant_text[: json_match.start()].strip()
        except json.JSONDecodeError:
            metadata = None

    return assistant_text, metadata

@app.route("/")
def home():
    tiles = [
        {"title": "Journal", "url": "/subpage1"},
        {"title": "Videos", "url": "/subpage2"},
        {"title": "Video Analysis", "url": "/subpage3"},
        {"title": "Chat with Coach", "url": "/chat"},
    ]
    return render_template("index.html", tiles=tiles)

@app.route("/subpage1", methods=["GET", "POST"])
def subpage1():
    global next_id
    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")
        if title and body:
            journal_entries.append({"id": next_id, "title": title, "body": body})
            next_id += 1
        return redirect(url_for("subpage1.html"))
    return render_template("subpage1.html", entries=journal_entries)
@app.route("/subpage1/<int:entry_id>")
def display(entry_id):
    entry = next((e for e in journal_entries if e["id"] == entry_id), None)
    if not entry:
        return "Entry not found", 404
    return render_template("view_entry.html", entry=entry)

@app.route("/subpage2", methods=["GET", "POST"])
def subpage2():
    search_query = request.form.get("search") if request.method == "POST" else None
    category = request.form.get("category") if request.method == "POST" else "instructional"
    
    videos = []
    if search_query:
        YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyCI4vZ7LJOVUyb7yzQNHaJAs9MiBHL5qs0")
        search_term = f"{search_query} tennis"
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": search_term,
            "key": YOUTUBE_API_KEY,
            "maxResults": 15,
            "type": "video",
            "videoCategoryId": "17",
            "publishedAfter": "2016-01-01T00:00:00Z"
        }
        response = requests.get(search_url, params=params)
        data = response.json()
        for item in data.get("items", []):
            videos.append({
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                "videoId": item["id"]["videoId"]
            })
    return render_template("subpage2.html", videos=videos, category=category)

@app.route("/subpage3")
def subpage3():
    return render_template("subpage3.html")

@app.route("/chat")
def chat_page():
    return render_template("chat.html")
@app.route("/api/chat", methods=["POST"])
def api_chat():
    try:
        data = request.json
        username = data.get("username", "Player")
        user_message = data.get("message", "")

        # Store user message
        insert_message(username=username, role="user", content=user_message)

        # Call OpenAI using new API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an encouraging tennis coach, supportive and positive."},
                {"role": "user", "content": user_message}
            ]
        )

        assistant_text = response.choices[0].message.content.strip()

        # Store assistant message
        insert_message(username=username, role="assistant", content=assistant_text)

        return jsonify({
            "ok": True,
            "reply": assistant_text,
            "metadata": {"encouragement": True}
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
if __name__ == "__main__":
    app.run(debug=True)
