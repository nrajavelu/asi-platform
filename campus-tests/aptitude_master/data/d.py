ROWS = [
    # ================= SECTION A: LATERAL THINKING / INNOVATIVE PROBLEM SOLVING =================

    # --- Fermi estimation (5) ---
    ("LAT-01", "lateral_thinking", "hard",
     "A standard school bus has a usable interior cargo volume of about 60 cubic meters. If every tennis ball, "
     "including the small packing gaps around it, can be thought of as occupying a cube of side 6 cm, estimate "
     "how many tennis balls could fit inside the bus.",
     "about 280,000", "about 2,800", "about 28,000", "about 2,800,000", 1, "A"),

    ("LAT-02", "lateral_thinking", "medium",
     "Assume an average adult heart beats 75 times per minute and a person lives for 80 years. Estimate the "
     "total number of heartbeats in that person's lifetime.",
     "about 31.5 million", "about 3.15 billion", "about 315 million", "about 31.5 billion", 1, "B"),

    ("LAT-03", "lateral_thinking", "hard",
     "A city has a population of 5,000,000 with an average household size of 2.5 people. Assume 1 in 20 "
     "households owns a piano, each piano is tuned once a year, and one full-time tuner can tune 4 pianos a day "
     "while working 250 days a year. Estimate the number of piano tuners the city's demand can support.",
     "about 10", "about 1,000", "about 100", "about 10,000", 1, "C"),

    ("LAT-04", "lateral_thinking", "hard",
     "A cubical container measures 1 meter on each side, giving a volume of 1,000,000 cm3. If each grain of "
     "rice, including the small gaps between grains, occupies about 0.025 cm3, estimate how many grains of "
     "rice would fill the container.",
     "about 400,000", "about 4 million", "about 400 million", "about 40 million", 1, "D"),

    ("LAT-05", "lateral_thinking", "medium",
     "At rest, an average human heart pumps about 5 liters of blood per minute (its cardiac output). Estimate "
     "the total volume of blood pumped by the heart over one full day.",
     "about 7,200 liters", "about 72 liters", "about 720 liters", "about 72,000 liters", 1, "A"),

    # --- Constraint-satisfaction optimization (5) ---
    ("LAT-06", "lateral_thinking", "hard",
     "You have 12 identical-looking coins. Exactly one is counterfeit and has a different weight than the "
     "rest, but you do not know whether it is heavier or lighter. Using a two-pan balance scale with no "
     "weights, what is the minimum number of weighings needed to guarantee you can identify the counterfeit "
     "coin AND determine whether it is heavier or lighter than the rest?",
     "2", "3", "4", "5", 1, "B"),

    ("LAT-07", "lateral_thinking", "hard",
     "You have 8 identical-looking balls. Exactly one is heavier than the rest (you already know it is "
     "heavier, not lighter). Using a two-pan balance scale, what is the minimum number of weighings needed to "
     "guarantee identifying the heavier ball?",
     "1", "3", "2", "4", 1, "C"),

    ("LAT-08", "lateral_thinking", "hard",
     "Four people need to cross a narrow bridge at night using a single flashlight. At most 2 people can cross "
     "at a time, and anyone crossing in either direction must carry the flashlight. The four people take 1, 2, "
     "5, and 10 minutes respectively to cross alone; a pair crossing together moves at the slower person's "
     "pace. What is the minimum total time for all four to get across?",
     "15 minutes", "19 minutes", "21 minutes", "17 minutes", 1, "D"),

    ("LAT-09", "lateral_thinking", "hard",
     "A farmer must ferry a wolf, a goat, and a cabbage across a river using a boat that holds the farmer plus "
     "only one item at a time. If left unattended together, the wolf will eat the goat, and the goat will eat "
     "the cabbage. What is the minimum number of one-way crossings of the boat (by the farmer, with or without "
     "cargo) needed to get everything across safely?",
     "7", "5", "6", "9", 1, "A"),

    ("LAT-10", "lateral_thinking", "hard",
     "You have an unmarked 3-liter jug, an unmarked 5-liter jug, and an unlimited water supply. Counting every "
     "fill, every emptying, and every pour between the two jugs as one step, what is the minimum number of "
     "steps needed to measure out exactly 4 liters in one of the jugs?",
     "5", "6", "4", "8", 1, "B"),

    # --- Probability / game theory (5) ---
    ("LAT-11", "lateral_thinking", "medium",
     "In a room of 23 randomly chosen people (ignore leap years, and assume birthdays are uniformly "
     "distributed over 365 days), what is the probability that at least two people in the room share the same "
     "birthday?",
     "about 6%", "about 27%", "about 51%", "about 93%", 1, "C"),

    ("LAT-12", "lateral_thinking", "medium",
     "In a game show there are 3 doors: one hides a car, the other two hide goats. You pick a door. The host, "
     "who knows what is behind every door, always opens one of the other two doors that has a goat (never the "
     "car, and he always opens a door regardless of your pick). You are then offered the chance to switch to "
     "the remaining unopened door. What is the probability of winning the car if you always switch?",
     "1/3", "1/2", "3/4", "2/3", 1, "D"),

    ("LAT-13", "lateral_thinking", "medium",
     "Two players alternately add a whole number from {1, 2, 3} to a running total that starts at 0. Whoever "
     "makes the total reach exactly 21 wins. Player 1 moves first. If Player 1 plays optimally from the start, "
     "what should their first move be to guarantee a win?",
     "1", "2", "3", "It doesn't matter -- Player 1 cannot force a win", 1, "A"),

    ("LAT-14", "lateral_thinking", "medium",
     "You roll a fair six-sided die repeatedly until you have seen all 6 faces at least once. What is the "
     "expected number of rolls required?",
     "6", "14.7", "10.9", "21", 1, "B"),

    ("LAT-15", "lateral_thinking", "hard",
     "A box contains 3 cards: one is black on both sides, one is white on both sides, and one is black on one "
     "side and white on the other. You draw a card at random and place it on a table; the side facing up is "
     "black. What is the probability that the other side of this same card is also black?",
     "1/3", "1/2", "2/3", "3/4", 1, "C"),

    # --- Efficiency / engineering-judgment optimization (5) ---
    ("LAT-16", "lateral_thinking", "hard",
     "Six jobs take 6, 5, 4, 3, 3, and 2 minutes respectively. They must be split between 2 identical machines "
     "running in parallel, and the workshop can close only once both machines have finished all of their "
     "assigned jobs. What is the minimum possible time (makespan) at which both machines can be finished, "
     "over all ways of splitting the 6 jobs between the 2 machines?",
     "13 minutes", "14 minutes", "15 minutes", "12 minutes", 1, "D"),

    ("LAT-17", "lateral_thinking", "hard",
     "An array of 1,000 numbers is sorted except for exactly 4 elements, each of which is at most 2 positions "
     "away from its correct sorted position. You need to sort the array completely as fast as possible. Which "
     "sorting method is most efficient for this specific input, and why?",
     "Insertion sort, because its running time is proportional to the array size plus the number of "
     "out-of-place elements, which is small here",
     "Merge sort, because it always runs in O(n log n) regardless of the input",
     "Heap sort, because it always runs in O(n log n) regardless of the input",
     "Standard (non-randomized) quicksort, because it has the best average-case performance",
     1, "A"),

    ("LAT-18", "lateral_thinking", "hard",
     "A web server caches pages in memory, but the cache can hold only 100 of the 10,000 distinct pages on the "
     "site. Traffic analysis shows strong temporal locality: 90% of requests are for a page that was also "
     "requested within the previous 5 minutes. Which cache eviction policy will minimize cache misses given "
     "this access pattern?",
     "FIFO -- evict whichever page entered the cache first, regardless of use",
     "LRU -- evict the page that was least recently requested",
     "Random eviction",
     "LFU based on total requests since the server started",
     1, "B"),

    ("LAT-19", "lateral_thinking", "hard",
     "A sorted list contains 1,000,000 distinct integers. Using binary search, what is the maximum number of "
     "comparisons needed in the worst case to determine whether a given value is present in the list?",
     "1,000", "1,000,000", "20", "500,000", 1, "C"),

    ("LAT-20", "lateral_thinking", "hard",
     "A delivery van starts at depot A and must visit stops B, C, D, and E exactly once each before returning "
     "to A. Using straight-line distances on a coordinate grid (in km): A(0,0), B(2,3), C(5,2), D(6,5), E(1,5). "
     "Which route minimizes the total distance traveled?",
     "A-B-C-D-E-A", "A-B-D-C-E-A", "A-E-B-C-D-A", "A-B-E-D-C-A", 1, "D"),

    # ================= SECTION B: QUANTITATIVE REASONING (INSIGHT WORD PROBLEMS) =================

    ("QR-01", "quant_reasoning", "medium",
     "Pipe A alone can fill a tank in 12 hours and Pipe B alone can fill it in 18 hours. Both pipes are opened "
     "together, and after some time Pipe A is shut off while Pipe B continues alone until the tank is "
     "completely full. If the tank takes a total of 15 hours to fill from empty, for how long was Pipe A "
     "open?",
     "2 hours", "3 hours", "5 hours", "10 hours", 1, "A"),

    ("QR-02", "quant_reasoning", "medium",
     "A train crosses a stationary pole in 15 seconds and crosses a 100-meter-long platform in 25 seconds, "
     "moving at constant speed throughout. What is the length of the train?",
     "100 m", "150 m", "200 m", "250 m", 1, "B"),

    ("QR-03", "quant_reasoning", "hard",
     "The present ages of A and B are in the ratio 3:4. Eight years from now, the ratio of their ages will be "
     "4:5. What is B's present age?",
     "24 years", "28 years", "36 years", "32 years", 1, "D"),

    ("QR-04", "quant_reasoning", "hard",
     "A vessel contains a mixture of milk and water in the ratio 5:3. If 16 liters of this mixture is removed "
     "and replaced with pure water, the new ratio of milk to water becomes 5:7. What was the initial quantity "
     "of mixture in the vessel?",
     "48 liters", "32 liters", "40 liters", "56 liters", 1, "A"),

    ("QR-05", "quant_reasoning", "hard",
     "A monkey starts at the bottom of a 30-meter pole. Each day it climbs up 5 meters, but each night -- "
     "except after the day it finally reaches the top -- it slips back down 3 meters. On which day does the "
     "monkey first reach the top of the pole?",
     "day 6", "day 13", "day 15", "day 14", 1, "D"),

    ("QR-06", "quant_reasoning", "medium",
     "A can complete a piece of work in 20 days. B is 25% more efficient than A. In how many days can B alone "
     "complete the same work?",
     "15 days", "16 days", "18 days", "25 days", 1, "B"),

    ("QR-07", "quant_reasoning", "hard",
     "A boat travels 30 km downstream in the same time it takes to travel 18 km upstream. If the speed of the "
     "stream is 4 km/h, what is the speed of the boat in still water?",
     "16 km/h", "12 km/h", "14 km/h", "20 km/h", 1, "A"),

    ("QR-08", "quant_reasoning", "hard",
     "A is twice as old as B was at the time when A was as old as B is now. The sum of their present ages is "
     "35 years. What is A's present age?",
     "15 years", "25 years", "20 years", "30 years", 1, "C"),

    ("QR-09", "quant_reasoning", "hard",
     "A tank contains 1,000 liters of pure milk. 100 liters of the mixture currently in the tank is drawn off "
     "and replaced with water; this draw-off-and-replace process is repeated for a total of 3 rounds. How much "
     "pure milk remains in the tank after the third replacement?",
     "700 liters", "810 liters", "900 liters", "729 liters", 1, "D"),

    ("QR-10", "quant_reasoning", "hard",
     "Between 3 o'clock and 4 o'clock, at what time will the minute hand and hour hand of a clock point in "
     "exactly opposite directions (180 degrees apart)?",
     "3:40", "3:45", "3:49 1/11", "3:54 6/11", 1, "C"),
]
