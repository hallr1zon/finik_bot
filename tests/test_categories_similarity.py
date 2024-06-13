import unittest

from app.utils import CategoriesSimilarity


class TestCategoriesSimilarity(unittest.TestCase):

    def test_process(self):
        words = ["кафе", "кафешка", "кава", "кава в кафе", "продукти", "магазин", "Баба балувана"]
        instance = CategoriesSimilarity(words)
        expected_result = {
            'кафе': ['кафе', 'кава', 'кава в кафе'],
            'кафешка': ['кафешка'],
            'продукти': ['продукти'],
            'магазин': ['магазин'],
            'баба балувана': ['Баба балувана'],
        }

        self.assertEqual(instance.process(), expected_result)


if __name__ == "__main__":
    unittest.main()
