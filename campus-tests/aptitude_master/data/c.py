ROWS = [
    # ---------------- A. NUMBER / LETTER SERIES (insight-based) ----------------
    (
        "SER-01", "number_series", "hard",
        "Find the next term in the series: 2, 3, 7, 16, 32, 57, ?",
        "93", "82", "87", "92", 1, "A",
    ),
    (
        "SER-02", "number_series", "medium",
        "Find the next term in the series: 2, 5, 4, 8, 8, 11, ?",
        "14", "16", "12", "19", 1, "B",
    ),
    (
        "SER-03", "number_series", "hard",
        "Find the next term in the series: 3, 7, 16, 35, 74, 153, ?",
        "306", "311", "312", "313", 1, "C",
    ),
    (
        "SER-04", "number_series", "hard",
        "Find the next term in the series: 3, 4, 7, 10, 17, 20, ?",
        "31", "34", "28", "27", 1, "D",
    ),
    (
        "SER-05", "number_series", "hard",
        "Find the next term in the series: 5, 8, 17, 24, 37, 48, ?",
        "65", "64", "63", "66", 1, "A",
    ),
    (
        "SER-06", "number_series", "hard",
        "Find the next term in the series: 1, 7, 25, 61, 121, 211, ?",
        "336", "337", "343", "349", 1, "B",
    ),
    (
        "SER-07", "number_series", "hard",
        "Find the next term in the series: 4, 5, 6, 8, 11, 16, ?",
        "21", "23", "24", "25", 1, "C",
    ),
    (
        "SER-08", "number_series", "hard",
        "Find the next term in the series: 5, 10, 7, 14, 11, 22, ?",
        "44", "20", "25", "19", 1, "D",
    ),
    (
        "SER-09", "number_series", "hard",
        "Find the next term in the series: 19, 29, 40, 44, 52, 59, ?",
        "73", "66", "63", "68", 1, "A",
    ),
    (
        "SER-10", "number_series", "hard",
        "Find the next term in the series: 1, 3, 4, 6, 9, 10, ?",
        "15", "16", "13", "12", 1, "B",
    ),
    (
        "SER-11", "number_series", "hard",
        "Find the next term in the series: 2, 3, 8, 31, 154, 923, ?",
        "6461", "5537", "6460", "6467", 1, "C",
    ),
    (
        "SER-12", "number_series", "hard",
        "Find the next term in the series: 3, 5, 10, 12, 24, 26, ?",
        "28", "50", "27", "52", 1, "D",
    ),
    (
        "SER-13", "number_series", "hard",
        "Find the next term in the series: 3, 8, 24, 48, 120, 168, ?",
        "288", "289", "360", "224", 1, "A",
    ),
    (
        "SER-14", "number_series", "hard",
        "Find the missing letter in the series: A, D, I, P, Y, ?  (Hint: look at the alphabet position of each letter)",
        "L", "J", "Z", "K", 1, "B",
    ),
    (
        "SER-15", "number_series", "hard",
        "Find the next term in the series: 1, 2, 5, 10, 17, 26, ?",
        "35", "36", "37", "38", 1, "C",
    ),

    # ---------------- B. CODING-DECODING (advanced) ----------------
    (
        "CODE-01", "coding_decoding", "medium",
        "In a certain code, GARDEN is written as HCSEGO. Using the same coding rule, how is MOUNTAIN written in that code?",
        "NQWOUCKO", "OPVPVBJP", "NPVOUBJO", "OQWPVCKP", 1, "A",
    ),
    (
        "CODE-02", "coding_decoding", "hard",
        "In a code language, FLOWER is written as GKPVFQ. Using the same rule, how is CRICKET written?",
        "BSHDJFS", "DQJBLDU", "DSJDLFU", "BQHBJDS", 1, "B",
    ),
    (
        "CODE-03", "coding_decoding", "hard",
        "In a certain code, TABLE is written as JQGFY. Using the same coding logic, how is CHAIR written?",
        "RIAHC", "HMFNW", "WNFMH", "VMELG", 1, "C",
    ),
    (
        "CODE-04", "coding_decoding", "hard",
        "In a code, MONEY is written as NQQID. Using the same rule, how is DOUBT coded?",
        "DPWEX", "ISXDU", "GRXEW", "EQXFY", 1, "D",
    ),
    (
        "CODE-05", "coding_decoding", "hard",
        "In a certain code, BRAIN is written as ZJASN. Using the same rule, how is STONE written?",
        "IHMNW", "HGLMV", "GFKLU", "TUPOF", 1, "A",
    ),
    (
        "CODE-06", "coding_decoding", "hard",
        "In a code, STAR is written as TVCT. Using the same rule, how is CLOCK written?",
        "ENQEM", "DMPDL", "EMPDL", "DNQEM", 1, "D",
    ),
    (
        "CODE-07", "coding_decoding", "hard",
        "In a code, HOUSE is written as GPVTF. Using the same rule, how is PLANT written?",
        "QMZOU", "QMBOU", "OKBMS", "OKZMS", 1, "C",
    ),
    (
        "CODE-08", "coding_decoding", "hard",
        "In a certain numeric-letter code, BAT is written as DBN. Using the same rule, how is GOLD written?",
        "NDXH", "USJL", "MCWG", "IQNF", 1, "A",
    ),
    (
        "CODE-09", "coding_decoding", "hard",
        "Study the following coded pairs: BOOK is written as CQRO, and LAMP is written as MCPT. Using the same rule, how is CHAIR coded?",
        "CICLV", "DJDMW", "HLDKS", "HMFNW", 1, "B",
    ),
    (
        "CODE-10", "coding_decoding", "hard",
        "In a code, SILVER is written as UDYOHV. Using the same rule, how is PLANET written?",
        "SOZQDW", "SHMDKO", "QFKBIM", "WDQZOS", 1, "D",
    ),

    # ---------------- C. DATA INTERPRETATION (multi-step reasoning) ----------------
    (
        "DI-01", "data_interpretation", "hard",
        "GreenLeaf Foods reported the following quarterly revenue and total expenses (Rs. lakh) for FY2024: "
        "Q1: Revenue 500, Expenses 400. Q2: Revenue 100, Expenses 50. Q3: Revenue 100, Expenses 60. "
        "Q4: Revenue 100, Expenses 70. What is the company's overall profit margin (total profit as a "
        "percentage of total revenue) for the full year?",
        "27.5%", "35%", "20%", "30%", 1, "A",
    ),
    (
        "DI-02", "data_interpretation", "medium",
        "Using the GreenLeaf Foods data above (Q1: Revenue 500, Expenses 400; Q2: Revenue 100, Expenses 50; "
        "Q3: Revenue 100, Expenses 60; Q4: Revenue 100, Expenses 70), which quarter recorded the highest "
        "profit margin (profit as a percentage of that quarter's revenue)?",
        "Q1", "Q2", "Q3", "Q4", 1, "B",
    ),
    (
        "DI-03", "data_interpretation", "hard",
        "Using the GreenLeaf Foods data above, by what percentage did the profit fall from Q1 to Q4?",
        "80%", "60%", "70%", "75%", 1, "C",
    ),
    (
        "DI-04", "data_interpretation", "hard",
        "Using the GreenLeaf Foods data above, what is the ratio of total expenses to total revenue for "
        "FY2024, expressed in simplest form?",
        "3:4", "7:10", "29:41", "29:40", 1, "D",
    ),
    (
        "DI-05", "data_interpretation", "hard",
        "A student's marks (out of 100) and the weightage assigned to each subject are: "
        "Maths 90 (weight 3), Physics 75 (weight 2), Chemistry 80 (weight 2), English 60 (weight 1), "
        "Computer Science 95 (weight 2). What is the student's weighted average score?",
        "83", "80", "82", "85", 1, "A",
    ),
    (
        "DI-06", "data_interpretation", "hard",
        "Using the student's marks above (Maths 90 wt.3, Physics 75 wt.2, Chemistry 80 wt.2, English 60 wt.1, "
        "Computer Science 95 wt.2), the passing rule requires a weighted average of at least 75 AND no "
        "individual subject score below 50. Which statement is correct?",
        "The student fails because the weighted average is below 75.",
        "The student passes both conditions.",
        "The student fails because the English score is below 50.",
        "The student fails both conditions.", 1, "B",
    ),
    (
        "DI-07", "data_interpretation", "hard",
        "Using the student's marks above, if the weight for Computer Science is increased from 2 to 4 "
        "(all other marks and weights unchanged), by how many marks does the weighted average increase?",
        "1", "3", "2", "4", 1, "C",
    ),
    (
        "DI-08", "data_interpretation", "medium",
        "Using the student's marks above, which subject contributes the highest weighted marks "
        "(marks x weight) to the total weighted sum?",
        "Computer Science", "Chemistry", "Physics", "Maths", 1, "D",
    ),
    (
        "DI-09", "data_interpretation", "hard",
        "Three trains P, Q and R travel between the same two cities, 360 km apart. Train P covers the "
        "distance in 6 hours. Train Q's speed is 20 km/h more than Train P's speed. Train R takes 2 hours "
        "less than Train Q to cover the same distance. What is Train R's speed?",
        "144 km/h", "120 km/h", "150 km/h", "132 km/h", 1, "A",
    ),
    (
        "DI-10", "data_interpretation", "hard",
        "Using the train data above (Train P's speed and Train R's speed as derived), if Train P and Train "
        "R start simultaneously from the same city, travelling in the same direction, how far apart will "
        "they be after 2 hours?",
        "84 km", "168 km", "144 km", "408 km", 1, "B",
    ),
    (
        "DI-11", "data_interpretation", "medium",
        "Using the train data above, what is the ratio of Train Q's speed to Train P's speed?",
        "3:2", "5:4", "4:3", "6:5", 1, "C",
    ),
    (
        "DI-12", "data_interpretation", "hard",
        "Using the train data above, Train Q leaves the station 30 minutes after Train P, from the same "
        "station towards the same destination, both maintaining their respective speeds derived earlier. "
        "How far from the start does Train Q catch up with Train P, and does this happen before either "
        "train reaches the destination city 360 km away?",
        "150 km from the start; yes, before reaching the destination.",
        "120 km from the start; no, only after reaching the destination.",
        "180 km from the start; yes, before reaching the destination.",
        "120 km from the start; yes, before reaching the destination.", 1, "D",
    ),
    (
        "DI-13", "data_interpretation", "hard",
        "A store sells a jacket with marked price Rs. 2400. During a sale it offers a 20% discount, "
        "followed by an additional 10% discount on the already-reduced price (successive discounts). "
        "What is the final selling price of the jacket?",
        "Rs. 1728", "Rs. 1680", "Rs. 1920", "Rs. 1752", 1, "A",
    ),
    (
        "DI-14", "data_interpretation", "hard",
        "Using the jacket data above (marked price Rs. 2400, successive discounts of 20% then 10%), the "
        "store's cost price for the jacket is Rs. 1500. What is the store's profit percentage, based on "
        "the cost price?",
        "13%", "15.2%", "12%", "18%", 1, "B",
    ),
    (
        "DI-15", "data_interpretation", "hard",
        "Using the jacket data above, if the store had instead given a single flat discount equivalent in "
        "value to the two successive discounts (20% then 10%) combined, what percentage flat discount "
        "would that be, relative to the marked price?",
        "30%", "27%", "28%", "26%", 1, "C",
    ),
]
