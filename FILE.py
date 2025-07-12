def FILE(a, b):
    if a > 0:
        if b < a:
            x = a + b
            if x > 20:
                assert(False)
        else:
            y = b - a
            if y == 0:
                assert(False)
    else:
        if b == 0:
            assert(False)
    return True

def expected_result():
	return [None, None, None, True, True, True]
