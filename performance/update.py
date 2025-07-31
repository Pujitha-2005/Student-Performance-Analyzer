import os
import time
import threading
import pandas as pd
import random
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
import matplotlib.pyplot as plt

DATASET_PATH = os.path.join(settings.BASE_DIR, 'student_performance', 'dataset', 'Student_Marks_500.xlsx')
user_sessions = {}

# ------------------------ BASIC VIEWS ------------------------
def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if password.isdigit():
            request.session['username'] = username
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials. Use numeric password.')
            return redirect('login_user')
    return render(request, 'login.html')

def logout_user(request):
    request.session.flush()
    return redirect('home')

def dashboard(request):
    username = request.session.get('username', 'User')
    return render(request, 'dashboard.html', {'username': username})

# ------------------------ ROLL NO CHECK ------------------------
def enter_rollno(request):
    return render(request, 'enter_rollno.html')


def check_roll_number(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no', '').strip()

        try:
            df = pd.read_excel(DATASET_PATH)

            # Dynamically detect columns
            roll_no_col = next((col for col in df.columns if 'roll' in col.lower()), None)
            percent_col = next((col for col in df.columns if 'percent' in col.lower()), None)

            if not roll_no_col:
                return render(request, 'enter_rollno.html', {'error': 'Roll Number column not found.'})

            # Clean and match roll number
            df[roll_no_col] = df[roll_no_col].astype(str).str.strip()
            roll_no = roll_no.strip()

            if roll_no not in df[roll_no_col].values:
                return render(request, 'enter_rollno.html', {'error': 'Roll number not found. Please try again.'})

            student_data = df[df[roll_no_col] == roll_no]
            request.session['rollno'] = roll_no

            # Check if student is a slow learner
            is_slow = False
            slow_learner_msg = ""
            if percent_col:
                percentage = pd.to_numeric(student_data.iloc[0][percent_col], errors='coerce')
                if pd.notna(percentage) and percentage < 60:
                    is_slow = True
                    slow_learner_msg = "❗ You are a Slow Learner based on your percentage."
                else:
                    slow_learner_msg = "✅ You are NOT a Slow Learner."

            # Detect weak subjects
            weak_subjects = []
            for col in df.columns:
                if col not in [roll_no_col, percent_col] and df[col].dtype in ['int64', 'float64']:
                    score = pd.to_numeric(student_data.iloc[0][col], errors='coerce')
                    if pd.notna(score) and score < 40:
                        weak_subjects.append(col)

            return render(request, 'performance.html', {
                'rollno': roll_no,
                'is_slow': is_slow,
                'slow_learner_msg': slow_learner_msg,
                'weak_subjects': weak_subjects
            })

        except Exception as e:
            return render(request, 'enter_rollno.html', {'error': f"Error loading dataset: {e}"})

    return render(request, 'enter_rollno.html')

# ------------------------ PERFORMANCE ------------------------
def after_performance(request):
    rollno = request.session.get('rollno')
    return render(request, 'after_performance.html', {'rollno': rollno})

def view_all_data(request):
    df = pd.read_excel(DATASET_PATH)
    data_html = df.to_html(index=False)
    return render(request, 'view_all_data.html', {'data_html': data_html})

def view_details(request):
    try:
        df = pd.read_excel(DATASET_PATH)
        df.columns = df.columns.str.strip()
        student_table_html = df.to_html(index=False, classes='table table-bordered table-striped')
        return render(request, "view_details.html", {"students_table": student_table_html})
    except Exception as e:
        return render(request, "error.html", {"message": f"Error loading dataset: {str(e)}"})

def view_slow_learners(request):
    try:
        df = pd.read_excel(DATASET_PATH)
        df.columns = df.columns.str.strip()
        percentage_col = next((col for col in df.columns if 'percentage' in col.lower()), None)
        if not percentage_col:
            return HttpResponse("❌ Percentage column not found.")

        df[percentage_col] = pd.to_numeric(df[percentage_col], errors='coerce')
        slow_learners_df = df[df[percentage_col] < 60]

        if slow_learners_df.empty:
            return render(request, 'slow_learners.html', {
                'message': "✅ No slow learners found (all students scored 60% or above).",
                'learners': ''
            })

        learners_html = slow_learners_df.to_html(index=False, classes='table table-bordered')
        return render(request, 'slow_learners.html', {
            'message': "",
            'learners': learners_html
        })
    except Exception as e:
        return HttpResponse(f"❌ Error occurred: {str(e)}")
from django.shortcuts import render

def confirm_understanding(request):
    if request.method == 'POST':
        feedback = request.POST.get('feedback')
        topic = request.session.get('selected_topic')

        if feedback == 'yes':
            return redirect('enter_emails')  # Next step
        else:
            messages.info(request, "Let's go through it once again in simpler terms.")
            return redirect('provide_content_rephrased')  # Trigger rephrase mode

    return redirect('dashboard')
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render, redirect
import random

def start_assessment(request):
    if request.method == 'POST':
        topic = request.session.get('selected_topic')

        if not topic:
            return redirect('dashboard')

        # Generate 15 random MCQs dynamically for the selected topic
        questions = []
        for i in range(1, 16):
            questions.append({
                'question': f"Sample Question {i} on {topic}?",
                'options': [
                    f"{topic} Option A",
                    f"{topic} Option B",
                    f"{topic} Option C",
                    f"{topic} Option D"
                ],
                'answer': f"{topic} Option A"
            })

        # Save the questions in session for scoring later
        request.session['quiz_questions'] = questions
        return render(request, 'quiz.html', {'questions': questions, 'topic': topic})

    return redirect('dashboard')

@csrf_exempt
def prep_timer(request):
    return render(request, 'pre_timer.html')  # Template with dropdown and countdown

@csrf_exempt
def show_quiz(request):
    return render(request, 'quiz.html')  # Replace with your quiz logic/template

# ------------------------ PIE CHART ------------------------
def analyze_weak_subjects(request):
    rollno = request.session.get('rollno')
    if not rollno:
        return redirect('dashboard')

    df = pd.read_excel(DATASET_PATH)
    roll_col = next((col for col in df.columns if 'roll' in col.lower()), None)
    df[roll_col] = df[roll_col].astype(str)
    student_row = df[df[roll_col] == rollno]

    if student_row.empty:
        return HttpResponse("Student not found.")

    excluded_cols = [roll_col, 'Name', 'Overall Percentage']
    marks = student_row.drop(columns=[col for col in excluded_cols if col in student_row.columns])
    marks_dict = marks.iloc[0].to_dict()

    weak_subjects = {subj: score for subj, score in marks_dict.items() if score < 60}
    if not weak_subjects:
        return HttpResponse("🎉 You have no weak subjects!")

    plt.figure(figsize=(6, 6))
    plt.pie(weak_subjects.values(), labels=weak_subjects.keys(), autopct='%1.1f%%')
    pie_path = os.path.join(settings.BASE_DIR, 'static', 'weak_subjects_pie.png')
    plt.savefig(pie_path)
    plt.close()

    return render(request, 'analyze_subjects.html', {
        'weak_subjects': weak_subjects,
        'pie_chart': 'static/weak_subjects_pie.png'
    })

# ------------------------ CONTENT EXPLANATION ------------------------
import requests
from django.shortcuts import render, redirect

TOGETHER_API_KEY = '19544a0ff9260f3ec9964701e97a1e730aaa593e48d9c5c3976f72a93f6677c4'  # 🔑 Replace with your actual key
def provide_content(request, rephrase=False):
    topic = request.session.get('selected_topic')

    if not topic:
        return redirect('dashboard')

    prompt = f"""
    {'Explain again in a simpler way with different examples.' if rephrase else 'Explain clearly'} 
    the topic '{topic}' for a student. Use easy language and real-world examples.
    """

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": "You are a helpful teacher who explains concepts clearly."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 700,
        "temperature": 0.7
    }

    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        explanation = response.json()['choices'][0]['message']['content']
    except Exception as e:
        explanation = f"⚠ Error: {str(e)}"

    return render(request, 'topic_content.html', {
        'topic': topic,
        'explanation': explanation,
        'ask_feedback': True
    })

# ------------------------ TIMER & EMAIL ------------------------
def start_prep_timer(request):
    student_email = request.session.get('student_email')
    parent_email = request.session.get('parent_email')

    if not student_email or not parent_email:
        messages.error(request, "Missing email data. Please enter both emails.")
        return redirect('enter_emails')

    return render(request, 'pre_timer.html', {
        'student_email': student_email,
        'parent_email': parent_email,
    })
# ------------------------ QUIZ SYSTEM ------------------------
def start_quiz(request):
    topic = request.session.get('topic')
    if not topic:
        return HttpResponse("Topic not found in session.")

    questions = []
    for i in range(1, 16):
        q = {
            'id': i,
            'question': f"What is a key concept in {topic} - Question {i}?",
            'options': [f"{topic} Option A", f"{topic} Option B", f"{topic} Option C", f"{topic} Option D"],
            'answer': f"{topic} Option A"
        }
        questions.append(q)

    request.session['quiz_questions'] = questions
    return render(request, 'quiz.html', {'questions': questions})
def enter_emails(request):
    if request.method == 'POST':
        student_email = request.POST.get('student_email')
        parent_email = request.POST.get('parent_email')

        if student_email and parent_email:
            request.session['student_email'] = student_email
            request.session['parent_email'] = parent_email
            messages.success(request, "Emails saved. Let's start preparing!")
            return redirect('start_prep_timer')
        else:
            messages.error(request, "Both emails are required.")

    return render(request, 'enter_emails.html')

from django.shortcuts import render

def collect_emails(request):
    return render(request, 'enter_emails.html')
# views.py

from django.shortcuts import render
def start_prep_timer(request):
    student_email = request.session.get('student_email')
    parent_email = request.session.get('parent_email')

    if not student_email or not parent_email:
        messages.error(request, "Missing email data. Please enter both emails.")
        return redirect('enter_emails')

    return render(request, 'pre_timer.html', {
        'student_email': student_email,
        'parent_email': parent_email
    })

def submit_quiz(request):
    if request.method == 'POST':
        topic = request.session.get('selected_topic')
        questions = request.session.get('questions')
        previous_score = request.session.get('previous_score', 0)

        if not questions:
            return HttpResponse("No questions found in session.")

        score = 0
        total = len(questions)
        results = []

        for i in range(total):
            user_answer = request.POST.get(f'q{i}')
            correct_answer = request.POST.get(f'correct{i}')

            results.append({
                'question': questions[i]['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': user_answer == correct_answer,
                'options': questions[i]['options']
            })

            if user_answer == correct_answer:
                score += 1

        # Save latest score
        request.session['previous_score'] = score

        # Email parent if no improvement
        if score <= previous_score:
            parent_email = request.session.get('parent_email')
            student_name = request.session.get('student_name', 'Student')

            if parent_email:
                send_mail(
                    subject="Student Performance Alert",
                    message=f"Dear Parent,\n\n{student_name} attempted a quiz on '{topic}' and did not show improvement.\nScore: {score}/{total}\n\nPlease provide extra support.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[parent_email],
                )

        return render(request, 'quiz_result.html', {
            'score': score,
            'total': total,
            'results': results,
            'topic': topic
        })