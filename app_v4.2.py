import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Auditoria de Movimentação Única", layout="wide")

st.title("📊 Painel de Movimentação e Auditoria de Acessos")
st.markdown("""
**Blindagem de Dados:**
1. Se a coluna **'Tipo de abertura'** não existir na planilha, o sistema ignorará a auditoria de aberturas remotas sem travar.
2. Registros sem **Nome** ou **Unidade** são descartados automaticamente.
""")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        # Limpeza de strings em todas as colunas existentes
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        
        # --- REGRA 1: Filtro de Campos Obrigatórios ---
        # Garantimos que existam as colunas 'Pessoa' e 'Unidades' antes de filtrar
        if 'Pessoa' in df.columns and 'Unidades' in df.columns:
            df = df[~df['Pessoa'].isin(['', 'nan', 'None', 'N/A'])]
            df = df[~df['Unidades'].isin(['', 'nan', 'None', 'N/A'])]
        else:
            st.error("Erro: As colunas 'Pessoa' ou 'Unidades' não foram encontradas no arquivo.")
            st.stop()

        # --- REGRA 2: Filtros de Categoria e Unidades Específicas ---
        if 'Tipo' in df.columns:
            tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
            df = df[~df['Tipo'].isin(tipos_para_ignorar)]
        
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME"]
        df = df[~df['Unidades'].isin(unidades_bloqueadas)]

        # --- REGRA 3: Apenas Acessos Autorizados ---
        if 'Situação' in df.columns:
            df = df[df['Situação'].str.contains('autorizada', case=False)].copy()

        # 2. Identificação de ENTRADAS INCONSISTENTES (Proteção contra KeyError)
        df['Status Movimentação'] = "Normal"
        total_inconsistentes = 0
        
        # SÓ executa a lógica se a coluna existir no CSV carregado
        if 'Tipo de abertura' in df.columns:
            mascara_inconsistente = df['Tipo de abertura'].str.contains('Abertura Remota', case=False, na=False)
            df.loc[mascara_inconsistente, 'Status Movimentação'] = "⚠️ Entrada Inconsistente"
            total_inconsistentes = df[df['Status Movimentação'] == "⚠️ Entrada Inconsistente"].shape[0]
        
        # 3. Tratamento de Tempo e Consolidação Única
        if 'Data' in df.columns and 'Hora' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
            df_mov = df.sort_values(by='Timestamp', ascending=False)
            # Registro mais recente de cada unidade
            relatorio_unico = df_mov.drop_duplicates(subset='Unidades', keep='first').copy()
        else:
            st.error("Erro: Colunas de Data/Hora não encontradas.")
            st.stop()

        # --- EXIBIÇÃO ---
        total_unidades_validas = len(relatorio_unico)

        c1, c2 = st.columns(2)
        c1.metric("Unidades com Movimentação Única", total_unidades_validas)
        c2.metric("Entradas Inconsistentes (Abertura Remota)", total_inconsistentes)

        st.divider()

        # Contagem por Categoria
        st.subheader("🏢 Unidades Únicas por Categoria")
        if total_unidades_validas > 0 and 'Tipo' in relatorio_unico.columns:
            contagem_tipo = relatorio_unico['Tipo'].value_counts()
            cols_tipo = st.columns(max(len(contagem_tipo), 2))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)

        st.divider()

        # Tabela Detalhada
        st.subheader("📋 Relatório Consolidado")
        
        # Definindo colunas que vamos mostrar (apenas se existirem)
        cols_view = ['Unidades', 'Status Movimentação', 'Tipo', 'Pessoa', 'Data', 'Hora']
        existentes = [c for c in cols_view if c in relatorio_unico.columns]
        
        df_view = relatorio_unico[existentes].rename(columns={
            'Unidades': 'Unidade',
            'Tipo': 'Categoria',
            'Pessoa': 'Nome'
        })

        st.dataframe(df_view.sort_values('Unidade'), use_container_width=True, hide_index=True)

        # Download
        csv = df_view.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório", csv, "auditoria_acessos.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro inesperado: {e}")
else:
    st.info("Aguardando upload do arquivo CSV.")