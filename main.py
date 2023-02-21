from flask import render_template, request, jsonify

from app import *
from db import *

RESULTSPERPAGE = 24

@app.route("/")
def r_index():
	positive = []
	negative = []
	q = request.args.get("q")
	p = int(request.args.get("p", 0))

	if q:
		for word in q.split(","):
			if word.startswith("-"):
				negative.append(word[1:])
			else:
				positive.append(word)
	tags, results = search_all_tags(positive, negative)
	numresults = len(results)
	results = results[p*RESULTSPERPAGE:(p+1)*RESULTSPERPAGE]
	return render_template("index.html", tags=tags, results=results, numresults=numresults, page=p, query=positive+["-"+q for q in negative], RESULTSPERPAGE=RESULTSPERPAGE)

@app.route("/i/<path:path>")
def r_dirimg(path):
    return render_template("image.html", metadata=load_metadata(path))

@app.route("/save", methods=["POST"])
def r_save():

    data = request.json["data"]

    code = save_json(data)

    return jsonify({"code": code})

@app.route("/update", methods=["POST"])
def r_update():

    metadata = request.json["metadata"]

    update_metadata(metadata)

    return jsonify({"metadata": metadata})

wc(update_db)

if __name__ == "__main__":
    app.run("localhost", 1337, debug=True)
