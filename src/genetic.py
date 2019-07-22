"""

Crossover and mutation operators are taken from the following study:

    Larranaga, P., Kuijpers, C. M. H., Murga, R. H., Inza, I., 
    & Dizdarevic, S. (1999). Genetic algorithms for the travelling 
    salesman problem: A review of representations and operators. 
    Artificial Intelligence Review, 13(2), 129-170.
"""

import heapq
from operator import itemgetter
from random import randint, random, sample
from statistics import mean

from .algorithms import greedy, tour_length


# taken from study above
POPULATION_SIZE = 200

MAX_ITERATIONS = 50000
ITERATIONS_WITHOUT_IMPROVEMENT = 1000

CROSSOVER_PROBA = 1.0
MUTATION_PROBA = 0.1


def genetic(graph):

    # generate initial population
    population = generate_population(graph, POPULATION_SIZE)

    # get initial fitness of the population
    #prev_mean_fitness = mean_fitness(population)

    #no_improvement_counter = 0

    # stopping condition - MAX_ITERATIONS limit reached
    for _ in range(MAX_ITERATIONS):

        # make sure population is not overly saturated
        # if is_population_saturated(population):
        #    print('Population oversaturated. Returning best solution.')
        #    break

        # select parents from the population
        parent1, parent2 = select_two_parents(population)

        # TODO: put next two into additional routine
        # apply OX1 crossover w. high probability proba_crossover
        child1 = ox1(parent1, parent2)

        # apply SIM mutation w. low proba_mutation
        if random() <= MUTATION_PROBA:
            sim(child1)

        # replace ancestor in a population
        child1_item = _get_fitness(child1, graph), child1
        update_population(child1_item, population)

        # same for second child, but flip order of parents
        child2 = ox1(parent2, parent1)
        sim(child2) if random() <= MUTATION_PROBA else None

        child2_item = _get_fitness(child2, graph), child2
        update_population(child2_item, population)

        # check for no improvement
        #current_mean_fitness = mean_fitness(population)
        #is_fitness_improved = current_mean_fitness > prev_mean_fitness

        # reassign prev_average_fitness to be current value
        #prev_mean_fitness = current_mean_fitness

        # if not is_fitness_improved:
        #    no_improvement_counter += 1
        # else:
        # in case of improvement, reset the counter
        #    no_improvement_counter = 0

        # if no_improvement_counter >= ITERATIONS_WITHOUT_IMPROVEMENT:
        #    s = ITERATIONS_WITHOUT_IMPROVEMENT
        # print('\nNo improvement recorded for {} iterations'.format(s))
        # print('Stopping Genetic Algorithm.')
        # break

    #best_solution = heapq.nlargest(1, population)[0][1]
    _, best_tour = max(population, key=itemgetter(0))

    return best_tour


# TODO
def mean_fitness(population):
    """Returns average fitness of population."""

    avg = mean(item[0] for item in population)
    return round(avg, 2)

# TODO
def is_population_saturated(population):
    """Checks wheter all values in population are same."""
    return len(set(fitness for (fitness, _) in population)) <= 1

# TODO
def update_population(item, population):
    """Updates population with new item if item is good enough.

    If provided items fitness is better than that of worst item in
    population, remove worst item and add provided item.
    """

    # if items fitness is better than population's worst items fitness
    if item[0] > population[0][0]:
        # get rid of worst item, add this one
        heapq.heappushpop(population, item)

    return


# --- working with population ---
def generate_population(graph, size):
    """Returns initial population of possible solutions.

    Uses heuristic to approximate shortest tour and then repeatedly 
    mutates it to construct other members.

    Taken from:
        Abdoun, O., Abouchaka, J. (2011). A Comparative Study of Adaptive 
        Crossover Operators for GA to Resolve TSP.

    Returns:
        list: contains tuples (fitness score, tour)
    """

    population = []

    # construct first individual, add it to population
    initial_tour = greedy(graph)
    item = _get_fitness(initial_tour, graph), initial_tour
    population.append(item)

    # mutate initial solution to generate remaining members
    for _ in range(size - 1):
        mutated_tour = initial_tour[:]
        sim(mutated_tour)  # mutation

        item = _get_fitness(mutated_tour, graph), mutated_tour
        population.append(item)

    return population


def _get_fitness(tour, graph):
    """Returns fitness of a tour.

    The smaller the tour, the larger is its fitness.
    """

    length = tour_length(tour, graph)

    return -1 * length


def select_two_parents(population):
    """Selects two parent solutions from population.
    
    They could be same.
    """

    parent1 = _tournament_selection(population)
    parent2 = _tournament_selection(population)  # could be same as parent1

    return parent1, parent2


def _tournament_selection(population):
    """Selects a solution from the population using 2-way tournament.

    Taken from:
        Blickle, T., & Thiele, L. (1996). A comparison of selection schemes 
        used in evolutionary algorithms. Evolutionary Computation, 4(4), 
        361-394.
    """

    # choose two individuals randomly from population
    # without replacement
    chosen_items = sample(population, 2)

    # select best-fitted individual from chosen ones according to fitness
    best_item = max(chosen_items, key=itemgetter(0))
    _, tour = best_item

    return tour


# --- Crossover Operators ---
def ox1(main_seq, secondary_seq):
    """Returns a result of OX1 order crossover between parents.

    Copies random portion of main_seq into child. Then uses 
    secondary_seq to fill in missing values, preserving relative 
    order of secondary_seq's genes.

    See Larranaga et al. (1999) for detailed explanation.

    Returns:
        sequence
    """

    # preconditions
    length = len(main_seq)
    assert(length == len(secondary_seq))

    child = length * [None]
    swath = _get_valid_swath(length)

    # copy subtour from main parent into a child
    child[swath] = main_seq[swath]

    # fill child's missing genes with alleles from secondary_parent
    _fill_missing_genes(swath, source=secondary_seq, target=child)

    return child


def _fill_missing_genes(prefilled_slice, source, target):
    """Uses source's remaining alleles to fill missing genes in target."""
    
    source_length = len(source)
    start_point = prefilled_slice.stop

    # remember already filled values to skip them later
    already_filled_values = set(target[prefilled_slice])

    # keep target's offset to support simulatneous updates
    target_offset = 0

    # traverse the source using offsetting, wrap around if needed
    for source_offset in range(source_length):
        idx_source = (source_offset + start_point) % source_length
        next_val = source[idx_source]

        if next_val not in already_filled_values:
            idx_target = (target_offset + start_point) % source_length

            # fill in target's gene with parent's allele
            target[idx_target] = next_val

            # move to next available place in target
            target_offset += 1


# --- Mutation Operators ---
def sim(seq):
    """Applies simple inversion mutator to a sequence.

    Modifies seq in place by reversing its random portion. Length of 
    modified sub-sequence is in interval [2, length - 1].

    See Larranaga et al. (1999) for detailed explanation.

    Args:
        seq: sequence with length greater than one.    
    """

    # precondition
    assert len(seq) > 2, \
        'length of seq should be greater than 2.'

    # select random portion of a sequence
    swath = _get_valid_swath(len(seq))

    # reverse that portion
    seq[swath] = reversed(seq[swath])


# --- utility funcs ---
def _get_valid_swath(seq_length):
    """Returns random slice with length in [2, seq_length - 1] interval.
    
    Args:
        seq_length (int): should be integer greater than 2.
    """

    # preconditions
    assert seq_length > 2, 'seq_length should be integer greater than 2.'

    swath = _random_slice(seq_length)

    # make sure swath contains more than 1 member
    while (swath.stop - swath.start) <= 1:
        swath = _random_slice(seq_length)

    # make sure swath does not cover full parent
    while (swath.start == 0) and (swath.stop == seq_length):
        swath = _random_slice(seq_length)

    return swath


def _random_slice(seq_length):
    """Returns random slice object given sequence length.

    Args:
        seq_length (int): length of full sequence.
            Should be a positive integer.

    Returns:
        slice: start and end are chosen randomly.
            Contains at least one member.

    """

    # precondition
    assert isinstance(seq_length, int) and seq_length > 0, \
        'seq_length should be positive integer.'

    # +1 to consider last index of sequence as well
    cut_points = sample(range(seq_length + 1), 2)
    first_cut, last_cut = min(cut_points), max(cut_points)

    return slice(first_cut, last_cut)
