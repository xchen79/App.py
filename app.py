from flask import Flask, render_template, request, redirect, url_for

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
    return render_template("subpage1.html")
@app.route("/subpage1/<int:entry_id>")
def display(entry_id):
    entry = next((entry for entry in entries if entry["id"] == entry_id), None)
    if not entry:
        return "Entry not found", 404
    return render_template("view_entry.html", entry=entry)

@app.route("/subpage2")
def subpage2():
    return render_template("subpage2.html")

@app.route("/subpage3")
def subpage3():
    return render_template("subpage3.html")

if __name__ == "__main__":
    app.run(debug=True)
