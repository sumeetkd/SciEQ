import spacy
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from sklearn.neighbors import NearestNeighbors
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

    def __generate_vocab(self, data_for_vocab):
        vocab_run = TfidfVectorizer(input = 'content', tokenizer = self.spacy_tokenizer)
        #print(data_for_vocab)
        vocab_run.fit_transform(data_for_vocab)
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

    def similarity(self, paper_list, findterms):
        data_of_interest = self.db.provide_abstract(paper_list)
        totalcount = self.db.total_count(findterms)
        print(totalcount)
        vocabulary = self.__generate_vocab(data_of_interest)
        print(vocabulary)
        count_vector = CountVectorizer(input='content', tokenizer= self.spacy_tokenizer, vocabulary=vocabulary)
        batchsize = 100
        full_paper_ids = []
        counts = []
        for i in range(totalcount//batchsize + 1):
            skipsize = batchsize*i
            abstracts , paper_ids = self.db.batch_generator(findterms, batchsize, skipsize)
            counts.append(count_vector.fit_transform(abstracts))
            full_paper_ids += paper_ids
            print('End of Batch')
        fullcount = vstack([item for item in counts])
        del counts
        transform = TfidfTransformer()
        result = transform.fit_transform(fullcount)
        nbrs = NearestNeighbors(n_neighbors=4, metric='cosine').fit(result)
        _, indices = nbrs.kneighbors(result)
        base_paper_index = full_paper_ids.index(paper_list[0])
        nearestpapers = [full_paper_ids[i] for i in indices[base_paper_index]]
        print(nearestpapers)
        return self.db.indices_to_papers(nearestpapers)
