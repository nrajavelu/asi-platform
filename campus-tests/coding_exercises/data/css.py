EXERCISES = [
    {
        "id": "CSS-01",
        "flavor": "debugging",
        "difficulty": "medium",
        "title": "Vertically Centered Login Card",
        "scenario": "A login page should show a card centered both horizontally and vertically in the browser window. The developer applied `flex` to the full-height wrapper but the card is still stuck at the top-left corner.",
        "code_reference": '<div class="flex h-screen bg-gray-100">\n  <div class="w-96 bg-white p-8 rounded-lg shadow-md">\n    <h2 class="text-xl font-bold">Sign in</h2>\n    <p>Email and password fields go here.</p>\n  </div>\n</div>',
        "tasks": [
            "Explain why the card is not centered given the current classes.",
            "Add the minimum utility classes needed to center the card both horizontally and vertically.",
            "Keep `h-screen` on the wrapper."
        ],
        "reference_solution_code": '<div class="flex h-screen items-center justify-center bg-gray-100">\n  <div class="w-96 bg-white p-8 rounded-lg shadow-md">\n    <h2 class="text-xl font-bold">Sign in</h2>\n    <p>Email and password fields go here.</p>\n  </div>\n</div>',
        "check_points": [
            "items-center is added for cross-axis (vertical) centering.",
            "justify-center is added for main-axis (horizontal) centering.",
            "h-screen is retained so the flex container actually has full viewport height to center within.",
            "No absolute positioning or margin hacks introduced."
        ],
        "common_mistakes": [
            "Adding only justify-center, assuming it centers on both axes.",
            "Confusing items- (cross-axis) with justify- (main-axis) in a row-direction flex container.",
            "Using text-center on the card, which only centers inline text, not the block itself.",
            "Removing h-screen, which removes the vertical space needed for centering to be visible."
        ],
        "rubric": [
            ["Correct items-center for vertical centering", 40],
            ["Correct justify-center for horizontal centering", 40],
            ["Explanation of axis distinction", 20]
        ]
    },
    {
        "id": "CSS-02",
        "flavor": "responsive",
        "difficulty": "medium",
        "title": "Responsive Photo Gallery Grid",
        "scenario": "A photo gallery currently always shows 4 columns via `grid-cols-4`, which squashes thumbnails into unreadably thin strips on mobile phones. It should show 1 column on small phones, 2 columns on tablets, and 4 columns on desktop.",
        "code_reference": '<div class="grid grid-cols-4 gap-4">\n  <img src="a.jpg" class="w-full"/>\n  <img src="b.jpg" class="w-full"/>\n  <img src="c.jpg" class="w-full"/>\n  <img src="d.jpg" class="w-full"/>\n</div>',
        "tasks": [
            "Rewrite the grid classes so the layout is mobile-first: 1 column by default.",
            "Add a breakpoint that switches to 2 columns for tablet-sized screens.",
            "Add a breakpoint that switches to 4 columns for large desktop screens.",
            "Keep a consistent gap between images at every size."
        ],
        "reference_solution_code": '<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">\n  <img src="a.jpg" class="w-full"/>\n  <img src="b.jpg" class="w-full"/>\n  <img src="c.jpg" class="w-full"/>\n  <img src="d.jpg" class="w-full"/>\n</div>',
        "check_points": [
            "Base (unprefixed) class is grid-cols-1 for mobile-first default.",
            "sm: breakpoint sets grid-cols-2.",
            "lg: breakpoint sets grid-cols-4.",
            "gap-4 (or similar) is present at every size, and grid (not flex) is used."
        ],
        "common_mistakes": [
            "Starting from grid-cols-4 and never overriding it, keeping mobile broken.",
            "Using md: instead of sm: for the 2-column tablet step (still valid but skips the intended breakpoint).",
            "Forgetting the unprefixed base class, leaving mobile at whatever grid-cols-4 was doing.",
            "Dropping gap-4, causing images to touch edge-to-edge."
        ],
        "rubric": [
            ["Correct base + sm + lg column classes", 60],
            ["Gap retained at all sizes", 15],
            ["Mobile-first ordering understanding", 25]
        ]
    },
    {
        "id": "CSS-03",
        "flavor": "component-variants",
        "difficulty": "medium",
        "title": "Card Component with Variant Modifiers",
        "scenario": "A design system needs a reusable card pattern. All cards share the same base look (white background, rounded corners, shadow, padding), but a 'featured' card needs a highlighted border and stronger shadow, and a 'compact' card needs reduced padding and smaller text for dense lists.",
        "code_reference": '<div class="p-6 rounded-lg shadow bg-white">\n  <h3 class="font-bold">Plan Name</h3>\n  <p>Plan description text.</p>\n</div>',
        "tasks": [
            "Write markup for a base card using the given classes.",
            "Write a 'featured' variant that adds a colored border and a stronger shadow while keeping the base look.",
            "Write a 'compact' variant that reduces padding and text size compared to the base."
        ],
        "reference_solution_code": '<div class="p-6 rounded-lg shadow bg-white">\n  <h3 class="font-bold">Standard Plan</h3>\n  <p>Plan description text.</p>\n</div>\n\n<div class="p-6 rounded-lg shadow-lg bg-white border-2 border-blue-500">\n  <h3 class="font-bold">Featured Plan</h3>\n  <p>Plan description text.</p>\n</div>\n\n<div class="p-2 rounded-lg shadow bg-white">\n  <h3 class="font-bold text-sm">Compact Plan</h3>\n  <p class="text-sm">Plan description text.</p>\n</div>',
        "check_points": [
            "Base classes (rounded-lg, bg-white, shadow family) stay consistent across all three cards.",
            "Featured variant visibly adds a border and a stronger shadow (shadow-lg) than the base.",
            "Compact variant clearly reduces padding (e.g. p-2 instead of p-6) and text size.",
            "No single element carries two contradictory sizing classes (e.g. both p-6 and p-2)."
        ],
        "common_mistakes": [
            "Applying both shadow and shadow-lg on the same element, relying on unpredictable class order instead of picking one.",
            "Forgetting rounded-lg on the featured or compact variant, breaking visual consistency of the family.",
            "Using inline style attributes instead of utility classes for the variant differences.",
            "Making the compact variant smaller only in padding but not in text size, defeating the density goal."
        ],
        "rubric": [
            ["Shared base classes stay consistent", 40],
            ["Featured variant correctness", 30],
            ["Compact variant correctness", 30]
        ]
    },
    {
        "id": "CSS-04",
        "flavor": "component-variants",
        "difficulty": "medium",
        "title": "Button Variant System",
        "scenario": "A team needs three buttons — primary, secondary, and danger — that share identical padding, rounding, and font weight, but differ in color, and each needs a hover state that is visibly distinct from its resting state.",
        "code_reference": '<button class="px-4 py-2">Primary</button>\n<button class="px-4 py-2">Secondary</button>\n<button class="px-4 py-2">Danger</button>',
        "tasks": [
            "Give all three buttons identical base spacing and rounding classes.",
            "Style Primary with a solid blue background and white text.",
            "Style Secondary as an outlined gray button with dark text.",
            "Style Danger with a solid red background, and give all three a hover state one shade darker."
        ],
        "reference_solution_code": '<button class="px-4 py-2 rounded font-medium bg-blue-600 text-white hover:bg-blue-700">Primary</button>\n<button class="px-4 py-2 rounded font-medium border border-gray-400 text-gray-700 hover:bg-gray-100">Secondary</button>\n<button class="px-4 py-2 rounded font-medium bg-red-600 text-white hover:bg-red-700">Danger</button>',
        "check_points": [
            "px-4 py-2 rounded font-medium (or equivalent) identical across all three buttons.",
            "Each variant has a distinct, correct background/border color for its purpose.",
            "hover: prefix is used, not a permanently-applied darker color.",
            "Text color contrasts correctly (white on solid colors, dark on the light secondary button)."
        ],
        "common_mistakes": [
            "Forgetting the hover: prefix and applying bg-blue-700 directly, making the button permanently dark.",
            "Giving each button different padding, breaking the shared base look.",
            "Leaving Secondary without a border, making it look like plain unstyled text.",
            "Using text-white on the Secondary button, making the label invisible against its light background."
        ],
        "rubric": [
            ["Shared base classes across variants", 30],
            ["Correct variant colors", 40],
            ["Correct hover states", 30]
        ]
    },
    {
        "id": "CSS-05",
        "flavor": "flexbox",
        "difficulty": "medium",
        "title": "Sticky Footer Layout",
        "scenario": "A page has a header, a main content area of variable length, and a footer. On pages with little content the footer should still sit at the bottom of the viewport; on pages with lots of content the footer should be pushed down naturally below it, never overlapping. Write plain CSS — no framework classes.",
        "code_reference": '<body>\n  <header>Site Header</header>\n  <main>Page content of varying length.</main>\n  <footer>Copyright 2026</footer>\n</body>',
        "tasks": [
            "Write plain CSS rules (not Tailwind) so the footer sticks to the bottom of the viewport when content is short.",
            "Make sure the footer is pushed down naturally, not overlapping, when content is long.",
            "Do not use position: fixed for the footer."
        ],
        "reference_solution_code": "body {\n  display: flex;\n  flex-direction: column;\n  min-height: 100vh;\n  margin: 0;\n}\n\nmain {\n  flex: 1;\n}",
        "check_points": [
            "body (or a wrapper) uses display: flex with flex-direction: column.",
            "min-height: 100vh is used (not height: 100vh, which would clip long content).",
            "main is given flex: 1 (or flex-grow: 1) so it expands to push the footer down.",
            "No position: fixed or position: absolute used on the footer."
        ],
        "common_mistakes": [
            "Using position: fixed on the footer, which overlaps short content instead of sitting below it.",
            "Using height: 100vh instead of min-height: 100vh, clipping content taller than the viewport.",
            "Forgetting flex-direction: column, leaving header/main/footer side by side in a row.",
            "Forgetting flex: 1 on main, so the footer does not get pushed to the bottom on short pages."
        ],
        "rubric": [
            ["flex column + min-height:100vh on wrapper", 40],
            ["flex:1 on main content", 40],
            ["Avoids fixed/absolute positioning hacks", 20]
        ]
    },
    {
        "id": "CSS-06",
        "flavor": "grid",
        "difficulty": "medium",
        "title": "Holy Grail Layout with CSS Grid",
        "scenario": "A classic app shell needs a full-width header on top, a full-width footer on bottom, a 200px left navigation sidebar, a flexible main content area, and a 150px right sidebar — all built with plain CSS Grid template areas, no framework.",
        "code_reference": '<div class="layout">\n  <header class="header">Header</header>\n  <nav class="nav">Nav</nav>\n  <main class="main">Main</main>\n  <aside class="aside">Aside</aside>\n  <footer class="footer">Footer</footer>\n</div>',
        "tasks": [
            "Define .layout as a CSS Grid with named template areas for header, nav, main, aside, and footer.",
            "Make the header and footer span the full width above and below the three middle columns.",
            "Size the nav column to 200px, the aside column to 150px, and let main take the remaining space.",
            "Assign each child element to its named grid area."
        ],
        "reference_solution_code": ".layout {\n  display: grid;\n  grid-template-columns: 200px 1fr 150px;\n  grid-template-rows: auto 1fr auto;\n  grid-template-areas:\n    \"header header header\"\n    \"nav main aside\"\n    \"footer footer footer\";\n  min-height: 100vh;\n}\n.header { grid-area: header; }\n.nav    { grid-area: nav; }\n.main   { grid-area: main; }\n.aside  { grid-area: aside; }\n.footer { grid-area: footer; }",
        "check_points": [
            "grid-template-areas rows each contain exactly 3 tokens, matching the 3 defined columns.",
            "grid-template-columns matches the layout: 200px / 1fr / 150px in the nav/main/aside order.",
            "header and footer area names repeat across all 3 column positions in their rows to span full width.",
            "Every child element has a grid-area declaration matching a name used in the template."
        ],
        "common_mistakes": [
            "Mismatched token counts per row versus the number of defined columns, which makes the whole grid-template-areas rule invalid.",
            "Forgetting to repeat 'header'/'footer' across all three columns, leaving them confined to one cell.",
            "Omitting grid-area on one of the child elements, so it falls back to normal auto-placement.",
            "Typo mismatch between a name used in grid-template-areas and the grid-area value on the element."
        ],
        "rubric": [
            ["Valid grid-template-areas syntax with consistent columns", 40],
            ["Correct column sizing (200px / 1fr / 150px)", 30],
            ["Correct grid-area assignment on every child", 30]
        ]
    },
    {
        "id": "CSS-07",
        "flavor": "debugging",
        "difficulty": "medium",
        "title": "Flex Child Text Overflow Bug",
        "scenario": "A file-row component shows an icon and a filename. The filename should truncate with an ellipsis when too long, and `truncate` is already applied, but the long filename still overflows the fixed-width row and breaks the layout instead of truncating.",
        "code_reference": '<div class="flex items-center gap-2 w-64 border p-2">\n  <svg class="w-5 h-5 shrink-0"></svg>\n  <span class="truncate">this-is-a-very-long-filename-that-should-truncate.pdf</span>\n</div>',
        "tasks": [
            "Explain why `truncate` is not taking effect on the flex child even though it is applied.",
            "Add exactly one utility class to fix the truncation.",
            "Keep the icon from shrinking when the filename is long."
        ],
        "reference_solution_code": '<div class="flex items-center gap-2 w-64 border p-2">\n  <svg class="w-5 h-5 shrink-0"></svg>\n  <span class="min-w-0 truncate">this-is-a-very-long-filename-that-should-truncate.pdf</span>\n</div>',
        "check_points": [
            "Candidate identifies that flex items default to min-width: auto, which prevents shrinking below their content's intrinsic width.",
            "min-w-0 is added to the span (the shrinking child), not the parent.",
            "truncate class is kept on the span.",
            "shrink-0 stays on the icon so only the text shrinks, not the icon."
        ],
        "common_mistakes": [
            "Adding overflow-hidden to the parent container instead of min-w-0 on the child, which does not fix the underlying flex sizing issue.",
            "Removing shrink-0 from the icon, letting the icon itself shrink or distort.",
            "Wrapping the text with break-all instead of truncating it to a single line.",
            "Not recognizing the flex min-width:auto default as the root cause."
        ],
        "rubric": [
            ["Correct diagnosis of the min-width:auto flex default", 40],
            ["Correct fix (min-w-0 on the shrinking child)", 40],
            ["Rest of the row layout (icon, gap, width) preserved", 20]
        ]
    },
    {
        "id": "CSS-08",
        "flavor": "bootstrap",
        "difficulty": "medium",
        "title": "Responsive Bootstrap Navbar",
        "scenario": "A marketing site needs a navbar that shows nav links inline on desktop but collapses behind a toggle button on mobile, built with Bootstrap 5 navbar components.",
        "code_reference": '<nav>\n  <a href="#">Brand</a>\n  <a href="#">Home</a>\n  <a href="#">About</a>\n  <a href="#">Contact</a>\n</nav>',
        "tasks": [
            "Build the navbar using Bootstrap's navbar, navbar-brand, and collapse components.",
            "Add a toggler button that shows only below the large breakpoint.",
            "Put the three nav links inside a properly structured nav-item/nav-link list that collapses on mobile."
        ],
        "reference_solution_code": '<nav class="navbar navbar-expand-lg navbar-light bg-light">\n  <div class="container">\n    <a class="navbar-brand" href="#">Brand</a>\n    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu">\n      <span class="navbar-toggler-icon"></span>\n    </button>\n    <div class="collapse navbar-collapse" id="navMenu">\n      <ul class="navbar-nav ms-auto">\n        <li class="nav-item"><a class="nav-link" href="#">Home</a></li>\n        <li class="nav-item"><a class="nav-link" href="#">About</a></li>\n        <li class="nav-item"><a class="nav-link" href="#">Contact</a></li>\n      </ul>\n    </div>\n  </div>\n</nav>',
        "check_points": [
            "navbar-expand-lg used to set the breakpoint at which the menu switches from collapsed to inline.",
            "data-bs-target on the toggler button matches the id on the collapse div.",
            "Links are structured as li.nav-item > a.nav-link inside ul.navbar-nav.",
            "container wraps the navbar content for centering and side padding."
        ],
        "common_mistakes": [
            "Mismatched data-bs-target and collapse div id, so the toggler does nothing.",
            "Forgetting the navbar-toggler-icon span inside the toggler button.",
            "Using plain div elements instead of ul/li for the nav-item structure.",
            "Omitting navbar-expand-{breakpoint}, so the menu is always collapsed or never collapses."
        ],
        "rubric": [
            ["Correct navbar/toggler/collapse structure", 50],
            ["Correct expand breakpoint class", 20],
            ["Correct nav-item/nav-link markup", 30]
        ]
    },
    {
        "id": "CSS-09",
        "flavor": "positioning",
        "difficulty": "medium",
        "title": "Status Badge Positioned on an Avatar",
        "scenario": "A small green online-status dot should sit at the bottom-right corner of a circular avatar, slightly overlapping its edge, with a white ring separating it from the avatar image behind it. Currently the badge just renders inline below the avatar.",
        "code_reference": '<div class="w-16 h-16 rounded-full bg-gray-300">\n  <span class="w-4 h-4 bg-green-500 rounded-full"></span>\n</div>',
        "tasks": [
            "Position the badge at the bottom-right corner of the avatar circle.",
            "Add a white border ring around the badge so it stands out from the avatar behind it.",
            "Use relative/absolute positioning utilities, not manual margins."
        ],
        "reference_solution_code": '<div class="relative w-16 h-16 rounded-full bg-gray-300">\n  <span class="absolute bottom-0 right-0 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></span>\n</div>',
        "check_points": [
            "relative added on the avatar parent.",
            "absolute added on the badge.",
            "bottom-0 right-0 used to pin the badge to the bottom-right corner.",
            "border-2 border-white added for contrast against the avatar."
        ],
        "common_mistakes": [
            "Forgetting relative on the parent, so the badge positions relative to the nearest positioned ancestor or the viewport instead.",
            "Using top-0 left-0 instead of bottom-0 right-0, placing the badge in the wrong corner.",
            "Forgetting rounded-full on the badge itself, leaving it square.",
            "Using margin-based offsets instead of absolute positioning, which breaks at different avatar sizes."
        ],
        "rubric": [
            ["relative/absolute pairing on parent/child", 40],
            ["Correct corner offset classes", 35],
            ["White border ring for contrast", 25]
        ]
    },
    {
        "id": "CSS-10",
        "flavor": "positioning",
        "difficulty": "medium",
        "title": "Sticky Table Header on Scroll",
        "scenario": "A data table lives inside a scrollable panel with a bounded height. As users scroll through many rows, the column header row should stay pinned to the top of the panel instead of scrolling out of view.",
        "code_reference": '<div class="max-h-96 overflow-y-auto">\n  <table class="w-full">\n    <thead>\n      <tr><th class="p-2">Name</th><th class="p-2">Score</th></tr>\n    </thead>\n    <tbody>...</tbody>\n  </table>\n</div>',
        "tasks": [
            "Make the header row stick to the top of the scrollable panel while the body scrolls beneath it.",
            "Give the header a background color so scrolled rows don't show through underneath it.",
            "Keep the scrollable container's bounded height and overflow behavior."
        ],
        "reference_solution_code": '<div class="max-h-96 overflow-y-auto">\n  <table class="w-full">\n    <thead class="sticky top-0 bg-white shadow">\n      <tr><th class="p-2">Name</th><th class="p-2">Score</th></tr>\n    </thead>\n    <tbody>...</tbody>\n  </table>\n</div>',
        "check_points": [
            "sticky and top-0 applied to the thead (or its row).",
            "The scrollable ancestor keeps overflow-y-auto and a bounded height (max-h-96).",
            "A background color (bg-white or similar) is set on the sticky header.",
            "th padding and table structure otherwise unchanged."
        ],
        "common_mistakes": [
            "Using fixed instead of sticky, detaching the header from the table's own scroll container entirely.",
            "Forgetting a background color, so scrolled body rows visually show through the header text.",
            "Applying sticky to the whole table element instead of the thead/tr.",
            "Removing the bounded height/overflow on the ancestor, leaving sticky with no scrolling context to stick within."
        ],
        "rubric": [
            ["sticky + top-0 on header", 40],
            ["Scroll container setup preserved", 30],
            ["Background color fix for overlap", 30]
        ]
    },
    {
        "id": "CSS-11",
        "flavor": "responsive",
        "difficulty": "medium",
        "title": "Responsive Typography for a Hero Heading",
        "scenario": "A marketing hero heading is a single fixed large size (`text-5xl`), which wraps awkwardly on mobile screens and looks too small relative to the hero image on large desktop monitors.",
        "code_reference": '<h1 class="text-5xl font-bold">Build faster with our platform</h1>',
        "tasks": [
            "Apply a smaller base font size for mobile.",
            "Scale the heading up at the sm and lg breakpoints in ascending order.",
            "Constrain the heading's line length with a max-width utility so lines don't run too wide on large screens."
        ],
        "reference_solution_code": '<h1 class="text-3xl sm:text-4xl lg:text-6xl font-bold max-w-2xl leading-tight">Build faster with our platform</h1>',
        "check_points": [
            "Base (mobile) size is smaller than the original text-5xl, e.g. text-3xl.",
            "sm: and lg: breakpoints increase the size in ascending order.",
            "A max-w-* utility constrains line length.",
            "A tighter leading (line-height) utility is considered appropriate for a large heading."
        ],
        "common_mistakes": [
            "Breakpoint sizes not in ascending order (e.g. the lg: size accidentally smaller than the sm: size).",
            "Omitting the unprefixed base class, leaving mobile at the browser default size instead of an intentional smaller size.",
            "Missing a max-w-* constraint, causing very long unreadable lines on wide screens.",
            "Using px-based margin instead of a width constraint to try to limit line length."
        ],
        "rubric": [
            ["Correct ascending responsive text sizes", 50],
            ["max-width constraint added", 25],
            ["Leading/line-height consideration", 25]
        ]
    },
    {
        "id": "CSS-12",
        "flavor": "spacing",
        "difficulty": "medium",
        "title": "Consistent Vertical Spacing in a Form",
        "scenario": "A stacked form has inconsistent gaps between its field groups because each field div carries a different, ad-hoc margin class (or none at all).",
        "code_reference": '<form>\n  <div class="mb-1"><label>Name</label><input class="border w-full"/></div>\n  <div><label>Email</label><input class="border w-full"/></div>\n  <div class="mb-5"><label>Password</label><input class="border w-full"/></div>\n</form>',
        "tasks": [
            "Remove the inconsistent per-field margin classes.",
            "Apply a single spacing utility to the form so every field group gets uniform vertical spacing automatically.",
            "Explain which siblings the spacing utility actually applies margin to."
        ],
        "reference_solution_code": '<form class="space-y-4">\n  <div><label>Name</label><input class="border w-full"/></div>\n  <div><label>Email</label><input class="border w-full"/></div>\n  <div><label>Password</label><input class="border w-full"/></div>\n</form>',
        "check_points": [
            "space-y-4 (or similar single value) applied to the form.",
            "Individual mb-1 / mb-5 classes removed from the children.",
            "The same spacing value is used consistently rather than mixed values.",
            "Candidate understands space-y-* only adds margin-top to non-first children."
        ],
        "common_mistakes": [
            "Leaving the old mb-1/mb-5 classes on children alongside space-y-4, causing uneven doubled gaps.",
            "Applying space-y-4 to a flex-row container, where it has no visible effect without flex-col since it targets vertical stacking.",
            "Expecting space-y-4 to add padding instead of margin between siblings.",
            "Assuming space-y-4 also adds spacing above the first field or below the last."
        ],
        "rubric": [
            ["Correct space-y-4 usage on parent", 45],
            ["Removal of conflicting per-child margins", 35],
            ["Understanding of sibling-only application", 20]
        ]
    },
    {
        "id": "CSS-13",
        "flavor": "bootstrap",
        "difficulty": "medium",
        "title": "Bootstrap Responsive Column Layout",
        "scenario": "A product listing page needs cards that show 1 per row on mobile, 2 per row on tablets, and 3 per row on desktop, using the Bootstrap grid system.",
        "code_reference": '<div class="row">\n  <div class="col"><div class="card">Product A</div></div>\n  <div class="col"><div class="card">Product B</div></div>\n  <div class="col"><div class="card">Product C</div></div>\n</div>',
        "tasks": [
            "Wrap the row in a container.",
            "Apply column classes so cards are full-width on mobile, 2-per-row on medium screens, and 3-per-row on large screens.",
            "Add gutter spacing between the cards."
        ],
        "reference_solution_code": '<div class="container">\n  <div class="row g-3">\n    <div class="col-12 col-md-6 col-lg-4"><div class="card">Product A</div></div>\n    <div class="col-12 col-md-6 col-lg-4"><div class="card">Product B</div></div>\n    <div class="col-12 col-md-6 col-lg-4"><div class="card">Product C</div></div>\n  </div>\n</div>',
        "check_points": [
            "col-12 used as the mobile-first full-width base.",
            "col-md-6 produces 2 cards per row on medium screens.",
            "col-lg-4 produces 3 cards per row on large screens (12/4=3).",
            "row is wrapped inside a container, and a gutter class like g-3 is applied."
        ],
        "common_mistakes": [
            "Using col-md-4 without a col-12 base, leaving mobile behavior undefined or relying on auto-sizing instead of explicit full width.",
            "Column math error, e.g. col-lg-3 giving 4 per row instead of the requested 3.",
            "Forgetting the .row wrapper around the .col elements, breaking the grid's negative-margin gutter system.",
            "Omitting the container, causing content to touch the viewport edges."
        ],
        "rubric": [
            ["Correct column breakpoint math", 55],
            ["Row/container structure correct", 25],
            ["Gutter spacing applied", 20]
        ]
    },
    {
        "id": "CSS-14",
        "flavor": "debugging",
        "difficulty": "medium",
        "title": "Flex Items Not Wrapping to a New Line",
        "scenario": "A tag/chip list inside a fixed-width container should wrap onto multiple lines as more tags are added, but currently all tags are being squeezed onto a single line and overflow horizontally past the container border.",
        "code_reference": '<div class="flex gap-2 w-80 border p-2">\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Design</span>\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Engineering</span>\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Marketing</span>\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Sales</span>\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Support</span>\n</div>',
        "tasks": [
            "Identify the default flex behavior causing the overflow.",
            "Fix the container so tags wrap onto additional lines instead of overflowing.",
            "Ensure there is visible gap between wrapped lines, not just between items on the same line."
        ],
        "reference_solution_code": '<div class="flex flex-wrap gap-2 w-80 border p-2">\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Design</span>\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Engineering</span>\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Marketing</span>\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Sales</span>\n  <span class="px-3 py-1 bg-gray-200 rounded-full">Support</span>\n</div>',
        "check_points": [
            "flex-wrap added to the container.",
            "gap-2 (single gap utility) is recognized as covering spacing on both the row axis and between wrapped lines.",
            "w-80 and border are retained, keeping the container's bounded width.",
            "Candidate names the default flex-nowrap as the root cause."
        ],
        "common_mistakes": [
            "Removing the width constraint instead of adding flex-wrap, defeating the purpose of a bounded container.",
            "Using flex-wrap-reverse instead of flex-wrap, unnecessarily reversing row order.",
            "Assuming gap doesn't apply to wrapped rows and manually adding extra margin classes instead.",
            "Not recognizing flex-nowrap as the default behavior causing the overflow in the first place."
        ],
        "rubric": [
            ["flex-wrap added", 50],
            ["Gap spacing correct on both axes", 30],
            ["Container width/border preserved", 20]
        ]
    },
    {
        "id": "CSS-15",
        "flavor": "grid",
        "difficulty": "medium",
        "title": "Dashboard Layout with Named Grid Areas",
        "scenario": "An analytics dashboard needs a fixed-width sidebar spanning the full height, a topbar across the remaining width, a large main chart area, and two smaller stacked stat widgets to the right of the chart — all with plain CSS Grid, no framework.",
        "code_reference": '<div class="dashboard">\n  <div class="sidebar">Sidebar</div>\n  <div class="topbar">Topbar</div>\n  <div class="main">Chart</div>\n  <div class="stat1">Stat 1</div>\n  <div class="stat2">Stat 2</div>\n</div>',
        "tasks": [
            "Write a grid-template-areas layout where the sidebar spans the full height on the left.",
            "Make the topbar span the remaining width above the chart and stat widgets.",
            "Make the main chart area span two rows on the left of the remaining content, with stat1 and stat2 stacked in a narrower column on the right.",
            "Assign each element its grid-area."
        ],
        "reference_solution_code": '.dashboard {\n  display: grid;\n  grid-template-columns: 220px 2fr 1fr;\n  grid-template-rows: 60px 1fr 1fr;\n  grid-template-areas:\n    "sidebar topbar topbar"\n    "sidebar main   stat1"\n    "sidebar main   stat2";\n  min-height: 100vh;\n  gap: 1rem;\n}\n.sidebar { grid-area: sidebar; }\n.topbar  { grid-area: topbar; }\n.main    { grid-area: main; }\n.stat1   { grid-area: stat1; }\n.stat2   { grid-area: stat2; }',
        "check_points": [
            "sidebar area name repeats in all three row strings, spanning the full grid height.",
            "topbar spans the remaining two columns in the first row.",
            "main area name repeats across rows 2 and 3 to span two rows.",
            "Each row string in grid-template-areas has exactly 3 tokens, matching grid-template-columns."
        ],
        "common_mistakes": [
            "Row strings with inconsistent token counts across rows, invalidating the whole grid-template-areas rule.",
            "Forgetting to repeat 'sidebar' in every row, leaving it confined to a single cell.",
            "Not applying grid-area to one or more of the child elements.",
            "Confusing the order of grid-template-columns and grid-template-rows values."
        ],
        "rubric": [
            ["Valid template-areas with consistent columns", 40],
            ["Correct area spans (sidebar full height, main 2 rows)", 40],
            ["Correct grid-area assignment on children", 20]
        ]
    },
    {
        "id": "CSS-16",
        "flavor": "tailwind-layout",
        "difficulty": "medium",
        "title": "Uniform Aspect-Ratio Image Cards",
        "scenario": "A product image grid looks jagged because source images have inconsistent aspect ratios. Every image should be forced into a consistent square shape and cropped to fill the box without stretching or distorting.",
        "code_reference": '<div class="grid grid-cols-3 gap-4">\n  <img src="a.jpg" class="w-full"/>\n  <img src="b.jpg" class="w-full"/>\n  <img src="c.jpg" class="w-full"/>\n</div>',
        "tasks": [
            "Force each image into a consistent 1:1 square aspect ratio.",
            "Ensure the image fills the square box completely by cropping rather than stretching.",
            "Keep the grid responsive by not using a fixed pixel height."
        ],
        "reference_solution_code": '<div class="grid grid-cols-3 gap-4">\n  <img src="a.jpg" class="w-full aspect-square object-cover"/>\n  <img src="b.jpg" class="w-full aspect-square object-cover"/>\n  <img src="c.jpg" class="w-full aspect-square object-cover"/>\n</div>',
        "check_points": [
            "aspect-square applied to each image for a consistent 1:1 ratio.",
            "object-cover used so the image crops to fill the box without distortion.",
            "w-full retained so aspect-square has a width basis to compute height from.",
            "grid-cols-3 layout left unchanged."
        ],
        "common_mistakes": [
            "Using object-contain instead of object-cover, leaving empty letterboxed space instead of filling the box.",
            "Dropping w-full, leaving aspect-square with no defined width to compute a height from.",
            "Setting a fixed h-* value instead of aspect-square, breaking consistency across responsive column widths.",
            "Forgetting object-cover entirely, leaving the image stretched/distorted to fit the square."
        ],
        "rubric": [
            ["aspect-square applied correctly", 40],
            ["object-cover applied correctly", 40],
            ["Responsive width retained (no fixed height)", 20]
        ]
    },
    {
        "id": "CSS-17",
        "flavor": "positioning",
        "difficulty": "medium",
        "title": "Modal Overlay Centering with Z-Index",
        "scenario": "A confirmation modal should appear centered on screen above a dimmed backdrop covering the entire page. Currently the modal renders at the top-left of its container and the backdrop does not cover the full page. Write plain CSS.",
        "code_reference": '<div class="overlay">\n  <div class="modal">Are you sure you want to delete this item?</div>\n</div>',
        "tasks": [
            "Write CSS for .overlay so it covers the full viewport with a dimmed, semi-transparent background regardless of page scroll position.",
            "Center .modal within the overlay using Flexbox.",
            "Make sure the overlay stacks above all other page content using z-index."
        ],
        "reference_solution_code": ".overlay {\n  position: fixed;\n  inset: 0;\n  background: rgba(0, 0, 0, 0.5);\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  z-index: 50;\n}\n\n.modal {\n  background: white;\n  padding: 2rem;\n  border-radius: 8px;\n  max-width: 400px;\n  width: 90%;\n}",
        "check_points": [
            "overlay uses position: fixed with inset: 0 (or all four offsets set to 0) to cover the full viewport regardless of scroll.",
            "overlay is a flex container with align-items and justify-content set to center the modal.",
            "z-index is set high enough on the overlay to sit above normal page content.",
            "modal has a solid, contrasting background so it reads clearly against the dimmed backdrop."
        ],
        "common_mistakes": [
            "Using position: absolute instead of fixed, tying the overlay to its nearest positioned ancestor instead of the viewport, breaking full-page coverage on scroll.",
            "Forgetting z-index, so the overlay renders behind other stacked page content.",
            "Trying to center the modal with margin: auto alone without a flex or defined height context, which fails vertically.",
            "Using an opaque background color instead of a semi-transparent rgba value for the dimming effect."
        ],
        "rubric": [
            ["Fixed full-screen overlay with inset:0", 35],
            ["Flex centering of modal", 35],
            ["Correct z-index/stacking", 30]
        ]
    },
    {
        "id": "CSS-18",
        "flavor": "tailwind-layout",
        "difficulty": "medium",
        "title": "Divided Settings List",
        "scenario": "A settings list of options should show a thin horizontal divider line between each row, but no divider above the first item or below the last one. Manually adding borders to every list item would put an extra line at the bottom.",
        "code_reference": '<ul class="border rounded-lg">\n  <li class="p-4">Notifications</li>\n  <li class="p-4">Privacy</li>\n  <li class="p-4">Security</li>\n</ul>',
        "tasks": [
            "Add dividers between the list items only, not around the outside of the list, using a single utility on the parent.",
            "Keep the existing outer border and rounded corners on the list.",
            "Specify a visible divider color."
        ],
        "reference_solution_code": '<ul class="border rounded-lg divide-y divide-gray-200">\n  <li class="p-4">Notifications</li>\n  <li class="p-4">Privacy</li>\n  <li class="p-4">Security</li>\n</ul>',
        "check_points": [
            "divide-y applied to the parent ul.",
            "A divide color class (e.g. divide-gray-200) is specified.",
            "The outer border and rounded-lg remain unchanged on the list.",
            "No manual border-b classes added to individual li elements."
        ],
        "common_mistakes": [
            "Adding border-b to every li including the last one, creating an extra unwanted line that duplicates the outer border.",
            "Using divide-x instead of divide-y, which is the wrong axis for a vertically stacked list.",
            "Forgetting a divide color class, leaving dividers effectively invisible.",
            "Removing the outer border thinking divide-y replaces it."
        ],
        "rubric": [
            ["divide-y on parent list", 45],
            ["Divide color specified", 30],
            ["No redundant per-item borders", 25]
        ]
    },
    {
        "id": "CSS-19",
        "flavor": "bootstrap",
        "difficulty": "medium",
        "title": "Equal-Height Pricing Card Grid",
        "scenario": "Three pricing cards in a Bootstrap row have different amounts of text, so they currently render with mismatched heights, looking uneven. They should all stretch to match the tallest card in the row.",
        "code_reference": '<div class="row">\n  <div class="col-md-4"><div class="card"><div class="card-body">Short text</div></div></div>\n  <div class="col-md-4"><div class="card"><div class="card-body">A much longer paragraph of text that wraps across multiple lines.</div></div></div>\n  <div class="col-md-4"><div class="card"><div class="card-body">Medium length text</div></div></div>\n</div>',
        "tasks": [
            "Make all three cards stretch to equal height without hardcoding a pixel height.",
            "Rely on Bootstrap's row/column flex behavior rather than a fixed-height hack.",
            "Keep consistent gutter spacing between the cards."
        ],
        "reference_solution_code": '<div class="row g-3">\n  <div class="col-md-4 d-flex"><div class="card w-100"><div class="card-body">Short text</div></div></div>\n  <div class="col-md-4 d-flex"><div class="card w-100"><div class="card-body">A much longer paragraph of text that wraps across multiple lines.</div></div></div>\n  <div class="col-md-4 d-flex"><div class="card w-100"><div class="card-body">Medium length text</div></div></div>\n</div>',
        "check_points": [
            "Candidate relies on the fact that .row is already a flex container with default stretch behavior across its columns.",
            "d-flex is added to each column and w-100 to each card so the card fills the stretched column's full height and width.",
            "g-3 gutter class retained for spacing.",
            "No fixed pixel height applied to the cards."
        ],
        "common_mistakes": [
            "Setting a fixed height (e.g. height: 300px) on the cards, which breaks on longer text or different screen sizes.",
            "Not realizing Bootstrap rows are already flex containers, and adding unnecessary float or clearfix hacks instead.",
            "Forgetting w-100 on the card, so it doesn't fill the stretched flex column's width and height.",
            "Applying d-flex to the card itself instead of the surrounding column."
        ],
        "rubric": [
            ["Correct use of row's flex-stretch behavior", 50],
            ["Card fills column via d-flex + w-100", 30],
            ["No fixed-height hack used", 20]
        ]
    },
    {
        "id": "CSS-20",
        "flavor": "flexbox",
        "difficulty": "medium",
        "title": "Equal Height Columns Without Explicit Heights",
        "scenario": "Three sidebar/content/aside columns with differing content lengths need matching background heights so the layout looks like solid equal-height columns, without hardcoding any pixel heights. Write plain CSS.",
        "code_reference": '<div class="columns">\n  <div class="col-a">Short</div>\n  <div class="col-b">Much longer content spanning several lines of text.</div>\n  <div class="col-c">Medium length content</div>\n</div>',
        "tasks": [
            "Write plain CSS so all three columns automatically match the height of the tallest column.",
            "Distribute the columns to share the row's width equally.",
            "Explain why this works without any explicit height property."
        ],
        "reference_solution_code": ".columns {\n  display: flex;\n}\n\n.col-a, .col-b, .col-c {\n  flex: 1;\n  padding: 1rem;\n}",
        "check_points": [
            "Parent .columns set to display: flex.",
            "Columns given flex: 1 to share width equally.",
            "No explicit height or height:100% needed — candidate relies on (or explicitly restates) the default align-items: stretch behavior.",
            "Candidate can explain why flex containers equalize child height by default in the row direction."
        ],
        "common_mistakes": [
            "Using float: left on the columns, a classic pre-flexbox pattern that does not equalize height at all.",
            "Explicitly setting align-items: flex-start, which overrides the helpful default stretch behavior and reintroduces uneven heights.",
            "Hardcoding a fixed height value instead of relying on flex's stretch default.",
            "Forgetting flex: 1, leaving columns sized only to their content width instead of sharing the row evenly."
        ],
        "rubric": [
            ["display:flex on parent", 40],
            ["flex:1 for equal width distribution", 30],
            ["Correct reasoning about the stretch default", 30]
        ]
    },
    {
        "id": "CSS-21",
        "flavor": "debugging",
        "difficulty": "medium",
        "title": "Container Not Centering on Wide Screens",
        "scenario": "A page section should be centered with a constrained max width on large monitors, but it stays flush against the left edge of the browser window no matter how wide the screen is.",
        "code_reference": '<div class="max-w-4xl px-4">\n  <h1>Welcome</h1>\n  <p>Section content goes here.</p>\n</div>',
        "tasks": [
            "Fix the class list so the section is horizontally centered in the viewport.",
            "Keep the existing max-width constraint and inner padding.",
            "Explain why the fix works and why margin-based centering needs a bounded width."
        ],
        "reference_solution_code": '<div class="max-w-4xl mx-auto px-4">\n  <h1>Welcome</h1>\n  <p>Section content goes here.</p>\n</div>',
        "check_points": [
            "mx-auto added to the div.",
            "max-w-4xl retained, since mx-auto has no visible centering effect on a full-width block.",
            "px-4 inner padding retained.",
            "Candidate explains margin:auto centering requires a constrained width to have any visible effect."
        ],
        "common_mistakes": [
            "Adding justify-center or items-center, which only work inside a flex or grid parent, not on a plain block-level div by itself.",
            "Removing max-w-4xl, leaving the div full-width with no visible effect from mx-auto.",
            "Using text-center, which centers inline content/text but not the block container itself.",
            "Wrapping in a new flex parent instead of using the simpler mx-auto fix."
        ],
        "rubric": [
            ["mx-auto added correctly", 50],
            ["Understanding of the max-width prerequisite", 30],
            ["Padding retained", 20]
        ]
    },
    {
        "id": "CSS-22",
        "flavor": "grid",
        "difficulty": "medium",
        "title": "Auto-Responsive Card Grid Without Media Queries",
        "scenario": "A card grid should automatically add or remove columns as the browser window is resized, without writing any breakpoint-specific media queries, while keeping every card at least 220px wide. Write plain CSS.",
        "code_reference": '<div class="card-grid">\n  <div class="card">Card 1</div>\n  <div class="card">Card 2</div>\n  <div class="card">Card 3</div>\n  <div class="card">Card 4</div>\n</div>',
        "tasks": [
            "Write a single grid-template-columns declaration that produces fluid, responsive columns with no media queries.",
            "Ensure each card is never narrower than 220px.",
            "Add consistent spacing between cards."
        ],
        "reference_solution_code": ".card-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));\n  gap: 1rem;\n}",
        "check_points": [
            "Uses repeat() together with auto-fit (or auto-fill).",
            "minmax(220px, 1fr) sets the minimum card width and lets columns grow to fill remaining space.",
            "gap property set for spacing between cards.",
            "No media queries used, satisfying the fluid/no-breakpoint requirement."
        ],
        "common_mistakes": [
            "Using a fixed repeat(4, 1fr) with manual media queries to change the column count at each breakpoint, which works but does not satisfy the no-media-query fluid requirement.",
            "Using auto-fill instead of auto-fit when the design wants existing items to stretch and fill leftover space rather than leaving invisible empty tracks.",
            "Omitting the minmax lower bound, letting columns shrink below a readable width on narrow screens.",
            "Using percentage-based fixed columns instead of minmax, losing the auto column count adjustment."
        ],
        "rubric": [
            ["Correct repeat(auto-fit, minmax()) syntax", 55],
            ["Appropriate min/max values", 25],
            ["Gap and no-media-query requirement met", 20]
        ]
    },
    {
        "id": "CSS-23",
        "flavor": "tailwind-layout",
        "difficulty": "medium",
        "title": "Aligned Label-Input Form Rows",
        "scenario": "A settings form has label/input pairs arranged in flex rows, but labels of different text lengths (like 'Email Address' versus 'Phone') push the inputs out of alignment, so the input column looks ragged instead of forming a clean vertical line.",
        "code_reference": '<form>\n  <div class="flex gap-2"><label>Name</label><input class="border flex-1"/></div>\n  <div class="flex gap-2"><label>Email Address</label><input class="border flex-1"/></div>\n  <div class="flex gap-2"><label>Phone</label><input class="border flex-1"/></div>\n</form>',
        "tasks": [
            "Give every label a consistent fixed width so the inputs align into a clean column.",
            "Prevent longer label text from shrinking below the fixed width.",
            "Keep the inputs filling the remaining row width."
        ],
        "reference_solution_code": '<form class="space-y-2">\n  <div class="flex gap-2"><label class="w-32 shrink-0">Name</label><input class="border flex-1"/></div>\n  <div class="flex gap-2"><label class="w-32 shrink-0">Email Address</label><input class="border flex-1"/></div>\n  <div class="flex gap-2"><label class="w-32 shrink-0">Phone</label><input class="border flex-1"/></div>\n</form>',
        "check_points": [
            "A fixed width (e.g. w-32) is applied consistently to every label.",
            "shrink-0 added on each label so long text like 'Email Address' does not shrink below the fixed width.",
            "flex-1 retained on each input to fill the remaining row width.",
            "The same width value is used across all rows for true alignment."
        ],
        "common_mistakes": [
            "Using different width values per label row instead of one consistent value across all rows.",
            "Forgetting shrink-0, so the longer 'Email Address' label shrinks below its intended width, breaking alignment.",
            "Setting the width on the input instead of the label.",
            "Using min-w-32 instead of w-32, allowing labels to still vary in width based on content."
        ],
        "rubric": [
            ["Consistent fixed label width across rows", 45],
            ["shrink-0 to prevent label shrinking", 30],
            ["Input flex-1 retained", 25]
        ]
    },
    {
        "id": "CSS-24",
        "flavor": "tailwind-layout",
        "difficulty": "medium",
        "title": "Multi-Line Text Truncation for Card Descriptions",
        "scenario": "Blog preview cards have descriptions of varying length. Each card's description should show at most 3 lines with an ellipsis when the text is longer, so cards in the same row stay a uniform height.",
        "code_reference": '<div class="grid grid-cols-3 gap-4">\n  <div class="p-4 border rounded">\n    <h3 class="font-bold">Title</h3>\n    <p>A long description that could run to many lines and break the card grid\'s uniform height across the row.</p>\n  </div>\n</div>',
        "tasks": [
            "Constrain the description paragraph to a maximum of 3 lines with an ellipsis when truncated.",
            "Explain why a single-line truncate utility would not satisfy this requirement.",
            "Keep the surrounding grid layout unchanged."
        ],
        "reference_solution_code": '<div class="grid grid-cols-3 gap-4">\n  <div class="p-4 border rounded">\n    <h3 class="font-bold">Title</h3>\n    <p class="line-clamp-3">A long description that could run to many lines and break the card grid\'s uniform height across the row.</p>\n  </div>\n</div>',
        "check_points": [
            "line-clamp-3 applied to the description paragraph.",
            "Candidate explains truncate only clamps to a single line and is insufficient here.",
            "grid-cols-3 gap-4 layout left unchanged.",
            "Ellipsis behavior is expected to appear at the 3rd line cutoff."
        ],
        "common_mistakes": [
            "Using truncate instead of line-clamp-3, which only handles single-line clamping via white-space:nowrap.",
            "Using overflow-hidden alone without line-clamp-3, which hides overflow abruptly with no ellipsis and no reliable line count.",
            "Picking an arbitrary max-height in pixels instead of line-clamp-3, which doesn't guarantee a whole-line cutoff or ellipsis.",
            "Forgetting that line-clamp requires the text to actually be a block of wrapped text, not a single inline span."
        ],
        "rubric": [
            ["Correct line-clamp-3 usage", 55],
            ["Correct reasoning versus single-line truncate", 25],
            ["Surrounding layout preserved", 20]
        ]
    },
    {
        "id": "CSS-25",
        "flavor": "bootstrap",
        "difficulty": "medium",
        "title": "Bootstrap Toolbar Alignment",
        "scenario": "A document library toolbar should show a title on the far left and two action buttons grouped together on the far right, vertically centered. Currently the title and buttons are stacked vertically on the left because no flex utilities are applied.",
        "code_reference": '<div class="toolbar p-2 border-bottom">\n  <h5>Documents</h5>\n  <button class="btn btn-primary">New</button>\n  <button class="btn btn-outline-secondary">Import</button>\n</div>',
        "tasks": [
            "Use Bootstrap flex utilities to push the title to the left and the button group to the right.",
            "Keep the two buttons grouped together as a single unit rather than spread apart.",
            "Vertically center all items in the toolbar, and add a small gap between the two buttons."
        ],
        "reference_solution_code": '<div class="toolbar p-2 border-bottom d-flex justify-content-between align-items-center">\n  <h5 class="mb-0">Documents</h5>\n  <div class="d-flex gap-2">\n    <button class="btn btn-primary">New</button>\n    <button class="btn btn-outline-secondary">Import</button>\n  </div>\n</div>',
        "check_points": [
            "d-flex applied to the outer toolbar.",
            "justify-content-between used to push the title and the button group to opposite ends.",
            "align-items-center used for vertical alignment.",
            "The two buttons are wrapped in their own d-flex gap-2 sub-container so they stay grouped together on the right."
        ],
        "common_mistakes": [
            "Applying justify-content-between directly across all three items (title, btn, btn) instead of grouping the buttons, which spreads all three across the row instead of keeping the buttons together.",
            "Forgetting align-items-center, leaving the title and buttons misaligned vertically.",
            "Forgetting mb-0 on the heading, leaving default heading margin that throws off vertical centering.",
            "Using justify-content-end instead of justify-content-between, which pushes the title to the right along with the buttons."
        ],
        "rubric": [
            ["d-flex + justify-content-between on outer toolbar", 40],
            ["Button grouping in its own sub-flex container", 35],
            ["align-items-center for vertical alignment", 25]
        ]
    },
    {
        "id": "CSS-26",
        "flavor": "component-variants",
        "difficulty": "medium",
        "title": "Button with Dark Mode and Focus States",
        "scenario": "A primary 'Save' button needs to look correct in both light and dark mode, with a visibly distinct hover state and a keyboard-accessible focus ring that only appears for keyboard navigation, not for mouse clicks.",
        "code_reference": '<button class="px-4 py-2 rounded bg-blue-600 text-white">Save</button>',
        "tasks": [
            "Add a hover state that is a visibly darker shade than the base color.",
            "Add a dark-mode variant that adjusts the background color appropriately.",
            "Add a focus ring that only appears for keyboard focus, not for mouse clicks."
        ],
        "reference_solution_code": '<button class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-400 dark:bg-blue-500 dark:hover:bg-blue-400">\n  Save\n</button>',
        "check_points": [
            "dark: prefix used for a dark-mode-specific background color.",
            "hover: prefix used for a distinct shade on hover, different from the base color.",
            "focus-visible: (not plain focus:) used for the keyboard-only focus ring, with a ring utility.",
            "Base (unprefixed) classes remain as the default light-mode appearance."
        ],
        "common_mistakes": [
            "Using focus: instead of focus-visible:, which shows the ring on every mouse click too, not just keyboard navigation.",
            "Forgetting the dark: prefix entirely and using one universal color that doesn't adapt to dark mode.",
            "Writing hover:dark:bg-blue-400 instead of dark:hover:bg-blue-400, getting the variant stacking order backwards.",
            "Omitting ring color/width utilities alongside focus-visible:, leaving an invisible or default-only ring."
        ],
        "rubric": [
            ["Correct dark: variant usage", 35],
            ["Correct hover: variant", 30],
            ["Correct focus-visible: ring for accessibility", 35]
        ]
    },
    {
        "id": "CSS-27",
        "flavor": "positioning",
        "difficulty": "medium",
        "title": "Sticky Sidebar That Scrolls With Content",
        "scenario": "A documentation page has a table-of-contents sidebar next to a long article. The sidebar should stay pinned near the top of the viewport while the article scrolls, but should not overlap the footer once the article ends.",
        "code_reference": '<div class="flex gap-8">\n  <aside class="w-64">Table of contents links here.</aside>\n  <article class="flex-1">Long article content spanning many screens of scrolling.</article>\n</div>',
        "tasks": [
            "Make the sidebar stick near the top of the viewport while scrolling through the article, offset 1rem from the top.",
            "Fix whatever default flex behavior would otherwise prevent the sticky positioning from having any visible effect.",
            "Leave the article column's layout unaffected."
        ],
        "reference_solution_code": '<div class="flex gap-8 items-start">\n  <aside class="w-64 sticky top-4">Table of contents links here.</aside>\n  <article class="flex-1">Long article content spanning many screens of scrolling.</article>\n</div>',
        "check_points": [
            "sticky applied to the aside.",
            "top-4 (or a similar top offset) provided as the stick threshold.",
            "items-start added on the flex parent, since without it the default items-stretch makes the aside's box span the full article height, leaving sticky with no room to move.",
            "article/content column layout otherwise unaffected."
        ],
        "common_mistakes": [
            "Forgetting items-start on the flex container, so align-items:stretch makes the sidebar's box already span the full content height, making sticky appear to do nothing.",
            "Using fixed instead of sticky, detaching the sidebar from its column and risking overlap with content at different widths.",
            "Omitting a top-* offset value, which sticky positioning requires to actually activate.",
            "Applying sticky to the outer flex container instead of the aside element itself."
        ],
        "rubric": [
            ["sticky + top offset on aside", 45],
            ["items-start on flex parent, correctly explained", 35],
            ["Article layout preserved", 20]
        ]
    },
    {
        "id": "CSS-28",
        "flavor": "grid",
        "difficulty": "medium",
        "title": "Featured Item Spanning Multiple Grid Cells",
        "scenario": "A news homepage grid has 3 columns. The lead story should stand out by spanning 2 columns and 2 rows, while the remaining smaller stories fill single cells around it.",
        "code_reference": '<div class="grid grid-cols-3 gap-4">\n  <div class="border p-4">Featured Story</div>\n  <div class="border p-4">Story 2</div>\n  <div class="border p-4">Story 3</div>\n  <div class="border p-4">Story 4</div>\n  <div class="border p-4">Story 5</div>\n</div>',
        "tasks": [
            "Make the first item span 2 columns and 2 rows.",
            "Keep the remaining story items as normal single grid cells.",
            "Keep the 3-column base grid layout."
        ],
        "reference_solution_code": '<div class="grid grid-cols-3 grid-rows-2 gap-4">\n  <div class="col-span-2 row-span-2 border p-4">Featured Story</div>\n  <div class="border p-4">Story 2</div>\n  <div class="border p-4">Story 3</div>\n  <div class="border p-4">Story 4</div>\n  <div class="border p-4">Story 5</div>\n</div>',
        "check_points": [
            "col-span-2 and row-span-2 both applied to the featured item.",
            "grid-cols-3 retained on the parent.",
            "grid-rows-2 (or reasoning about implicit row sizing) considered so the row span has row tracks to span.",
            "The other story items are left without any span classes."
        ],
        "common_mistakes": [
            "Applying row-span-2 without considering that items beyond the explicit rows will flow into an implicit row sized differently (auto) than the explicit ones.",
            "Forgetting col-span-2 and only setting row-span-2, making the story tall but not wide.",
            "Adding span classes to more than one item unintentionally, breaking the single-featured-item intent.",
            "Using col-start/col-end line numbers inconsistently instead of the simpler col-span-2 utility when a span was all that was needed."
        ],
        "rubric": [
            ["Correct col-span-2 row-span-2 on featured item", 55],
            ["grid-cols-3 base retained", 25],
            ["Other items left unspanned", 20]
        ]
    },
    {
        "id": "CSS-29",
        "flavor": "debugging",
        "difficulty": "medium",
        "title": "Navbar Items Misaligned Despite justify-between",
        "scenario": "A navbar has a logo and a group of nav links spread to opposite ends with `justify-between`, but the logo image sits visibly higher than the baseline of the link text next to it.",
        "code_reference": '<nav class="flex justify-between p-4 border-b">\n  <img src="logo.svg" class="h-8"/>\n  <div class="flex gap-4">\n    <a href="#">Home</a>\n    <a href="#">Pricing</a>\n    <a href="#">Contact</a>\n  </div>\n</nav>',
        "tasks": [
            "Fix the vertical misalignment between the logo and the nav links.",
            "Do not change the horizontal spacing behavior already provided by justify-between.",
            "Explain which flex axis controls this alignment versus which axis justify-between controls."
        ],
        "reference_solution_code": '<nav class="flex justify-between items-center p-4 border-b">\n  <img src="logo.svg" class="h-8"/>\n  <div class="flex gap-4">\n    <a href="#">Home</a>\n    <a href="#">Pricing</a>\n    <a href="#">Contact</a>\n  </div>\n</nav>',
        "check_points": [
            "items-center added to fix the cross-axis (vertical) alignment.",
            "justify-between retained unchanged for horizontal distribution.",
            "Candidate explains justify- controls the main axis while items- controls the cross axis in a flex row.",
            "The inner nav-link group's own flex gap-4 remains unaffected."
        ],
        "common_mistakes": [
            "Replacing justify-between with items-center instead of adding both, losing the intended left/right spacing between logo and links.",
            "Trying to fix the misalignment with margin/padding tweaks on the image instead of the correct cross-axis alignment utility.",
            "Confusing align-content with align-items — align-content affects multi-line/wrapped flex containers, not a single-line row like this one.",
            "Adding items-center only to the inner link group instead of the outer nav, which does not fix the logo's alignment."
        ],
        "rubric": [
            ["items-center added correctly", 50],
            ["justify-between preserved", 25],
            ["Correct axis reasoning explained", 25]
        ]
    },
    {
        "id": "CSS-30",
        "flavor": "responsive",
        "difficulty": "medium",
        "title": "Responsive Padding for a Hero Section",
        "scenario": "A hero section looks cramped on mobile because of minimal horizontal padding, and disproportionately padded on large desktop screens because of one large fixed vertical padding value applied at every screen size.",
        "code_reference": '<section class="px-2 py-24 bg-indigo-600 text-white">\n  <h1>Welcome to our platform</h1>\n  <p>Get started in minutes.</p>\n</section>',
        "tasks": [
            "Increase horizontal padding on mobile for better breathing room.",
            "Scale both horizontal and vertical padding up across the sm and lg breakpoints in ascending order.",
            "Ensure the base (mobile) vertical padding is smaller than the desktop value, rather than one fixed large value everywhere."
        ],
        "reference_solution_code": '<section class="px-4 py-12 sm:px-8 sm:py-16 lg:px-16 lg:py-24 bg-indigo-600 text-white">\n  <h1>Welcome to our platform</h1>\n  <p>Get started in minutes.</p>\n</section>',
        "check_points": [
            "Horizontal padding increases across breakpoints (px-4 base, larger sm:/lg: values).",
            "Vertical padding starts smaller on mobile (py-12) and increases at sm/lg rather than being one large fixed value everywhere.",
            "Breakpoint values are in ascending order at each successive prefix.",
            "Base (unprefixed, mobile) classes are present for both axes."
        ],
        "common_mistakes": [
            "Only adjusting horizontal padding and leaving py-24 unprefixed at every screen size, leaving the original mobile cramped/imbalanced complaint only partly fixed.",
            "Breakpoint values not in ascending order, e.g. an lg: value smaller than the sm: value.",
            "Using margin utilities instead of padding, when the scenario specifically describes internal breathing room within the section's background.",
            "Forgetting the base unprefixed classes and relying only on sm:/lg: prefixed values, leaving mobile unstyled."
        ],
        "rubric": [
            ["Responsive horizontal padding scaling", 35],
            ["Responsive vertical padding scaling", 35],
            ["Ascending/mobile-first correctness", 30]
        ]
    }
]
