# import User for studentsa nd TAs
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied

from django.db import models

# Create your models here.
class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    weight = models.IntegerField()
    points = models.IntegerField()

# i ahd a lot of errors with the null=True and the blank=True and it gave a lot of errors with github Autograde.
class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    grader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_set')
    file = models.FileField()
    score = models.FloatField(null=True, blank=True)

    # HW5 Phase 4 addition for security check.
    def change_grade(correct_user, user, new_grade):
        # check here if the user is the assigned grader
        if user != correct_user.grader:
            raise PermissionDenied("You are not the correct TA and thus will not be allowed to change this grade. ")
        
        correct_user.score = new_grade

    # HW5 Phase 5 addition for file uploads protect.
    def view_submission(self, user):
        # check user is 3 people --> submission's author, submission's grader/TA, or admin user.
        if user == self.author or user == self.grader or user.is_superuser:
            return self.file
        else:
            raise PermissionDenied("You are not allowed to view this submission. ")