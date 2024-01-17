import pandas as pd
import plotly.express as px
import streamlit as st

# initialize page config
st.set_page_config(page_title="Atmind Restaurant Performance", page_icon=":bar_chart:", layout="wide")
st.title(" :bar_chart: Restaurant Performance Report")
st.markdown("<style>div.block-container{padding-top:1rem;}<style>", unsafe_allow_html=True)

# import dataset
file_path = "Dataset/test_data.csv"
df = pd.read_csv(file_path)

# convert data format
df["Date"] = pd.to_datetime(df["Date"])
df["Order Time"] = pd.to_datetime(df["Order Time"])
df["Serve Time"] = pd.to_datetime(df["Serve Time"])
df["Serve Time"] = df["Serve Time"].dt.strftime("%Y-%m-%d %H:%M:%S")
df["Serve Time"] = pd.to_datetime(df["Serve Time"])
df["Hour"] = df["Hour"].astype("category")

# create waiting order column
df["Pending Order"] =  df["Serve Time"] - df["Order Time"]
df["Pending Order"] = round(df["Pending Order"].dt.total_seconds()/60)

# date feature extraction
df["Month"] = df["Date"].dt.month
df["Day"] = df["Date"].dt.day
df["Month"] = df["Month"].astype("category")
df["Day"] = df["Day"].astype("category")

# convert all object into category
for col in df.columns:
    if df[col].dtype == "object":
        df[col] = df[col].astype("category")

# convert day of week column to have ordinal order
df['Day Of Week'] = pd.Categorical(df['Day Of Week'], categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], ordered=True)



# date sidebar
st.sidebar.header("Date Selection")
col1, col2 = st.sidebar.columns((2))
df["Date"] = pd.to_datetime(df["Date"])
startDate = pd.to_datetime(df["Date"].min())
endtDate = pd.to_datetime(df["Date"].max())

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endtDate))

df = df[(df["Date"] >= date1) & (df["Date"] <= date2)].copy() 

# category filter
st.sidebar.header("Filter Selection")
category = st.sidebar.multiselect("Category", df["Category"].unique())
if not category:
    df2 = df.copy()
else:
    df2 = df[df["Category"].isin(category)]

# menu filter
menu = st.sidebar.multiselect("Menu", df2["Menu"].unique())

# filter data based on category combination
if not category and not menu:
    filter_df = df
elif not menu:
    filter_df = df2[df2["Category"].isin(category)]
elif menu:
    filter_df = df2[df2["Menu"].isin(menu)]
else:
    filter_df = df2[df2["Category"].isin(category) & df2["Menu"].isin(menu)]

# kpi cards
kpi1, kpi2, kpi3= st.columns(3)

kpi1.metric("Total Revenue ($)", value="{:,.2f}".format(filter_df["Price"].sum())) # total revenue
kpi2.metric(label= "Total Orders", value="{:,.0f}".format(filter_df["Category"].count())) # total order
kpi3.metric(label= "AVG. Waiting Time (minutes)", value="{:.0f}".format(filter_df["Pending Order"].mean())) # average order wating time



# Revenue over last year

# chart setting
col1, col2, col3 = st.columns([0.2, 0.2, 1])
with col1:
    selected_interval = st.selectbox("Select Interval", options=['Month', 'Quarter', 'Day'])
with col2:
    selected_group = st.selectbox("Group by", options=['Default', 'Category', 'Menu'])

filter_df['Date'] = pd.to_datetime(filter_df['Date'])
groupby_params = {
    ('Day', 'Default'): [pd.Grouper(key='Date', freq='D')],
    ('Day', 'Category'): [pd.Grouper(key='Date', freq='D'), 'Category'],
    ('Day', 'Menu'): [pd.Grouper(key='Date', freq='D'), 'Menu'],
    ('Month', 'Default'): [pd.Grouper(key='Date', freq='M')],
    ('Month', 'Category'): [pd.Grouper(key='Date', freq='M'), 'Category'],
    ('Month', 'Menu'): [pd.Grouper(key='Date', freq='M'), 'Menu'],
    ('Quarter', 'Default'): [pd.Grouper(key='Date', freq='Q')],
    ('Quarter', 'Category'): [pd.Grouper(key='Date', freq='Q'), 'Category'],
    ('Quarter', 'Menu'): [pd.Grouper(key='Date', freq='Q'), 'Menu'],
}

df_grouped = filter_df.groupby(groupby_params.get((selected_interval, selected_group), []))["Price"].sum().reset_index()
if selected_group != "Default":
    title = f'{selected_interval.capitalize()}ly Sales Over Last Year Group by {selected_group}'
else:
    title = f'{selected_interval.capitalize()}ly Sales Over Last Year'

title = title.replace("Dayly", "Daily") 

# no data label for category and menu
if selected_group in ['Category', 'Menu']:
    fig = px.line(df_grouped, x='Date', y='Price', color=selected_group, template="seaborn", title=title)
else:
    fig = px.line(df_grouped, x='Date', y='Price', text=["{:,.0f}".format(x) for x in df_grouped["Price"]], title=title)
    for i, row in df_grouped.iterrows():
        annotation = dict(
            x=row['Date'],
            y=row['Price'],
            xref='x',
            yref='y',
            text="{:,.0f}".format(row['Price']),
            showarrow=False,
            font=dict(color='white'),
            bordercolor='black',  # Set the border color
            borderwidth=2,  # Set the border width
            bgcolor='rgba(0,0,0,0.7)',  # Set the background color with transparency
            align='center',
        )
        fig.add_annotation(annotation)

fig.update_xaxes(title_text='Date')
fig.update_yaxes(title_text='Sales', showgrid=False)
st.plotly_chart(fig, use_container_width=True)

# sale performance
st.subheader("Restaurant Sales Sammary")
fig_col1, fig_col2 = st.columns(2)
with fig_col1:
    sales = filter_df.groupby(by=["Menu", "Category"], as_index=False)["Price"].sum().sort_values(by=["Price"], ascending=[True])
    fig = px.bar(sales, y="Menu", x="Price", color="Category", text= ["{:,.0f}".format(x) for x in sales["Price"]],
                 category_orders={"Menu": filter_df.groupby("Menu")["Price"].sum().sort_values(ascending=False).index}, title= "Sales by Menu")
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(title_text = "Sales")
    st.plotly_chart(fig, use_container_width=True)

with fig_col2:
    quantity = filter_df.groupby(by=["Category", "Menu"], as_index=False)["Price"].count().sort_values(by=["Category", "Price"], ascending=[True, True])
    fig = px.bar(quantity, x="Price", y="Menu", color="Category",  text= ['{:,.0f}'.format(x) for x in quantity["Price"]],
                 category_orders={"Menu": filter_df.groupby("Menu")["Price"].count().sort_values(ascending=False).index}, title= "Units Sold by Menu")
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(title_text = "Quantity")
    st.plotly_chart(fig, use_container_width=True)


# order density
st.subheader("Order Summary")
fig1, fig2 = st.columns(2)
with fig1:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    fig = px.density_heatmap(filter_df.query("Category == 'food'"), x="Day Of Week", y="Hour", z="Price", histfunc="count", text_auto=True, color_continuous_scale="YlGnBu", title="Frequency of Food Orders")
    fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': day_order})
    st.plotly_chart(fig, use_container_width=True)
with fig2:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    fig = px.density_heatmap(filter_df.query("Category == 'drink'"), x="Day Of Week", y="Hour", z="Price", histfunc="count", text_auto=True, color_continuous_scale="YlGnBu", title="Frequency of Drink Orders")
    fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': day_order})
    st.plotly_chart(fig, use_container_width=True)

# restaurant performance
st.subheader("Restaurant Performance")
fig1 ,fig2 = st.columns(2)
with fig1:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    fig = px.box(filter_df, x="Day Of Week", y="Pending Order", color="Category", template="seaborn", title= "Order Waiting Time Distribution by Category")
    fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': day_order})
    fig.update_yaxes(title_text='Waiting Time (minutes)')
    st.plotly_chart(fig, use_container_width=True)
with fig2:
    fig = px.box(filter_df, x="Pending Order", y="Menu", color="Category", template="seaborn",
                 category_orders={"Menu": filter_df.groupby("Menu")["Pending Order"].mean().sort_values(ascending=False).index}, title="Order Waiting Time by Menu")
    fig.update_xaxes(title_text='Waiting Time (minutes)')
    st.plotly_chart(fig, use_container_width=True)

# menu insight
st.subheader("Menu Insight")
fig1, fig2 = st.columns(2)
with fig1:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    fig = px.density_heatmap(filter_df.query("Category == 'food'"), y="Menu", x="Hour", z="Price", histfunc="count", text_auto=True, color_continuous_scale="YlGnBu", title="Hourly Order Frequency of Food Items")
    fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': day_order})
    st.plotly_chart(fig, use_container_width=True)
with fig2:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    fig = px.density_heatmap(filter_df.query("Category == 'drink'"), y="Menu", x="Hour", z="Price", histfunc="count", text_auto=True, color_continuous_scale="YlGnBu", title="Hourly Order Frequency of Drink Items")
    fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': day_order})
    st.plotly_chart(fig, use_container_width=True)
with fig1:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    fig = px.density_heatmap(filter_df.query("Category == 'food'"), y="Menu", x="Day Of Week", z="Price", histfunc="count", text_auto=True, color_continuous_scale="YlGnBu", title="Daily Order Frequency of Food Items")
    fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': day_order})
    st.plotly_chart(fig, use_container_width=True)
with fig2:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    fig = px.density_heatmap(filter_df.query("Category == 'drink'"), y="Menu", x="Day Of Week", z="Price", histfunc="count", text_auto=True, color_continuous_scale="YlGnBu", title="Daily Order Frequency of Drink Items")
    fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': day_order})
    st.plotly_chart(fig, use_container_width=True)