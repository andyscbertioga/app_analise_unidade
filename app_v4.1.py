import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Relatório de Movimentação e Integridade", layout="wide")

st.title("📊 Painel de Movimentação e Auditoria")
st.markdown("""
**Regras de Filtragem e Auditoria:**
1. **Campos Obrigatórios:** Ignora registros sem Nome ou Unidade.
2. **Entradas Inconsistentes:** Detecta e conta aberturas do tipo 'Abertura Remota'.
3. **Público-Alvo:** Foco em Moradores e Visitantes (Ignora Funcionários/Prestadores).
4. **Unidades Excluídas:** Remove Beach House e Administração.
""")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza de Espaços
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        # Garantir que as colunas essenciais existam como string
        cols_limpeza = ['Unidades', 'Tipo', 'Situação', 'Pessoa']
        if 'Tipo de abertura' in df.columns:
            cols_limpeza.append('Tipo de abertura')
        
        for col in [c for c in cols_limpeza if c in df.columns]:
            df[col] = df[col].astype(str).str.strip()
        
        # --- FILTRO 1: Campos Obrigatórios (Nome e Unidade) ---
        # Remove se Pessoa ou Unidades forem vazios ou "nan"
        df = df[~df['Pessoa'].isin(['', 'nan', 'None'])]
        df = df[~df['Unidades'].isin(['', 'nan', 'None'])]
        df = df.dropna(subset=['Pessoa', 'Unidades'])

        # --- FILTRO 2: Unidades e Tipos Bloqueados ---
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME"]
        df = df[~df['Unidades'].isin(unidades_bloqueadas)]
        
        tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
        df = df[~df['Tipo'].isin(tipos_para_ignorar)]

        # --- FILTRO 3: Apenas Autorizados ---
        df = df[df['Situação'].str.contains('autorizada', case=False)].copy()

        # 2. Identificação de Inconsistências (Abertura Remota)
        df['Status Movimentação'] = "Normal"
        if 'Tipo de abertura' in df.columns:
            inconsistentes_mask = df['Tipo de abertura'].str.contains('Abertura Remota', case=False, na=False)
            df.loc[inconsistentes_mask, 'Status Movimentação'] = "⚠️ Entrada Inconsistente"
        
        # 3. Tratamento de Tempo
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        df_mov = df.sort_values(by='Timestamp', ascending=False)

        # 4. Consolidação Única por Unidade
        relatorio = df_mov.drop_duplicates(subset='Unidades', keep='first').copy()

        # --- EXIBIÇÃO NO BROWSER ---

        # Métricas de Topo
        total_unidades = len(relatorio)
        
        # Contagem de inconsistências (no dataset filtrado total)
        total_inconsistentes = 0
        if 'Tipo de abertura' in df.columns:
            total_inconsistentes = df[df['Status Movimentação'] == "⚠️ Entrada Inconsistente"].shape[0]

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Unidades com Movimentação Única", total_unidades)
        col_m2.metric("Entradas Inconsistentes (Total no Período)", total_inconsistentes, delta_color="inverse")

        st.divider()

        # Contagem por Categoria
        st.subheader("🏢 Unidades por Categoria")
        if total_unidades > 0:
            contagem_tipo = relatorio['Tipo'].value_counts()
            cols_tipo = st.columns(max(len(contagem_tipo), 2))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)
        else:
            st.info("Nenhuma movimentação válida encontrada.")

        st.divider()

        # Tabela Detalhada
        st.subheader("📋 Relatório Detalhado de Última Movimentação")
        
        # Organização das colunas para visualização
        colunas_exibir = ['Unidades', 'Status Movimentação', 'Tipo', 'Pessoa', 'Data', 'Hora']
        # Verifica se 'Tipo de abertura' existe para mostrar na tabela se quiser, 
        # mas 'Status Movimentação' já resume.
        
        resultado_view = relatorio[colunas_exibir].rename(columns={
            'Unidades': 'Unidade',
            'Tipo': 'Tipo de Ocupante',
            'Pessoa': 'Nome'
        })

        # Estilização para destacar inconsistências
        st.dataframe(
            resultado_view.sort_values('Unidade'), 
            use_container_width=True, 
            hide_index=True
        )

        # Exportação
        csv = resultado_view.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório de Auditoria", csv, "auditoria_movimentacao.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
else:
    st.info("Aguardando upload do CSV para análise.")