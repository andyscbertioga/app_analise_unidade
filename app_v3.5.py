import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Monitor de Ocupação Completo", layout="wide")

st.title("📊 Painel de Ocupação (Histórico de Saída)")
st.markdown("Agora exibindo os dados da última pessoa que passou pela unidade, mesmo que ela esteja vazia.")

uploaded_file = st.file_uploader("Carregue a planilha CSV", type="csv")

if uploaded_file is not None:
    try:
        # 1. Carregamento e Limpeza Inicial
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        for col in ['Unidades', 'Tipo', 'Situação', 'Pessoa']:
            df[col] = df[col].astype(str).str.strip()
        
        # --- FILTROS DE EXCLUSÃO ---
        # Remover unidades vazias
        df = df[~df['Unidades'].isin(['', 'nan', 'None'])]
        
        # Remover unidades específicas
        unidades_bloqueadas = ["BEACH HOUSE RESTAURANTE", "ADM ADM, ADMINISTRAÇÃO ALLTIME"]
        df = df[~df['Unidades'].isin(unidades_bloqueadas)]

        # Ignorar Funcionários e Prestadores
        tipos_para_ignorar = ['Funcionário', 'Prestador de serviço']
        df = df[~df['Tipo'].isin(tipos_para_ignorar)]

        # Manter apenas Acessos Autorizados (Ignora Negados)
        df = df[df['Situação'].str.contains('autorizada', case=False)].copy()

        # 2. Tratamento de Tempo
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        df_mov = df.sort_values(by='Timestamp', ascending=False)

        # 3. LÓGICA DE OCUPAÇÃO (Quem está dentro AGORA)
        # Pegamos o último evento de cada pessoa por unidade
        ultimo_evento_pessoa = df_mov.drop_duplicates(subset=['Unidades', 'Pessoa'], keep='first')
        # Uma unidade só é ocupada se houver alguém com status "Entrada autorizada"
        unidades_com_alguem = ultimo_evento_pessoa[ultimo_evento_pessoa['Situação'] == 'Entrada autorizada']['Unidades'].unique()

        # 4. LÓGICA DE DADOS (Último movimento da UNIDADE para preencher a tabela)
        # Aqui pegamos o último registro GERAL da unidade, seja entrada ou saída
        ultimo_registro_unidade = df_mov.drop_duplicates(subset='Unidades', keep='first').copy()

        # Criamos a coluna de Situação Atual baseada na lista de quem está dentro
        ultimo_registro_unidade['Situação Atual'] = ultimo_registro_unidade['Unidades'].apply(
            lambda x: "🔴 Ocupada" if x in unidades_com_alguem else "🟢 Livre"
        )

        # 5. Organização da Tabela Final
        relatorio = ultimo_registro_unidade[['Unidades', 'Situação Atual', 'Tipo', 'Pessoa', 'Hora']].rename(
            columns={
                'Unidades': 'Unidade',
                'Tipo': 'Tipo Ocupante',
                'Pessoa': 'Último Acesso',
                'Hora': 'Horário'
            }
        )

        # --- EXIBIÇÃO ---
        ocupadas_df = relatorio[relatorio['Situação Atual'] == "🔴 Ocupada"]
        qtd_ocupadas = len(ocupadas_df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Unidades Monitoradas", len(relatorio))
        col2.metric("Ocupadas (Mor/Vis)", qtd_ocupadas)
        col3.metric("Unid. Livres", len(relatorio) - qtd_ocupadas)

        st.divider()

        # Contagem por Categoria (Apenas das Ocupadas)
        st.subheader("🏢 Unidades Ocupadas por Categoria")
        if qtd_ocupadas > 0:
            contagem_tipo = ocupadas_df['Tipo Ocupante'].value_counts()
            cols_tipo = st.columns(max(len(contagem_tipo), 2))
            for i, (tipo, total) in enumerate(contagem_tipo.items()):
                cols_tipo[i].metric(f"Unid. com {tipo}", total)
        else:
            st.info("Nenhuma unidade ocupada no momento.")

        st.divider()

        # Tabela (Agora com dados em todas as linhas)
        st.subheader("📋 Relatório Detalhado")
        st.dataframe(relatorio.sort_values('Unidade'), use_container_width=True, hide_index=True)

        # Exportação
        csv = relatorio.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Planilha Completa", csv, "relatorio_ocupacao.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("Aguardando upload do CSV.")