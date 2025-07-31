from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),

    # Auth
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Roll number
    path('enter-rollno/', views.enter_rollno, name='enter_rollno'),
    path('check-roll-number/', views.check_roll_number, name='check_roll_number'),

    # Performance
    path('after-performance/', views.after_performance, name='after_performance'),
    path('view-all-data/', views.view_all_data, name='view_all_data'),
    path('view-details/', views.view_details, name='view_details'),
    path('view-slow-learners/', views.view_slow_learners, name='view_slow_learners'),
    path('analyze-weak-subjects/', views.analyze_weak_subjects, name='analyze_weak_subjects'),

    # Content explanation
    path('provide-content/', views.provide_content, name='provide_content'),
    path('provide-content-rephrased/', views.provide_content, {'rephrase': True}, name='provide_content_rephrased'),
    path('confirm-understanding/', views.confirm_understanding, name='confirm_understanding'),

    # Email & Timer
    path('enter-emails/', views.enter_emails, name='enter_emails'),
    path('start-prep-timer/', views.start_prep_timer, name='start_prep_timer'),

    # Quiz
    path('start-assessment/', views.start_quiz, name='start_assessment'),
    path('submit-quiz/', views.submit_quiz, name='submit_quiz'),
]
