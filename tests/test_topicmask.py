"""The step-3b topic mask: deterministic, label-blind, length-preserving."""

from topicmask import MASK, is_topic_word, mask_words


def test_length_is_preserved_and_count_is_right():
    words = "I teach at the school and love linux".split()
    out, n = mask_words(words)
    assert len(out) == len(words)
    assert n == out.count(MASK) == 3
    assert out[0] == "I" and out[2] == "at"


def test_masks_every_industry_whatever_the_label():
    for w in ["teacher", "software", "painting", "newspaper", "Radio,", "(guitar)"]:
        assert is_topic_word(w), w


def test_short_stems_match_exactly_not_as_prefixes():
    assert is_topic_word("art") and is_topic_word("TV") and is_topic_word("pc")
    assert not is_topic_word("party")
    assert not is_topic_word("partial") and not is_topic_word("apple")


def test_plain_words_survive():
    assert not is_topic_word("yesterday") and not is_topic_word("dinner")
