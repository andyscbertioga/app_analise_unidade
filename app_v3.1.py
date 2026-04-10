import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Monitor de Ocupação", layout="wide")

st.title("📊 Painel de Ocupação por Unidade")
st.markdown("Contagem única por unidade com separação por tipo de ocupante.")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza
        df = pd.read_csv(uploaded_file)
        # Remove espaços extras nos nomes das colunas e dados
        df.columns = df.columns.str.strip()
        df['Unidades'] = df['Unidades'].astype(str).str.strip()
        df['Tipo'] = df['Tipo'].astype(str).str.strip()
        
        # Converte para data/hora real
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        
        # 2. Lista Geral de todas as unidades que existem no arquivo
        todas_unidades = pd.DataFrame({'Unidade': df['Unidades'].unique()})

        # 3. Filtrar apenas movimentos que mudam o status (Entrada/Saída Autorizada)
        status_validos = ['Entrada autorizada', 'Saída autorizada']
        df_mov = df[df['Situação'].isin(status_validos)].copy()
        df_mov = df_mov.sort_values(by='Timestamp', ascending=False)

        # 4. Descobrir quem está dentro (último registro de cada pessoa deve ser Entrada)
        # Pega o último evento de cada pessoa em cada unidade
        ultimo_evento_pessoa = df_mov.drop_duplicates(subset=['Unidades', 'Pessoa'], keep='first')
        
        # Filtramos apenas quem o último status foi ENTRADA (ou seja, ainda não saiu)
        pessoas_dentro = ultimo_evento_pessoa[ultimo_evento_pessoa['Situação'] == 'Entrada autorizada'].copy()

        # 5. Lógica de UNIDADE OCUPADA (Contagem Única)
        # Se uma unidade tem várias pessoas, pegamos a mais recente para ser a "Responsável" pela ocupação
        # Isso garante que a unidade seja contada apenas uma vez
        unidades_ocupadas = pessoas_dentro.sort_values('Timestamp', ascending=False).drop_duplicates('Unidades')
        
        # 6. Cruzamento de dados para gerar o relatório final
        # Juntamos a lista de todas as unidades com a lista das que estão ocupadas
        relatorio = pd.merge(todas_unidades, unidades_ocupadas, left_on='Unidade', right_on='Unidades', how='left')
        
        # Define o status visual
        relatorio['Situação Atual'] = relatorio['Situação'].apply(
            lambda x: "🔴 Ocupada" if x == "Entrada autorizada" else "🟢 Livre"
        )
        
        # Limpa colunas desnecessárias
        relatorio = relatorio[['Unidade', 'Situação Atual', 'Tipo', 'Pessoa', 'Hora']].rename(
            columns={'Tipo': 'Tipo Ocupante', 'Pessoa': 'Último Acesso', 'Hora': 'Horário'}
        )
        relatorio = relatorio.fillna("-")

        # --- EXIBIÇÃO ---

        # Métricas de Unidades
        total_unid = len(relatorio)
        ocupadas_df = relatorio[relatorio['Situação Atual'] == "🔴 Ocupada"]
        qtd_ocupadas = len(ocupadas_df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Unidades", total_unid)
        col2.metric("Total Ocupadas", qtd_ocupadas)
        col3.metric("Total Vazias", total_unid - qtd_ocupadas)

        st.divider()

        # CONTAGEM ÚNICA POR TIPO (A soma aqui será igual ao total de ocupadas)
        st.subheader("🏢 Unidades Ocupadas por Categoria")
        if qtd_ocupadas > 0:
            contagem_tipo = ocupadas_df['Tipo Ocupante'].value_counts()
            cols_tipo = st.columns(len(contagem_tipo))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)
        else:
            st.info("Nenhuma unidade ocupada no momento.")

        st.divider()

        # Tabela Final
        st.subheader("📋 Status Detalhado")
        st.dataframe(relatorio.sort_values('Unidade'), use_container_width=True, hide_index=True)

        # Botão de Download
        csv = relatorio.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório", csv, "ocupacao_unidades.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro ao processar os dados: {e}")
else:
    st.info("Aguardando arquivo CSV...")