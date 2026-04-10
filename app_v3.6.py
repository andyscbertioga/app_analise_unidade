import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Monitor de Ocupação - Filtro de Tipo", layout="wide")

st.title("📊 Painel de Ocupação Final")
st.markdown("""
**Novas regras aplicadas:**
1. Linhas sem informação de **Tipo de Ocupante** são totalmente ignoradas.
2. Unidades vazias mostram agora os dados da última pessoa que saiu (Tipo, Nome e Hora).
""")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza Inicial
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        # Limpeza de strings para evitar erros de comparação
        for col in ['Unidades', 'Tipo', 'Situação', 'Pessoa']:
            df[col] = df[col].astype(str).str.strip()
        
        # --- FILTRO 1: Ignorar se Tipo estiver vazio ou inválido ---
        # Remove "nan", campos vazios ou nulos na coluna Tipo
        df = df[df['Tipo'].notna()]
        df = df[~df['Tipo'].isin(['', 'nan', 'None', 'N/A'])]

        # --- FILTRO 2: Remover Unidades Específicas e Vazias ---
        df = df[~df['Unidades'].isin(['', 'nan', 'None'])]
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME"]
        df = df[~df['Unidades'].isin(unidades_bloqueadas)]

        # --- FILTRO 3: Ignorar Funcionários e Prestadores ---
        tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
        df = df[~df['Tipo'].isin(tipos_para_ignorar)]

        # --- FILTRO 4: Apenas Acessos Autorizados ---
        df = df[df['Situação'].str.contains('autorizada', case=False)].copy()

        # 2. Tratamento de Tempo e Ordenação
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        df_mov = df.sort_values(by='Timestamp', ascending=False)

        # 3. Lógica de Ocupação Atual (Pessoas que entraram e não saíram)
        ultimo_evento_pessoa = df_mov.drop_duplicates(subset=['Unidades', 'Pessoa'], keep='first')
        unidades_com_alguem = ultimo_evento_pessoa[ultimo_evento_pessoa['Situação'] == 'Entrada autorizada']['Unidades'].unique()

        # 4. Dados para a Tabela (Último registro de cada unidade)
        ultimo_registro_unidade = df_mov.drop_duplicates(subset='Unidades', keep='first').copy()

        # Define Situação atual baseada na presença real
        ultimo_registro_unidade['Situação Atual'] = ultimo_registro_unidade['Unidades'].apply(
            lambda x: "🔴 Ocupada" if x in unidades_com_alguem else "🟢 Livre"
        )

        # 5. Organização Final
        relatorio = ultimo_registro_unidade[['Unidades', 'Situação Atual', 'Tipo', 'Pessoa', 'Hora']].rename(
            columns={
                'Unidades': 'Unidade',
                'Tipo': 'Tipo Ocupante',
                'Pessoa': 'Último Acesso',
                'Hora': 'Horário'
            }
        )

        # --- EXIBIÇÃO NO BROWSER ---
        ocupadas_df = relatorio[relatorio['Situação Atual'] == "🔴 Ocupada"]
        qtd_ocupadas = len(ocupadas_df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Unidades com Morador/Vis", len(relatorio))
        col2.metric("Ocupadas Agora", qtd_ocupadas)
        col3.metric("Livre / Saíram", len(relatorio) - qtd_ocupadas)

        st.divider()

        # Contagem por Categoria (Unidades Ocupadas)
        st.subheader("🏢 Unidades Ocupadas por Categoria")
        if qtd_ocupadas > 0:
            contagem_tipo = ocupadas_df['Tipo Ocupante'].value_counts()
            cols_tipo = st.columns(max(len(contagem_tipo), 2))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)
        else:
            st.info("Nenhuma unidade ocupada no momento.")

        st.divider()

        # Tabela Detalhada (Sempre preenchida)
        st.subheader("📋 Relatório de Movimentação Recente")
        st.dataframe(relatorio.sort_values('Unidade'), use_container_width=True, hide_index=True)

        # Exportação
        csv = relatorio.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Planilha Atualizada", csv, "relatorio_final.csv", "text/csv")

    except Exception as e:
        st.error(f"Ocorreu um erro no processamento: {e}")
else:
    st.info("Aguardando upload do CSV...")