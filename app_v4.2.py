import streamlit as st
import pandas as pd

# 1. Configuração da página e CSS para Impressão
st.set_page_config(page_title="Relatório de Acessos - Impressão", layout="wide")

# CSS para esconder elementos do Streamlit na hora de imprimir
st.markdown("""
    <style>
    @media print {
        /* Esconde botões, header e menus do Streamlit */
        header, [data-testid="stSidebar"], .stButton, [data-testid="stFileUploader"], .stDownloadButton {
            display: none !important;
        }
        /* Ajusta o layout para ocupar a página inteira */
        .main .block-container {
            padding: 0 !important;
            margin: 0 !important;
        }
    }
    </style>
""", unsafe_allow_stdio=True)

st.title("📊 Painel de Movimentação e Auditoria")

# Botão de Impressão nativo do browser
if st.button("🖨️ Imprimir Relatórios"):
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()

        # --- FILTROS DE INTEGRIDADE ---
        if 'PESSOA' not in df.columns or 'UNIDADES' not in df.columns:
            st.error("Erro: Colunas 'PESSOA' ou 'UNIDADES' não encontradas.")
            st.stop()

        df = df[~df['PESSOA'].isin(['', 'nan', 'None', 'N/A'])]
        df = df[~df['UNIDADES'].isin(['', 'nan', 'None', 'N/A'])]
        
        if 'TIPO' in df.columns:
            df = df[~df['TIPO'].isin(['Funcionário', 'Prestador de serviço'])]
        
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME"]
        df = df[~df['UNIDADES'].isin(unidades_bloqueadas)]

        if 'SITUAÇÃO' in df.columns:
            df = df[df['SITUAÇÃO'].str.contains('autorizada', case=False)].copy()

        # --- SEGREGAÇÃO DE INCONSISTÊNCIAS ---
        possiveis_nomes_abertura = ['TIPO DE ABERTURA', 'TIPO ABERTURA', 'ABERTURA']
        col_abertura_encontrada = next((c for c in possiveis_nomes_abertura if c in df.columns), None)

        if col_abertura_encontrada:
            mask_inconsistente = df[col_abertura_encontrada].str.contains('Abertura Remota', case=False, na=False)
            df_inconsistentes = df[mask_inconsistente].copy()
            df_normal = df[~mask_inconsistente].copy()
        else:
            df_inconsistentes = pd.DataFrame(columns=df.columns)
            df_normal = df.copy()

        # --- PROCESSAMENTO ---
        df_normal['Timestamp'] = pd.to_datetime(df_normal['DATA'] + ' ' + df_normal['HORA'], dayfirst=True)
        relatorio_normal = df_normal.sort_values(by='Timestamp', ascending=False).drop_duplicates(subset='UNIDADES', keep='first')
        
        df_inconsistentes['Timestamp'] = pd.to_datetime(df_inconsistentes['DATA'] + ' ' + df_inconsistentes['HORA'], dayfirst=True)
        relatorio_inconsistente = df_inconsistentes.sort_values(by='Timestamp', ascending=False)

        # --- EXIBIÇÃO ---
        st.write(f"**Data do Relatório:** {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
        
        c1, c2 = st.columns(2)
        c1.metric("Unidades com Movimentação Normal", len(relatorio_normal))
        c2.metric("Total de Entradas Inconsistentes", len(relatorio_inconsistente))

        st.divider()

        # SEÇÃO 1: NORMAL
        st.subheader("🏠 Movimentações Únicas Validadas")
        if len(relatorio_normal) > 0:
            # Usamos st.table para impressão pois o st.dataframe cria barras de rolagem que cortam no papel
            st.table(relatorio_normal[['UNIDADES', 'TIPO', 'PESSOA', 'DATA', 'HORA']].rename(
                columns={'UNIDADES': 'Unidade', 'TIPO': 'Categoria', 'PESSOA': 'Nome'}
            ).sort_values('Unidade'))

        st.divider()

        # SEÇÃO 2: INCONSISTÊNCIAS
        st.subheader("⚠️ Auditoria de Entradas Inconsistentes")
        if len(relatorio_inconsistente) > 0:
            cols_auditoria = ['UNIDADES', 'PESSOA', 'DATA', 'HORA', col_abertura_encontrada]
            if 'ZONA' in relatorio_inconsistente.columns:
                cols_auditoria.append('ZONA')
            
            st.table(relatorio_inconsistente[cols_auditoria].rename(
                columns={'UNIDADES': 'Unidade', 'PESSOA': 'Nome', col_abertura_encontrada: 'Tipo de Acesso'}
            ))
        else:
            st.write("Nenhuma inconsistência detectada.")

    except Exception as e:
        st.error(f"Erro: {e}")
