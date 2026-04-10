import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Monitor de Ocupação - Moradores e Visitantes", layout="wide")

st.title("📊 Painel de Ocupação (Moradores e Visitantes)")
st.markdown("Foco exclusivo em unidades ocupadas por moradores ou visitantes. Funcionários e Prestadores são ignorados na análise.")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza Inicial
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        df['Unidades'] = df['Unidades'].astype(str).str.strip()
        df['Tipo'] = df['Tipo'].astype(str).str.strip()
        
        # --- NOVO FILTRO: Ignorar Funcionários e Prestadores ---
        tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
        df = df[~df['Tipo'].isin(tipos_para_ignorar)].copy()
        # -------------------------------------------------------

        # Converte para data/hora real
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        
        # 2. Lista Geral de unidades (após o filtro de tipos)
        todas_unidades = pd.DataFrame({'Unidade': df['Unidades'].unique()})

        # 3. Filtrar apenas movimentos de Entrada/Saída Autorizada
        status_validos = ['Entrada autorizada', 'Saída autorizada']
        df_mov = df[df['Situação'].isin(status_validos)].copy()
        df_mov = df_mov.sort_values(by='Timestamp', ascending=False)

        # 4. Descobrir o estado atual de cada pessoa
        ultimo_evento_pessoa = df_mov.drop_duplicates(subset=['Unidades', 'Pessoa'], keep='first')
        
        # Filtramos quem ainda está DENTRO
        pessoas_dentro = ultimo_evento_pessoa[ultimo_evento_pessoa['Situação'] == 'Entrada autorizada'].copy()

        # 5. Lógica de UNIDADE OCUPADA (Contagem Única)
        # Se houver várias pessoas (ex: 2 moradores), pegamos o registro mais recente daquela unidade
        unidades_ocupadas = pessoas_dentro.sort_values('Timestamp', ascending=False).drop_duplicates('Unidades')
        
        # 6. Cruzamento de dados (Merge)
        relatorio = pd.merge(todas_unidades, unidades_ocupadas, left_on='Unidade', right_on='Unidades', how='left')
        
        relatorio['Situação Atual'] = relatorio['Situação'].apply(
            lambda x: "🔴 Ocupada" if x == "Entrada autorizada" else "🟢 Livre"
        )
        
        relatorio = relatorio[['Unidade', 'Situação Atual', 'Tipo', 'Pessoa', 'Hora']].rename(
            columns={'Tipo': 'Tipo Ocupante', 'Pessoa': 'Último Acesso', 'Hora': 'Horário'}
        )
        relatorio = relatorio.fillna("-")

        # --- EXIBIÇÃO ---

        # Métricas de Unidades (Moradores/Visitantes)
        ocupadas_df = relatorio[relatorio['Situação Atual'] == "🔴 Ocupada"]
        qtd_ocupadas = len(ocupadas_df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Unidades com Movimentação", len(relatorio))
        col2.metric("Unid. Ocupadas (Mor/Vis)", qtd_ocupadas)
        col3.metric("Unid. Livres", len(relatorio) - qtd_ocupadas)

        st.divider()

        # CONTAGEM ÚNICA POR TIPO (Somente Moradores e Visitantes)
        st.subheader("🏢 Unidades Ocupadas por Categoria")
        if qtd_ocupadas > 0:
            contagem_tipo = ocupadas_df['Tipo Ocupante'].value_counts()
            cols_tipo = st.columns(max(len(contagem_tipo), 2)) # Garante pelo menos 2 colunas
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)
        else:
            st.info("Nenhuma unidade ocupada por moradores ou visitantes no momento.")

        st.divider()

        # Tabela Final
        st.subheader("📋 Status Detalhado")
        st.dataframe(relatorio.sort_values('Unidade'), use_container_width=True, hide_index=True)

        # Botão de Download
        csv = relatorio.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório Filtrado", csv, "ocupacao_moradores_visitantes.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro ao processar os dados: {e}")
else:
    st.info("Aguardando upload do arquivo CSV para análise de Moradores e Visitantes.")