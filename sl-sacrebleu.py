#!/usr/bin/env python3

from typing import List
from sacrebleu import corpus_bleu, SMOOTH_VALUE_DEFAULT, DEFAULT_TOKENIZER
from sacrebleu import BLEU as BLEU_STRUCT
import argparse
import gzip

def calculate_bleu(
              hyps: List[List[str]],
              refs: List[List[List[str]]],
              smoothing: str = 'exp',
              smoothing_value: float = SMOOTH_VALUE_DEFAULT,
              lowercase: bool = False,
              tokenize: str = DEFAULT_TOKENIZER
              ) -> BLEU_STRUCT:
    """
    calculate BLEU for hyps wrt to refs
    De-tokenizes hyps and refs if self.detokenize=True
    Args:
        hyps: Hypotheses
        refs: References
        smoothing: Smoothing method ['exp', 'floor', 'add-n', 'none'] (Default exp)
        smoothing_value: smoothing value default see sacrebleu.SMOOTH_VALUE_DEFAULT
        lowercase: calculate case-insensitive BLEU
        tokenize: select tokenizer [13a, intl, zh, none] default 13a
    Returns: BLEU score according to sacre bleu

    """
    hyps = [' '.join(sentence) for sentence in hyps]
    refs = [' '.join(sentence) for sentence in refs]

    bleu = corpus_bleu(
        hyps,
        [refs],
        smooth_method=smoothing,
        smooth_value=smoothing_value,
        force=False,
        lowercase=lowercase,
        tokenize=tokenize)
    return bleu


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentence Level BLEU")
    parser.add_argument("--hyp", type=str, required=True, help="Hypothesis")
    parser.add_argument("--ref", type=str, required=True, help="References")
    parser.add_argument("--score", action="store_true", help="just print score")
    args = parser.parse_args()

    if args.hyp.endswith(".gz"):
        hyps = gzip.open(args.hyp)
    else:
        hyps = open(args.hyp)
    if args.ref.endswith(".gz"):
        refs = gzip.open(args.ref)
    else:
        refs = open(args.ref)

    for h,r in zip(hyps, refs):
        h = h.split(' ')
        r = r.split(' ')
        bleu = calculate_bleu([h], [r])
        if args.score:
            print("%0.2f" % bleu.score)
        else:
            print(bleu)



