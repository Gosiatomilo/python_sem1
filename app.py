from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import plotly.express as px
import os

app = Flask(__name__)
app.secret_key = 'super_tajny_klucz_zaliczeniowy'

# LOGIKA BAZY DANYCH
def verify_user(username, password):
    if not os.path.exists("users.csv"):
        return False
    users_df = pd.read_csv("users.csv")
    user = users_df[(users_df['username'] == username) & (users_df['password'] == password)]
    return not user.empty

# LOGIKA ANALIZY DANYCH
def load_and_process_data():
    file_path = "dane.csv"
    df = pd.read_csv(file_path, skiprows=4)
    df.columns = [str(c).strip() for c in df.columns]
    years_cols = [str(y) for y in range(1990, 2026)]
    
    def clean_row(idx):
        return df.loc[idx, years_cols].astype(str).str.replace(r'\s+', '', regex=True).str.replace('x', 'NaN').astype(float)
    
    total = clean_row(3)
    women = clean_row(8)
    men = total - women
    
    df_gender = pd.DataFrame({
        'Rok': years_cols,
        'Kobiety': women.values,
        'Mężczyźni': men.values
    })
    
    age_labels = ["15-17", "18-24", "25-34", "35-44", "45-54", "55-59", "60 i więcej"]
    age_indices = range(13, 20)
    df_age = pd.DataFrame({'Rok': years_cols})
    for idx, label in zip(age_indices, age_labels):
        df_age[label] = clean_row(idx).values
        
    edu_labels = ["wyższe", "policealne/średnie zawodowe", "średnie ogólnokształcące", "zasadnicze zawodowe", "gimnazjalne/podstawowe"]
    edu_indices = range(21, 26)
    df_edu = pd.DataFrame({'Rok': years_cols})
    for idx, label in zip(edu_indices, edu_labels):
        df_edu[label] = clean_row(idx).values
        
    return df_gender, df_age, df_edu

# ROUTING WEBOWY
@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Błędny login lub hasło!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    df_gender, df_age, df_edu = load_and_process_data()
    
    fig_gender = px.line(df_gender, x='Rok', y=['Kobiety', 'Mężczyźni'], title="Bezrobocie wg płci (1990-2025)", labels={'value': 'Liczba bezrobotnych', 'variable': 'Płeć'}, markers=True)
    gender_html = fig_gender.to_html(full_html=False)
    
    fig_age = px.line(df_age, x='Rok', y=df_age.columns[1:], title="Bezrobocie wg wieku (1990-2025)", labels={'value': 'Liczba bezrobotnych', 'variable': 'Wiek'}, markers=True)
    age_html = fig_age.to_html(full_html=False)
    
    fig_edu = px.line(df_edu, x='Rok', y=df_edu.columns[1:], title="Bezrobocie wg wykształcenia (1990-2025)", labels={'value': 'Liczba bezrobotnych', 'variable': 'Wykształcenie'}, markers=True)
    edu_html = fig_edu.to_html(full_html=False)
    
    return render_template('dashboard.html', 
                           gender_html=gender_html, 
                           age_html=age_html, 
                           edu_html=edu_html, 
                           username=session['username'])

if __name__ == '__main__':
    app.run(debug=True)