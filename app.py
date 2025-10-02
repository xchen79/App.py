from flask import Flask, render_template, request, redirect, url_for
import os
import requests

app = Flask(__name__)
entries = []
next_id = 1
@app.route("/")
def home():
    tiles = [
        {"title": "Journal", "url": "/subpage1"},
        {"title": "Videos", "url": "/subpage2"},
        {"title": "Video Analysis", "url": "/subpage3"},
    ]
    return render_template("index.html", tiles=tiles)

@app.route("/subpage1", methods=["GET", "POST"])
def subpage1():
    global next_id
    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")
        if title and body:
            entries.append({"id": next_id, "title": title, "body": body})
            next_id += 1
        return redirect(url_for("subpage1.html"))
    return render_template("subpage1.html", entries=entries)
@app.route("/subpage1/<int:entry_id>")
def display(entry_id):
    entry = next((e for e in entries if e["id"] == entry_id), None)
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

if __name__ == "__main__":
    app.run(debug=True)
