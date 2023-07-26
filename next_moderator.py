import random
import pandas as pd
import numpy as np
import streamlit as st
import datetime as dt
import altair as alt
from azure.storage.blob import BlobServiceClient
import io


# ================= #
#  AZURE FUNCTIONS  #
# ================= #


def upload_to_blob_storage(file_path, file_name, connection_string, container_name):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=file_name
    )
    blob_client.upload_blob(file_path, overwrite=True)


def read_from_blob_storage(file_name, connection_string, container_name):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=file_name
    )
    blob_string = blob_client.download_blob().content_as_text()
    df = pd.read_csv(io.StringIO(blob_string))
    return df


# ===================== #
#  STREAMLIT FUNCTIONS  #
# ===================== #


# get list of previous moderators
@st.cache_data  # to only run this function once at the beginning instead of with every click
def get_df_mod():
    df_mod = read_from_blob_storage(
        "moderator_history.csv", connection_string, container_name
    )
    df_mod["Date"] = pd.to_datetime(df_mod["Date"], format="%Y-%m-%d").dt.date
    return df_mod


@st.cache_data
def get_df_usr():
    df_usr = read_from_blob_storage("moderators.csv", connection_string, container_name)
    users = df_usr["Moderator"].to_list()
    users.sort()
    return users


def save_df_usr(users):
    df_usr = pd.DataFrame({"Moderator": users})
    output = df_usr.to_csv(encoding="utf-8", index=False)
    upload_to_blob_storage(output, "moderators.csv", connection_string, container_name)


# randomize the next moderator
def get_nxt_mod(lst_mod, available_team):
    nxt_mod = random.choice(available_team)
    while nxt_mod == lst_mod:
        nxt_mod = random.choice(available_team)
    return nxt_mod


# add the next moderator to the previous moderators list
def add_nxt_mod(df_mod, nxt_mod, nxt_dt, connection_string, container_name):
    insert_row = {
        "Date": nxt_dt,
        "Moderator": nxt_mod,
    }
    df_mod = pd.concat([df_mod, pd.DataFrame([insert_row])], ignore_index=True)
    df_mod["Date"] = pd.to_datetime(df_mod["Date"], format="%Y-%m-%d").dt.date
    output = df_mod.to_csv(encoding="utf-8", index=False)
    upload_to_blob_storage(
        output, "moderator_history.csv", connection_string, container_name
    )
    return df_mod


def drop_new_rows(df_mod, tdy):
    df_mod = df_mod[df_mod["Date"] <= tdy]
    df_mod.to_csv("moderator_history.csv", encoding="utf-8", index=False)
    return df_mod


# =============== #
#  STREAMLIT APP  #
# =============== #


# set the page title, icon, and layout
st.set_page_config(page_title="Next Moderator", page_icon="📣", layout="wide")

# this aligns all buttons to the center of the container
customized_button = st.markdown(
    """<style >.stDownloadButton, div.stButton {text-align:center}</style>""",
    unsafe_allow_html=True,
)

# this hides the dataframe index column
hide_table_row_index = """<style> thead tr th:first-child {display:none} tbody th {display:none} </style>"""

# the header for the page
col1, col2 = st.columns([1, 1])
with col1:
    st.image("logo.png", width=120)
with col2:
    st.markdown(
        "<p style='text-align: right; font-size: 25px; color: #FFB000'><b>BI Fulfillment's <span style='color: #072543'>Next Moderator</span></b></p>",
        unsafe_allow_html=True,
    )

# initialize data for initial view
connection_string = st.secrets.blob_credentials.connection_string
container_name = st.secrets.blob_credentials.container_name

df_mod = get_df_mod()
users = get_df_usr()
lst_mod = df_mod["Moderator"].iloc[-1]
lst_dt = df_mod["Date"].iloc[-1]
tdy = dt.datetime.date(dt.datetime.today())

# shut down tool on Saturdays and Sundays, otherwise set default next moderation date
# default next moderation date will default to next Monday, Wednesday, or Friday, whichever is closest
if tdy.isoweekday() == 6:
    st.markdown(
        "<p style='text-align: center; font-size: 50px; color: #072543'><b>Tool is under contract, and Saturdays are off!</b></p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; font-size: 75px'><b>🛌</b></p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; font-size: 25px; color: #FFB000'><b>Next Moderator</b></p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align: center; font-size: 50px; color: #072543'><b>{lst_mod}</b></p>",
        unsafe_allow_html=True,
    )
elif tdy.isoweekday() == 7:
    st.markdown(
        "<p style='text-align: center; font-size: 50px; color: #072543'><b>Tool is under contract, and Sundays are off!</b></p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; font-size: 75px'><b>🛌",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; font-size: 25px; color: #FFB000'><b>Next Moderator</b></p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align: center; font-size: 50px; color: #072543'><b>{lst_mod}</b></p>",
        unsafe_allow_html=True,
    )
else:
    if tdy.isoweekday() in [1, 2]:
        nxt_dt_dflt = tdy + dt.timedelta(days=(3 - tdy.isoweekday()))
    elif tdy.isoweekday() in [3, 4]:
        nxt_dt_dflt = tdy + dt.timedelta(days=(5 - tdy.isoweekday()))
    elif tdy.isoweekday() == 5:
        nxt_dt_dflt = tdy + dt.timedelta(days=3)

    st.markdown(
        "<p style='text-align: center; font-size: 25px; color: #FFB000'><b>Today's Moderator</b></p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align: center; font-size: 50px; color: #072543'><b>{lst_mod}</b></p>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([7, 2])
    with col1:
        available_team = st.multiselect(
            "Who is available to moderate?",
            users,
            users,
        )
    with col2:
        nxt_dt = st.date_input("Next Stand-Up's Date", nxt_dt_dflt)

    col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 0.75, 1, 0.25, 3, 1, 2])
    with col5:
        button_nxt_mod = st.button(label="Get Lucky!")
    with col7:
        save_ck = st.checkbox("Save Results", True)
    with col1:
        user_ck = st.checkbox("Edit Moderators", False)
    with col2:
        if user_ck:
            action = st.radio(
                "",
                ("➕", "➖"),
                label_visibility="collapsed",
                horizontal=True,
            )
    with col3:
        if user_ck:
            if action == "➕":
                edit = st.text_input("", label_visibility="collapsed").title()
            elif action == "➖":
                edit = st.selectbox("", users, label_visibility="collapsed")
    with col4:
        if user_ck:
            button_save = st.button(label="💾")
            if button_save & (action == "➕") & len(edit) > 0:
                users.append(edit)
                save_df_usr(users)
                get_df_usr.clear()
            elif button_save & (action == "➖"):
                users.remove(edit)
                save_df_usr(users)
                get_df_usr.clear()

    st.write("")

    # if button is clicked, get the next moderator and show some stats
    if button_nxt_mod:
        # clear cache at the beginning of the instance
        st.cache_data.clear()

        # some fool proofing
        if len(available_team) < 1:
            st.markdown(
                "<p style='text-align: center; font-size: 70px'><b>🤔</b></p>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align: center; font-size: 35px; color: #072543'><b>Select at least one team member!</b></p>",
                unsafe_allow_html=True,
            )
        elif len(available_team) == 1:
            st.markdown(
                "<p style='text-align: center; font-size: 35px; color: #072543'><b>There's only one team member available... Why did you even run this thing?</b></p>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align: center; font-size: 70px'><b>🤨</b></p>",
                unsafe_allow_html=True,
            )
        else:
            if lst_dt == nxt_dt:
                df_mod = df_mod[df_mod["Date"] < nxt_dt]
                nxt_mod = get_nxt_mod(lst_mod, available_team)
                if save_ck:
                    df_mod = add_nxt_mod(
                        df_mod, nxt_mod, nxt_dt, connection_string, container_name
                    )
            else:
                nxt_mod = get_nxt_mod(lst_mod, available_team)
                if save_ck:
                    df_mod = add_nxt_mod(
                        df_mod, nxt_mod, nxt_dt, connection_string, container_name
                    )

            st.markdown(
                f"<p style='text-align: center; font-size: 25px; color: #FFB000'><b>{nxt_dt} Stand-Up's Moderator</b></p>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='text-align: center; font-size: 75px; color: #072543'><b>{nxt_mod}</b></p>",
                unsafe_allow_html=True,
            )
            st.write("")

            col1, col2, col3 = st.columns([2, 1, 2])
            # current month's leaderboard
            with col1:
                st.markdown(
                    f"<p style='text-align: center; font-size: 20px; color: #072543'><b>This Month's Leaderboard</b></p>",
                    unsafe_allow_html=True,
                )
                df_lb_tm = df_mod[
                    (df_mod["Date"] >= dt.date(tdy.year, tdy.month, 1))
                    & (df_mod["Date"] < nxt_dt_dflt)
                ]
                df_lb_tm = df_lb_tm.groupby("Moderator", as_index=False).count()
                df_lb_tm.rename(columns={"Date": "Number of Moderations"}, inplace=True)
                df_lb_tm["Colour"] = np.where(
                    df_lb_tm["Number of Moderations"]
                    == df_lb_tm["Number of Moderations"].max(),
                    "#FFB000",
                    "#072543",
                )
                domain = df_lb_tm["Moderator"].tolist()
                range = df_lb_tm["Colour"].tolist()
                chart_data = (
                    alt.Chart(df_lb_tm)
                    .mark_bar()
                    .encode(
                        x="Moderator",
                        y=alt.Y("Number of Moderations", axis=alt.Axis(tickMinStep=1)),
                        color=alt.Color(
                            "Moderator",
                            scale=alt.Scale(domain=domain, range=range),
                            legend=None,
                        ),
                    )
                )
                st.altair_chart(chart_data, use_container_width=True)
            # recent moderators table
            with col2:
                st.markdown(
                    f"<p style='text-align: center; font-size: 20px; color: #072543'><b>Previous Moderators</b></p>",
                    unsafe_allow_html=True,
                )
                df_mod_dsply = df_mod[df_mod["Date"] < nxt_dt_dflt].iloc[::-1].head(8)
                st.markdown(hide_table_row_index, unsafe_allow_html=True)
                st.table(df_mod_dsply)
            # overall leaderboard
            with col3:
                st.markdown(
                    f"<p style='text-align: center; font-size: 20px; color: #072543'><b>All Time Leaderboard</b></p>",
                    unsafe_allow_html=True,
                )
                df_lb = df_mod[:-1].groupby("Moderator", as_index=False).count()
                df_lb.rename(columns={"Date": "Number of Moderations"}, inplace=True)
                df_lb["Colour"] = np.where(
                    df_lb["Number of Moderations"]
                    == df_lb["Number of Moderations"].max(),
                    "#FFB000",
                    "#072543",
                )
                domain = df_lb["Moderator"].tolist()
                range = df_lb["Colour"].tolist()
                chart_data = (
                    alt.Chart(df_lb)
                    .mark_bar()
                    .encode(
                        x="Moderator",
                        y=alt.Y("Number of Moderations", axis=alt.Axis(tickMinStep=1)),
                        color=alt.Color(
                            "Moderator",
                            scale=alt.Scale(domain=domain, range=range),
                            legend=None,
                        ),
                    )
                )
                st.altair_chart(chart_data, use_container_width=True)
