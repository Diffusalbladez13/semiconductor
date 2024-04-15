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
    st.markdown("<h1 style='text-align: center;'>Semiconductor Ecosystem</h1>", unsafe_allow_html=True)

    # Detailed graph URL - replace with your actual URL
    detailed_graph_url = "https://ouestware.gitlab.io/retina/beta/#/graph/?url=https%3A%2F%2Fgist.githubusercontent.com%2FDiffusalbladez13%2F95624373e22ba0cbf9eda3660772eebc%2Fraw%2F92907a8fc8fe9ea248cb37c4d13c6ef1d4c1f65f%2Fnetwork-9b01f649-aab.gexf"
    # Fancy button for the detailed graph
    button_html = f"""<a href="{detailed_graph_url}" target="_blank">
                      <button style='color: white; background-color: #4CAF50; border: none; padding: 10px 20px; 
                      text-align: center; text-decoration: none; display: inline-block; font-size: 16px; 
                      margin: 4px 2px; cursor: pointer; border-radius: 12px;'>Click here for detailed graph</button></a>"""
    st.markdown(button_html, unsafe_allow_html=True)

    # Embedding the initial graph - replace with your actual URL
    graph_url = "https://ouestware.gitlab.io/retina/beta/#/graph/?url=https://gist.githubusercontent.com/Diffusalbladez13/5d5b8f2593120f01f9777b6421c1c117/raw/d122abbfa929be4273d4bc84431479210cbe7071/network-d00f20a4-22d.gexf"
    st.markdown(f'<iframe src="{graph_url}" width="100%" height="600" frameborder="0"></iframe>', unsafe_allow_html=True)

    # Center-align "Analyze challenges" button with styling
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Analyze challenges", key="analyze"):
            st.session_state['analyze_challenges_clicked'] = True

    if st.session_state.get('analyze_challenges_clicked', False):
        challenge_df, tools_df = load_csv_data()
        display_challenge_analysis(challenge_df, tools_df)

# Function to display challenge analysis options and corresponding tools
def display_challenge_analysis(challenge_df, tools_df):
    # Dropdown for "Player" with "All" option, preserving selection
    player_options = ['All'] + list(challenge_df['player'].unique())
    selected_player = st.selectbox("Ecosystem players", options=player_options, index=0, key='selected_player')

    # Dropdown for "Cat 2" with "All" option, preserving selection
    cat2_options = ['All'] + list(challenge_df['cat 2'].unique())
    selected_cat2 = st.selectbox("Type of Challenge", options=cat2_options, index=0, key='selected_cat2')

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
            if st.checkbox(challenge, key=f'checkbox_{challenge}_2', value=False):
                selected_challenges.append(challenge)

    # Display tools related to selected challenges in a 3x3 grid
    if selected_challenges:
        st.write("Tools for Selected Challenges:")
        filtered_tools = tools_df
        cols = ['Consumers of semiconductors', 'Education and Research Institutions', 'Financial & Legal', 'Government & Regulators', 'Industry Associations and Alliances', 'Semiconductor manufacturing']  # Adjust column names as necessary
        selected_tools = {col: [] for col in cols}
        
        # Determine the maximum number of tools in any column to ensure alignment
        max_tools = max(len(filtered_tools[col].dropna().unique()) for col in cols)
        
        # Create a 3x3 grid for tool checkboxes, ensuring top alignment for all rows
        grid_cols = st.columns(3)
        for index, col in enumerate(cols):
            with grid_cols[index % 3]:
                st.markdown(f"#### {col}")
                st.markdown("<hr>", unsafe_allow_html=True)  # Horizontal line for visual separation
                values = filtered_tools[col].dropna().unique()
                # Ensure each column creates checkboxes for the maximum number of tools
                for _ in range(max_tools):
                    if _ < len(values):
                        value = values[_]
                        # Determine if this tool should be selected by default based on the "risk" filter
                        default_selected = value in filtered_tools[filtered_tools['risk'].isin(selected_challenges)][col].unique()
                        if st.checkbox(f"{value}", key=f'{col}_{value}_{_}', value=default_selected):
                            selected_tools[col].append(value)
                    else:
                        # Create a placeholder to maintain alignment
                        st.empty()

    # Analyze button to display selected tools and challenges
    if st.button("Analyze"):
        st.write("Selected Challenges and Tools:")
        # Display in a table
        selected_data = {"Challenges": selected_challenges}
        selected_data.update({col: selected_tools[col] for col in cols})
        st.table(pd.DataFrame(dict([(k, pd.Series(v)) for k, v in selected_data.items()])))

if __name__ == "__main__":
    main()
