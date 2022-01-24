from flask import Flask, render_template, request
from data import dbAccess
app = Flask(__name__)
db = dbAccess()

@app.route('/search_form')
def search_form():
    """
    Simple form that collects the parameters for finding equivalent documents.
    The variables are defined in the search_form.html.
    Variable name is defines using name = XYZ
    :return:
    """
    return render_template('search_form.html')

@app.route('/search_results',methods = ['POST', 'GET'])
def search_results():
    """
    On submission of the form on /search_form, the variables are submitted to create an instance of

    Which can then be passed on to the  function which provides the
    :return: Displays the variables in an html page
    """
    if request.method == 'POST':
       result = request.form.to_dict()
       list = db.subject_filter([result['subject']])
       search_results = db.search(list,result['keyword'])
       return render_template("search_results.html",results = search_results)


@app.route('/selected',methods = ['POST', 'GET'])
def selected():
    if request.method == 'POST':
        selected_items= request.form.getlist('papers')
        return render_template("selected.html", results=selected_items)


if __name__ == "__main__":
    app.run(debug=True)