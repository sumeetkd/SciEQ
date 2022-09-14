import spacy
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from sklearn.neighbors import NearestNeighbors
from src.data import metadata_class
from scipy.sparse import vstack
from src.data import dbAccess

metadb = metadata_class()

class tfidf:
    """
    This class evaluates the similarity of a paper with a subset of papers.
    """

    def __init__(self, paper_id=0, paper_abstract=""):
        # self.db = dbAccess()
        self.paper_id = paper_id
        self.paper_abstract = paper_abstract
        # Moving counts and full paper ids to where it starts getting edited
        # self.counts = []
        # self.full_paper_ids = []

    def set_paper(self, paper_id, abstract):
        # Might need to be dropped
        self.paper_id = paper_id
        self.paper_abstract = abstract

    def spacy_tokenizer(self, document):
        nlp = spacy.load("en_core_web_sm")
        tokens = nlp(document)
        tokens = [token.lemma_ for token in tokens if (
            token.is_stop == False and
            token.is_punct == False and
            token.lemma_.strip()!= '')]
        return tokens

    def __generate_vocab(self, paper):
        data_for_vocab = metadb.provide_abstract(paper)
        vocab_run = TfidfVectorizer(input='content', tokenizer = self.spacy_tokenizer)
        #print(data_for_vocab)
        vocab_run.fit_transform([data_for_vocab])
        vocab = vocab_run.vocabulary_
        return vocab

    def generate_vocab(self):
        vocab_run = TfidfVectorizer(
            input='content',
            tokenizer=self.spacy_tokenizer
        )
        # print(data_for_vocab)
        vocab_run.fit_transform([self.paper_abstract])
        vocab = vocab_run.vocabulary_
        return vocab

    def CountMatrix(self, abstracts):
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

    def count_vectorizer(self):
        # Check if this works out
        return CountVectorizer(
                                    input='content',
                                    tokenizer=self.spacy_tokenizer,
                                    vocabulary=self.generate_vocab()
                                        )

    def process_data(self, batch_generator):
        self.counts = []
        self.full_paper_ids = []
        batch_number = 0
        for abstracts, paper_ids in batch_generator:
            print(type(batch_generator))
            batch_number += 1
            count_vectorizer = self.count_vectorizer()
            self.counts.append(count_vectorizer.fit_transform(abstracts))
            # print(paper_ids)
            self.full_paper_ids += paper_ids
            print('End of Batch')
            print('Batch Number: {}'.format(batch_number))
            print('Papers', paper_ids)
            yield batch_number


    def tfidf_nn(self):
        # Combine the count matrices of the full database
        fullcount = vstack([item for item in self.counts])

        # Adding the paper that was compared into the full list. Ensures that the paper that is closest is always the paper itself.
        if self.paper_id not in self.full_paper_ids:
            abstractcounts = self.count_vectorizer.fit_transform([self.paper_abstract])
            fullcount = vstack([fullcount, abstractcounts])
            self.full_paper_ids.append(self.paper_id)

        # Convert the count matrix into a TFIDF matrix
        transform = TfidfTransformer()
        tfidfmatrix = transform.fit_transform(fullcount)

        # Use NearestNeighbors from scikit NearestNeighbors to get the indices of the nearest neighbours
        nbrs = NearestNeighbors(n_neighbors=4, metric='cosine').fit(tfidfmatrix)
        _, indices = nbrs.kneighbors(tfidfmatrix)

        # NearestNeighbors evaluated for all entries. Get the row relevant to our paper
        # From the full_paper_ids get the index for the chosen paper
        # From the row, convert the indices given by NN to actual paper_ids
        base_paper_index = self.full_paper_ids.index(self.paper_id)
        nearestpapers = [self.full_paper_ids[i] for i in indices[base_paper_index]]
        print(nearestpapers)
        return nearestpapers

    
    def similarity(self, paper_id, findterms):

        batchsize = 100
        full_paper_ids = []
        counts = []

        vocabulary = self.__generate_vocab(paper_id)
        count_vector = CountVectorizer(input='content', tokenizer=self.spacy_tokenizer, vocabulary=vocabulary)

        metadb = metadata_class()
        for abstracts, paper_ids in metadb.batch_generator(findterms, batchsize):
            counts.append(count_vector.fit_transform(abstracts))
            # print(paper_ids)
            full_paper_ids += paper_ids
            print('End of Batch')

        fullcount = vstack([item for item in counts])
        # Check if this is needed after restructuring
        del counts

        # Adding the paper that was compared into the full list. Ensures that the paper that is closest is always the paper itself.

        if paper_id not in full_paper_ids:
            abstract = metadb.provide_abstract(paper_id)
            abstractcounts = count_vector.fit_transform([abstract])
            fullcount = vstack([fullcount, abstractcounts])
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
