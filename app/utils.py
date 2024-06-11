from datetime import datetime, timedelta
from difflib import SequenceMatcher


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
    def __init__(self, words: [set, list]):
        self.words = sorted(list(words), key=len)

    @staticmethod
    def _similarity(a, b):
        return SequenceMatcher(None, a, b).ratio()

    def _merge_similarities_to_dict(self, use_similarity=True, threshold=0.7):
        merged_dict = {}
        used_indices = set()

        for i, word1 in enumerate(self.words):
            if i in used_indices:
                continue

            similar_words = [word1]

            for j, word2 in enumerate(self.words):
                if j == i or j in used_indices:
                    continue
                if (use_similarity and self._similarity(word1, word2) > threshold) or word1 in word2 or word2 in word1:
                    similar_words.append(word2)
                    used_indices.add(j)

            merged_dict[word1] = similar_words

        return merged_dict

    def process(self):
        res_similarity = self._merge_similarities_to_dict(use_similarity=True)
        res_containing = self._merge_similarities_to_dict(use_similarity=False)

        merged_dict = {**res_similarity}

        for key, value in res_containing.items():
            is_unique_key = []
            for values in res_similarity.values():
                if key in values:
                    is_unique_key.append(False)
                else:
                    is_unique_key.append(True)
            if all(is_unique_key):
                merged_dict[key] = value

        return merged_dict
