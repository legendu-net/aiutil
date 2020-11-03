import hashlib
from typing import Union, List, Tuple
from pathlib import Path
from loguru import logger


def rmd5(path: Union[str, Path], output: Union[str, Path] = "") -> str:
    """Calculate md5sums recursively for the given path.

    :param path: The path of a file or directory.
    :param output: An optional path to a file to ouput md5sums of files.
    :returns: The md5sum of md5sums of files.
    """
    if isinstance(path, str):
        path = Path(path)
    md5sums = []
    _rmd5(path, md5sums)
    md5sums.sort()
    text = "\n".join(md5sums)
    if output:
        if isinstance(output, str):
            output = Path(output)
        with output.open("w") as fout:
            fout.write(text)
    return hashlib.md5(text.encode()).hexdigest()


def _rmd5(path: Path, res: List[Tuple[str, str]]) -> None:
    """Helper function of rmd5.

    :param path: The Path object of a file or directory.
    :param res: A list to record the result.
    """
    if path.is_file():
        md5sum = hashlib.md5(path.read_bytes()).hexdigest()
        line = f"{str(path)}: {md5sum}"
        res.append(line)
        logger.info(line)
        return
    for p in path.iterdir():
        _rmd5(p, res)
