"""Module for log filtering.
"""
from __future__ import annotations
from typing import Sequence, TextIO
import sys
import os
import re
from collections import deque
from difflib import SequenceMatcher
import time
from tqdm import tqdm

DASH_50 = "-" * 50
DASH_100 = "-" * 100


class LogDeduper:
    """Dedup similar log lines.
    """
    def __init__(self, threshold: float = 0.5):
        self._lines = []
        self._threshold = threshold

    def similarity(self, line):
        """Calcualte similarity between 2 lines.

        :param line1: A line of logging message.
        :param line2: Another line of logging message.
        :return: A similarity score (between 0 and 1) between the 2 lines.
        """
        return max(
            (SequenceMatcher(None, line, target).ratio() for target in self._lines), default=0
        )

    def add(self, line, line_num):
        """Add a line.

        :param line: A line of logging message.
        :param line_num: The row number (0-based) of the line.
        """
        if self.similarity(line) < self._threshold:
            self._lines.append(f"L{line_num}: {line}\n")

    def write(self, fout: TextIO):
        """Write deduplicated log into a file.

        :param fout: A file handler for outputing log.
        """
        fout.write(DASH_50 + "SUMMARY" + DASH_50 + "\n")
        for line in self._lines:
            fout.write(line)


class LogFilter:
    """A class for log filtering.
    """
    KEYWORDS = (
        "User class threw exception",
        "spark.yarn.executor.memoryOverhead",
        "FileAlreadyExists",
        "InvalidResourceRequestException",
        "has no attribute",
        "not found",
        "exec /bin/bash ",
        "OOM",
        "Error",
        "error",
        "Exception",
        "exception",
    )
    PATTERNS = (
        r"\d\d[\/](0?[1-9]|1[0-2])[\/](0?[1-9]|[12][0-9]|3[01])\s\d+[:]\d+:\d+",
        r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}",
    )
    MSG = "\rProcessing line {line_num} ({progress}%); Time Used: {time_used}s; Time Left: {time_left}s"

    def __init__(
        self,
        log_file,
        context_size=5,
        keywords: Sequence[str] = KEYWORDS,
        patterns: Sequence[str] = PATTERNS,
        output_file: str = "",
    ):
        self._log_file = log_file
        self._context_size = context_size
        self._keywords = keywords
        self._patterns = patterns
        self._num_rows = None
        self._lookup = {}
        self._queue = deque()
        self._output_file = self._get_output_file(output_file)

    def _get_output_file(self, output_file):
        """Get a valid output file.

        :param output_file: The path to the output file.
        """
        if output_file:
            return output_file
        title, ext = os.path.splitext(self._log_file)
        return title + "_s" + ext

    def _regularize(self, line) -> str:
        """Get rid of substrings with patterns specified by the regular expressions.

        :param line: A line of logging message.
        :return: The regularized the line message.
        """
        for pattern in self._patterns:
            line = re.sub(pattern, "", line)
        return line

    def _dump_queue(self, lines) -> None:
        """Dump content in the queue.

        :param lines: A list to dump the queue to.
        """
        lines.append(DASH_100 + "\n")
        lines.extend(self._queue)
        self._queue.clear()

    def _keep(self, idx: int, line: str) -> bool:
        """Check whether the line should be kept.

        :param idx: The original row number (0-based) of the line. 
        :param line: A line of logging message.
        :return: True if the line is to be kept and False otherwise.
        """
        # TODO: group by keywords and dedup in each group first
        if any(kw in line for kw in self._keywords):
            line = self._regularize(line)
            if line not in self._lookup:
                self._lookup[line] = idx
                return True
        return False

    def _count_rows(self):
        """Count the total number of rows.
        """
        if self._num_rows is not None:
            return
        print("Counting total number of rows ...")
        with open(self._log_file, "r") as fin:
            self._num_rows = sum(1 for line in fin)
        print(f"Total number of rows: {self._num_rows:,}")

    def filter(self):
        """Filter informative liens from a Spark application log.
        """
        self._count_rows()
        lines = [DASH_50 + "START" + DASH_50 + "\n"]
        with open(self._log_file, "r") as fin:
            dump_flag = -1
            for idx, line in tqdm(enumerate(fin), total=self._num_rows):
                line_with_num = f"L{idx}: {line}"
                self._queue.append(line_with_num)
                keep = self._keep(idx, line)
                # fill up context_head with anything only if found
                if len(self._queue) < self._context_size and not keep:
                    self._queue.append(line_with_num)
                    continue
                if not keep and dump_flag == -1:
                    self._queue.popleft()
                elif not keep and dump_flag >= 0:
                    dump_flag += 1
                    if dump_flag == self._context_size:
                        self._dump_queue(lines)
                        dump_flag = -1
                else:
                    dump_flag = 0
            lines.append(DASH_50 + "EOF" + DASH_50 + "\n")
            self._dump_queue(lines)
        self._dedup_dump_log(lines)

    def _dedup_dump_log(self, lines):
        print("Deduplicating logs ...")
        deduper = LogDeduper()
        for line, idx in tqdm(self._lookup):
            deduper.add(line, idx)
        deduper.write(sys.stdout)
        with open(self._output_file, "w") as fout:
            deduper.write(fout)
            fout.writelines(lines)
        print(f"\nFile saved in {self._output_file}\n")
