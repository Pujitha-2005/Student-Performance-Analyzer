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

def enter_rollno(request):
    return render(request, 'enter_rollno.html')


def check_roll_number(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no', '').strip()

        try:
            df = pd.read_excel(DATASET_PATH)

            roll_no_col = next((col for col in df.columns if 'roll' in col.lower()), None)
            percent_col = next((col for col in df.columns if 'percent' in col.lower()), None)

            if not roll_no_col:
                return render(request, 'enter_rollno.html', {'error': 'Roll Number column not found.'})

            df[roll_no_col] = df[roll_no_col].astype(str).str.strip()
            roll_no = roll_no.strip()

            if roll_no not in df[roll_no_col].values:
                return render(request, 'enter_rollno.html', {'error': 'Roll number not found. Please try again.'})

            student_data = df[df[roll_no_col] == roll_no]
            request.session['rollno'] = roll_no

            is_slow = False
            slow_learner_msg = ""
            if percent_col:
                percentage = pd.to_numeric(student_data.iloc[0][percent_col], errors='coerce')
                if pd.notna(percentage) and percentage < 60:
                    is_slow = True
                    slow_learner_msg = "❗ You are a Slow Learner based on your percentage."
                else:
                    slow_learner_msg = "✅ You are NOT a Slow Learner."

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
            'weak_subjects': weak_subjects,
            'offer_suggestions': not is_slow
        })


        except Exception as e:
            return render(request, 'enter_rollno.html', {'error': f"Error loading dataset: {e}"})

    return render(request, 'enter_rollno.html')
def suggest_topic(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        request.session['selected_topic'] = topic
        return redirect('provide_content')  # already implemented
    return redirect('dashboard')


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
        if feedback == 'yes':
            return redirect('enter_emails')  # make sure this name exists in urls.py
        else:
            messages.info(request, "Let's go through it once again.")
            topic = request.session.get('selected_topic')
            return redirect('provide_content') if topic else redirect('dashboard')
    return redirect('dashboard')



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


import requests
from django.shortcuts import render, redirect

TOGETHER_API_KEY = '19544a0ff9260f3ec9964701e97a1e730aaa593e48d9c5c3976f72a93f6677c4'  # 🔑 Replace with your actual key
def provide_content(request):
    if request.method == 'POST':
        topic = request.POST.get('topic') or request.session.get('selected_topic')
        request.session['selected_topic'] = topic
        rephrase = request.POST.get('rephrase') == 'true'

        prompt = f"""
        {'Explain again in a simpler way and with different examples.' if rephrase else 'Explain clearly'} 
        the topic '{topic}' for a student. Use clear formatting and practical examples.
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
            'ask_feedback': True  # Show yes/no buttons
        })

    return redirect('check_roll_number')



def start_prep_timer(request):
    topic = request.session.get('topic')
    rollno = request.session.get('rollno')
    if not topic or not rollno:
        return HttpResponse("Required session data missing.")

    end_time = datetime.now() + timedelta(minutes=1)
    user_sessions[rollno] = {'end_time': end_time}

    def send_reminder_email():
        time.sleep(30)  # simulate 6 hours
        send_mail(
            subject="⏰ Preparation Reminder!",
            message=f"Dear Student,\n\nThis is a reminder that your preparation time for '{topic}' is about to end. Please be ready for the quiz!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_TO_EMAIL]
        )

    threading.Thread(target=send_reminder_email).start()
    return render(request, 'prep_timer.html', {'end_time': end_time.timestamp()})

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

        request.session['student_email'] = student_email
        request.session['parent_email'] = parent_email

        messages.success(request, "Emails saved. Let's start preparing!")
        return redirect('start_prep_timer')

    return render(request, 'enter_emails.html')

from django.shortcuts import render, redirect
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib import messages

def collect_emails(request):
    if request.method == 'POST':
        student_email = request.POST.get('student_email')
        parent_email = request.POST.get('parent_email')

        if not student_email or not parent_email:
            return HttpResponse("Missing data. Please complete the previous steps.")

        request.session['student_email'] = student_email
        request.session['parent_email'] = parent_email

        return render(request, 'prep_timer.html') 

    return redirect('enter_emails')


import time
from django.shortcuts import redirect

def start_prep_timer(request):
    topic = request.session.get('topic')
    rollno = request.session.get('rollno')
    student_email = request.session.get('student_email')
    parent_email = request.session.get('parent_email')

    if not all([topic, rollno, student_email, parent_email]):
        messages.error(request, "Missing data. Please complete the previous steps.")
        return redirect('collect_emails')

    difficulty_levels = {
        'easy': 1,
        'medium': 2,
        'hard': 3
    }
    difficulty = random.choice(list(difficulty_levels.keys()))
    minutes = difficulty_levels[difficulty]
    end_time = datetime.now() + timedelta(minutes=minutes)


    user_sessions[rollno] = {
        'end_time': end_time,
        'difficulty': difficulty
    }
    return render(request, 'prep_timer.html', {'end_time': end_time.timestamp()})

from datetime import datetime, timedelta

def preparation_timer(request):
    exam_start_time = request.session.get('exam_start_time')
    return render(request, 'pre_timer.html', {'exam_start_time': exam_start_time})

from django.shortcuts import render

def enter_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        request.session['student_email'] = email

        exam_start_time = datetime.now() + timedelta(hours=6)
        request.session['exam_start_time'] = exam_start_time.strftime('%Y-%m-%d %H:%M:%S')

        threading.Thread(target=send_reminder_email, args=(email, exam_start_time)).start()

        return redirect('preparation_timer')

    return render(request, 'enter_email.html')
def start_quiz(request):
    return render(request, 'quiz.html')
def send_reminder_email(email, exam_start_time):
    now = datetime.now()
    reminder_time = exam_start_time - timedelta(minutes=1)  
    delay = (reminder_time - now).total_seconds()

    if delay > 0:
        threading.Event().wait(delay)  

    subject = '⏰ Reminder: Your Assessment Starts Soon!'
    message = 'Hi,\n\nThis is a reminder that your preparation time is almost over.\nGet ready to start your assessment.\n\nGood luck!'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        print(f"Reminder email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def submit_quiz(request):
    if request.method == 'POST':
        questions = request.session.get('quiz_questions', [])
        correct = sum(1 for q in questions if request.POST.get(str(q['id'])) == q['answer'])
        percentage = round((correct / len(questions)) * 100)
        previous = request.session.get('previous_score', 0)

        if percentage > previous:
            return render(request, 'thank_you.html', {
                'message': f'🎉 Congratulations! You improved with {percentage}%. Keep going!'
            })
        else:
            send_mail(
                subject="🚨 Student Performance Alert",
                message=f"The student did not improve in the quiz on '{request.session.get('topic')}'.\nScore: {percentage}% vs previous {previous}%",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_PARENT_EMAIL]
            )
            return render(request, 'thank_you.html', {
                'message': f"You scored {percentage}%. Your parent has been notified for further guidance."
            })
    return redirect('dashboard')