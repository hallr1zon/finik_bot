from collections import Counter, defaultdict
from datetime import datetime, timedelta

import pymorphy2
from sklearn.cluster import MeanShift
from sklearn.feature_extraction.text import TfidfVectorizer


def get_this_month_filter() -> dict:
    current_datetime = datetime.now()

    first_day_of_month = current_datetime.replace(day=1)

    next_month = current_datetime.replace(month=current_datetime.month + 1, day=1)
    last_day_of_month = next_month - timedelta(days=1)

    return {
        "date__gte": first_day_of_month.replace(hour=0, minute=0, second=0),
        "date__lte": last_day_of_month.replace(hour=23, minute=59, second=59),
    }


def get_this_day_filter() -> dict:
    current_datetime = datetime.now()
    return {
        "date__gte": current_datetime.replace(hour=0, minute=0, second=0),
        "date__lte": current_datetime.replace(hour=23, minute=59, second=59),
    }


class CategoriesSimilarity:
    uk_stop_words = [
        'та',
        'і',
        'в',
        'на',
        'у',
        'з',
        'до',
        'це',
        'що',
        'як',
        'за',
        'він',
        'вона',
        'вони',
        'його',
        'її',
        'їх',
        'який',
        'яка',
        'яке',
        'які',
        'для',
        'чи',
        'але',
        'ми',
        'ви',
        'так',
        'бо',
        'ж',
        'аби',
        'також',
        'не',
        'щоб',
        'ще',
        'ти',
        'нас',
        'нам',
        'ним',
        'ними',
        'тому',
        'усі',
        'усіх',
        'усе',
        'свої',
        'свій',
        'того',
        'все',
        'всі',
        'цей',
        'того',
        'ж',
        'ну',
        'інший',
        'будь',
        'може',
        # Add more stop words as needed
    ]

    @classmethod
    def lemmatize_text(cls, morph, text):
        return ' '.join([morph.parse(word)[0].normal_form for word in text.split()])

    @classmethod
    def most_repeated_word_simple(cls, strings):
        # Split all strings into words and combine them into a single list
        if len(strings) == 1:
            return strings[0]
        words = []
        for string in strings:
            words.extend(string.split())

        word_counts = Counter(words)
        most_common_word, _ = word_counts.most_common(1)[0]

        return most_common_word

    def __init__(self, words: list[str]):
        self.words = words
        self.morph = pymorphy2.MorphAnalyzer(lang='uk')

    def process(self):

        product_names_uk_lemmatized = [self.lemmatize_text(self.morph, name.lower()) for name in self.words]

        vectorizer = TfidfVectorizer(stop_words=self.uk_stop_words)
        X = vectorizer.fit_transform(product_names_uk_lemmatized)

        meanshift = MeanShift()
        meanshift.fit(X.toarray())
        labels = meanshift.labels_

        clusters = defaultdict(list)
        for product, label in zip(self.words, labels):
            clusters[label].append(product)

        naming_clusters = defaultdict(list)
        for cluster, products in clusters.items():
            naming_clusters[self.most_repeated_word_simple(products).lower()] = products

        return dict(naming_clusters)
