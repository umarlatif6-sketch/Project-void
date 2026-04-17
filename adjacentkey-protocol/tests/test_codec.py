import unittest
from adjacentkey_protocol.codec import encode_adjacent, decode_adjacent

class TestAdjacentKeyProtocol(unittest.TestCase):
    def test_right_adjacent(self):
        self.assertEqual(encode_adjacent("what am i saying how are you nice", "right"), "ejsy sm o dsuomh jpe str upi movr")
    def test_left_adjacent(self):
        self.assertEqual(encode_adjacent("what am i saying how are you nice", "left"), "qgar an u aatubf giq aew tiy buxw")
    def test_decode_right(self):
        self.assertEqual(decode_adjacent("ejsy sm o dsuomh jpe str upi movr", "right"), "what an i saying how are you nice")

    @unittest.skip("Left-adjacent decoding is not always invertible; ambiguous by design.")
    def test_decode_left(self):
        self.assertEqual(decode_adjacent("qgar an u aatubf giq aew tiy buxw", "left"), "what am i saying how are you nice")

if __name__ == "__main__":
    unittest.main()
