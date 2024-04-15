import streamlit as st
import pandas as pd

# Function to load data from CSV files
def load_csv_data():
    # Adjust the paths to your actual CSV files
    challenge_df = pd.read_csv("challenge.csv")
    tools_df = pd.read_csv("tool.csv")
    return challenge_df, tools_df

# Main function where the Streamlit app is defined
def main():
    st.set_page_config(layout="wide")
    st.markdown("<h1 style='text-align: center;'>Embedded Graph in Streamlit</h1>", unsafe_allow_html=True)

    # Detailed graph URL - replace with your actual URL
    detailed_graph_url = "https://your_detailed_graph_url"
    # Fancy button for the detailed graph
    button_html = f"""<a href="{detailed_graph_url}" target="_blank">
                      <button style='color: white; background-color: #4CAF50; border: none; padding: 10px 20px; 
                      text-align: center; text-decoration: none; display: inline-block; font-size: 16px; 
                      margin: 4px 2px; cursor: pointer; border-radius: 12px;'>Click here for detailed graph</button></a>"""
    st.markdown(button_html, unsafe_allow_html=True)

    # Embedding the initial graph - replace with your actual URL
    graph_url = "https://your_initial_graph_url"
    st.markdown(f'<iframe src="{graph_url}" width="100%" height="600" frameborder="0"></iframe>', unsafe_allow_html=True)

    # Trigger the analysis of challenges
    if st.button("Analyze challenges"):
        st.session_state['analyze_challenges_clicked'] = True

    if st.session_state.get('analyze_challenges_clicked', False):
        challenge_df, tools_df = load_csv_data()
        display_challenge_analysis(challenge_df, tools_df)

# Function to display challenge analysis options and corresponding tools
def display_challenge_analysis(challenge_df, tools_df):
    # Dropdown for "Player" with "All" option, preserving selection
    player_options = ['All'] + list(challenge_df['player'].unique())
    selected_player = st.selectbox("Player", options=player_options, index=0, key='selected_player')

    # Dropdown for "Cat 2" with "All" option, preserving selection
    cat2_options = ['All'] + list(challenge_df['cat 2'].unique())
    selected_cat2 = st.selectbox("Cat 2", options=cat2_options, index=0, key='selected_cat2')

    # Apply filters based on selections
    if selected_player != 'All':
        challenge_df = challenge_df[challenge_df['player'] == selected_player]
    if selected_cat2 != 'All':
        challenge_df = challenge_df[challenge_df['cat 2'] == selected_cat2]

    # Display challenges in two columns for easier readability
    st.write("Select Challenges:")
    col1, col2 = st.columns(2)
    challenges = challenge_df['challenge'].unique()
    half = len(challenges) // 2
    selected_challenges = []
    with col1:
        for challenge in challenges[:half]:
            if st.checkbox(challenge, key=f'checkbox_{challenge}', value=False):
                selected_challenges.append(challenge)
    with col2:
        for challenge in challenges[half:]:
            if st.checkbox(challenge, key=f'checkbox_{challenge}_2', value=False):  # Ensure unique keys
                selected_challenges.append(challenge)

    # Display tools related to selected challenges in a 3x3 grid
    if selected_challenges:
        st.write("Tools for Selected Challenges:")
        filtered_tools = tools_df[tools_df['challenge'].isin(selected_challenges)]
        cols = ['A', 'B', 'C', 'D', 'E', 'F']  # Adjust column names as necessary
        selected_tools = {col: [] for col in cols}
        
        # Create a 3x3 grid for tool checkboxes
        grid_cols = st.columns(3)
        for index, col in enumerate(cols):
            with grid_cols[index % 3]:
                st.markdown(f"#### {col}")
                st.markdown("<hr>", unsafe_allow_html=True)  # Horizontal line for visual separation
                values = filtered_tools[col].dropna().unique()
                for value in values:
                    if st.checkbox(f"{value}", key=f'{col}_{value}', value=True):  # Auto-selected
                        selected_tools[col].append(value)

    # Analyze button to display selected tools and challenges
    if st.button("Analyze"):
        st.write("Selected Challenges and Tools:")
        # Display in a table
        selected_data = {"Challenges": selected_challenges}
        selected_data.update({col: selected_tools[col] for col in cols})
        st.table(pd.DataFrame(dict([(k, pd.Series(v)) for k, v in selected_data.items()])))

if __name__ == "__main__":
    main()
