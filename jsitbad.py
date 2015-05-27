import glob
import string
import re
import numpy as np
from sklearn import manifold
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import matplotlib.pylab as plt
from slimit.lexer import Lexer


def load_js_files(pattern):
    '''Load all the files that glob will return when fed the pattern.

    Args:
        pattern (str): The pattern that will be passed down to glob()

    Returns:
        list. A list of dictionaries. One dict by JS file.

    By convention, malicious files should end in '.out', minified files in '.min.js' and normal files simply in '.js'.

    The dictionary created for each file will have the folowing fields:
    * name : The filename
    * code : The contents of the file
    * nature : One of 'Minified', 'Normal' and 'Malicious'
    * color : 'r' for malicious files, 'b' for minified files and 'g' for normal files.
    '''
    # Loading the data
    data = []
    for js_file in glob.glob(pattern):
        new = {}
        new['name'] = js_file.split('/')[-1]
        new['code'] = open(js_file,'r').read()
        if new['name'][-2:] == 'js':
            if new['name'][-6:] == 'min.js':
                new['nature'] = 'Minified'
                new['color'] = 'b'
            else:
                new['nature'] = 'Normal'
                new['color'] = 'g'
        elif new['name'][-3:] == 'out':
            new['nature'] = 'Malicious'
            new['color'] = 'r'
        data.append(new)
    return data

#Simple features
def length(code):
    return len(code)

def nb_lines(code):
    return len(code.split('\n'))

def avg_char_per_line(code):
    return length(code)/nb_lines(code)

def nb_strings(code):
    '''Ugly approximation, no simple way out of this short of actually parsing the JS.'''
    return len(code.split("'"))+len(code.split('"'))

def nb_non_printable(code):
    '''\cite{likarish2009obfuscated} use unicode symbol, but we are more general'''
    return len([x for x in code if not x in string.printable])

hex_octal_re = re.compile('([^A-F0-9]0[0-7]+|0x[A-F0-9]+)')
def hex_or_octal(code):
    '''Ugly as hell, but we dont want to parse'''
    return len(list(hex_octal_re.finditer(code)))

def max_nesting_level(code):
    l = 0
    max_l = 0
    for c in code:
        if c in '({[':
            l+=1
            max_l = l if l > max_l else max_l
        elif c in ')}]':
            l-=1
    return max_l

def simple_features(text_list):
    '''Transform the list of text into a feature matrix'''
    features = [length, nb_lines, avg_char_per_line, nb_strings, nb_non_printable, hex_or_octal, max_nesting_level]
    answer = []
    for t in text_list:
        answer.append([f(t) for f in features])
    return np.array(answer)

#Features based on lexing
def train_tfidf(corpus):
    '''Return the tf_idf transformer trained on the supplied corpus

    Args:
        corpus (list): List of text elements'''
    count_vect = CountVectorizer()
    train_counts = count_vect.fit_transform(corpus)
    tfidf_transformer = TfidfTransformer().fit(train_counts)
    def text2tfidf(text_list):
        '''Transform a list of text into a tfidf matrix'''
        return tfidf_transformer.transform(count_vect.transform(text_list))
    return text2tfidf

def train_from_js_tokens(corpus):
    lexer = Lexer()
    tokens_corpus = []
    for t in corpus:
        lexer.input(t)
        tokens_corpus.append(' '.join([token.type for token in lexer]))
    return train_tfidf(tokens_corpus)


def place_labels(labels, Y):
    for label, x, y in zip(labels, Y[:, 0], Y[:, 1]):
        plt.annotate(label ,xy=[x,y])

def single_projection(X, s, l, color, labels=None):
    Y = l.fit_transform(X)
    plt.title(s)
    plt.scatter(Y[:, 0], Y[:, 1], c=color, alpha=0.7)
    plt.axis('tight')
    if labels:
        place_labels(labels, Y)

def project_on_plane(X, color, n_neighbors = 10, n_components = 2, title='2D projection', unique=None, labels=None):
    '''Give multiple 2D representations of a high-dimenstional dataset

    See http://scikit-learn.org/stable/auto_examples/manifold/plot_compare_methods.html'''
    fig = plt.figure(figsize=(15,8))
    learners = [['Isomap', manifold.Isomap(n_neighbors, n_components)],
                ['LLE', manifold.LocallyLinearEmbedding(n_neighbors, n_components, eigen_solver='auto')],
                ['LTSA', manifold.LocallyLinearEmbedding(n_neighbors, n_components, eigen_solver='auto', method='ltsa')],
                ['Hessian', manifold.LocallyLinearEmbedding(n_neighbors, n_components, eigen_solver='auto', method='hessian')],
                ["Modified", manifold.LocallyLinearEmbedding(n_neighbors, n_components, eigen_solver='auto', method='hessian')],
                ["MDS", manifold.MDS(n_components, max_iter=100, n_init=1)],
                ["Spectral Embedding", manifold.SpectralEmbedding(n_components=n_components,n_neighbors=n_neighbors)],
                ["t-SNE", manifold.TSNE(n_components=n_components, init='pca', random_state=0)]
                ]
    fig_num = 331
    if unique:
        s,l = [x for x in learners if x[0] == unique][0]
        single_projection(X, s, l, color, labels)
    else:
        for s, l in learners:
            ax = fig.add_subplot(fig_num)
            fig_num += 1
            single_projection(X, s, l, color, labels)
    plt.savefig(title+'.pdf')
    plt.show()


