import unittest
pytdl = __import__('parallel-ytdl')

class TestParallelYTDL(unittest.TestCase):
	def setUp(self) -> None:
		self.formatter = pytdl.AuthorTitleFormatter()

	def test_format(self):
		format = self.formatter._format
		self.assertEqual(format('1Test2', 'VideoTitle'), '1Test2 - VideoTitle')
		self.assertEqual(format('AUTHOR', 'AUTHOR - TITLE'), 'AUTHOR - TITLE')
		self.assertEqual(format('au', 't - au'), 'au - t')
		self.assertEqual(format('author - Topic', 'vidtitle'), 'author - vidtitle')
		
		self.assertEqual(format('author', 'title   '), 'author - title   ')
		self.assertEqual(format('2', '   1'), '2 -    1')

if __name__ == '__main__':
	unittest.main()
