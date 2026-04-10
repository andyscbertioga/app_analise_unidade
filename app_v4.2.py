import streamlit as st
import pandas as pd

# 1. Configuração da página e CSS para Impressão
st.set_page_config(page_title="Relatório de Acessos - Impressão", layout="wide")

# CSS para esconder elementos desnecessários na hora de imprimir
st.markdown("""
    <style>
    @media print {
        /* Esconde botões, cabeçalho e menus do Streamlit */
        header, [data-testid="stSidebar"], .stButton, [data-testid="stFileUploader"], .stDownloadButton, footer {
            display: none !important;
        }
        /* Ajusta o container principal para usar todo o papel */
        .main .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Painel de Movimentação e Auditoria")

# Botão de Impressão
if st.button("🖨️ Abrir Opções de Impressão"):
    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Padronização
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()
        
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()

        # --- FILTROS DE INTEGRIDADE ---
        if 'PESSOA' not in df.columns or 'UNIDADES' not in df.columns:
            st.error("Erro: Colunas 'PESSOA' ou 'UNIDADES' não encontradas no arquivo.")
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
        if 'DATA' in df.columns and 'HORA' in df.columns:
            df_normal['Timestamp'] = pd.to_datetime(df_normal['DATA'] + ' ' + df_normal['HORA'], dayfirst=True)
            relatorio_normal = df_normal.sort_values(by='Timestamp', ascending=False).drop_duplicates(subset='UNIDADES', keep='first')
            
            df_inconsistentes['Timestamp'] = pd.to_datetime(df_inconsistentes['DATA'] + ' ' + df_inconsistentes['HORA'], dayfirst=True)
            relatorio_inconsistente = df_inconsistentes.sort_values(by='Timestamp', ascending=False)
        else:
            st.error("Erro: Colunas DATA e HORA não encontradas.")
            st.stop()

        # --- EXIBIÇÃO ---
        st.write(f"**Relatório gerado em:** {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
        
        c1, c2 = st.columns(2)
        c1.metric("Unidades com Movimentação Única", len(relatorio_normal))
        c2.metric("Total de Entradas Inconsistentes", len(relatorio_inconsistente))

        st.divider()

        # SEÇÃO 1: NORMAL
        st.subheader("🏠 Movimentações Únicas Validadas")
        if len(relatorio_normal) > 0:
            # Usamos st.table para garantir que tudo apareça impresso sem barras de rolagem
            df_normal_view = relatorio_normal[['UNIDADES', 'TIPO', 'PESSOA', 'DATA', 'HORA']].rename(
                columns={'UNIDADES': 'Unidade', 'TIPO': 'Categoria', 'PESSOA': 'Nome'}
            ).sort_values('Unidade')
            st.table(df_normal_view)

        st.divider()

        # SEÇÃO 2: INCONSISTÊNCIAS
        st.subheader("⚠️ Relatório de Entradas Inconsistentes")
        if len(relatorio_inconsistente) > 0:
            cols_auditoria = ['UNIDADES', 'PESSOA', 'DATA', 'HORA']
            if col_abertura_encontrada: cols_auditoria.append(col_abertura_encontrada)
            if 'ZONA' in relatorio_inconsistente.columns: cols_auditoria.append('ZONA')
            
            df_inc_view = relatorio_inconsistente[cols_auditoria].rename(
                columns={'UNIDADES': 'Unidade', 'PESSOA': 'Nome'}
            )
            st.table(df_inc_view)
        else:
            st.success("Nenhuma abertura remota detectada.")

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
else:
    st.info("Aguardando upload do CSV para gerar relatórios e opção de impressão.")
