for i in range(5):
    try:
        raise Exception('hello')
    except Exception:
        continue
    print('should not print')