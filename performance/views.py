import matplotlib
matplotlib.use('Agg') # MUST be called BEFORE importing pyplot
import matplotlib.pyplot as plt
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
import requests
import json

DATASET_PATH = os.path.join(settings.BASE_DIR, 'student_performance', 'dataset', 'Student_Marks_500.xlsx')
user_sessions = {}
GEMINI_API_KEY = "AIzaSyD89Brg7p-jyi-9aIUaDt4fH_ZSpgQ0Uv0"
GEMINI_MODEL = "gemini-2.0-flash" 
GEMINI_API_BASE_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'

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
            else:
                slow_learner_msg = "Percentage column not found to determine slow learner status."

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

def confirm_understanding(request):
    if request.method == 'POST':
        feedback = request.POST.get('feedback')
        topic = request.session.get('selected_topic')

        if feedback == 'yes':
            return redirect('enter_emails')  # Next step
        else:
            messages.info(request, "Let's go through it once again in simpler terms.")
            return redirect(reverse('provide_content') + '?rephrase=true')

    return redirect('dashboard')


# ------------------------ PIE CHART ------------------------
# In your views.py file:

# ... (rest of your imports and views.py code above this function) ...

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
    marks = student_row.drop(columns=[col for col in excluded_cols if col in student_row.columns], errors='ignore')
    marks = marks.select_dtypes(include=['number'])

    if marks.empty:
        return HttpResponse("No numeric subject scores found for analysis.")

    marks_dict = marks.iloc[0].to_dict()

    weak_subjects = {subj: score for subj, score in marks_dict.items() if score < 60}
    if not weak_subjects:
        return HttpResponse("🎉 You have no weak subjects!")

    plt.figure(figsize=(6, 6))
    plt.pie(weak_subjects.values(), labels=weak_subjects.keys(), autopct='%1.1f%%')
    plt.title(f'Weak Subjects for Roll No: {rollno}')
    plt.axis('equal')

    # Ensure the static directory exists and save the pie chart
    static_dir = os.path.join(settings.BASE_DIR, 'static')
    os.makedirs(static_dir, exist_ok=True)
    pie_path = os.path.join(static_dir, f'weak_subjects_pie_{rollno}.png')
    plt.savefig(pie_path)
    plt.close() # Close the plot to free up memory

    pie_chart_url = f'/static/weak_subjects_pie_{rollno}.png' # URL to access the image

    return render(request, 'analyze_subjects.html', {
        'weak_subjects': weak_subjects,
        'pie_chart': pie_chart_url
    })

# ------------------------ CONTENT EXPLANATION (USING GEMINI API) ------------------------
def provide_content(request):
    if request.method == 'POST':
        topic_from_post = request.POST.get('doubt_topic')
        if topic_from_post:
            request.session['selected_topic'] = topic_from_post
            topic = topic_from_post
        else:
            messages.error(request, "Please enter a topic.")
            return redirect('dashboard')
    else:
        topic = request.session.get('selected_topic')

    if not topic:
        messages.error(request, "Please select a topic first.")
        return redirect('dashboard')

    rephrase = request.GET.get('rephrase', 'false').lower() == 'true'

    prompt_text = f"""
    {'Explain again in a simpler way with different examples.' if rephrase else 'Explain clearly'}
    the topic '{topic}' for a student. Use easy language and real-world examples.
    """

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "maxOutputTokens": 700,
            "temperature": 0.7
        }
    }

    explanation = "Error: Could not get explanation from AI."
    try:
        response = requests.post(
            GEMINI_API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        explanation = result['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Gemini API Request failed: {e}. Please check your API key and internet connection.")
        explanation = f"⚠ Error connecting to explanation service: {e}"
    except (KeyError, IndexError) as e:
        messages.error(request, f"Unexpected response format from Gemini AI: {e}. Please check API key and model access.")
        explanation = f"⚠ Error parsing Gemini AI response: {e}. Response: {response.text if 'response' in locals() else 'No response'}"
    except Exception as e:
        messages.error(request, f"An unexpected error occurred with Gemini: {e}")
        explanation = f"⚠ An unexpected error occurred: {e}"

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

# ------------------------ QUIZ SYSTEM (USING GEMINI API) ------------------------
def start_quiz(request):
    topic = request.session.get('selected_topic')
    if not topic:
        return HttpResponse("❌ Topic not found in session. Please select a topic first.")

    prompt_text = f"""
    Generate 15 multiple-choice questions (MCQs) on the topic "{topic}" for a student.
    Each question should have:
    - a clear question text
    - 4 options labeled A, B, C, D
    - indicate the correct answer. The correct answer should be one of the provided options.
    Format the response strictly as a JSON array of objects, like this example:
    [
      {{
        "question": "What is the capital of France?",
        "options": ["Paris", "Berlin", "Rome", "Madrid"],
        "answer": "Paris"
      }},
      {{
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Jupiter", "Venus"],
        "answer": "Mars"
      }}
    ]
    Ensure the JSON is perfectly formed and contains only the array. Do not include any introductory or concluding text or markdown formatting.
    """

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt_text}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature": 0.7,
            "topP": 0.9
        }
    }

    try:
        response = requests.post(
            GEMINI_API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        output_text = result['candidates'][0]['content']['parts'][0]['text']

        if not output_text:
            return HttpResponse("❌ No output returned from the Gemini model. Please try again.")

        # --- FIX: Strip Markdown code block delimiters before JSON parsing ---
        if output_text.strip().startswith('```json') and output_text.strip().endswith('```'):
            output_text = output_text.strip()[len('```json'):-len('```')].strip()
        # --- End FIX ---

        questions = json.loads(output_text)

        if not isinstance(questions, list):
            print(f"❌ Gemini output was not a list: {output_text}")
            return HttpResponse("❌ AI output was not in the expected list format for quiz. Please try again.")

        cleaned_questions = []
        for i, q in enumerate(questions, start=1):
            if all(key in q for key in ['question', 'options', 'answer']) and isinstance(q['options'], list) and q['answer'] in q['options']:
                q['id'] = i
                cleaned_questions.append(q)
            else:
                messages.warning(request, f"Skipping malformed question from Gemini AI: {q}")

        if not cleaned_questions:
            messages.error(request, "No valid questions were generated by Gemini AI.")
            return redirect('dashboard')


        request.session['quiz_questions'] = cleaned_questions
        return render(request, 'quiz.html', {'questions': cleaned_questions, 'topic': topic})

    except requests.exceptions.RequestException as e:
        print("❌ Gemini API Request failed:", e)
        return HttpResponse(f"❌ Failed to reach Gemini API: {e}. Check your API key and network.")
    except json.JSONDecodeError as e:
        print("❌ Failed to parse Gemini model output as JSON:", e)
        print(f"Raw output causing error: {output_text}")
        return HttpResponse("❌ Gemini output was not in expected JSON format. Please try again.")
    except (KeyError, IndexError) as e:
        print("❌ Unexpected Gemini API response structure:", e)
        print(f"Raw response: {response.text if 'response' in locals() else 'No response object'}")
        return HttpResponse(f"❌ Unexpected Gemini API response. Error: {e}")
    except Exception as e:
        print("❌ An unexpected error occurred in start_quiz with Gemini:", e)
        return HttpResponse("❌ An unexpected error occurred during quiz generation with Gemini.")


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

def collect_emails(request):
    return render(request, 'enter_emails.html')

def submit_quiz(request):
    if request.method != 'POST':
        return HttpResponse("Invalid method.")

    questions = request.session.get('quiz_questions', [])
    previous_score = request.session.get('previous_score', 0)

    if not questions:
        return HttpResponse("No quiz questions found in session.")

    current_score = 0
    total_questions = len(questions)
    wrong_answers_details = []

    for q in questions:
        user_answer = request.POST.get(f'q{q["id"]}')
        correct_answer = q['answer']

        if user_answer == correct_answer:
            current_score += 1
        else:
            wrong_answers_details.append({
                'question': q['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'options': q['options']
            })

    current_percentage = round((current_score / total_questions) * 100) if total_questions > 0 else 0

    request.session['previous_score'] = current_percentage

    parent_email = request.session.get('parent_email')
    student_name = request.session.get('username', 'Student')
    selected_topic = request.session.get('selected_topic', 'a topic')

    if current_percentage > previous_score:
        message = f'🎉 Congratulations! You improved with {current_percentage}% (Previous: {previous_score}%). Keep going!'
    else:
        message = f"You scored {current_percentage}% (Previous: {previous_score}%). Your parent has been notified for further guidance."
        if parent_email:
            send_mail(
                subject="🚨 Student Performance Alert",
                message=f"Dear Parent,\n\n{student_name} attempted a quiz on '{selected_topic}' and did not show improvement.\nScore: {current_percentage}% vs previous {previous_score}%.\n\nPlease provide extra support if needed.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[parent_email],
            )
            messages.info(request, "An email regarding performance has been sent to your parent.")

    return render(request, 'quiz_result.html', {
        'score': current_score,
        'total': total_questions,
        'percentage': current_percentage,
        'wrong_answers': wrong_answers_details,
        'message': message,
        'topic': selected_topic
    })
