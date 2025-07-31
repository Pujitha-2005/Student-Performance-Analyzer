from django.db import models

# Student model to store student data
class Student(models.Model):
    roll_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    parent_email = models.EmailField()
    dob = models.DateField()

    def __str__(self):
        return self.name

# Performance model to store marks for students
class Performance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    marks = models.IntegerField()

    def __str__(self):
        return f"{self.student.name} - {self.subject}"

# SlowLearner model to track if a student is a slow learner
class SlowLearner(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    is_slow_learner = models.BooleanField(default=False)
    difficult_topics = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.name} - Slow Learner: {self.is_slow_learner}"

# Model for quiz questions
class QuizQuestion(models.Model):
    question_text = models.CharField(max_length=255)
    option_1 = models.CharField(max_length=100)
    option_2 = models.CharField(max_length=100)
    option_3 = models.CharField(max_length=100)
    option_4 = models.CharField(max_length=100)
    correct_option = models.IntegerField()  # 1, 2, 3, or 4 for the correct option

    def __str__(self):
        return self.question_text
from django.db import models

class QuizScore(models.Model):
    rollno = models.CharField(max_length=20)
    topic = models.CharField(max_length=255)
    score = models.IntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rollno} - {self.topic} - {self.score}"
