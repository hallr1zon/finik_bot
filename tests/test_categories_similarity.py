import unittest

from app.utils import CategoriesSimilarity


class TestCategoriesSimilarity(unittest.TestCase):
    def test_similarity(self):
        instance = CategoriesSimilarity(set())
        self.assertEqual(instance._similarity("hello", "hella"), 0.8)
        self.assertEqual(instance._similarity("hello", "world"), 0.2)
        self.assertEqual(instance._similarity("apple", "apple"), 1.0)

    def test_merge_similarities_for_similarity(self):
        words = ["apple", "appla", "banana", "banane", "carrot"]
        instance = CategoriesSimilarity(words)
        expected_result = {'apple': ['apple', 'appla'], 'banana': ['banana', 'banane'], 'carrot': ['carrot']}
        self.assertEqual(instance._merge_similarities_to_dict(use_similarity=True), expected_result)

    def test_merge_similarities_for_containing(self):
        words = ["apple", "bigapple", "banana", "bananacake", "carrot"]
        instance = CategoriesSimilarity(words)
        expected_result = {"apple": ["apple", "bigapple"], "carrot": ["carrot"], "banana": ["banana", "bananacake"]}

        self.assertEqual(instance._merge_similarities_to_dict(use_similarity=False), expected_result)

    def test_process(self):
        words = ["кафе", "кафешка", "кава", "кава в кафе", "продукти", "магазин", "Баба балувана"]
        instance = CategoriesSimilarity(words)
        expected_result = {
            'кафе': ['кафе', 'кафешка', 'кава в кафе'],
            'кава': ['кава'],
            'магазин': ['магазин'],
            'продукти': ['продукти'],
            'Баба балувана': ['Баба балувана'],
        }

        self.assertEqual(instance.process(), expected_result)


if __name__ == "__main__":
    unittest.main()
