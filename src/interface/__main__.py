from flask import Flask, render_template, request
from src.data import metadata_class
from src.data import pdfparse_class
from src.semantic.tfidf import tfidf
app = Flask(__name__)

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
       metadb = metadata_class()
       pdfdb = pdfparse_class()
       list = metadb.subject_filter([result['subject']], int(result['year_start']), int(result['year_end']))
       search_results = pdfdb.search(list, result['keyword'])
       return render_template("search_results.html",results = search_results)


@app.route('/selected',methods = ['POST', 'GET'])
def selected():
    semantictfidf = tfidf()
    similar_papers = []
    if request.method == 'POST':
        #selected_items= request.form.getlist('papers')
        result = request.form.to_dict()
        papers_to_compare = request.form.getlist('papers')
        subject, year_start, year_end = [result['subject']], int(result['year_start']), int(result['year_end'])
        paper_pool_query = {'$and':[{'mag_field_of_study': {'$in': subject}},{'abstract':{'$ne':None}},{'year':{'$gte':year_start, '$lte': year_end} }]}
        print(paper_pool_query)
        #print(selected_items)
        for paper in papers_to_compare:
            similarity_results = semantictfidf.similarity(paper, paper_pool_query)
            print(similarity_results)
            similar_papers += similarity_results
            print(similar_papers)
        return render_template("selected.html", results=similar_papers, papers_to_compare=papers_to_compare)



if __name__ == "__main__":
    print("executing")
    #app.run(debug=True, host='0.0.0.0', port=5000)
    app.run(port=5000)
