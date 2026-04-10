import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Gestão de Acessos e Auditoria", layout="wide")

st.title("📊 Painel de Movimentação e Auditoria")
st.markdown("Ferramenta configurada para análise de Moradores e Visitantes com auditoria de Aberturas Remotas.")

uploaded_file = st.file_uploader("Carregue a planilha CSV externa", type="csv")

if uploaded_file is not None:
    try:
        # 1. Leitura e Padronização de Colunas
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper() # Tudo para MAIÚSCULO para evitar erros
        
        # Limpeza de espaços nos dados
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()

        # --- VERIFICAÇÃO DE COLUNAS VITAIS ---
        if 'PESSOA' not in df.columns or 'UNIDADES' not in df.columns:
            st.error("Erro: Colunas 'PESSOA' ou 'UNIDADES' não encontradas no CSV.")
            st.stop()

        # --- FILTROS DE INTEGRIDADE E REGRAS DE NEGÓCIO ---
        # 1. Remove registros sem Nome ou Unidade
        df = df[~df['PESSOA'].isin(['', 'nan', 'None', 'N/A'])]
        df = df[~df['UNIDADES'].isin(['', 'nan', 'None', 'N/A'])]
        
        # 2. Ignora Tipos específicos
        if 'TIPO' in df.columns:
            df = df[~df['TIPO'].isin(['Funcionário', 'Prestador de serviço'])]
        
        # 3. Remove Unidades Administrativas
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME"]
        df = df[~df['UNIDADES'].isin(unidades_bloqueadas)]

        # 4. Apenas Acessos Autorizados
        if 'SITUAÇÃO' in df.columns:
            df = df[df['SITUAÇÃO'].str.contains('autorizada', case=False)].copy()

        # --- SEGREGAÇÃO DE INCONSISTÊNCIAS (ABERTURA REMOTA) ---
        possiveis_nomes_abertura = ['TIPO DE ABERTURA', 'TIPO ABERTURA', 'ABERTURA']
        col_abertura_encontrada = next((c for c in possiveis_nomes_abertura if c in df.columns), None)

        if col_abertura_encontrada:
            mask_inconsistente = df[col_abertura_encontrada].str.contains('Abertura Remota', case=False, na=False)
            df_inconsistentes = df[mask_inconsistente].copy()
            df_normal = df[~mask_inconsistente].copy()
        else:
            df_inconsistentes = pd.DataFrame(columns=df.columns)
            df_normal = df.copy()

        # --- PROCESSAMENTO CRONOLÓGICO ---
        if 'DATA' in df.columns and 'HORA' in df.columns:
            df_normal['Timestamp'] = pd.to_datetime(df_normal['DATA'] + ' ' + df_normal['HORA'], dayfirst=True)
            relatorio_normal = df_normal.sort_values(by='Timestamp', ascending=False).drop_duplicates(subset='UNIDADES', keep='first')
            
            df_inconsistentes['Timestamp'] = pd.to_datetime(df_inconsistentes['DATA'] + ' ' + df_inconsistentes['HORA'], dayfirst=True)
            relatorio_inconsistente = df_inconsistentes.sort_values(by='Timestamp', ascending=False)
        else:
            st.error("Erro: Colunas de DATA e HORA não encontradas.")
            st.stop()

        # --- EXIBIÇÃO DE RESULTADOS ---
        c1, c2 = st.columns(2)
        c1.metric("Unidades com Movimentação Normal", len(relatorio_normal))
        c2.metric("Total de Entradas Inconsistentes", len(relatorio_inconsistente))

        st.divider()

        # SEÇÃO 1: MOVIMENTAÇÃO NORMAL
        st.subheader("🏠 Movimentações Únicas Validadas (Morador/Visitante)")
        if len(relatorio_normal) > 0:
            if 'TIPO' in relatorio_normal.columns:
                contagem_tipo = relatorio_normal['TIPO'].value_counts()
                cols_t = st.columns(max(len(contagem_tipo), 2))
                for i, (tipo, total) in enumerate(contagem_tipo.items()):
                    cols_t[i].metric(f"Unid. com {tipo}", total)
            
            st.dataframe(
                relatorio_normal[['UNIDADES', 'TIPO', 'PESSOA', 'DATA', 'HORA']].rename(
                    columns={'UNIDADES': 'Unidade', 'TIPO': 'Categoria', 'PESSOA': 'Nome'}
                ).sort_values('Unidade'),
                use_container_width=True, hide_index=True
            )

        st.divider()

        # SEÇÃO 2: INCONSISTÊNCIAS (AUDITORIA)
        st.subheader("⚠️ Auditoria de Entradas Inconsistentes")
        if not col_abertura_encontrada:
            st.info("ℹ️ Auditoria desativada: Coluna de 'Tipo de abertura' não detectada no arquivo.")
        elif len(relatorio_inconsistente) > 0:
            st.warning(f"Foram encontradas {len(relatorio_inconsistente)} aberturas remotas.")
            
            cols_auditoria = ['UNIDADES', 'PESSOA', 'DATA', 'HORA', col_abertura_encontrada]
            if 'ZONA' in relatorio_inconsistente.columns:
                cols_auditoria.append('ZONA')
            
            st.dataframe(
                relatorio_inconsistente[cols_auditoria].rename(
                    columns={'UNIDADES': 'Unidade', 'PESSOA': 'Nome', col_abertura_encontrada: 'Tipo de Acesso'}
                ),
                use_container_width=True, hide_index=True
            )
            
            csv_inc = relatorio_inconsistente.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Relatório de Inconsistências", csv_inc, "auditoria_remota.csv", "text/csv")
        else:
            st.success("Nenhuma abertura remota detectada no arquivo carregado.")

    except Exception as e:
        st.error(f"Erro inesperado ao processar os dados: {e}")
else:
    st.info("Aguardando upload do arquivo CSV para iniciar.")
