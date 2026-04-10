import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Relatório de Auditoria e Zonas", layout="wide")

st.title("📊 Painel de Movimentação e Auditoria Detalhada")
st.markdown("""
**Atualização de Auditoria:**
1. **Relatório de Inconsistências:** Agora inclui a coluna **ZONA** para identificar a origem da abertura.
2. **Segregação:** Inconsistências permanecem separadas da contagem de unidades validadas.
""")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()

        # --- FILTROS OBRIGATÓRIOS (Nome e Unidade) ---
        df = df[~df['Pessoa'].isin(['', 'nan', 'None', 'N/A'])]
        df = df[~df['Unidades'].isin(['', 'nan', 'None', 'N/A'])]
        
        # --- FILTROS DE CATEGORIA E UNIDADES BLOQUEADAS ---
        tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
        df = df[~df['Tipo'].isin(tipos_para_ignorar)]
        
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME"]
        df = df[~df['Unidades'].isin(unidades_bloqueadas)]

        # --- FILTRO DE SITUAÇÃO (Apenas Autorizados) ---
        df = df[df['Situação'].str.contains('autorizada', case=False)].copy()

        # 2. SEGREGAÇÃO DE DADOS (Inconsistências vs Normal)
        if 'Tipo de abertura' in df.columns:
            mask_inconsistente = df['Tipo de abertura'].str.contains('Abertura Remota', case=False, na=False)
            df_inconsistentes = df[mask_inconsistente].copy()
            df_normal = df[~mask_inconsistente].copy()
        else:
            df_inconsistentes = pd.DataFrame(columns=df.columns)
            df_normal = df.copy()

        # 3. PROCESSAMENTO - RELATÓRIO NORMAL (Último movimento por unidade)
        df_normal['Timestamp'] = pd.to_datetime(df_normal['Data'] + ' ' + df_normal['Hora'], dayfirst=True)
        relatorio_normal = df_normal.sort_values(by='Timestamp', ascending=False).drop_duplicates(subset='Unidades', keep='first')

        # 4. PROCESSAMENTO - RELATÓRIO INCONSISTENTE
        df_inconsistentes['Timestamp'] = pd.to_datetime(df_inconsistentes['Data'] + ' ' + df_inconsistentes['Hora'], dayfirst=True)
        relatorio_inconsistente = df_inconsistentes.sort_values(by='Timestamp', ascending=False)

        # --- INTERFACE: MÉTRICAS ---
        c1, c2 = st.columns(2)
        c1.metric("Unidades com Movimentação Única (Normal)", len(relatorio_normal))
        c2.metric("Total de Entradas Inconsistentes", len(relatorio_inconsistente))

        st.divider()

        # --- SEÇÃO 1: UNIDADES NORMAIS ---
        st.subheader("🏠 Movimentações Únicas Validadas")
        if len(relatorio_normal) > 0:
            contagem_tipo = relatorio_normal['Tipo'].value_counts()
            cols_t = st.columns(max(len(contagem_tipo), 2))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_t[i].metric(f"Unid. com {tipo}", total)
            
            # Tabela Normal
            st.dataframe(
                relatorio_normal[['Unidades', 'Tipo', 'Pessoa', 'Data', 'Hora']].rename(
                    columns={'Unidades': 'Unidade', 'Tipo': 'Categoria', 'Pessoa': 'Nome'}
                ).sort_values('Unidade'),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Nenhuma movimentação normal encontrada.")

        st.divider()

        # --- SEÇÃO 2: INCONSISTÊNCIAS (Auditoria com ZONA) ---
        st.subheader("⚠️ Relatório de Entradas Inconsistentes (Auditoria de Zonas)")
        if len(relatorio_inconsistente) > 0:
            st.warning(f"Atenção: {len(relatorio_inconsistente)} registros de abertura remota encontrados.")
            
            # Definindo colunas para exibir na auditoria
            cols_auditoria = ['Unidades', 'Pessoa', 'Data', 'Hora', 'Tipo de abertura']
            if 'ZONA' in relatorio_inconsistente.columns:
                cols_auditoria.append('ZONA')
            
            # Tabela Inconsistente
            st.dataframe(
                relatorio_inconsistente[cols_auditoria].rename(
                    columns={'Unidades': 'Unidade', 'Pessoa': 'Nome'}
                ),
                use_container_width=True, hide_index=True
            )
            
            # Download específico
            csv_inc = relatorio_inconsistente.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Relatório de Auditoria (CSV)", csv_inc, "auditoria_zonas.csv", "text/csv")
        else:
            st.success("Nenhuma inconsistência de abertura remota detectada.")

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
else:
    st.info("Aguardando upload do CSV para auditoria de zonas.")