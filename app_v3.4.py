import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Monitor de Ocupação - Filtro Personalizado", layout="wide")

st.title("📊 Painel de Ocupação Filtrado")
st.markdown("""
**Filtros aplicados nesta versão:**
1. Ignora as unidades: **BEACH HOUSE RESTAURANTE** e **ADM ADM, ADMINISTRAÇÃO ALLTIME**.
2. Ignora unidades sem nome/vazias.
3. Foco exclusivo em **Moradores e Visitantes** com acesso **Autorizado**.
""")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza Inicial
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        # Converte para string e remove espaços em branco das bordas
        for col in ['Unidades', 'Tipo', 'Situação']:
            df[col] = df[col].astype(str).str.strip()
        
        # --- FILTRO 1: Remover Unidades Vazias ou "nan" ---
        df = df[df['Unidades'].notna()]
        df = df[~df['Unidades'].isin(['', 'nan', 'None'])]

        # --- FILTRO 2: Remover Unidades Específicas ---
        unidades_bloqueadas = [
            "BEACH HOUSE RESTAURANTE", 
            "ADM ADM, ADMINISTRAÇÃO ALLTIME"
        ]
        df = df[~df['Unidades'].isin(unidades_bloqueadas)].copy()

        # --- FILTRO 3: Ignorar Funcionários e Prestadores ---
        tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
        df = df[~df['Tipo'].isin(tipos_para_ignorar)].copy()

        # --- FILTRO 4: Manter apenas Acessos Autorizados ---
        df = df[df['Situação'].str.contains('autorizada', case=False)].copy()

        # 2. Tratamento de Tempo
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        
        # 3. Lista de Unidades Únicas Restantes
        todas_unidades = pd.DataFrame({'Unidade': df['Unidades'].unique()})

        # 4. Determinar estado atual (Mais recente primeiro)
        df_mov = df.sort_values(by='Timestamp', ascending=False)
        ultimo_evento_pessoa = df_mov.drop_duplicates(subset=['Unidades', 'Pessoa'], keep='first')
        
        # Unidades ocupadas (pessoas que entraram e não saíram)
        pessoas_dentro = ultimo_evento_pessoa[ultimo_evento_pessoa['Situação'] == 'Entrada autorizada'].copy()
        
        # Consolidação por Unidade (Contagem única de unidades)
        unidades_ocupadas = pessoas_dentro.sort_values('Timestamp', ascending=False).drop_duplicates('Unidades')
        
        # 5. Cruzamento Final (Merge)
        relatorio = pd.merge(todas_unidades, unidades_ocupadas, left_on='Unidade', right_on='Unidades', how='left')
        
        relatorio['Situação Atual'] = relatorio['Situação'].apply(
            lambda x: "🔴 Ocupada" if x == "Entrada autorizada" else "🟢 Livre"
        )
        
        relatorio = relatorio[['Unidade', 'Situação Atual', 'Tipo', 'Pessoa', 'Hora']].rename(
            columns={'Tipo': 'Tipo Ocupante', 'Pessoa': 'Último Acesso', 'Hora': 'Horário'}
        )
        relatorio = relatorio.fillna("-")

        # --- EXIBIÇÃO ---

        # Métricas
        ocupadas_df = relatorio[relatorio['Situação Atual'] == "🔴 Ocupada"]
        qtd_ocupadas = len(ocupadas_df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Unidades Monitoradas", len(relatorio))
        col2.metric("Ocupadas (Mor/Vis)", qtd_ocupadas)
        col3.metric("Unid. Livres", len(relatorio) - qtd_ocupadas)

        st.divider()

        # Contagem por Categoria
        st.subheader("🏢 Unidades Ocupadas por Categoria")
        if qtd_ocupadas > 0:
            contagem_tipo = ocupadas_df['Tipo Ocupante'].value_counts()
            cols_tipo = st.columns(max(len(contagem_tipo), 2))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)
        else:
            st.info("Nenhuma unidade ocupada no momento.")

        st.divider()

        # Tabela
        st.subheader("📋 Relatório por Unidade")
        st.dataframe(relatorio.sort_values('Unidade'), use_container_width=True, hide_index=True)

        # Botão de Exportação
        csv = relatorio.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Planilha Processada", csv, "relatorio_ocupacao_final.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro inesperado: {e}")
else:
    st.info("Aguardando upload do CSV para aplicar os filtros personalizados.")