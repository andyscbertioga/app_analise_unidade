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
        
        # Contagem