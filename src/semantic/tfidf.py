import spacy
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from sklearn.neighbors import NearestNeighbors
from src.data import metadata_class
from scipy.sparse import vstack
from src.data import dbAccess

class tfidf:

    def __init__(self):
        self.db = dbAccess()

    def spacy_tokenizer(self, document):
        nlp = spacy.load("en_core_web_sm")
        tokens = nlp(document)
        tokens = [token.lemma_ for token in tokens if (
            token.is_stop == False and \
            token.is_punct == False and \
            token.lemma_.strip()!= '')]
        return tokens

    def __generate_vocab(self, paper):
        metadb = metadata_class()
        data_for_vocab = metadb.provide_abstract(paper)
        vocab_run = TfidfVectorizer(input = 'content', tokenizer = self.spacy_tokenizer)
        #print(data_for_vocab)
        vocab_run.fit_transform([data_for_vocab])
        vocab = vocab_run.vocabulary_
        return vocab

    def CountMatrix(self,abstracts):
        """
        :param abstracts: Abstracts are supplied in the form of a generator
        :return:
        """
        count_vector = CountVectorizer(input='content', vocabulary=vocab)
        matrix = count_vector.fit_transform(abstracts)
#        for document in abstracts:
#            counts = count_vector.fit_transform(list(document['abstract']))
#            try:
#                matrix
#                matrix = vstack(matrix,counts)
#            except NameError:
#                matrix = vstack(counts)
        return matrix

    def similarity(self, paper_id, findterms):

        batchsize = 100
        full_paper_ids = []
        counts = []

        vocabulary = self.__generate_vocab(paper_id)
        count_vector = CountVectorizer(input='content', tokenizer= self.spacy_tokenizer, vocabulary=vocabulary)

        metadb = metadata_class()
        for abstracts , paper_ids in metadb.batch_generator(findterms, batchsize):
            counts.append(count_vector.fit_transform(abstracts))
            #print(paper_ids)
            full_paper_ids += paper_ids
            print('End of Batch')

        fullcount = vstack([item for item in counts])
        del counts

        if paper_id not in full_paper_ids:
            abstract = metadb.provide_abstract(paper_id)
            abstractcounts = count_vector.fit_transform([abstract])
            fullcount = vstack([fullcount,abstractcounts])
            full_paper_ids.append(paper_id)


        transform = TfidfTransformer()
        tfidfmatrix = transform.fit_transform(fullcount)

        nbrs = NearestNeighbors(n_neighbors=4, metric='cosine').fit(tfidfmatrix)
        _, indices = nbrs.kneighbors(tfidfmatrix)

        # Forces the paper_id to be part of the selected set of papers
        base_paper_index = full_paper_ids.index(paper_id)
        nearestpapers = [full_paper_ids[i] for i in indices[base_paper_index]]
        print(nearestpapers)
        return metadb.displayresults(nearestpapers)
