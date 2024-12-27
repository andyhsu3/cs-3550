from django.http import Http404, HttpResponse, HttpResponseBadRequest
from . import models
from django.contrib.auth.models import User, Group
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.exceptions import PermissionDenied

# Create your views here.
@login_required
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, 'index.html', {'assignments': assignments})

@login_required
def assignment(request, assignment_id):
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    current_user = request.user
    
    # Check user roles
    is_student_user = is_student(current_user)
    is_ta_user = is_ta(current_user)
    is_admin_user = current_user.is_superuser

    # Handle student submission or file upload
    student_submission = models.Submission.objects.filter(assignment=assignment, author=current_user).first()

    error_message = None  # Initialize error message

    # Prevent submission if deadline has passed and handle file upload
    if request.method == 'POST' and 'file' in request.FILES:
        if timezone.now() > assignment.deadline:
            return HttpResponseBadRequest("The deadline for this assignment has passed.")
        
        student_file = request.FILES['file']

        if student_file.size > 64 * 1024 * 1024:
            error_message = "The file is too big, you are only allowed to submit a file 64 MiB or smaller. "
        elif not is_pdf_file(student_file):
            error_message = "This file is not a valid PDF file to submit as your submission. "

        if error_message is None:
            if student_submission:
                student_submission.file = student_file
            else:
                assigned_grader = pick_grader(assignment)
                student_submission = models.Submission(
                    assignment=assignment,
                    author=current_user,
                    file=student_file,
                    grader=assigned_grader,
                    score=None
                )
            student_submission.save()
            return redirect('assignment', assignment_id=assignment_id)

    # Determine submission status and message for students
    submission_status = None
    submission_message = None
    if is_student_user:
        if student_submission:
            filename = student_submission.file.name
            if student_submission.score is not None:  # Submitted and graded
                x = student_submission.score
                y = assignment.points
                z = (x / y) * 100
                submission_status = "graded"
                submission_message = f"Your submission, {filename}, received {x}/{y} points ({z:.1f}%)"
            elif assignment.deadline < timezone.now():  # Submitted, ungraded, and past due
                submission_status = "ungraded_past_due"
                submission_message = f"Your submission, {filename}, is being graded"
            else:  # Submitted and not yet due
                submission_status = "submitted_not_due"
                submission_message = f"Your current submission is {filename}"
        else:
            if assignment.deadline < timezone.now():  # Not submitted and past due
                submission_status = "not_submitted_past_due"
                submission_message = "You did not submit this assignment and received 0 points"
            else:  # Not submitted and not yet due
                submission_status = "not_submitted_not_due"
                submission_message = "No current submission"

    # Display submissions for TAs and Admins
    if is_ta_user or is_admin_user:
        total_submissions = assignment.submission_set.count()
        assigned_submissions = assignment.submission_set.filter(grader=current_user, score__isnull=False).count()
    else:
        total_submissions = 0
        assigned_submissions = 0

    if is_admin_user:
        # Admin sees all submissions, not just assigned ones
        assigned_submissions = total_submissions

    students_group = Group.objects.filter(name="Students").first()
    total_students = students_group.user_set.count() if students_group else 0

    context = {
        'assignment': assignment,
        'total_submissions': total_submissions,
        'assigned_submissions': assigned_submissions,
        'total_students': total_students,
        'student_submission': student_submission,
        'submission_plural': 'submission' if total_submissions == 1 else 'submissions',
        'assigned_submission_plural': 'submission' if assigned_submissions == 1 else 'submissions',
        'student_plural': 'student' if total_students == 1 else 'students',
        'is_student': is_student_user,
        'is_ta': is_ta_user,
        'is_admin': is_admin_user,
        'submission_status': submission_status,
        'submission_message': submission_message,
        'error_message': error_message  # Add the error message to the context
    }
    
    return render(request, 'assignment.html', context)

@login_required
def submissions(request, assignment_id):
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    current_user = request.user

    if not is_ta(current_user):
        raise PermissionDenied("Only TAs are allowed access to this page. ")

    # We just want to identify if the user is a student, TA, or admin for action-card viewing purposes
    is_ta_user = is_ta(current_user)
    is_admin_user = current_user.is_superuser

    # Initialize the submissions list -- The main reason we'll be using this is to filter all submissions based on who is logged in
    # Admins see all, TAs will only see their specified submissions, and rest will see none.
    submissions = []

    if not current_user.is_authenticated:
        return redirect('/profile/login')
    if  is_admin_user:
        submissions = assignment.submission_set.all().order_by('author__username')
    elif is_ta_user:
        submissions = assignment.submission_set.filter(grader=current_user).order_by('author__username')
    else:
        return redirect('/profile/')

    errors = {}
    if request.method == "POST":
        errors = save_grades(request, assignment)

        if not errors:
            return redirect(f"/{assignment_id}/submissions")

    context = {
        'assignment': assignment,
        'submissions': submissions,
        'errors': errors,
        'error': None
    }
    return render(request, "submissions.html", context)

# the profile will also undergo different performances based on whether it is for a TA, student, or for admin. 
@login_required
def profile(request):
    current_user = request.user
    context = {
        'is_student': is_student(current_user),
        'is_ta': is_ta(current_user),
        'is_admin': current_user.is_superuser,
    }

    if context['is_student']:
        profile_data = []
        assignments = models.Assignment.objects.all()
        for assignment in assignments:
            submission = models.Submission.objects.filter(author=current_user, assignment=assignment).first()
            status = 'Ungraded'
            if submission:
                if submission.score is not None:
                    status = f"{submission.score}%"
                elif assignment.deadline < timezone.now():
                    status = 'Missing'
            else:
                status = 'Not Due'
            profile_data.append({'assignment': assignment, 'status': status})
        current_grade = calculate_current_grade(current_user)
        context['profile_data'] = profile_data
        context['current_grade'] = current_grade

    elif context['is_ta']:
        profile_data = []
        assignments = models.Assignment.objects.all()

        # the TAs will loop through every single submission and only sort through the submissions they must grade -- however, any assignment with no submission will return a 0/0
        for assignment in assignments:
            total_count = models.Submission.objects.filter(assignment=assignment, grader=current_user).count()
            graded_count = models.Submission.objects.filter(assignment=assignment, grader=current_user, score__isnull=False).count()
            profile_data.append({
                'assignment': assignment,
                'graded_submissions': graded_count,
                'total_assigned_submissions': total_count,
            })
        context['profile_data'] = profile_data

    elif context['is_admin']:
        profile_data = []
        assignments = models.Assignment.objects.all()
        for assignment in assignments:
            graded_count = models.Submission.objects.filter(assignment=assignment, score__isnull=False).count()
            total_count = models.Submission.objects.filter(assignment=assignment).count()
            profile_data.append({
                'assignment': assignment,
                'graded_submissions': graded_count,
                'total_assigned_submissions': total_count,
            })
        context['profile_data'] = profile_data

    return render(request, 'profile.html', context)

def login_form(request):
    # use the next method to identify where we should take the user upon a successful login -- default is set to /profile/
    next_url_for_user = request.GET.get("next", "/profile/")
    # if the request method is POST then we will apply -- 
    if request.method == "POST":
        # Here, extract username and password from the POST request
        extracted_username = request.POST.get("usernameInput", "")
        extracted_password = request.POST.get("passwordInput", "")
        # now call Django's authenticate function.
        login_user = authenticate(username=extracted_username, password=extracted_password)
        next_url_for_user = request.POST.get("next", "/profile/")

        if login_user is not None:
            login(request, login_user)
            if url_has_allowed_host_and_scheme(next_url_for_user, None):
                return redirect(next_url_for_user)
            else:
                return redirect('/profile/')
        else:
            # phase 4 -- add in the error message
            error = "Username and password do not match."
            return render(request, "login.html", {'error': error, 'next': next_url_for_user})
    
    # if the request method is GET then just render the page.
    return render(request, "login.html", {'next': next_url_for_user})
        
# phase 1 HW 5 -- define a logout_form
def logout_form(request):
    logout(request)
    return redirect('/profile/login/')


# Helper method that will be used in submissions for homework 4 phase 2 --> Saving grades and iterating through request.POST
def save_grades(request, assignment):
    graded_submission = []
    errors = {}

    for key in request.POST:
        if key.startswith("grade-"):
            submission_id = int(key.removeprefix("grade-"))
            submission = assignment.submission_set.filter(id=submission_id).first()

            if submission:
                assignment_grade = request.POST[key]
                submission_errors = []

                # Validate the grades. We want to go over and check our errors here --> first one is that the number must be between 0 and however many points the assignment is worth.
                # second error is to make sure that the grade canNOT be empty.
                # third error is to make sure that no strings are used and only numbers are accepted.
                try:
                    if assignment_grade:
                        score = float(assignment_grade)
                        if score < 0 or score > assignment.points:
                            submission_errors.append("Grade provided must be between 0 and {}.".format(assignment.points))
                    else:
                        submission_errors.append("Grade provided cannot be empty. ")

                except ValueError:
                    submission_errors.append("Grade provided cannot contain any strings.")

                if submission_errors:
                    errors[submission_id] = submission_errors  # Collect errors
                else:
                    try:
                        submission.change_grade(request.user, score)
                        graded_submission.append(submission)
                    except PermissionDenied:
                        errors[submission_id] = ["You are not able to change this grade. "]

    if graded_submission:
        models.Submission.objects.bulk_update(graded_submission, ["score"])

    return errors  # Return errors to the controller submission so that we can continue and print out the errors.

# i was unable to complete this since i was stuck and had to revert a few commits.
@login_required
def show_upload(request, filename):
    submission = models.Submission.objects.get(file=filename)

    try:
        file = submission.view_submission(request.user)
        
        if is_pdf_file(file):
            response = HttpResponse(file.open(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"' 
            return response
        else:
            raise Http404
    except PermissionDenied:
        return HttpResponse("You can't view this file. ", status=403)

# Phase2 HW5 - helper defs
def is_student(user):
    return user.groups.filter(name="Students").exists()

def is_ta(user):
    return user.groups.filter(name="Teaching Assistants").exists()

# Phase 3 HW 3 - helper defs (calculate_current_grade and pick_grader)
def calculate_current_grade(user):
    assignments = models.Assignment.objects.all()
    available_points = 0
    earned_points = 0

    for assignment in assignments:
        submission = models.Submission.objects.filter(author=user, assignment=assignment).first()

        # this if stateemnt checks if it's a graded submission and if it is -- then we add the earned points in to process total grade.
        if submission and submission.score is not None:
            available_points += assignment.weight
            earned_points += (submission.score / assignment.points) * assignment.weight

        # this just checks if it's a missing assignment.
        elif assignment.deadline < timezone.now() and not submission:
            available_points += assignment.weight

    if available_points > 0:
        current_grade = (earned_points / available_points) * 100
    else:
        current_grade = 100
    return round(current_grade, 2)

# HW 5 helper function.
def pick_grader(assignment):
    # Step 1 & 2 - Go through "Teaching Assistants" group and pull the user_set
    ta_group = Group.objects.filter(name="Teaching Assistants").first()
    if not ta_group:
        return None 

    # Step 3 - using the Django annotate function, we will use the total_assigned field -- counts the graded set.
    # Step 4 - by using Count, it also orders by total assigned.
    TA_assigned_list = ta_group.user_set.annotate(
        total_assigned=Count('graded_set', filter=Q(graded_set__assignment=assignment))).order_by('total_assigned')

    # step 5 is to get the first ta that exists inside of the ta group.
    return TA_assigned_list.first() if TA_assigned_list.exists() else None

# is_pdf_file(file) function for show_upload
def is_pdf_file(file):
    if not file.name.lower().endswith('.pdf'):
        return False
    
    try:
        first_chunk = next(file.chunks())
        if not first_chunk.startswith(b'%PDF-'):
            return False
    except StopIteration:
        return False
    
    return True