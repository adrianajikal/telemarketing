# Imports
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# Configurar página (deve ser a primeira linha)
st.set_page_config(page_title='Telemarketing Analysis',
                   page_icon='📊',
                   layout='wide',
                   initial_sidebar_state='expanded')

# Tema do Seaborn
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

# Funções utilitárias
@st.cache_data(show_spinner=True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=';')
    except:
        return pd.read_excel(file_data)

@st.cache_data
def multiselect_filter(relatorio, col, selecionados):
    if 'all' in selecionados:
        return relatorio
    else:
        return relatorio[relatorio[col].isin(selecionados)].reset_index(drop=True)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# Função principal da aplicação
def main():
    st.title('Telemarketing Analysis')
    st.markdown("---")

    # Sidebar - Upload
    image = Image.open("Bank-Branding.jpg")
    st.sidebar.image(image)

    st.sidebar.write("## Suba o arquivo")
    data_file = st.sidebar.file_uploader("Bank marketing data", type=['csv', 'xlsx'])

    if data_file is not None:
        bank_raw = load_data(data_file)
        bank = bank_raw.copy()

        st.write('## Antes dos filtros')
        st.write(bank_raw.head())

        # Formulário de filtros
        with st.sidebar.form(key='filters_form'):
            graph_type = st.radio('Tipo de gráfico:', ('Barras', 'Pizza'))

            max_age = int(bank.age.max())
            min_age = int(bank.age.min())
            idades = st.slider('Idade', min_value=min_age, max_value=max_age, value=(min_age, max_age), step=1)

            def add_multiselect_options(column):
                options = bank[column].unique().tolist()
                options.append('all')
                return st.multiselect(column, options, ['all'])

            jobs_selected = add_multiselect_options('job')
            marital_selected = add_multiselect_options('marital')
            default_selected = add_multiselect_options('default')
            housing_selected = add_multiselect_options('housing')
            loan_selected = add_multiselect_options('loan')
            contact_selected = add_multiselect_options('contact')
            month_selected = add_multiselect_options('month')
            day_of_week_selected = add_multiselect_options('day_of_week')

            submit_button = st.form_submit_button(label='Aplicar')

        # Se o botão foi clicado, aplicar os filtros e gerar gráficos
        if submit_button:
            bank = (bank.query("age >= @idades[0] and age <= @idades[1]")
                        .pipe(multiselect_filter, 'job', jobs_selected)
                        .pipe(multiselect_filter, 'marital', marital_selected)
                        .pipe(multiselect_filter, 'default', default_selected)
                        .pipe(multiselect_filter, 'housing', housing_selected)
                        .pipe(multiselect_filter, 'loan', loan_selected)
                        .pipe(multiselect_filter, 'contact', contact_selected)
                        .pipe(multiselect_filter, 'month', month_selected)
                        .pipe(multiselect_filter, 'day_of_week', day_of_week_selected)
                    )

            st.write('## Após os filtros')
            st.write(bank.head())

            # Download do Excel filtrado
            df_xlsx = to_excel(bank)
            st.download_button('📥 Download tabela filtrada em EXCEL',
                               data=df_xlsx,
                               file_name='bank_filtered.xlsx')

            st.markdown("---")

            # Proporção do target antes e depois do filtro
            col1, col2 = st.columns(2)

            def calculate_target_percentage(df):
                return df.y.value_counts(normalize=True).to_frame() * 100

            bank_raw_target_perc = calculate_target_percentage(bank_raw).sort_index()
            bank_target_perc = calculate_target_percentage(bank).sort_index()

            col1.write('### Proporção original')
            col1.write(bank_raw_target_perc)
            col1.download_button('📥 Download', data=to_excel(bank_raw_target_perc), file_name='bank_raw_y.xlsx')

            col2.write('### Proporção da tabela com filtros')
            col2.write(bank_target_perc)
            col2.download_button('📥 Download', data=to_excel(bank_target_perc), file_name='bank_y.xlsx')

            st.markdown("---")

            # Gráficos de comparação
            st.write('## Proporção de aceite')
            fig, ax = plt.subplots(1, 2, figsize=(12, 4))

            if graph_type == 'Barras':
                sns.barplot(x=bank_raw_target_perc.index, y='y', data=bank_raw_target_perc, ax=ax[0])
                ax[0].bar_label(ax[0].containers[0])
                ax[0].set_title('Dados brutos', fontweight="bold")

                sns.barplot(x=bank_target_perc.index, y='y', data=bank_target_perc, ax=ax[1])
                ax[1].bar_label(ax[1].containers[0])
                ax[1].set_title('Dados filtrados', fontweight="bold")

            else:
                bank_raw_target_perc.plot(kind='pie', autopct='%.2f', y='y', ax=ax[0], legend=False)
                ax[0].set_title('Dados brutos', fontweight="bold")
                ax[0].set_ylabel('')

                bank_target_perc.plot(kind='pie', autopct='%.2f', y='y', ax=ax[1], legend=False)
                ax[1].set_title('Dados filtrados', fontweight="bold")
                ax[1].set_ylabel('')

            st.pyplot(fig)

if __name__ == '__main__':
    main()
