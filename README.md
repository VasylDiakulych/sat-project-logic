# Numberlink solved by SAT-solver

This is Propositional & Predicate logic SAT-project repository. 
Made by Vasyl Diakulych

## Documentation

### Problem description

The player has to pair up all the matching numbers on the grid with single continuous lines (or paths). The lines cannot branch off or cross over each other, and the numbers have to fall at the end of each line (i.e., not in the middle). Also, paths and numbers on their ends together should cover entire board.
Also, this project is oriented on variation, where you cannot include "U-turns".

![[Pasted image 20251125170535.png]]

In image above you can see an example of such U-turn. If this was allowed, such input would be solvable, but with this constraint it isn't.

For the size of the grid itself, there is only one constraint that it should be a rectangle(maybe there are even some variations and do not have this constraint).

### Input format

As input, program takes a grid $n \times m$, where each cell is either '.'(dot) or other character. 

Any character, except the dot, must appear either 0 times or exactly twice.
Valid input example:

...f... '\n'
.3..@a.
...31..
...a...
.......
..1....
@...f..

Output for this example is:

![[Pasted image 20251125174808.png]]

## Encoding

We define two types of boolean variables to represent the state of the board. All variables are indexed by the coordinates on the grid(row - r, column - c) and color k they carry.

- Node Variables ($N_{r,c,k}$​):
    
    - Represents the assignment of a specific color to a grid cell.
        
    - True: Cell (r,c) is assigned color k.
        
    - False: Cell (r,c) is NOT assigned color k.
        
- Edge Variables ($E_{u,v,k}$​):
    
    - Represents the flow of a pipe across the boundary between two adjacent cells.
        
    - Because the grid is structured, we split these into:
        
        - Horizontal Edges ($H_{r,c,k}$​): Connection between (r,c) and (r,c+1).
            
        - Vertical Edges ($V_{r,c,k}$​): Connection between (r,c) and (r+1,c).
            
    - True: There is an active pipe of color k connecting the two cells.

To generate DIMACS format, 3D coordinates are flattened into unique integer IDs using an offset strategy:
1. Nodes: IDs 1...A
2. Horizontal edges: IDs A+1...B
3. Vertical edges: IDs B+1...C

To represent constraints of the puzzle we should introduce following logical constraints:
- The initial position of endpoints on a grid
	- For every pre-filled colored dot at (r,c) with color k:
		- The variable $N_{r,c,k}$ must be True
		- All other colors k' for that cell are set to False
- Neighborhood constraint
	- Endpoints have exactly 1 edge connected
		-  At least 1: $e_{1} \ OR \ e_{2} \ OR\dots$
		-  At most 1: pairwise ($NOT \ e_{1} \ OR \ NOT \ e_{2}$)
	- Path cells have exactly 2 edges connected
		-  Equivalent to:
			-  Not 0: $e_{1} \ OR  \ e_{2} \ OR \dots$
			-  Not 1: $e_{1} \to (e_{2} \ OR \ e_{3} \ OR\dots)$ ~ $(NOT \ e_{1}) \ OR \ (e_{2} \ OR \ e_{3} \ OR \dots)$ ~ $(NOT \ e_{1}) \ OR \ e_{2} \ OR \ e_{3} \ OR\dots$
			- Less than 3: NOT ($e_{1} \  AND \ e_{2} \ AND \ e_{3}$) ~ $(NOT \ e_{1}) \ OR \ (NOT \ e_{2}) \ OR \ (NOT \ e_{3})$ 
- Consistency constraints(has several parts)
	- Each cell should have a color
		- $N_{1} \ OR \ N_{2} \ OR \dots$
		- N is shortcut for some cell, index is a color
	- Forbid clusters 2x2 of the same color(no U-turns)\
		- For each cell (row, col):
			- NOT ((row, col) AND (row + 1, col) AND (row, col + 1) AND (row + 1, col + 1)) ~ (NOT (row, col)) OR (NOT (row + 1, col)) OR (NOT (row, col + 1)) OR (NOT (row + 1, col + 1))
	- Mutual exclusion(cell cannot be 2 colors at once)
		- For each cell(row, col)
			- For each pair of colors $(k_{1},k_{2})$
				- NOT ((row, col, $k_{1}$) AND (row, col, $k_{2}$)) ~ (NOT (row, col $k_1$)) OR (NOT (row, col, $k_2$))
	- Edge consistency(both ends of the edge must have the same color)
		- For each horizontal edge
			- $edge \to$ cell_left ~ NOT edge OR cell_left 
			- $edge \to$ cell_right ~ NOT edge OR cell_right
		- Same for vertical edges, but top and bottom cells 


## User documentation

Basic usage:

```
python numberlink.py [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v BOOL]
```

Command-line options:
- `-i INPUT`, `--input INPUT` : The instance file. Default: "instances/test-sat"
- `-o OUTPUT`, `--output OUTPUT` : Output file for the DIMACS format (i.e. the CNF formula)
- `-s SOLVER`, `--solver SOLVER` : The SAT solver to be used. Default: "glucose-syrup"
- `-v BOOL`, `--verbose BOOL`: Verbosity of the program. Default: False

Example instances:
- `instances/test-sat`: 10 by 10 solvable test instance, verifiable by human
- `instances/test-unsat`: 10 by 10 unsolvable test instance
- `instances/test-hard`: 20 by 36, solvable via SAT in about 10 seconds

## Experiments
After project was done, I was experimenting with different starting grids. 

Grid 30x30 with 15 colors took about 5 minutes 40 seconds
Grid 25x25 with 12 colors took about 36 seconds
Grid 20x20 with 10 colors took about 2 seconds
Grids with more than 1 solution, produce always the same solution(expected)
