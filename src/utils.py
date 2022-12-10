import os
import pickle
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def __create_path():
    Path(os.getenv("PICKLE_FILEPATH")).mkdir(parents=True, exist_ok=True)


def __get_filename_path(filename):
    return f'{os.getenv("PICKLE_FILEPATH")}/{filename}'


def write_file(filename, data) -> bool:
    try:
        __create_path()
        with open(__get_filename_path(filename), 'wb') as file:
            pickle.dump(data, file, pickle.HIGHEST_PROTOCOL)
    except IOError:
        return False
    else:
        return True


def read_file(filename, key=None) -> object:
    try:
        with open(__get_filename_path(filename), 'rb') as file:
            data = pickle.load(file)
            if key is None:
                return data
            else:
                return data[key] if key in data else None
    except:
        return None


def empty_file(filename) -> bool:
    try:
        open(__get_filename_path(filename), 'w').close()
    except IOError:
        return False
    else:
        return True
