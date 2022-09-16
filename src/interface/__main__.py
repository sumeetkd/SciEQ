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


@app.route('/search_results', methods=['POST', 'GET'])
def search_results():
    """
    Search results generated are displayed by this route.
    Page displays the results and also allows to choose papers for semantic comparison.
    Submission of the form calls the route '/semantic_progressbar'
    """
    return render_template("search_results.html", results=pdfdb.search_results())


class similarlity_evaluation():
    """
    Contains the connections between the database and the tfidf batch evaluator class

    Should initialize tfidf to preserve the counts variables

    """

    def __init__(self, paper_list = [], filter_dict = {}):
        self.paper_list = paper_list
        self.filter_dict = filter_dict

    # TODO: Move to separate class in the semantic folder
    # TODO: Combine the paper_list_update and filter_dict_update into one function

    def paper_list_update(self, paper_list):
        """Create individual similarity calculators from the list of papers

        :param paper_list: List of papers obtained from :py:func:semantic_progressbar

        Set the list of papers to be evaluated by :py:class:similarlity_evaluation.
        Creates a new connection to the metadata db to handle all filtering and abstract requests.
        Create a list of instances of :py:class:tfidf to handle evaluation for each paper.
        """

        # Reinitialized when a new list of papers is submitted
        self.metadb = metadata_class()
        self.paper_list = paper_list
        # Reinitialize the evaluator instances for the new form
        self.evaluator_instances = []
        # Create instances of the similarity calculator class to allow separate namespace for each paper
        for paper_id in paper_list:
            self.evaluator_instances.append(tfidf(
                                paper_id,
                                self.metadb.provide_abstract(paper_id))
                                            )

    def repr_paper_list(self):
        return self.paper_list

    def filter_dict_update(self, filter_dict):
        """Update the :py:class:metadata_class with the filters chosen

        :param filter_dict: Filters in the form of a dictionary

        Allows one to change the filter after a refresh of the page
        """

        self.filter_dict = filter_dict
        self.metadb.param_update(self.filter_dict)

    def evaluator(self, batchsize):
        """Processing the database for all the papers selected for evaluation

        :param batchsize: Batchsize for evaluation of the database

        The :py:meth:evaluator loops through the papers and then calls the function by calling evaluator_instances from the list which in turn are supplied the :py:meth:filtered_batch_generator  
        """
        # Define the count which goes from 0 to the number of papers chosen
        count = -1
        # Loop through the list of papers
        for evaluator in self.evaluator_instances:
            count += 1
            # Evaluation of the 
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
    """Route accepts a form to initiate semantic comparison and displays its progress.

    :param request.form.getlist('papers'): List of papers to be analyzed
    :param request.form.to_dict()['subject']: Limiting the subject of the database
    :param request.form.to_dict()['year_end']: Limiting the latest year of publication
    :param request.form.to_dict()['year_start']: Limiting the earliest year of publication

    Obtains the above parameters from the form submitted in `/search_results` and initiates the semantic evaluation.
    Renders the template that displays 'N' progress bars that shows the percentage of the database remaining.

    """
    if request.method == 'POST':
        #print(request.form)

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

        # TODO: Combine the paper_list_update, batchsize and filter_dict_update into one function

    # Pass number of papers to build X number of progress bars
    return render_template(
                    "semantic_progressbar.html",
                    num_bars=len(papers_to_compare))


@app.route('/semantic_progress', methods=['GET', 'POST'])
def semantic_progress():
    """Route to get the status of the evaluation

    Start the database processing using :py:method:evaluator which yields the progress on the database through a Flask Response
    # TODO move batchsize into a variable that can be set by webpage
    """
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
