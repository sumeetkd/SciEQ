import pymongo
import re
# Connect to a database using keyword
# Provide sections of a database when specifying paperid
# Have a search function

class metadatadb:

    def __enter__(self):
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.mydb = self.myclient["mydatabase"]
        self.metadata = self.mydb["metadata"]
        return self.metadata

    def __exit__(self, type, value, traceback):
        self.myclient.close()

class pdfparsedb:

    def __enter__(self):
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.mydb = self.myclient["mydatabase"]
        self.pdfparse = self.mydb["pdf_parses"]
        return self.pdfparse

    def __exit__(self, type, value, traceback):
        self.myclient.close()


class metadata_class:

    def __init__(self, subjectlist=['Physics'], year_start=2019, year_end=2020):
        """
        Defining default values for the parameters
        """
        self.subjectlist = subjectlist
        self.year_start = year_start
        self.year_end = year_end
        self.filtered_size = 0
        self.batchsize = 100
        # Moving paper_ids to allow them to change only during param_update
        # self.paper_ids = []

    def param_update(self, filter_dict):
        """Initializing the filter

        :param filter_dict: Consists of :py:data:subject, :py:data:year_start and :py:data:year_end
        
        Run :py:meth:__filtered_data to populate :py:attr:self.paper_ids necessary for limiting database for other methods.
        """

        self.subjectlist = filter_dict['subject']
        self.year_start = filter_dict['year_start']
        self.year_end = filter_dict['year_end']
        # Run the filtering and extract relevant paper_ids as soon as parameters are set
        self.__filtered_data()

    def batchsize_update(self, batchsize):
        self.batchsize = batchsize

    def repr_total_count(self):
        return self.filtered_size

    def __query(self):
        query = {
            '$and': [
                {'mag_field_of_study': {'$in': self.subjectlist}},
                {'abstract': {'$ne': None}},
                {'year': {'$gte': self.year_start, '$lte': self.year_end}}
            ]
        }
        return query

    def subject_filter(self, subjectlist, year_start, year_end):
        paper_ids = []
        # query = {'mag_field_of_study': {'$in': subjectlist}, }
        query = {
            '$and': [
                {'mag_field_of_study': {'$in': subjectlist}},
                {'year': {'$gte': year_start, '$lte': year_end}}
            ]
        }
        with metadatadb() as metadb:
            filtered = metadb.find(query, {'_id': 0, 'paper_id': 1})
            for item in filtered:
                paper_ids.append(item['paper_id'])
        return paper_ids

    def __filtered_data(self):
        """Updating :py:attr:paper_ids which is used to limit the db

        Also sets the :py:attr:filtered_size useful for calculating state of calculation
        """
        # Moved to prevent appending to previous semantic session
        self.paper_ids = []
        query = self.__query()
        # Search through the db using the query and add the paper_id to a list
        with metadatadb() as metadb:
            filtered = metadb.find(query, {'_id': 0, 'paper_id': 1})
            for item in filtered:
                self.paper_ids.append(item['paper_id'])
        # Also set the total size of the db to allow for calculation of batch size
        self.filtered_size = len(self.paper_ids)

    # def provide_abstract(self, paperlist):
    #     with metadatadb() as metadb:
    #         metadata_selected = metadb.find({'paper_id': {'$in': paperlist}, {'abstract': 1 })
    #         yield metadata_selected['abstract']

    def provide_abstract(self, paper_id):
        with metadatadb() as metadb:
            metadata_selected = metadb.find_one(
                                                {'paper_id': paper_id},
                                                {'abstract': 1}
                                                )
            return metadata_selected['abstract']

    def total_count(self, queryterms):
        with metadatadb() as metadb:
            total = metadb.count_documents(queryterms)
        return total

    def batch_generator(self, batchsize):
        totalcount = self.total_count(findterms)
        with metadatadb() as metadb:
            for i in range(totalcount // batchsize + 1):
                abstracts = []
                paper_ids = []
                skipsize = batchsize * i
                abst = metadb.find(findterms, {'_id': 0, 'paper_id': 1, 'abstract': 1}).limit(batchsize).skip(skipsize)
                for item in abst:
                    abstracts.append(item['abstract'])
                    paper_ids.append(item['paper_id'])
                print('Batch ready')
                yield abstracts, paper_ids

    def filtered_batch_generator(self, batchsize):
        totalcount = self.filtered_size
        with metadatadb() as metadb:
            for i in range(totalcount // batchsize + 1):
                abstracts = []
                paper_ids = []
                skipsize = batchsize * i
                abst = metadb.find(
                    {'paper_id': {'$in': self.paper_ids}},
                    {'_id': 0, 'paper_id': 1, 'abstract': 1}
                                ).limit(batchsize).skip(skipsize)
                for item in abst:
                    abstracts.append(item['abstract'])
                    paper_ids.append(item['paper_id'])
                print('Batch ready')
                yield abstracts, paper_ids

    # May be dropped if displayorderedlist works
    def displayresults(self, nearestpapers):
        # This code actually extracts the papers in bulk and no particular order.
        # Order is important for the case of NearestNeighbors and this code needs to change
        results = []
        with metadatadb() as metadb:
            abstractcursor = metadb.find({'paper_id': {'$in': nearestpapers}}, {'paper_id': 1, 'abstract': 1})
            for items in abstractcursor:
                results.append({'paper_id': items['paper_id'], 'abstract': items['abstract']})
        return results

    def displayorderedlist(self, nearestpapers):
        # This code actually extracts the papers in bulk and no particular order.
        # Order is important for the case of NearestNeighbors and this code needs to change
        results = []
        for paper in nearestpapers:
            results.append({'paper_id': paper, 'abstract': self.provide_abstract(paper)})
        return results

    
class pdfparse_class:

    def __init__(self):
        self.paperlist = []
        self.search_keyword = ""

    def search_params(self, paperlist, search_keyword):
        self.paperlist = paperlist
        self.search_keyword = search_keyword

    def search(self):
        self.results = []
        pattern = re.compile(self.search_keyword)
        with pdfparsedb() as pdfdb:
            total_results = pdfdb.count_documents({'$and': [
                {'body_text.text': {'$regex': self.search_keyword}},
                {'paper_id': {'$in': self.paperlist}}
            ]
                                                   }
                                                  )
            keywordresults = pdfdb.find({'$and': [
                        {'body_text.text': {'$regex': self.search_keyword}},
                        {'paper_id': {'$in': self.paperlist}}
                                                ]
                                        },
                                    {'paper_id': 1, 'body_text.text': 1}
                                        )
            countitems = 0
            for items in keywordresults:
                countitems += 1
                sections = items['body_text']
                for section in sections:
                    if pattern.findall(section['text']):
                        self.results.append({'paper_id': items['paper_id'], 'text': section['text']})
                yield "data:" + str((countitems/total_results)*100) + "\n\n"

    def search_results(self):
        return self.results

class dbAccess:

    def __init__(self):
        self.myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.mydb = self.myclient["mydatabase"]
        self.metadata = self.mydb["metadata"]
        self.pdfparse = self.mydb["pdf_parses"]

    # def search(self, paperslist, keyword):
    #     results = []
    #     pattern = re.compile(keyword)
    #     keywordresults = self.pdfparse.find({'$and': [{'body_text.text': {'$regex': keyword}},
    #                                                   {'paper_id': {'$in': paperslist}}]}, {'paper_id': 1, 'body_text.text': 1})
    #     for items in keywordresults:
    #         sections = items['body_text']
    #         for section in sections:
    #             if pattern.findall(section['text']):
    #                 results.append({'paper_id': items['paper_id'], 'text': section['text']})
    #                 #print(results)
    #     return results

    # def provide_abstract(self, paperlist):
    #     metadata_selected = self.metadata.find_one({'paper_id': paperlist[0]}, {'abstract': 1 })
    #     return [metadata_selected['abstract']]

    # def total_count(self, queryterms):
    #     total = self.metadata.count_documents(queryterms)
    #     return total

    # def abstracts(self,paperslist):
    #     """
    #     The total size of abstracts might be too heavy, hence we have a generator.
    #     :param paperslist:
    #     :return:
    #     """
    #     abslist = self.metadata.find({'paper_id': {'$in': paperslist}}, {'paper_id': 1, 'abstract': 1 })
    #      for result in abslist:
    #          yield result
    #     return abslist

    # def batch_generator(self, findterms, batchsize, skipsize):
    #     abst = self.metadata.find(findterms, {'_id': 0, 'paper_id': 1, 'abstract': 1}).limit(batchsize).skip(skipsize)
    #     abstracts = []
    #     paper_ids = []
    #     for item in abst:
    #         abstracts.append(item['abstract'])
    #         paper_ids.append(item['paper_id'])
    #     print('Batch ready')
    #     #print(abstracts, paper_ids)
    #     return abstracts, paper_ids


    # def indices_to_papers(self, nearestpapers):
    #     results = []
    #     abstractcursor = self.metadata.find({'paper_id': {'$in': nearestpapers}}, {'paper_id': 1, 'abstract': 1})
    #     for items in abstractcursor:
    #         results.append({'paper_id': items['paper_id'], 'abstract': items['abstract']})
    #     return results

if __name__ == '__main__':
    test = dbAccess()
    list = test.subject_filter(['Physics'])
    search_results = test.search(list, 'Scanning Tunneling')
    abs = test.abstracts(list) # Deleted
    for item in test.batches(2,2,abs):
        print(item['paper_id'])

