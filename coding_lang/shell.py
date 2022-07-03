import index

while True:
    text = input('C_NS_N_NT> ')
    result, error = index.execute('<stdin>', text)

    if error: print(error.as_string())
    else:print(result)

