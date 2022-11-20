import pickle


def write_file(path, data) -> bool:
    try:
        with open(path, 'wb') as file:
            pickle.dump(data, file, pickle.HIGHEST_PROTOCOL)
    except IOError:
        return False
    else:
        return True


def read_file(path, key=None) -> object:
    try:
        with open(path, 'rb') as file:
            data = pickle.load(file)
            if key is None:
                return data
            else:
                return data[key] if key in data else None
    except:
        return None


def empty_file(path) -> bool:
    try:
        open(path, 'w').close()
    except IOError:
        return False
    else:
        return True
