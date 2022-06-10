from flask import Flask, render_template, request
from src.data import dbAccess
from src.semantic.tfidf import tfidf
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
       list = db.subject_filter([result['subject']], int(result['year_start']), int(result['year_end']))
       search_results = db.search(list, result['keyword'])
       return render_template("search_results.html",results = search_results)


@app.route('/selected',methods = ['POST', 'GET'])
def selected():
    semantictfidf = tfidf()
    if request.method == 'POST':
        selected_items= request.form.getlist('papers')
        year_start = 1951
        year_end = 1960
        findterms = {'$and':[{'mag_field_of_study': {'$in': ['Physics']}},{'abstract':{'$ne':None}},{'year':{'$gte':year_start, '$lte': year_end} }]}
        #print(selected_items)
        similarity_results = semantictfidf.similarity(selected_items, findterms)
        return render_template("selected.html", results=similarity_results)



if __name__ == "__main__":
    print("executing")
    #app.run(debug=True, host='0.0.0.0', port=5000)
    app.run(port=5000)
