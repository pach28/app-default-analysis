import streamlit as st
import pandas as pd
import plotly.express as px

def load_data():
    try:
        df = pd.read_csv("ventas_estacionales_3.csv")
        return df
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo 'df_ventas_chokorin.csv'")
        st.stop()

df_ventas = load_data()
df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha'], format='%Y-%m-%d')

# --- Obtener el rango de fechas disponible en los datos ---
min_date_data = df_ventas['Fecha'].min().date()
max_date_data = df_ventas['Fecha'].max().date()

# --- Filtros en Columnas (Layout) ---
st.header("Filtros de Análisis:")

# Usaremos dos columnas para los multiselect y una para el date_input
cols_filters_1, cols_filters_2 = st.columns([0.4, 0.6])

with cols_filters_1:
    sucursal_options = df_ventas['Sucursal'].unique().tolist()
    sucursal = st.multiselect(
        'Seleccione la Sucursal',
        options=sucursal_options,
        default=sucursal_options
    )

    hour_options = sorted(df_ventas['Hora'].unique().tolist())
    hora = st.multiselect(
        'Seleccione la Hora del Día',
        options=hour_options,
        default=hour_options
    )

    mes_options = df_ventas['Nombre_Mes'].unique().tolist()
    mes = st.multiselect(
        'Seleccione el Mes',
        options=mes_options,
        default=mes_options
    )

with cols_filters_2:
    st.markdown("##### Seleccione Rango de Fechas:")
    selected_date_range = st.date_input(
        ' ',
        value=(min_date_data, max_date_data),
        min_value=min_date_data,
        max_value=max_date_data,
        key='date_range_picker'
    )
    
    if len(selected_date_range) == 2:
        start_date_selected = pd.to_datetime(selected_date_range[0])
        end_date_selected = pd.to_datetime(selected_date_range[1])
    else:
        start_date_selected = pd.to_datetime(selected_date_range[0])
        end_date_selected = pd.to_datetime(selected_date_range[0])

# --- Filtrado de Datos ---
data_filtered = df_ventas[
    df_ventas['Sucursal'].isin(sucursal) &
    df_ventas['Hora'].isin(hora) &
    df_ventas['Nombre_Mes'].isin(mes) &
    (df_ventas['Fecha'] >= start_date_selected) &
    (df_ventas['Fecha'] <= end_date_selected)
]

# --- MÉTRICAS PRINCIPALES ---
st.header("📈 Métricas del Período Seleccionado")

if not data_filtered.empty:
    total_ventas = data_filtered['Precio Total'].sum()
    cantidad_productos_vendidos = data_filtered['Unidades'].sum() if 'Unidades' in data_filtered.columns else len(data_filtered)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="💰 Total de Ventas",
            value=f"${total_ventas:,.2f}"
        )
    
    with col2:
        st.metric(
            label="📦 Productos Vendidos",
            value=f"{cantidad_productos_vendidos:,}"
        )

    st.markdown("---")
    
    # --- GRÁFICO DE PASTEL POR SUCURSAL ---
    st.subheader("🏪 Distribución de Ventas por Sucursal")
    
    ventas_por_sucursal = data_filtered.groupby('Sucursal')['Precio Total'].sum().reset_index()
    
    fig_pie_sucursal = px.pie(
        ventas_por_sucursal,
        values='Precio Total',
        names='Sucursal',
        title=f'Distribución de Ventas por Sucursal ({start_date_selected.strftime("%d/%m/%Y")} - {end_date_selected.strftime("%d/%m/%Y")})',
        color_discrete_sequence=px.colors.qualitative.Set3,
        hover_data=['Precio Total']
    )
    
    fig_pie_sucursal.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>' +
                     'Ventas: $%{value:,.2f}<br>' +
                     'Porcentaje: %{percent}<br>' +
                     '<extra></extra>'
    )
    
    fig_pie_sucursal.update_layout(
        title_x=0.5,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig_pie_sucursal, use_container_width=True)

else:
    st.warning("⚠️ No hay datos para la combinación de filtros seleccionada. Por favor, ajusta los filtros.")

st.markdown("---")

# --- Gráfico de Ventas por Día ---
st.subheader("📅 Ventas Diarias por Día (Según Filtros Aplicados)")

if not data_filtered.empty:
    ventas_diarias_filtradas = data_filtered.groupby('Fecha')['Precio Total'].sum().reset_index()

    fig_ventas_diarias = px.bar(
        ventas_diarias_filtradas,
        x='Fecha',
        y='Precio Total',
        title=f'Ventas Diarias por Fecha ({start_date_selected.strftime("%d/%m/%Y")} - {end_date_selected.strftime("%d/%m/%Y")})',
        labels={'Fecha': 'Fecha', 'Precio Total': 'Ventas ($)'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_ventas_diarias.update_layout(
        hovermode="x unified",
        title_x=0.5,
        xaxis_title="Fecha",
        yaxis_title="Ventas Totales ($)"
    ) 
    fig_ventas_diarias.update_xaxes(
        tickangle=45,
        dtick="M1",
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    st.plotly_chart(fig_ventas_diarias, use_container_width=True)
else:
    st.warning("No hay datos para la combinación de filtros seleccionada. Por favor, ajusta los filtros.")

# --- Gráfico de Distribución de Ventas por Producto con Costos y Utilidad ---
st.subheader("🛍️ Análisis de Costos y Utilidad por Producto")

if not data_filtered.empty:
    ventas_por_producto = data_filtered.groupby('Producto')['Precio Total'].sum().reset_index()
    
    fig_ventas_producto = px.bar(
        ventas_por_producto,
        x='Producto',
        y='Precio Total',
        color='Producto',
        title=f'Análisis de Costos vs Utilidad por Producto ({start_date_selected.strftime("%d/%m/%Y")} - {end_date_selected.strftime("%d/%m/%Y")})',
        labels={'Precio Total': 'Importe ($)', 'Producto': 'Producto'}
    )
    fig_ventas_producto.update_xaxes(tickangle=45)

    st.plotly_chart(fig_ventas_producto, use_container_width=True)
else:
    st.warning("No hay datos para la combinación de filtros seleccionada para el gráfico de productos. Por favor, ajusta los filtros.")
