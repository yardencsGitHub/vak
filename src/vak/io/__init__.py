"""module that handles file input-output:
- audio files
- spectrograms made from audio files of vocalizations
- associated annotation files
- .csv files that represent a dataset of vocalizations that combines all those files together"""
from . import dataset
from .dataset import MetaSpect, Vocalization, Dataset
from . import annotation, audio, dataframe, spect