from flask import Flask, render_template, request, Response
from src.data import metadata_class
from src.data import pdfparse_class
from src.semantic.tfidf import tfidf
import json
app = Flask(__name__)

pdfdb = pdfparse_class()
metadb = metadata_class()

@app.route('/search_form')
def search_form():
    """
    Simple form that collects the parameters for finding equivalent documents.
    The variables are defined in the search_form.html.
    Variable name is defines using name = XYZ
    :return:
    """
    return render_template('search_form.html')


@app.route('/search_progressbar', methods = ['GET', 'POST'])
def search_progressbar():
    """
    On submission of the form on /search_form, the variables are submitted to create an instance of

    Which can then be passed on to the  function which provides the
    :return: Displays the variables in an html page
    """
    if request.method == 'POST':
       result = request.form.to_dict()
       metadb = metadata_class()
       paperlist = metadb.subject_filter([result['subject']], int(result['year_start']), int(result['year_end']))
       pdfdb.search_params(paperlist,result['keyword'])
    return render_template("search_progressbar.html")


@app.route('/search_progress', methods = ['GET', 'POST'])
def search_progress():
    return Response(pdfdb.search(), mimetype='text/event-stream')


@app.route('/search_results',methods = ['POST', 'GET'])
def search_results():
    return render_template("search_results.html",results = pdfdb.search_results())


class similarlity_evaluation():
    """
    Contains the connections between the database and the tfidf batch evaluator class

    Should initialize tfidf to preserve the counts variables
    TODO: Move to separate class in the semantic folder
    """

    def __init__(self, paper_list = [], filter_dict = {}):
        self.paper_list = paper_list
        self.filter_dict = filter_dict
        self.evaluator_instances = []
        # Moving to help solve repeat evaluation issue
        # self.metadb = metadata_class()

    def paper_list_update(self, paper_list):
        # Moved here to help with repeat evaluation
        self.metadb = metadata_class()
        self.paper_list = paper_list
        # To prevent adding of instances to the old list
        self.evaluator_instances = []
        for paper_id in paper_list:
            self.evaluator_instances.append(tfidf(
                                paper_id,
                                self.metadb.provide_abstract(paper_id))
                                            )

    def repr_paper_list(self):
        return self.paper_list

    def filter_dict_update(self, filter_dict):
        self.filter_dict = filter_dict
        self.metadb.param_update(self.filter_dict)

    def evaluator(self, batchsize):
        """
        TODO: Not sure if the yielding will work
        """
        # Define the count which goes from 0 to the number of papers chosen
        count = -1
        # Loop through the list of papers
        for evaluator in self.evaluator_instances:
            # super().__init__()
            count += 1
            # self.set_paper(paper_id, metadb.provide_abstract(paper_id))
            for state in evaluator.process_data(
                    self.metadb.filtered_batch_generator(batchsize)):
                print("State : {}".format(state))
                print("Total : {}".format(self.metadb.repr_total_count()))
                stream_dict = {
                    'bar': count,
                    'progress': (state /
                                 (self.metadb.repr_total_count() // batchsize + 1))*100
                                }
                print(stream_dict)
                yield "data:" + json.dumps(stream_dict) + "\n\n"

    def nearestneighbours(self):
        similar_papers = []
        for evaluator in self.evaluator_instances:
            similar_papers += evaluator.tfidf_nn()
            print(similar_papers)
        return self.metadb.displayorderedlist(similar_papers)
        #return self.metadb.displayresults(similar_papers)


simeval = similarlity_evaluation()


@app.route('/semantic_progressbar', methods=['GET', 'POST'])
def semantic_progressbar():
    """
    Route creates an intermediate page displaying the progress of evaluation for Semantic results.
    The page '/search_results' provides 'papers_to_compare' and parameters needed to define the subset of papers that will be compared to the papers.
    """
    if request.method == 'POST':
        print(request.form)

        # Passing the list of papers to evaluator
        papers_to_compare = request.form.getlist('papers')
        simeval.paper_list_update(papers_to_compare)

        # Parsing paramters to filter database for semantic evaluation and feeding them to evaluator
        # Might be redundant output and check if result can be directly passed
        result = request.form.to_dict()
        # print(result)
        subject, year_start, year_end = [result['subject']], int(result['year_start']), int(result['year_end'])
        filter_dict = {
            'subject': subject,
            'year_start': year_start,
            'year_end': year_end
        }
        # simeval.filter_dict_update(result)
        simeval.filter_dict_update(filter_dict)

    # Pass number of papers to build X number of progress bars
    return render_template(
                    "semantic_progressbar.html",
                    num_bars=len(papers_to_compare))


@app.route('/semantic_progress', methods=['GET', 'POST'])
def semantic_progress():
    return Response(simeval.evaluator(100), mimetype='text/event-stream')


@app.route('/semantic_results', methods=['POST', 'GET'])
def semantic_results():
    return render_template("semantic_results.html",
                           results=simeval.nearestneighbours(),
                           papers_to_compare=simeval.repr_paper_list())


@app.route('/selected', methods=['POST', 'GET'])
def selected():
    semantictfidf = tfidf()
    similar_papers = []
    if request.method == 'POST':
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
        return render_template("tfidf_results.html", results=similar_papers, papers_to_compare=papers_to_compare)



if __name__ == "__main__":
    print("executing")
    #app.run(debug=True, host='0.0.0.0', port=5000)
    app.run(port=5000)
