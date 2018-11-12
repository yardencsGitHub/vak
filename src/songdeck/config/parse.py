import os
from configparser import ConfigParser
from collections import namedtuple

from .data import parse_data_config
from .spectrogram import parse_spect_config
from .train import parse_train_config
from .output import parse_output_config
from .predict import parse_predict_config
from ..network import _load


ConfigTuple = namedtuple('ConfigTuple', ['data',
                                         'spect_params',
                                         'train',
                                         'output',
                                         'models',
                                         'predict'])


def parse_config(config_file):
    """parse a config.ini file

    Parameters
    ----------
    config_file

    Returns
    -------
    config_tuple : ConfigTuple
        instance of a ConfigTuple whose fields correspond to
        sections in the config.ini file.
    """
    # load entry points within function, not at module level,
    # to avoid circular dependencies
    # (user would be unable to import networks in other packages
    # that subclass songdeck.network.AbstractSongdeckNetwork
    # since the module in the other package would need to `import songdeck`)
    if not config_file.endswith('.ini'):
        raise ValueError('{} is not a valid config file, '
                         'must have .ini extension'.format(config_file))
    if not os.path.isfile(config_file):
        raise FileNotFoundError('config file {} is not found'
                                .format(config_file))
    config_obj = ConfigParser()
    config_obj.read(config_file)

    if config_obj.has_section('TRAIN') and config_obj.has_section('PREDICT'):
        raise ValueError('Please do not declare both TRAIN and PREDICT sections '
                         ' in one config.ini file: unclear which to use')

    if config_obj.has_section('DATA'):
        data = parse_data_config(config_obj, config_file)
    else:
        data = None

    ### if **not** using spectrograms from .mat files ###
    if data.mat_spect_files_path is None:
        # then user needs to specify spectrogram parameters
        if not config_obj.has_section('SPECTROGRAM'):
            raise ValueError('No annotation_path specified in config_file that '
                             'would point to annotated spectrograms, but no '
                             'parameters provided to generate spectrograms '
                             'either.')
        spect_params = parse_spect_config(config_obj)
    else:
        spect_params = None

    NETWORKS = _load()
    if config_obj.has_section('TRAIN'):
        train = parse_train_config(config_obj, config_file)
    else:
        train = None

    if config_obj.has_section('OUTPUT'):
        output = parse_output_config(config_obj)
    else:
        output = None

    if config_obj.has_section('PREDICT'):
        predict = parse_predict_config(config_obj)
    else:
        predict = None

    models = None

    return ConfigTuple(data,
                       spect_params,
                       train,
                       output,
                       models,
                       predict)
