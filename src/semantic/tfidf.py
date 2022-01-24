import spacy
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from scipy.sparse import vstack

class tfidf:

    def __spacy_tokenizer(self, document):
        nlp = spacy.load("en_core_web_sm")
        tokens = nlp(document)
        tokens = [token.lemma_ for token in tokens if (
            token.is_stop == False and \
            token.is_punct == False and \
            token.lemma_.strip()!= '')]
        return tokens

    def __generate_vocab(self):
        token_run = TfidfVectorizer(input = 'content', tokenizer = spacy_tokenizer)
        token_run.fit_transform([abstracts[0]])
        vocab = token_run.vocabulary_
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




def similarity(self,interested_list,papers_list):