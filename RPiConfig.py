#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sqlite3 as lite
from functools import wraps
from flask import *

app = Flask(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'RPiConfig.db'),
    DEBUG=True,
    SECRET_KEY='technext',
    USERNAME='tnext',
    PASSWORD='adm@tnext'
))

app.config.from_envvar('FLASK_SETTINGS', silent=True)

nome_log = 'RPiLog.txt'


def conecta_db():
    con = lite.connect(app.config['DATABASE'])
    con.row_factory = lite.Row
    return con


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = conecta_db()
    return g.sqlite_db


@app.teardown_appcontext
def fecha_db():
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# definição de campos requeridos
required = ['nome', 'senha']


def db_select():
    # conectar com o banco de dados
    db = get_db()
    rs = db.execute('select * from terminal')
    reg = rs.fetchone()
    return reg


def db_dicionario():
    # define os campos e o dicionario dos registros
    reg = db_select()
    rg_cp = reg.keys()
    rg_db = dict(zip(rg_cp, reg))
    return rg_db


def db_rg_prot():
    # seleção do protocolo
    rg_db = db_dicionario()
    pr_cp = {'TCP': '', 'UDP': ''}
    x = rg_db['protocolo']
    pr_cp[x] = 'selected'
    return pr_cp


def db_rg_baud():
    # selecao do baud rate
    rg_db = db_dicionario()
    br_cp = {300: '', 1200: '', 2400: '', 4800: '', 9600: '', 14400: '', 19200: '', 28800: '', 38400: '', 57600: '',
             115200: '', 230400: ''}
    x = rg_db['baud_rate']
    br_cp[x] = 'selected'
    return br_cp


def db_rg_pty():
    # seleção de Parity
    rg_db = db_dicionario()
    pt_cp = {'E': '', 'M': '', 'N': '', 'O': '', 'S': ''}
    x = rg_db['parity']
    pt_cp[x] = 'selected'
    return pt_cp


def db_rg_dbs():
    # seleção de Data Bits
    rg_db = db_dicionario()
    dt_cp = {5: '', 6: '', 7: '', 8: ''}
    x = rg_db['data_bits']
    dt_cp[x] = 'selected'
    return dt_cp


def db_rg_sbs():
    # seleção de stop bits
    rg_db = db_dicionario()
    sb_cp = {1: '', 1.5: '', 2: ''}
    x = rg_db['stop_bits']
    sb_cp[x] = 'selected'
    return sb_cp


def db_rg_log():
    # seleção do arquivo de log
    rg_db = db_dicionario()
    al_cp = {'A': '', 'I': ''}
    x = rg_db['arq_log']
    al_cp[x] = 'selected'
    return al_cp


# disponibiliza o registro para os templates
@app.context_processor
def registro():
    rg_db = db_dicionario()
    return dict(reg=rg_db)


# disponibiliza o protocolo para os templates
@app.context_processor
def protocolo():
    pr_db = db_rg_prot()
    return dict(prot=pr_db)


# disponibiliza o baud rate para os templates
@app.context_processor
def baud_rate():
    br_db = db_rg_baud()
    return dict(baud=br_db)


# disponibiliza o parity para os templates
@app.context_processor
def parity():
    pt_db = db_rg_pty()
    return dict(pty=pt_db)


# disponibiliza o data bits para os templates
@app.context_processor
def data_bits():
    dt_db = db_rg_dbs()
    return dict(dbs=dt_db)


# disponibiliza o stop bits para os templates
@app.context_processor
def stop_bits():
    sb_db = db_rg_sbs()
    return dict(sbs=sb_db)


# disponibiliza o arquivo de log para os templates
@app.context_processor
def arqui_log():
    al_db = db_rg_log()
    arq_log = "N"
    if os.path.isfile(nome_log):
        arq_log = "S"
    return dict(alg=al_db, down=arq_log)


def requer_login(f):
    @wraps(f)
    def logado(*args, **kwargs):
        if required[0] in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return logado


@app.errorhandler(404)
def page_not_found():
    return render_template('404.html'), 404


@app.route("/")
@requer_login
def index():
    return redirect(url_for('config'))


@app.route("/<page>/")
def paginas(page=None):
    page += ".html"
    if os.path.isfile(app.root_path + '/templates/' + page):
        return render_template(page)
    abort(404)


@app.route("/config/")
@requer_login
def config():
    return render_template('config.html')


@app.route("/login/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        for r in required:
            if r not in request.form:
                return render_template('login.html')
        username = request.form['nome']
        passwd = request.form['senha']
        if username == app.config['USERNAME'] and passwd == app.config['PASSWORD']:
            session['nome'] = username
            return redirect(url_for('config'))
        else:
            flash("Usuario ou senha incorreta!!!")
            return render_template('login.html')
    else:
        if app.config['USERNAME'] in session:
            return redirect(url_for('config'))
        else:
            return render_template('login.html')


@app.route('/logout/')
def logout():
    session.pop('nome', None)
    return redirect(url_for('login'))


@app.route('/reboot')
@requer_login
def reboot():
    os.system('sudo reboot')


@app.route('/download', methods=['GET', 'POST'])
@requer_login
def download():
    file_log = send_file(os.path.join(app.root_path, nome_log))
    response = make_response(file_log)
    response.headers["Content-Disposition"] = "attachment; filename=" + nome_log
    return response


def db_network():
    db = get_db()
    local = request.form.get('local')
    dispositivo = request.form.get('dispositivo')
    ip_local = request.form.get('ip_local')
    mascara_rede = request.form.get('mascara_rede')
    porta_local = request.form.get('porta_local')
    sql = "UPDATE terminal SET local='" + local
    sql += "',dispositivo='" + dispositivo
    sql += "',ip_local='" + ip_local
    sql += "',mascara_rede='" + mascara_rede
    sql += "',porta_local='" + porta_local + "'"
    db.execute(sql)
    db.commit()


def db_conexao():
    db = get_db()
    protocol = request.form.get('protocolo')
    ip_servidor = request.form.get('ip_servidor')
    porta_servidor = request.form.get('porta_servidor')
    sql = "UPDATE terminal SET protocolo='" + protocol
    sql += "',ip_servidor='" + ip_servidor
    sql += "',porta_servidor='" + porta_servidor + "'"
    db.execute(sql)
    db.commit()


def db_serial():
    db = get_db()
    bd_rate = request.form.get('baud_rate')
    prty = request.form.get('parity')
    dt_bits = request.form.get('data_bits')
    st_bits = request.form.get('stop_bits')
    sql = "UPDATE terminal SET baud_rate='" + bd_rate
    sql += "',parity='" + prty
    sql += "',data_bits='" + dt_bits
    sql += "',stop_bits='" + st_bits + "'"
    db.execute(sql)
    db.commit()


def db_log():
    db = get_db()
    arq_log = request.form.get('arq_log')
    sql = "UPDATE terminal SET arq_log='" + arq_log + "'"
    db.execute(sql)
    db.commit()
    if arq_log == 'A':
        os.system('sudo rm ' + os.path.join(app.root_path, nome_log))


def acao_form(op):
    acao = {
        'network': db_network,
        'conexao': db_conexao,
        'serial': db_serial,
        'log': db_log
    }
    acao[op]()


@app.route('/dados/')
@app.route('/dados/<acao>/', methods=['POST', 'GET'])
@requer_login
def dados(acao=None):
    if request.method == 'POST':
        acao_form(acao)
        return redirect(url_for('config'))
    else:
        abort(404)


app.run(debug=True, use_reloader=True, host='0.0.0.0', port=8080)
