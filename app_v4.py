import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Relatório de Movimentação Única", layout="wide")

st.title("📊 Relatório de Movimentação por Unidade")
st.markdown("""
**Lógica Atualizada:**
1. Contagem **Única** de unidades que registraram qualquer movimentação autorizada.
2. Exclusão de Funcionários, Prestadores, Registros Negados e Unidades Administrativas/Vazias.
3. A categoria da unidade é definida pela última pessoa (Morador ou Visitante) que interagiu com ela.
""")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        for col in ['Unidades', 'Tipo', 'Situação', 'Pessoa']:
            df[col] = df[col].astype(str).str.strip()
        
        # --- FILTROS DE HIGIENE DOS DADOS ---
        # Remover se Tipo estiver vazio
        df = df[~df['Tipo'].isin(['', 'nan', 'None', 'N/A'])]
        
        # Remover Unidades Vazias ou Específicas
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME", "nan", ""]
        df = df[~df['Unidades'].isin(unidades_bloqueadas)]

        # Ignorar Funcionários e Prestadores
        tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
        df = df[~df['Tipo'].isin(tipos_para_ignorar)]

        # Manter apenas Acessos Autorizados
        df = df[df['Situação'].str.contains('autorizada', case=False)].copy()

        # 2. Tratamento de Tempo
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        df_mov = df.sort_values(by='Timestamp', ascending=False)

        # 3. LÓGICA DE CONTAGEM ÚNICA
        # Pegamos apenas o registro mais recente de cada unidade para definir a categoria dela
        relatorio_consolidado = df_mov.drop_duplicates(subset='Unidades', keep='first').copy()

        # 4. Organização da Tabela Final
        relatorio = relatorio_consolidado[['Unidades', 'Tipo', 'Pessoa', 'Data', 'Hora']].rename(
            columns={
                'Unidades': 'Unidade',
                'Tipo': 'Tipo de Categoria',
                'Pessoa': 'Último Acesso',
                'Data': 'Data',
                'Hora': 'Horário'
            }
        )

        # --- EXIBIÇÃO NO BROWSER ---

        # Métrica Principal: Total de Unidades com Movimentação
        total_unidades_mov = len(relatorio)
        st.metric("Total de Unidades com Movimentação Única", total_unidades_mov)

        st.divider()

        # CONTAGEM POR CATEGORIA (Baseada no Total Único)
        st.subheader("🏢 Unidades por Categoria (Movimentação Total)")
        if total_unidades_mov > 0:
            contagem_tipo = relatorio['Tipo de Categoria'].value_counts()
            cols_tipo = st.columns(max(len(contagem_tipo), 2))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)
        else:
            st.info("Nenhuma movimentação registrada para os filtros selecionados.")

        st.divider()

        # Tabela Detalhada
        st.subheader("📋 Detalhamento da Última Movimentação")
        st.dataframe(relatorio.sort_values('Unidade'), use_container_width=True, hide_index=True)

        # Exportação
        csv = relatorio.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório de Movimentação", csv, "relatorio_movimentacao.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
else:
    st.info("Aguardando upload do CSV.")