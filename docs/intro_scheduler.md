This is our first time with this approach, so it is definitely experimental.  The overall idea is to use a website to receive worktime preferences, to generate the worktime assignments, and then to let parents modify their assignment (so the auto generated version doesn't have to be perfect).

The assignment gets generated more or less following this (I guess traditional) approach:

1. Use the submitted preferences to assign to each family one of its high-ranked repeating shifts, so that no shift is assigned to too many families.*
2. Commit each family to regularly repeating occurrences of its assigned shift.**

This approach was not too hard to automate, though there are some tricky situations we luckily didn't encounter.***

Given the automation, the scheduling task itself is pretty trivial.  Once all families have submitted their shift preferences, the scheduler first clicks a button to see a list of all optimal repeating-shift assignments; then clicks another button to generate from one of these the assignment of shift occurrences to families.

Of course the site requires of the scheduler some setup and upkeep tasks too.  Initially the scheduler enters for each child in the classroom, a nickname for the child and the email addresses of its parents; this generates signup invites to the parents and upon signup those users are affiliated to the child (and classroom) as its parents.  Around the turnover of each (four-month or so) assignment period, the scheduler also needs to enter data for that period (period end date and bigelow holidays); this exposes to parents for that period the new shift preference submission form.

As we just started using the system, there are still some wrinkles to work out.  But it does seem to make the scheduler's task a lot easier.

It would be good to hear your suggestions!

Cheers, 

Max

* Implementation details on part 1...
   - I required no shift to be assigned to more than two families.  Actually it would only be needed to ensure for each shift s that the sum, for all f assigned s, of required shifts per month is no greater than four.
   - Luckily everyone got a #1 ranked shift; in case this wouldn't have been possible I played around with cycling through all results of adding to the domain of some family their #2 ranked shifts, then all results of adding to domains of two families their respectively #2 ranked shifts, etc..., but I didn't test it much and unforeseen complications look threatening.
 
** Details on part 2...
   - For each shift s, enumerate all its occurrences in the period which do not overlap with a holiday.  We want to map its every second (or every fourth) occurrence to each family assigned s which owes two (or one) worktimes per month.  To do this, it remains just to find for each family a good "offset", i.e., pick whether their first commitment is the first, second, third, or fourth occurrence of the shift; an implementation of "good" might be at each step to pick the least-used offset.

*** (Possible) complications...

The procedure would not handle well situations where e.g. somebody wants half one shift and half another.  (This might be handled by hand-tweaking the result of part 1).  It also has trouble with the case where many occurrences of somebody's most preferred shift are impossible for that person (e.g. if they have a child in another classroom and want same shift in both rooms).  For the second problem, next time I may add a "choose offset" option, so that people can request e.g. the shift occurrences 0,2,4,6... or 1,3,5,7...

The procedure also doesn't guarantee that everybody gets assigned the same number of shift occurrences.  Some people complained about this, so I just said that they can drop some to get their number down to 8.

Finally, because the site lets people change their assignments it requires a little social engineering to make sure the teachers know the updated schedule and can keep track of whether people showed up for their worktime.  This part is still in progress :).  One solution would be to give Marcia admin access to see the worktime attendance as recorded on the site.
