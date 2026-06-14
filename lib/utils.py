
def string_join_and(items):
    items = list(items)
    if len(items) > 1:
        string = ", ".join(items[:-1])
        return '{} and {}'.format(string, items[-1])
    return items[0]
