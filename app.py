from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta
import time
import os
from flask_sqlalchemy import SQLAlchemy
from flask import render_template


app = Flask(__name__)


# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:password@localhost:3306/community_events'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Modelo de dados
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(100), nullable=False)
    participants = db.Column(db.Integer, nullable=False)
    revenue = db.Column(db.Float, nullable=False)
    expenses = db.Column(db.Float, nullable=False)
    satisfaction = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Event {self.id}>'
    

# Criar as tabelas no banco de dados
with app.app_context():
    db.create_all()

# ROTAS
# Rota principal
@app.route('/')
def index():
    return render_template('index.html')


# Rota para adicionar novo evento
@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        new_event = Event(
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            type=request.form['type'],
            participants=int(request.form['participants']),
            revenue=float(request.form['revenue']),
            expenses=float(request.form['expenses']),
            satisfaction=float(request.form['satisfaction'])
        )
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('view_events'))
    return render_template('add_event.html')


# Rota para importar eventos de um arquivo CSV
@app.route('/import_events', methods=['POST'])
def import_events():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file and file.filename.endswith('.csv'):
        df = pd.read_csv(file)
    elif file and file.filename.endswith('.xlsx'):
        df = pd.read_excel(file)
    else:
        return "Formato de arquivo não suportado", 400
    
    for index, row in df.iterrows():
        event = Event(
            date=pd.to_datetime(row['date']).date(),
            type=row['type'],
            participants=int(row['participants']),
            revenue=float(row['revenue']),
            expenses=float(row['expenses']),
            satisfaction=float(row['satisfaction'])
        )
        db.session.add(event)
    
    db.session.commit()
    return redirect(url_for('view_events'))


# Rota para fazer o upload do arquivo 
@app.route('/upload')
def upload():
    return render_template('upload.html')


# Rota para visualizar eventos
@app.route('/view_events')
def view_events():
    events = Event.query.all()
    return render_template('view_events.html', events=events)


# Rota para análise de dados
@app.route('/analysis')
def analysis():
    import pandas as pd
    import plotly.express as px
    import plotly.io as pio
    
    # Converter dados do banco de dados para DataFrame
    events = Event.query.all()
    df = pd.DataFrame([
        {
            'date': event.date,
            'type': event.type,
            'participants': event.participants,
            'revenue': event.revenue,
            'expenses': event.expenses,
            'satisfaction': event.satisfaction
        } for event in events
    ])
    
    # Gráfico de dispersão: Participantes vs Receita
    scatter_fig = px.scatter(df, x='participants', y='revenue', color='type',
                             title='Participantes vs Receita por Tipo de Evento')
    scatter_plot = pio.to_html(scatter_fig, full_html=False)
    
    # Gráfico de barras: Receita média por tipo de evento
    bar_fig = px.bar(df.groupby('type')['revenue'].mean().reset_index(), 
                     x='type', y='revenue', title='Receita Média por Tipo de Evento')
    bar_plot = pio.to_html(bar_fig, full_html=False)
    
    # Histograma: Distribuição da satisfação
    hist_fig = px.histogram(df, x='satisfaction', title='Distribuição da Satisfação')
    hist_plot = pio.to_html(hist_fig, full_html=False)
    
    return render_template('analysis.html', scatter_plot=scatter_plot, 
                           bar_plot=bar_plot, hist_plot=hist_plot)


# Rota para gerar relatório trimestral
@app.route('/generate_report')
def generate_report():
    # Calcular a data de três meses atrás
    three_months_ago = datetime.now() - timedelta(days=90)

    # Filtrar eventos dos últimos três meses
    events = Event.query.filter(Event.date >= three_months_ago).all()
    
    # Dados de exemplo para o relatório
    total_participants = sum(event.participants for event in events)
    total_revenue = sum(event.revenue for event in events)

    # Renderizar template HTML para o relatório
    return render_template('report_template.html', 
                           total_participants=total_participants, 
                           total_revenue=total_revenue, 
                           events=events)  



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
