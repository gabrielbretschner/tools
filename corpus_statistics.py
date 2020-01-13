#!/usr/bin/python3
import argparse, gzip
from collections import defaultdict
import json, re
from enum import OrderedDict
import operator


class Statistics:
    def __init__(self,
                 total_words,
                 uniq_words,
                 total_oovs,
                 uniq_oovs,
                 nn_oov,
                 nn_vocab_size,
                 singletons,
                 n_lines,
                 unk_words,
                 unk_lines
                 ):
        self.total_words = total_words
        self.uniq_words = uniq_words
        self.total_oovs = total_oovs
        self.uniq_oovs = uniq_oovs
        self.nn_oov = nn_oov
        self.nn_vocab_size = nn_vocab_size
        self.n_lines = n_lines
        self.singletons = singletons
        self.unk_words = unk_words
        self.unk_lines = unk_lines

        self.total_oov_rate = total_oovs / total_words
        self.uniq_oov_rate = uniq_oovs / uniq_words
        self.nn_oov_rate = nn_oov/total_words
        self.average_sentence_length = total_words / n_lines
        self.average_oovs_per_sentence = total_oovs / n_lines

    def __str__(self):
        out = "# lines: {}\n".format(self.n_lines) + \
              "running words: {}\n".format(self.total_words) + \
              "vocabulary size: {}\n".format(self.uniq_words) + \
              "nn vocabulary size: {}\n".format(self.nn_vocab_size) + \
              "total oov rate: {:.2f} %\n".format(self.total_oov_rate * 100) + \
              "uniq oov rate: {:.2f} %\n".format(self.uniq_oov_rate * 100) + \
              "nn oov rate: {:.2f} %\n".format(self.nn_oov_rate * 100) + \
              "oovs: {} \n".format(self.total_oovs) + \
              "unique oovs: {} \n".format(self.uniq_oovs) + \
              "nn oovs: {} \n".format(self.nn_oov) + \
              "singletons: {} \n".format(self.singletons) + \
              "avg. sentence length: {}\n".format(self.average_sentence_length) + \
              "avg. oov words per sentence: {}\n".format(self.average_oovs_per_sentence)

        return out


def smart_open(fname):
    if fname.endswith('.gz'):
        return gzip.open(fname, 'rt', encoding='utf-8')
    else:
        return open(fname, 'rt', encoding='utf-8')


def read_vocabulary(fname):
    with smart_open(fname) as f:
        data = json.load(f)
    vocab = {}
    for k,v in data.items():
        vocab[v[0]] = k
    return vocab


def read_corpus(fname,
                vocabulary_threshold = None,
                shared_vocabulary=None,
                vocab=None):
    word_counts = defaultdict(int)
    unk_lines = set()
    unk_words = set()

    with smart_open(fname) as f:
        total_words = 0
        for lineNr, s_line in enumerate(f):
            line = s_line.strip().split(' ')
            total_words += len(line)
            for word in line:
                word_counts[word] += 1
                if vocab is not None and word not in vocab:
                    unk_lines.add((lineNr, s_line))
                    unk_words.add(word)

    seen_vocabulary_size = len(word_counts)
    if shared_vocabulary is not None:
        total_oov_words = total_words - sum([word_counts[word] for word in word_counts if word in shared_vocabulary])
        uniq_oov_words = seen_vocabulary_size - len(shared_vocabulary)
    elif vocabulary_threshold != -1 and len(word_counts) > vocabulary_threshold:
        word_counts = dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[0:vocabulary_threshold])
        total_oov_words = total_words - sum(word_counts.values())
        uniq_oov_words = seen_vocabulary_size - vocabulary_threshold
    else:
        total_oov_words = 0
        uniq_oov_words = 0

    total_nn_oov = 0
    singletons = sum([1 if word_counts[word] == 1 else 0 for word in word_counts])
    if vocab is not None:
        total_nn_oov = sum([word_counts[k] if k not in vocab else 0 for k in word_counts])

    stats = Statistics(
        total_words=total_words,
        uniq_words=len(word_counts),
        total_oovs=total_oov_words,
        uniq_oovs=uniq_oov_words,
        nn_oov=total_nn_oov,
        nn_vocab_size=len(vocab) if vocab is not None else 0,
        singletons=singletons,
        n_lines=lineNr + 1,
        unk_words=unk_words,
        unk_lines=unk_lines
    )

    return word_counts, stats


def read_test(fname, vocabulary, nn_vocab = None):
    unk_lines = set()
    unk_words = set()
    with smart_open(fname) as f:
        seen_words = defaultdict(int)
        total_words = 0
        for lineNr, line in enumerate(f):
            line = line.strip().split(' ')
            total_words += len(line)
            for word in line:
                seen_words[word] += 1
                # if nn_vocab is not None and word not in vocab:
                #     unk_lines.add((lineNr, line))
                #     unk_words.add(word)

    oovs = set(seen_words.keys()) - set(vocabulary.keys())
    total_oov_words = sum([seen_words[word] for word in oovs])
    total_nn_oov = 0
    singletons = sum([1 if seen_words[word] == 1 else 0 for word in seen_words])
    if nn_vocab is not None:
        nn_oov = [seen_words[k] if k not in nn_vocab else 0 for k in seen_words]
        total_nn_oov = sum(nn_oov)

    stats = Statistics(
        total_words=total_words,
        uniq_words=len(seen_words),
        total_oovs=total_oov_words,
        uniq_oovs= len(oovs),
        nn_oov=total_nn_oov,
        nn_vocab_size = len(nn_vocab) if nn_vocab is not None else 0,
        singletons=singletons,
        n_lines=lineNr + 1,
        unk_lines=unk_lines,
        unk_words=unk_words
    )

    return stats


def output_corpus(stats, header=""):
    print(header)
    print(str(stats))

def _subword_prefix(line, subwords = False):
    if subwords:
        return "Sub"+line.lower()
    else:
        return line

def output_corpus_table(stats, subwords = False):
    out = [["", "", "SRC", "TRG"]]
    for name, (src_stat, trg_stat) in stats.items():
        out.append([
            name,
            "Sentences",
            "{:,}".format(src_stat.n_lines) if src_stat is not None else "",
            "{:,}".format(trg_stat.n_lines) if trg_stat is not None else "",
        ])
        out.append([
            "",
            _subword_prefix("Words", subwords=subwords),
            "{:,}".format(src_stat.total_words) if src_stat is not None else "",
            "{:,}".format(trg_stat.total_words) if trg_stat is not None else "",
        ])
        out.append([
            "",
            "NN Vocabulary",
            "%d" %  src_stat.nn_vocab_size if src_stat is not None else "",
            "%d" %  trg_stat.nn_vocab_size if trg_stat is not None else ""
        ])
        out.append([
            "",
            "Vocabulary",
            "%d" %  src_stat.uniq_words if src_stat is not None else "",
            "%d" %  trg_stat.uniq_words if trg_stat is not None else ""
        ])
        out.append([
            "",
            "OOV",
            "%d (%.2f %%)" %  (src_stat.nn_oov, src_stat.nn_oov_rate * 100) if src_stat is not None else "",
            "%d (%.2f %%)" %  (trg_stat.nn_oov, trg_stat.nn_oov_rate * 100) if trg_stat is not None else ""
        ])
        out.append([
            "",
            "avg sentence length",
            "%d" %  (src_stat.average_sentence_length) if src_stat is not None else "",
            "%d" %  (trg_stat.average_sentence_length) if trg_stat is not None else ""
        ])
        out.append([""])

    max_lengths = [0]*len(out[0])
    for row in out:
        for i, val in enumerate(row):
            max_lengths[i] = max(max_lengths[i], len(val))

    for row in out:
        print("\t".join([ val.ljust(max_lengths[i]) for i, val in enumerate(row)]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corpus statistics collector")
    parser.add_argument("--src", type=str, required=True, help="Source training corpus")
    parser.add_argument("--trg", type=str, required=True, help="Target training corpus")
    parser.add_argument("--src-test", type=str, default="",
                        help="Source test files (separate by comma to pass a list of corpora)")
    parser.add_argument("--trg-test", type=str, default="",
                        help="Target test files (separate by comma to pass a list of corpora)")
    parser.add_argument("--shared-vocab", action='store_true',
                        help="Calculate vocabulary statistics for source and target corpora together")
    parser.add_argument("--src-limit", type=int, default=-1, help="Source vocabulary limit")
    parser.add_argument("--trg-limit", type=int, default=-1, help="Target vocabulary limit")
    parser.add_argument('--subword', action="store_true", help="corpus contains subword tokens. ")
    parser.add_argument('--names', type=str, default="", help="comma separated name for the source and target files")

    parser.add_argument("--src-vocab", type=str, help="source vocabulary")
    parser.add_argument("--trg-vocab", type=str, help="target vocabulary")

    parser.add_argument('--table', action="store_true", help="write output as a table. ")
    parser.add_argument('--unks', type=str, help="write unknown words to given file. ", default=None)
    parser.add_argument('--unk-sentences', type=str,
                        help="write sentences containing unknown words to given file. ", default=None)

    args = parser.parse_args()

    output_stats = OrderedDict()
    nn_src_vocab = None
    if args.src_vocab:
        nn_src_vocab = read_vocabulary(args.src_vocab)

    nn_trg_vocab = None
    if args.trg_vocab:
        nn_trg_vocab = read_vocabulary(args.trg_vocab)

    if args.shared_vocab:
        assert args.src_limit == args.trg_limit

        # read source vocab
        vocab, _ = read_corpus(args.src, -1)

        # now update with the target vocab and limit it
        vocab, trg_train_stats = read_corpus(args.trg, args.src_limit,
                                             shared_vocabulary=vocab,
                                             vocab=nn_trg_vocab)

        # now just read the source corpus again and get the statistics
        vocab, src_train_stats = read_corpus(args.src, args.src_limit,
                                             shared_vocabulary=vocab,
                                             vocab=nn_src_vocab,
                                             subwords=args.subword)

        src_vocab = trg_vocab = vocab
    else:
        src_vocab, src_train_stats = read_corpus(args.src, args.src_limit, vocab=nn_src_vocab)
        trg_vocab, trg_train_stats = read_corpus(args.trg, args.trg_limit, vocab=nn_trg_vocab)

    output_stats['train'] = (src_train_stats, trg_train_stats)
    if not args.table:
        output_corpus(src_train_stats, "Train source corpus: {}".format(args.src))
        output_corpus(trg_train_stats, "Train target corpus: {}".format(args.trg))

    src_test_sets = args.src_test.split(',')
    trg_test_sets = args.trg_test.split(',')
    test_sets_names = args.names.split(',')
    if len(src_test_sets) == len(trg_test_sets) and len(src_test_sets) == len(test_sets_names):
        for name, trg, src in zip(test_sets_names, trg_test_sets, src_test_sets):
            trg_stats = None
            src_stats = None
            try:
                trg_stats = read_test(trg, trg_vocab, nn_vocab=nn_trg_vocab)
                if not args.table:
                    output_corpus(trg_stats, "Test source corpus: %s %s" % (name, src))
            except FileNotFoundError:
                pass
            try:
                src_stats = read_test(src, src_vocab, nn_vocab=nn_src_vocab)
                if not args.table:
                    output_corpus(src_stats, "Test target corpus: %s %s" % (name, trg))
            except FileNotFoundError:
                pass

            output_stats[name] = (src_stats, trg_stats)
    else:
        for test_set in args.src_test.split(','):
            try:
                stats = read_test(test_set, src_vocab)
                output_corpus(stats, "Test source corpus: {}".format(test_set))
            except FileNotFoundError:
                pass

        for test_set in args.trg_test.split(','):
            try:
                stats = read_test(test_set, trg_vocab)
                output_corpus(stats, "Test target corpus: {}".format(test_set))
            except FileNotFoundError:
                pass

    if args.table:
        output_corpus_table(output_stats, subwords=args.subword)

    if args.unks is not None:
        with open("%s.src" % args.unks, "w") as f:
            for word in src_train_stats.unk_words:
                f.write("%s %d\n" % (word, src_vocab[word]))

        with open("%s.tgt" % args.unks, "w") as f:
            for word in trg_train_stats.unk_words:
                f.write("%s %d\n" % (word, trg_vocab[word]))

    if args.unk_sentences is not None:
        with open("%s.src" % args.unk_sentences, "w") as f:
            for lineNr, line in src_train_stats.unk_lines:
                f.write("%d\t%s\n" % (lineNr, line))

        with open("%s.tgt" % args.unk_sentences, "w") as f:
            for lineNr, line in trg_train_stats.unk_lines:
                f.write("%d\t%s\n" % (lineNr, line))








