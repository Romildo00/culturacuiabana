from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import psycopg2
import os
import re
from urllib.parse import urlparse

app = Flask(__name__, template_folder='templates')
app.secret_key = 'cuiabania-energisa-senai-porto-2024'

# Configuração do Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://fjownmxohtckwkcthwao.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqb3dubXhvaHRja3drY3Rod2FvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5OTM3MjQsImV4cCI6MjA5MjU2OTcyNH0.8zKYaYBCiEC4-K7CtRJnIMsyL76R_CxJC-2Kkkrh2mc')

# Parse da URL de conexão do Supabase
def get_db_connection():
    # String de conexão do Supabase
    db_password = os.environ.get('DB_PASSWORD', '@DBSENAIPROJECT007008')
    conn = psycopg2.connect(
        host="db.fjownmxohtckwkcthwao.supabase.co",
        port="5432",
        database="postgres",
        user="postgres",
        password=db_password
    )
    return conn

DOMINIOS_PERMITIDOS = ["@senai.br", "@docente.senai.br", "@aluno.senai.br"]

def get_db():
    conn = get_db_connection()
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS participantes (
            id           SERIAL PRIMARY KEY,
            nome         TEXT NOT NULL,
            email        TEXT UNIQUE NOT NULL,
            turma        TEXT NOT NULL,
            tipo         TEXT NOT NULL CHECK(tipo IN ('aluno','professor')),
            criado_em    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id              SERIAL PRIMARY KEY,
            participante_id INTEGER,
            nota            INTEGER CHECK(nota >= 1 AND nota <= 5),
            comentario      TEXT,
            criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(participante_id) REFERENCES participantes(id)
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def validar_email(email):
    return any(email.lower().endswith(d) for d in DOMINIOS_PERMITIDOS)

def usuario_logado():
    return session.get('participante_id') is not None

# ── Rotas ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    logado = usuario_logado()
    participante = None
    if logado:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM participantes WHERE id = %s', (session['participante_id'],))
        participante = cur.fetchone()
        cur.close()
        conn.close()
    return render_template('index.html', logado=logado, participante=participante)

@app.route('/registrar', methods=['POST'])
def registrar():
    nome   = request.form.get('nome', '').strip()
    email  = request.form.get('email', '').strip()
    turma  = request.form.get('turma', '').strip()
    tipo   = request.form.get('tipo', '').strip()

    if not all([nome, email, turma, tipo]):
        flash('Preencha todos os campos.', 'erro')
        return redirect(url_for('index'))

    if not validar_email(email):
        flash('E-mail não permitido. Use domínio do Senai.', 'erro')
        return redirect(url_for('index'))

    if tipo not in ['aluno', 'professor']:
        flash('Tipo inválido.', 'erro')
        return redirect(url_for('index'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO participantes (nome, email, turma, tipo) VALUES (%s, %s, %s, %s) RETURNING id',
            (nome, email, turma, tipo)
        )
        pid = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        session['participante_id'] = pid
        session['participante_nome'] = nome
        flash(f'Bem-vindo, {nome}! Sua inscrição foi confirmada.', 'sucesso')
    except psycopg2.IntegrityError:
        # E-mail já existe — faz login direto
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM participantes WHERE email = %s', (email,))
        p = cur.fetchone()
        cur.close()
        conn.close()
        if p:
            session['participante_id'] = p[0]
            session['participante_nome'] = p[1]
            flash(f'Bem-vindo de volta, {p[1]}!', 'sucesso')
        else:
            flash('Erro ao processar cadastro.', 'erro')

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu com sucesso.', 'info')
    return redirect(url_for('index'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if not usuario_logado():
        flash('Faça seu registro para acessar o feedback.', 'aviso')
        return redirect(url_for('index'))

    if request.method == 'POST':
        nota       = request.form.get('nota')
        comentario = request.form.get('comentario', '').strip()

        if not nota:
            flash('Selecione uma nota.', 'erro')
            return redirect(url_for('feedback'))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO feedbacks (participante_id, nota, comentario) VALUES (%s, %s, %s)',
            (session['participante_id'], nota, comentario)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash('Obrigado pelo seu feedback!', 'sucesso')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM participantes WHERE id = %s', (session['participante_id'],))
    participante = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('feedback.html', participante=participante)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
