This is our first time with this approach, so it is definitely experimental.  But here is the overall idea.
 
I built a simple Django site to receive worktime preferences, generate the worktime schedule, then return the schedule to parents and teachers.  The site then lets parents modify their assignments, so that the initial schedule doesn't have to be perfect.

The actual schedule gets generated following (what I think) is the more or less traditional Bigelow approach:

1. Use the submitted preferences to assign to each family one of its high-ranked shifts, so that no shift is assigned to too many families.*
2. Commit each family to occurrences of its assigned shift.**

This procedure worked reasonably well, though there are some tricky situations we luckily didn't encounter.***

From the scheduler's perspective, the procedure goes like this.  On the first usage, enter each child's name and the email addresses of its parents.  Enter Bigelow holiday dates and also boundaries for the four-month period in question.  Send an email asking people to submit their preferences.

When the preferences are returned, then: from a page showing everybody's returned preferences, click a button "generate all possible shift assignments" (i.e., all solutions to part 1 above); for one of the listed solutions, click its "generate commitments" button (part 2 above); the next page is a calendar with the schedule.

For some reason it didn't occur to me that a parent would object to getting assigned more than eight shifts in the period, but of course somebody did, so I said that people can (through the web form) drop any of their committed shift occurrences so long as they stay with no fewer than eight.

Probably some other issues may come up (e.g., we are still working out guidelines for people to change their commitments).  It would be good to hear your suggestions!

Cheers, 

Max

* Details on part 1...
   - I just used the pyconstraint library
   - In practice I just required no shift to be assigned to more than two families.  But this is stricter than necessary; it would only be needed to ensure for each shift s that the sum, for all f assigned s, of required shifts per month is no greater than four.
   - Luckily everyone got a #1 ranked shift; in case this wouldn't have been possible I played around with cycling through all results of adding to the domain of some family their #2 ranked shifts, then all results of adding to domains of two families their respectively #2 ranked shifts, etc..., but I didn't test it much and unforeseen complications could be many.
 
** Details on part 2...
   - For each shift s, enumerate all its occurrences in the period which do not overlap with a holiday.  We want to map its every fourth (or every second) occurrence to each family assigned s which owes one (or two) worktimes per month.  To do this, it remains just to compute for each family a reasonable "offset", i.e., pick whether their first commitment is the first, second, third, or fourth occurrence of the shift; one strategy here is always to pick a least-used offset.

*** Possible complications...
The procedure would not handle well situations where e.g. somebody wants half one shift and half another.  (This might be handled by hand-tweaking the result of part 1).  It also has trouble with the case where many occurrences of somebody's most preferred shift are impossible for that person (e.g. if they have a child in another classroom and want same shift in both rooms).
