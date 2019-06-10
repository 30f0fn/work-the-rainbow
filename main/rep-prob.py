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
    return num_no_triples(n, k) / k**(n//2)

def random_assignment(num_shifts, num_kids):
    return [random.choice(range(num_shifts)) for i in range(num_kids)]
    
def legal(assignment):
    freqs = {i:0 for i in max(assignment)}
    for i in assignment:
        freqs[i] += 1
        if freqs[i] > 2:
            return False
    return True

def trial(shifts, kids, num_tests):
    return [legal(random_assignment(shifts, kids))
           for i in range(num_tests) / num_tests]
        
