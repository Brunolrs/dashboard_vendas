import streamlit as st
import requests
import pandas as pd
import plotly.express as px


#Formata números grandes com sufixos apropriados

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000.0:
            return f"{prefixo}{valor:.2f} {unidade}"
        valor /= 1000.0
    return f"{prefixo}{valor:.2f} milhões"

# Carrega os dados de vendas a partir de uma API

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Selecione a região', regioes)
if regiao == 'Brasil':
    regiao = ''
todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if not todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)
query_string = {'regiao': regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Selecione os vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas

### Tabelas de receita

receita_estados = dados.groupby('Local da compra')[['Preço']].sum()

receita_estados = (dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']]
                   .merge(receita_estados, left_on = 'Local da compra', right_index = True)
                   .sort_values('Preço', ascending = False)
                   )

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))[['Preço']].sum().reset_index()

receita_mensal['Ano']= receita_mensal['Data da Compra'].dt.year

receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name().str.slice(stop=3)

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

### Tabelas de quantidades de vendas 

# Quantidade de vendas por estado
quantidade_vendas_por_estado = dados.groupby('Local da compra').size().reset_index(name='Quantidade de Vendas').sort_values('Quantidade de Vendas', ascending=False)
quantidade_vendas_por_estado = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(quantidade_vendas_por_estado, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

# Quantidade de vendas mensal
quantidade_vendas_mensal = (
    dados.set_index('Data da Compra')
    .groupby(pd.Grouper(freq = 'M'))
    .size()
    .reset_index(name='Quantidade de Vendas')
)
quantidade_vendas_mensal['Ano']= quantidade_vendas_mensal['Data da Compra'].dt.year
quantidade_vendas_mensal['Mês'] = quantidade_vendas_mensal['Data da Compra'].dt.month_name().str.slice(stop=3)

# Top 5 estados por quantidade de vendas

quantidade_vendas_top_estados = quantidade_vendas_por_estado.sort_values('Quantidade de Vendas', ascending=False).head(5)
quantidade_vendas_top_estados.reset_index(drop=True, inplace=True)

# Quantidade de vendas por categoria de produto
quantidade_vendas_por_categoria = (dados.groupby('Categoria do Produto')
                                   .size()
                                   .reset_index(name='Quantidade de Vendas por Produto')
                                   .sort_values('Quantidade de Vendas por Produto', ascending=False))

### Tabelas de vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## Gráficos

### Gráficos de receita
fig_mapa_receita = px.scatter_geo(receita_estados,
                                   lat = 'lat',
                                   lon = 'lon',
                                   scope = 'south america',
                                   size = 'Preço',
                                   template = 'seaborn',
                                   hover_name = 'Local da compra',
                                   hover_data = {'lat':False,'lon':False},
                                   title = 'Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mês',
                             y = 'Preço',
                             markers=True,
                             range_y=(0,receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita Mensal'
                             )
fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                                            x = 'Local da compra',
                                            y = 'Preço',
                                            text_auto = True,
                                            title = 'Top estados')

fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto = True,
                                title = 'Receita por categoria')

fig_receita_categorias.update_layout(yaxis_title = 'Receita')

### Graficos de quantidade de vendas

fig_mapa_vendas = px.scatter_geo(quantidade_vendas_por_estado, 
                     lat = 'lat', 
                     lon= 'lon', 
                     scope = 'south america', 
                     #fitbounds = 'locations', 
                     template='seaborn', 
                     size = 'Preço', 
                     hover_name ='Local da compra', 
                     hover_data = {'lat':False,'lon':False},
                     title = 'Vendas por estado',
                     )

fig_vendas_estados = px.bar(quantidade_vendas_por_estado.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados'
)

fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_mensal = px.line(quantidade_vendas_mensal, 
              x = 'Mes',
              y='Preço',
              markers = True, 
              range_y = (0,quantidade_vendas_mensal.max()), 
              color = 'Ano', 
              line_dash = 'Ano',
              title = 'Quantidade de vendas mensal')

fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_categorias = px.bar(quantidade_vendas_por_categoria, 
                                text_auto = True,
                                title = 'Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')



##Visualização de dados com Streamlit

# Configuração da página

st.title('DASHBOARD DE VENDAS :shopping_cart:')

# Exibe métricas principais
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores']) 

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True, key='mapa_receita')
        st.plotly_chart(fig_receita_estados, use_container_width=True, key='top_estados')
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True, key='receita_mensal')
        st.plotly_chart(fig_receita_categorias, use_container_width=True, key='receita_categorias')

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))

st.dataframe(dados)
st.dataframe(quantidade_vendas_por_estado)
st.dataframe(quantidade_vendas_mensal)
st.dataframe(quantidade_vendas_top_estados)
st.dataframe(quantidade_vendas_por_categoria)

with aba3:
    
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
            x='sum',
            y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (receita)'
            )
        st.plotly_chart(fig_receita_vendedores)
    
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_quantidade_vendas = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
            x='count',
            y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)'
            )
        st.plotly_chart(fig_quantidade_vendas)

        

