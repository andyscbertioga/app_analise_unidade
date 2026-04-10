import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Auditoria de Movimentação Única", layout="wide")

st.title("📊 Painel de Movimentação e Auditoria de Acessos")
st.markdown("""
**Filtros de Integridade aplicados:**
1. **Obrigatórios:** Remove registros sem Nome (Pessoa) ou sem Unidade.
2. **Exclusões:** Ignora 'Funcionário', 'Prestador de serviço', 'BEACH HOUSE RESTAURANTE' e 'ADM ADM, ADMINISTRAÇÃO ALLTIME'.
3. **Inconsistências:** Conta e identifica 'Abertura Remota' na coluna 'Tipo de abertura'.
""")

uploaded_file = st.file_uploader("Carregue a planilha CSV atualizada", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza Geral
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        # Converte colunas para string e remove espaços
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        
        # --- REGRA 1: Ignorar se não houver Nome (Pessoa) ou Unidade ---
        # Filtramos 'nan', campos vazios ou nulos
        df = df[~df['Pessoa'].isin(['', 'nan', 'None', 'N/A'])]
        df = df[~df['Unidades'].isin(['', 'nan', 'None', 'N/A'])]

        # --- REGRA 2: Filtros de Categoria e Unidades Específicas ---
        tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
        df = df[~df['Tipo'].isin(tipos_para_ignorar)]
        
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME"]
        df = df[~df['Unidades'].isin(unidades_bloqueadas)]

        # --- REGRA 3: Apenas Acessos Autorizados ---
        df = df[df['Situação'].str.contains('autorizada', case=False)].copy()

        # 2. Identificação de ENTRADAS INCONSISTENTES (Abertura Remota)
        # Verificamos se a coluna existe antes de processar
        col_abertura = 'Tipo de abertura'
        df['Inconsistência'] = "Normal"
        
        if col_abertura in df.columns:
            # Marca como inconsistente se for Abertura Remota
            mascara_inconsistente = df[col_abertura].str.contains('Abertura Remota', case=False, na=False)
            df.loc[mascara_inconsistente, 'Inconsistência'] = "⚠️ Entrada Inconsistente"
        
        # 3. Tratamento de Tempo e Consolidação Única
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        df_mov = df.sort_values(by='Timestamp', ascending=False)
        
        # Pegamos o registro mais recente de cada unidade para o relatório
        relatorio_unico = df_mov.drop_duplicates(subset='Unidades', keep='first').copy()

        # --- EXIBIÇÃO ---

        # Métricas de Auditoria
        total_unidades_validas = len(relatorio_unico)
        
        # Contagem de inconsistências (Total de vezes que ocorreu no arquivo filtrado)
        total_inconsistentes = 0
        if col_abertura in df.columns:
            total_inconsistentes = df[df['Inconsistência'] == "⚠️ Entrada Inconsistente"].shape[0]

        c1, c2 = st.columns(2)
        c1.metric("Total de Unidades com Movimentação", total_unidades_validas)
        c2.metric("Total de Entradas Inconsistentes", total_inconsistentes)

        st.divider()

        # Contagem por Categoria (Unidades Únicas)
        st.subheader("🏢 Unidades Únicas por Categoria")
        if total_unidades_validas > 0:
            contagem_tipo = relatorio_unico['Tipo'].value_counts()
            cols_tipo = st.columns(max(len(contagem_tipo), 2))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)
        else:
            st.info("Nenhuma movimentação válida nos critérios selecionados.")

        st.divider()

        # Tabela Detalhada
        st.subheader("📋 Relatório Consolidado (Último Acesso)")
        
        # Seleção de colunas para a tabela final
        colunas_final = ['Unidades', 'Inconsistência', 'Tipo', 'Pessoa', 'Data', 'Hora']
        if col_abertura in relatorio_unico.columns:
            colunas_final.append(col_abertura)

        df_view = relatorio_unico[colunas_final].rename(columns={
            'Unidades': 'Unidade',
            'Tipo': 'Categoria',
            'Pessoa': 'Nome'
        })

        st.dataframe(df_view.sort_values('Unidade'), use_container_width=True, hide_index=True)

        # Download
        csv = df_view.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório de Auditoria", csv, "auditoria_acessos.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro ao processar: {e}. Verifique se as colunas estão corretas no CSV.")
else:
    st.info("Aguardando upload do arquivo CSV para auditoria.")