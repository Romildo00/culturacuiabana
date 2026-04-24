from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'cuiabania-energisa-senai-porto-2024'
DATABASE = 'database.db'

DOMINIOS_PERMITIDOS = ["@senai.br", "@fiesc.com.br", "@estudante.senai.br"]

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS participantes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nome         TEXT NOT NULL,
            email        TEXT UNIQUE NOT NULL,
            turma        TEXT NOT NULL,
            tipo         TEXT NOT NULL CHECK(tipo IN ('aluno','professor')),
            criado_em    DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feedbacks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            nota            INTEGER CHECK(nota >= 1 AND nota <= 5),
            comentario      TEXT,
            criado_em       DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(participante_id) REFERENCES participantes(id)
        );
    ''')
    conn.commit()
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
        conn = get_db()
        participante = conn.execute(
            'SELECT * FROM participantes WHERE id = ?', (session['participante_id'],)
        ).fetchone()
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
        conn = get_db()
        conn.execute(
            'INSERT INTO participantes (nome, email, turma, tipo) VALUES (?, ?, ?, ?)',
            (nome, email, turma, tipo)
        )
        conn.commit()
        pid = conn.execute(
            'SELECT id FROM participantes WHERE email = ?', (email,)
        ).fetchone()['id']
        conn.close()
        session['participante_id'] = pid
        session['participante_nome'] = nome
        flash(f'Bem-vindo, {nome}! Sua inscrição foi confirmada.', 'sucesso')
    except sqlite3.IntegrityError:
        # E-mail já existe — faz login direto
        conn = get_db()
        p = conn.execute(
            'SELECT * FROM participantes WHERE email = ?', (email,)
        ).fetchone()
        conn.close()
        if p:
            session['participante_id'] = p['id']
            session['participante_nome'] = p['nome']
            flash(f'Bem-vindo de volta, {p["nome"]}!', 'sucesso')
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

        conn = get_db()
        conn.execute(
            'INSERT INTO feedbacks (participante_id, nota, comentario) VALUES (?, ?, ?)',
            (session['participante_id'], nota, comentario)
        )
        conn.commit()
        conn.close()
        flash('Obrigado pelo seu feedback!', 'sucesso')
        return redirect(url_for('index'))

    conn = get_db()
    participante = conn.execute(
        'SELECT * FROM participantes WHERE id = ?', (session['participante_id'],)
    ).fetchone()
    conn.close()
    return render_template('feedback.html', participante=participante)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
