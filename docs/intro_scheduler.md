Hello, Brian,

Sorry I have only now gotten around to writing a reply to your question!

We used a web app to automate most of the scheduling in LRB (https://gitlab.com/max.morgan.weiss/work-the-rainbow).  The overall idea is that the app collects worktime preferences, generates and circulates worktime commitments, and then lets each family revise their commitments on-the-fly.  

The assignment gets generated more or less following this (I guess traditional) approach:

1. Use the submitted preferences to assign to each family one of its high-ranked shifts, so that no shift is oversubscribed.[*]
2. Commit each family to regular occurrences of its assigned shift.[**]

The algorithm works when the submitted preferences are pretty favorable, and leaves less favorable situations to be handled manually. [***]

Given this automation, the human labor required to build a schedule is pretty minimal: once all families have submitted their shift preferences, the scheduler hits a link to review a list of all optimal shift assignments; then hits another link to generate from one of these the commitment of families to shift occurrences.  At this point, the new schedule will be visible to all families in the classroom.  Because it is straightforward for each family to revise its own commitments, and because each family is assigned to more than the minimum number of slots they need to complete, the generated schedule doesn't have to be perfect.

Besides generating the actual schedule itself, the app also requires the person who is scheduler to do some some setup and upkeep.  Initially s/he enters for each child in the classroom, a nickname for the child and the email addresses of its parents; the app then sends signup invites to each parent address; upon signup the resulting users are affiliated as parents to the child (and thereby to the child's classroom).  Subsequently, at the turnover of each (four calendar month) assignment period, the scheduler also needs to enter data for that period (just the period start and end dates, and the bigelow holidays), check a box to expose to parents for that period the new shift preference submission form, and sends out preference solicitation email.

There are definitely still some wrinkles to work out [****] with this system, and we have so far only used it for one period.  But our impression is that this reduces the burden on the scheduler and also helps parents coordinate their worktime schedules.

Since you are both a computer scientist and a much more experienced scheduler than we are, it would be good to hear your thoughts and suggestions!

Cheers,

Max

* Implementation details on part 1...
   - The shift assignment gets generated using a simple constraint solver (pyconstraint), using the conditions that no more than two families are assigned the same shift, and each family is assigned a shift they rank as #1.
   - So it's mildly lucky that it's even possible to assign everyone a #1 ranked shift; in case this wouldn't have been possible I played around with examining each result, for a choice of one family, of allowing that family to be assigned a #2 ranked shift, then all results of allowing, for each choice of two families, an assignment of their #2 ranked shift, etc., but I haven't tested this much.
 
** Details on part 2...
   - For each shift s, enumerate all its occurrences in the period which do not overlap with a holiday.  We want to map its every second (or, its every fourth) occurrence to each family assigned s which owes two (or, one) worktimes per month.  To do this, it remains just to find for each family a good "offset", i.e., pick whether their first commitment is the first, second, third, or fourth occurrence of the shift; an implementation of "good" might be at each step to pick the least-used offset.

*** (Possible) complications...

The procedure would not handle well situations where e.g. somebody wants a mix e.g. of Mondays and Tuesdays.  (I addressed this in practice by just hand-tweaking a result of part 1).  It also has trouble with the case where many occurrences of somebody's most preferred shift are impossible for that person (which is natural if they have a child in another classroom and want same shift in both rooms; again this could luckily be addressed by hand-tweaking, but it might also be feasible to add a "choose offset" option, so that people can request e.g. the shift occurrences 0,2,4,6... or 1,3,5,7...). 

The procedure also doesn't guarantee that everybody gets assigned the same number of shift occurrences per period.  Some people complained about this, so I just said that having received their commitments, people can drop some to reduce the number to >= 8.

**** In particular, the site includes an interface for the teachers to record whether each worktime commitment was fulfilled, but LRB teachers prefer to use a hard copy since they don't have much on-the-clock cell phone use; so, parents then need to be sure to update the hard copy of the schedule after they have changed the digital one.


