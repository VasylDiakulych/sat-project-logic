import subprocess
from argparse import ArgumentParser

class NumberlinkSAT:
    def __init__(self, grid):
        self.grid = grid
        self.Rows = len(grid)
        self.Cols = len(grid[0])

        #getting unique colors
        self.colors = sorted(list(set(c for row in grid for c in row if c != 0)))
        self.K = len(self.colors)

        self.color_map = { color: i for i, color in enumerate(self.colors) }

        self.clauses = []

        #Counting number of prop variables
        self.num_nodes = self.Rows * self.Cols * self.K
        self.num_horizontal_edges = self.Rows * (self.Cols - 1) * self.K
        self.num_vertical_edges = (self.Rows - 1) * self.Cols * self.K

        self.total_variables = self.num_nodes + self.num_vertical_edges + self.num_horizontal_edges

    #helpers for getting ids
    def get_node_id(self, row, col, k_idx):
        return  (row * self.Cols * self.K) + (col * self.K) + k_idx + 1

    def get_horizontal_edge_id(self, row, col, k_idx):
        offset = self.num_nodes
        idx = (row * (self.Cols - 1) * self.K) + (col * self.K) + k_idx
        return offset + idx + 1

    def get_vertical_edge_id(self, row, col, k_idx):
        offset = self.num_nodes + self.num_horizontal_edges
        idx = (row * self.Cols * self.K) + (col * self.K) + k_idx
        return offset + idx + 1

    def write_dimacs(self, filename = "output.cnf"):
        with open(filename, 'w') as f:
            f.write(f"p cnf {self.total_variables} {len(self.clauses)}\n")
            for clause in self.clauses:
                f.write(" ".join(map(str,clause)) + " 0\n")

    def set_initial_state(self):
        for row in range(self.Rows):
            for col in range(self.Cols):
                val = self.grid[row][col]
                #if cell is endpoint
                if val != 0:
                    k_target = self.color_map[val]

                    #we know color of this node
                    id = self.get_node_id(row, col, k_target)
                    self.clauses.append([id])

                    #and we know that this node cannot have any other color
                    for k in range(self.K):
                        if k != k_target:
                            wrong_id = self.get_node_id(row,col,k)
                            self.clauses.append([-wrong_id])


    def get_neighb_edges(self, row, col, k):
        neighbors = []

        if row > 0:
            neighbors.append(self.get_vertical_edge_id(row-1, col, k))

        if row < self.Rows - 1:
            neighbors.append(self.get_vertical_edge_id(row, col, k))

        if col > 0:
            neighbors.append(self.get_horizontal_edge_id(row, col - 1, k))

        if col < self.Cols - 1:
            neighbors.append(self.get_horizontal_edge_id(row, col, k))

        return neighbors

    def add_neighborhood_constraints(self):
        for row in range(self.Rows):
            for col in range(self.Cols):
                value = self.grid[row][col]

                for k in range(self.K):
                    neighbors = self.get_neighb_edges(row, col, k)
                    n_count = len(neighbors)

                    node_id = self.get_node_id(row, col, k)
                    #can have only 1 adjacent edge
                    if value != 0 and self.color_map[value] == k:
                        #at least 1 edge
                        self.clauses.append(neighbors)

                        #at most 1, (NOT a OR NOT b)
                        for i in range (n_count):
                            for j in range (i + 1, n_count):
                                self.clauses.append([-neighbors[i], -neighbors[j]])

                    elif value != 0 and self.color_map[value] != k:
                        for edge in neighbors:
                            self.clauses.append([-edge])

                    #if it's not an end point, then it must have 2 adjacent edges
                    else:
                        #not 0 edges
                        self.clauses.append([-node_id] + neighbors)

                        #not exactly 1
                        #if e[i] = true, at least one other must be true
                        # a -> (b OR c) ~ (NOT a) OR (b OR c)
                        for i in range(n_count):
                            #NOT a
                            clause = [-node_id, -neighbors[i]]

                            #b OR c
                            for j in range(n_count):
                                if i != j:
                                    clause.append(neighbors[j])

                            self.clauses.append(clause)

                        #at most 2
                        for i in range(n_count):
                            for j in range(i + 1, n_count):
                                for l in range(j + 1, n_count):
                                    self.clauses.append([
                                        -node_id,
                                        -neighbors[i],
                                        -neighbors[j],
                                        -neighbors[l]
                                    ])

    def add_consistency_constraints(self):

        #each cell should have an assigned color
        for row in range(self.Rows):
            for col in range(self.Cols):
                self.clauses.append([self.get_node_id(row, col, k) for k in range(self.K)])

        #forbid clusters 2x2 of the same color
        for row in range(self.Rows - 1):
            for col in range(self.Cols - 1):
                for k in range(self.K):
                    self.clauses.append([
                        -self.get_node_id(row, col, k),
                        -self.get_node_id(row, col + 1, k),
                        -self.get_node_id(row + 1, col, k),
                        -self.get_node_id(row + 1, col + 1, k)
                    ])

        #mutual exclusion, a cell cannot be 2 colors at once
        for row in range(self.Rows):
            for col in range(self.Cols):
                for k1 in range(self.K):
                    for k2 in range(k1+1, self.K):
                        id1 = self.get_node_id(row, col, k1)
                        id2 = self.get_node_id(row, col, k2)

                        self.clauses.append([-id1, -id2])

        #edge consistency, if edge is colored in color k, both nodes it connects should have color k

        #horizontal edges
        for row in range(self.Rows):
            for col in range(self.Cols - 1):
                for k in range(self.K):
                    edge = self.get_horizontal_edge_id(row, col, k)
                    node_left = self.get_node_id(row, col, k)
                    node_right = self.get_node_id(row, col + 1, k)

                    #edge -> node_left ~ NOT edge OR node_left
                    self.clauses.append([-edge, node_left])

                    #edge -> node_right ~ NOT edge OR node_right
                    self.clauses.append([-edge, node_right])

        #vertical edges
        for row in range(self.Rows - 1):
            for col in range(self.Cols):
                for k in range(self.K):
                    edge = self.get_vertical_edge_id(row, col, k)
                    node_top = self.get_node_id(row, col, k)
                    node_bot = self.get_node_id(row + 1, col, k)

                    #edge -> node_top ~ NOT edge OR node_top
                    self.clauses.append([-edge, node_top])

                    #edge -> node_bot ~ NOT edge OR node_bot
                    self.clauses.append([-edge, node_bot])

    def solve(self, output = "formula.cnf", solver_path="glucose-syrup"):

        self.write_dimacs(output)

        try:
            process = subprocess.run([solver_path, "-model", output],
                                     capture_output=True,
                                     text=True
                                     )
        except FileNotFoundError:
            print(f"Error: Could not find executable at '{solver_path}'")
            return

        output = process.stdout

        if "UNSATISFIABLE" in output:
            print("UNSATISFIABLE: No solution exists")
            return

        vars = set()
        for line in output.splitlines():
            if line.startswith('v'):
                parts = line.split()
                for x in parts[1:]:
                    val = int(x)
                    if val > 0:
                        vars.add(val)

        #interpret the output
        final_grid = [[0] * self.Cols for _ in range(self.Rows)]

        for row in range(self.Rows):
            for col in range(self.Cols):
                for k in range(self.K):
                    node_id = self.get_node_id(row, col, k)

                    if node_id in vars:
                        color = self.colors[k]
                        final_grid[row][col] = color
                        break

        print("\n--- SOLUTION ---")
        #colorcoding the solution for better visibility
        for row in final_grid:
            line_str = ""
            for val in row:
                # if everything works fine, you should never see this color, since it is reserved for empty cells
                if val == 0:
                    color_code = 235
                else:
                    #simple hashing to get "random" color
                    color_code = ((val * 1013) % 216) + 16
                line_str += f"\033[48;5;{color_code}m  \033[0m"
            print(line_str)

def parse_grid(filename):
    with open(filename, 'r') as f:
        lines = [line.rstrip() for line in f if line.strip()]

    if not lines:
        return None

    height = len(lines)
    width = max(len(line) for line in lines)

    unique_chars = set()
    for line in lines:
        for char in line:
            if char != '.' and char != ' ':
                unique_chars.add(char)

    sorted_chars = sorted(list(unique_chars))
    char_to_id = {char: i + 1 for i, char in enumerate(sorted_chars)}

    grid = []
    for line in lines:
        row = []
        padded_line = line.ljust(width, '.')

        for char in padded_line:
            if char in char_to_id:
                row.append(char_to_id[char])
            else:
                row.append(0)
        grid.append(row)

    return grid

if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        default="instances/test-sat",
        type=str,
        help=(
            "Path to the input file"
        )
    )

    parser.add_argument(
        "-o",
        "--output",
        default="formula.cnf",
        type=str,
        help=(
            "Output file for the DIMACS format (i.e. the CNF formula)."
        ),
    )

    parser.add_argument(
        "-s",
        "--solver",
        default="./glucose-syrup",
        type=str,
        help=(
            "The SAT solver to be used."
        )
    )

    args = parser.parse_args()

    grid = parse_grid(args.input)

    solver = NumberlinkSAT(grid)

    solver.set_initial_state()
    solver.add_neighborhood_constraints()
    solver.add_consistency_constraints()

    solver.solve(output=args.output, solver_path=args.solver)
