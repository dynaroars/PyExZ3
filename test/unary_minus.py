def unary_minus(a):
    b = -a
    c = -b

    if b < 0:
        if a > 0 and a == c:
            return 1
        else:
            return -1
    elif b > 0:
        if a < 0 and a == c:
            return 2
        else:
            return -2
    else:
        if a == 0 and a == c:
            return 3
        else:
            return -3


def expected_result():
	return [1, 2, 3]
