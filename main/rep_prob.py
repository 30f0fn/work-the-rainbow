def factorial(n):
    return 1 if n == 0 else n * factorial(n-1)

def choose(n, k):
    num = factorial(n)
    den = factorial(k) * factorial(n-k)
    return num // den

def num_no_triples(num_shifts, num_kids):
    return sum([choose(num_shifts, num_kids-k) * choose(num_kids-k, k)\
                for k in range(0, num_kids // 2)])

def prob(n, k):
    return num_no_triples(n, k) / (n//2)**k

def random_assignment(num_shifts, num_kids):
    return [random.choice(range(num_shifts)) for i in range(num_kids)]
    
def legal(assignment):
    freqs = {i:0 for i in range(max(assignment)+1)}
    for i in assignment:
        freqs[i] += 1
        if freqs[i] > 2:
            return False
    return True

# def trial(shifts, kids, num_tests):
    # return [legal(i) for i in range(num_tests)]

 # [legal(random_assignment(shifts, kids)) for i in range(num_tests) / num_tests


def trial(shifts, kids, num_tests):
    yesses = sum([legal(random_assignment(shifts, kids)) for i in range(num_tests)])
    return yesses / num_tests
        
    
