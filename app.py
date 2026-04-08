import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Análise de Ocupação de Unidades", layout="wide")

st.title("📊 Monitor de Ocupação de Unidades")
st.markdown("Carregue a planilha de acessos para verificar quais unidades estão ocupadas no momento.")

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha o arquivo CSV (export-report-access)", type="csv")

if uploaded_file is not None:
    try:
        # Lógica de processamento
        df = pd.read_csv(uploaded_file)
        
        # Criar timestamp para ordenação correta
        df['Timestamp'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], dayfirst=True)
        
        # Filtros conforme solicitado
        status_validos = ['Entrada autorizada', 'Saída autorizada']
        df_filtrado = df[df['Situação'].isin(status_validos)].copy()
        
        # Ordenar por tempo e remover duplicados para pegar o estado MAIS RECENTE
        df_filtrado = df_filtrado.sort_values(by='Timestamp', ascending=False)
        ultimo_estado = df_filtrado.drop_duplicates(subset='Unidades', keep='first')
        
        # Mapeamento de Situação
        ultimo_estado['Ocupação'] = ultimo_estado['Situação'].apply(
            lambda x: "🔴 Ocupada" if x == "Entrada autorizada" else "🟢 Livre"
        )
        
        # Preparar tabela final
        resultado = ultimo_estado[['Unidades', 'Ocupação', 'Data', 'Hora', 'Pessoa']].rename(
            columns={'Unidades': 'Unidade', 'Data': 'Última Data', 'Hora': 'Última Hora', 'Pessoa': 'Último Acesso'}
        )

        # --- Exibição no Browser ---
        
        # Métricas rápidas
        col1, col2, col3 = st.columns(3)
        total_unidades = len(resultado)
        ocupadas = len(resultado[resultado['Ocupação'] == "🔴 Ocupada"])
        livres = total_unidades - ocupadas
        
        col1.metric("Total de Unidades", total_unidades)
        col2.metric("Ocupadas", ocupadas)
        col3.metric("Livres", livres)

        st.divider()

        # Tabela de Resultados
        st.subheader("Estado Atual das Unidades")
        st.dataframe(resultado, use_container_width=True)

        # Botão para Download
        csv_download = resultado.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Descarregar Relatório (CSV)",
            data=csv_download,
            file_name="relatorio_ocupacao.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("Aguardando carregamento de arquivo...")