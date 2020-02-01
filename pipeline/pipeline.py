from dataclasses import dataclass

import random
import itertools
from pathlib import Path

import joblib
from tqdm import tqdm
from wasabi import msg


@dataclass
class Pipe:
    """
    Comments!
    """

    source: str
    dest: str = None
    input_suffix: str = ""
    output_suffix: str = ""
    shuffle: bool = False
    limit: int = None
    prefilter: bool = True
    progress_bar: bool = True

    def __post_init__(self, *args, **kwargs):
        """
        Setups up the pipe for processing. Creates an ouput directory if needed,
        shuffles data, and validiates input path or generic iterators.
        """

        # If input is a path, build an iterable from a glob
        if self.is_input_from_files:

            self.input_suffix = Path(self.input_suffix)

            # Fix the empty string case
            if self.input_suffix == Path():
                self.input_suffix = ""

            # Strip any glob characters passed
            self.input_suffix = str(self.input_suffix).lstrip("*")

            self.F_IN = Path(self.source).glob("*" + self.input_suffix)

        # Otherwise assume source is an iterable
        else:
            self.F_IN = self.source

        # If output is a path, build a reference set of outputs
        if self.is_output_to_files:

            self.dest = Path(self.dest)

            # Create an output directory if needed
            self.dest.mkdir(parents=True, exist_ok=True)

            if not self.output_suffix:
                self.output_suffix = self.input_suffix

            if not self.output_suffix:
                msg.fail(
                    f"{self.__class__.__name__}: Must set either 'input_suffix' or 'output_suffix' if 'dest' is specified"
                )
                raise ValueError

            # Strip any glob characters passed
            if self.output_suffix == ".":
                self.output_suffix = ""

            self.output_suffix = str(self.output_suffix).lstrip("*")
            self.F_OUT = set(self.dest.glob("*" + self.output_suffix))

            # Conditionally filter the input
            if self.prefilter:
                self.F_IN = [
                    f for f in self.F_IN if self.get_output_file(f) not in self
                ]
        else:
            self.F_OUT = set()

        # Shuffle the input data if requested
        if self.shuffle:
            self.F_IN = sorted(list(self.F_IN))
            random.shuffle(self.F_IN)

    @property
    def is_input_from_files(self):
        """
        Return True if the input is a Path or string, read those files.
        """
        return isinstance(self.source, (str, Path))

    @property
    def is_output_to_files(self):
        """
        Return True if destination is a valid path.
        """
        return isinstance(self.dest, (str, Path))

    def __len__(self):
        """
        The length is the minimum size of the input iterator and the limit.
        """

        try:
            n = len(self.F_IN)
        except TypeError:
            n = None

        if not self.limit or self.limit < 0:
            return n

        return min(self.limit, n)

    def __iter__(self):
        """
        Iterates over the valid inputs. If self.dest is a path, will perform
        an additional check to make sure it has not recently been created.
        """

        k = itertools.count()

        for f0 in self.F_IN:

            # Short circuit if limit is reached
            if self.limit and next(k) > self.limit:
                break

            if self.is_output_to_files:
                f1 = self.get_output_file(f0)

                if f1 is not None and f1.exists():
                    msg.warn(f"Did not expect {f1} to exist, skipping")
                    continue

                yield (f0, f1)

            else:
                yield (f0,)

    def __contains__(self, f):
        """
        Check if the input is in the precompiled list.
        """
        return f in self.F_OUT

    def get_output_file(self, f0):
        """
        If 'dest' is a path, return the new output filename.
        """
        f1 = self.dest / Path(str(f0)).stem
        return f1.with_suffix(self.output_suffix)

    def __call__(self, func, n_jobs=-1):
        """
        Call the input function. If n_jobs==-1 [default] run in parallel with
        full cores.
        """
        if self.progress_bar:
            ITR = tqdm(self)
        else:
            ITR = self

        if n_jobs == 1:
            return [func(*args) for args in ITR]

        with joblib.Parallel(n_jobs) as MP:
            dfunc = joblib.delayed(func)
            return MP(dfunc(*args) for args in ITR)
