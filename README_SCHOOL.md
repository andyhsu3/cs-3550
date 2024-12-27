Your assignment repository
==========================

Please use this repository to hold all of your work for CS 3550
web dev 1. You will submit your assigments, and they will be graded,
using the contents of this repository only, at the commit
corresponding to the latest possible submission time (including
all granted extensions).

This repository is private. You should not be able to view another
student's repository and they should not be able to view yours.

Initial contents
----------------

There's a folder in this repository called `.github`. This folder
defines the autotester. Do not modify any files in it.

There's also a file in this repository called `.gitignore`. This file
tells `git` not to commit certain files; it's been pre-filled with
some Python defaults but you can edit it if you notice junk files
being committed to your repository.

Do not, under any circumstances, create a folder called `autotester`
in the root of this repository. If you do, the autotester will break.

Github Actions
--------------

Every time you push to this repository, it will auto-test the current
homework assignment. The auto-test will roll over to the next week's
assignment on the Monday after the previous assignment is due. The
auto-tester only tests the "presubmission" component of the homework
assignment. Passing the auto-tester doesn't mean you get full points
on the homework!

Github actions will email you every time you push, if you fail a test.
This will be pretty often while you're working on the presubmission.
That will be _very_ annoying. We recommend [turning this
off][notification].

[notification]: https://docs.github.com/en/account-and-profile/managing-subscriptions-and-notifications-on-github/setting-up-notifications/about-notifications
